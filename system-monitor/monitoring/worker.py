"""Zabbix -> durable queue -> expert tables -> topology correlation, without ML."""
from collections import defaultdict
import hashlib
import json
import time
import uuid

from .correlation import correlate
from .vector import feature_vector


class Worker:
    def __init__(self, backend, catalog, topology, store, profiles, *, clock=time.time, initial_lookback=60, page_limit=200, probe_interval=30):
        self.backend, self.catalog, self.topology, self.store = backend, catalog, topology, store
        self.clock, self.initial_lookback, self.page_limit = clock, initial_lookback, page_limit
        self.probe_interval = probe_interval
        self.profiles = {profile["node"]: profile for profile in profiles}
        self.host_map = {}
        for profile in profiles:
            for host in profile.get("event_host_ids", [profile["host_id"]]):
                if str(host) in self.host_map:
                    raise ValueError("One Zabbix host maps to multiple topology nodes")
                self.host_map[str(host)] = profile["node"]

    def normalize_raw(self, result):
        if not isinstance(result, list):
            raise ValueError("Invalid event.get result")
        events=[]
        for raw in result:
            identities={str(host['hostid']) for host in raw.get('hosts',[]) if str(host['hostid']) in self.host_map}
            if len(identities)!=1 or not str(raw['eventid']).isdigit() or str(raw['value']) not in {'0','1'}:
                raise ValueError('Ambiguous/unconfigured Zabbix event; cursor unchanged')
            host_id=identities.pop();node=self.host_map[host_id]
            tags={row['tag']:row['value'] for row in raw.get('tags',[])}
            kind=self.profiles[node].get('trigger_kinds',{}).get(str(raw['objectid']),tags.get('diag.kind','unknown'))
            events.append({'source':'zabbix','event_id':str(raw['eventid']),'clock':int(raw['clock']),'node':node,'kind':kind,
                           'state':'problem' if str(raw['value'])=='1' else 'recovery','key':str(raw['objectid']),
                           'host_id':host_id,'name':raw.get('name',''),'raw':raw})
        return events

    def bootstrap(self, now):
        # A new runtime DB must also discover problems older than the lookback.
        # Backfill does not advance the chronological cursor or lose fresh events.
        if self.store.metadata('open_problems_bootstrapped'):
            return 0
        problems=self.backend.api('problem.get',{'hostids':list(self.host_map),'recent':False,'output':['eventid']})
        if not isinstance(problems,list):raise ValueError('Invalid problem.get result')
        identities=[str(row['eventid']) for row in problems]
        added=0
        for start in range(0,len(identities),200):
            raw=self.backend.api('event.get',{'eventids':identities[start:start+200],'output':['eventid','clock','objectid','value','name','severity'],
                                            'selectHosts':['hostid','host'],'selectTags':'extend'})
            added+=self.store.ingest(self.normalize_raw(raw),now)
        self.store.metadata('open_problems_bootstrapped','1')
        return added

    def poll(self, now):
        ingested, pages = self.bootstrap(now), 0
        for _ in range(20):
            cursor = self.store.cursor("zabbix")
            params = {"source": 0, "object": 0, "hostids": list(self.host_map),
                      "output": ["eventid", "clock", "objectid", "value", "name", "severity"],
                      "selectHosts": ["hostid", "host"], "selectTags": "extend", "sortfield": "eventid", "sortorder": "ASC", "limit": self.page_limit}
            if cursor:
                params["eventid_from"] = str(int(cursor) + 1)
            else:
                params["time_from"] = now - self.initial_lookback
            result = self.backend.api("event.get", params)
            if not isinstance(result, list):
                raise ValueError("Invalid event.get result")
            if not result:
                break
            events = self.normalize_raw(result)
            next_cursor = max(int(raw["eventid"]) for raw in result)
            if cursor and next_cursor <= int(cursor):
                raise ValueError("event.get page did not advance")
            ingested += self.store.ingest(events, now, stream="zabbix", cursor=next_cursor)
            pages += 1
            if len(result) < self.page_limit:
                break
        return ingested, pages

    def observe_nodes(self, now):
        observed = self.backend.node_states(self.topology)
        previous = self.store.node_states()
        events = []
        for node, value in observed.items():
            self.store.set_node_state(node, value["status"], value["observed_at"], value["evidence"])
            old = previous.get(node, {}).get("status")
            if value["status"] in {"up", "down"} and old != value["status"] and (value["status"] == "down" or old == "down"):
                events.append({"source": "probe", "event_id": uuid.uuid4().hex, "clock": value["observed_at"], "node": node,
                               "kind": "reachability", "state": "problem" if value["status"] == "down" else "recovery",
                               "key": node + ":availability", "evidence": value["evidence"]})
        return self.store.ingest(events, now)

    def cycle(self, *, force_collect=False):
        started = int(self.clock())
        added, pages = self.poll(started)
        added += self.observe_nodes(started)
        jobs = defaultdict(list)
        for event in self.store.pending_jobs(int(self.clock())):
            jobs[event["node"]].append(event)
        last_refresh = int(self.store.metadata("last_full_probe") or 0)
        refresh = force_collect or self.probe_interval > 0 and started - last_refresh >= self.probe_interval
        if refresh:
            for node in self.profiles:
                jobs.setdefault(node, [])
        diagnostics = []
        states = self.store.node_states()
        for node, pending in jobs.items():
            profile = self.profiles[node]
            try:
                observation = self.backend.collect(profile)
                parent = self.topology.parent(node)
                state = states.get(parent, {}) if parent else {"status": "not_applicable"}
                parent_status = state.get("status", "unknown")
                if parent and not (type(state.get("observed_at")) is int and 0 <= observation["decision_time"] - state["observed_at"] <= self.catalog.metadata["policy"]["max_age"]):
                    parent_status = "unknown"
                assessment = self.catalog.assess(profile, observation["evidence"], observation["decision_time"], parent_status=parent_status,
                                                 window_alert_count=sum(event["state"] == "problem" and not self.topology.is_notice(event) and observation["decision_time"] - self.catalog.metadata["correlation_window_seconds"] < event["clock"] <= observation["decision_time"] for event in self.store.events()))
                assessment["feature_vector"] = feature_vector(assessment["facts"], self.catalog.metadata["policy"])
                diagnostic_id = self.store.save_diagnostic(profile["profile_id"], observation, assessment)
                diagnostics.append({"id": diagnostic_id, "node": node, "jobs": len(pending), "assessment": assessment})
                if any(value["status"] == "error" for value in observation["sources"].values()):
                    self.store.retry_jobs(pending, int(self.clock()), "PartialSourceError")
                else:
                    self.store.complete_jobs(pending, diagnostic_id)
            except Exception as error:
                self.store.retry_jobs(pending, int(self.clock()), type(error).__name__)
                diagnostics.append({"node": node, "error_type": type(error).__name__})
        if refresh:
            self.store.metadata("last_full_probe", str(started))
        now = int(self.clock())
        events = self.store.events()
        # Direct local service observations are independent measurements, not
        # inferred from the same failed remote connection that gets suppressed.
        for diagnostic in diagnostics:
            assessment = diagnostic.get("assessment")
            if not assessment:
                continue
            node = diagnostic["node"]
            facts = assessment["facts"]
            for field, kind in (("local_service_state", "http_service"), ("local_agent_state", "agent_service")):
                state = facts.get(field)
                if state not in {"active", "inactive", "failed"}:
                    continue
                cache_key = node + ":" + kind
                old = self.store.metadata(cache_key)
                new = "problem" if state in {"inactive", "failed"} else "recovery"
                if new != old and (new == "problem" or old == "problem"):
                    event = {"source": "local_service_probe", "event_id": uuid.uuid4().hex, "clock": now, "node": node, "kind": kind,
                             "state": new, "key": cache_key, "independent_fault": True, "diagnostic_id": diagnostic["id"]}
                    self.store.ingest([event], now)
                    self.store.complete_jobs([event], diagnostic["id"])
                    self.store.metadata(cache_key, new)
        events = self.store.events()
        correlation = correlate(events, self.topology, self.store.node_states(), now, window_seconds=self.catalog.metadata["correlation_window_seconds"])
        fingerprint_input = [{"id": group["group_id"], "members": group["members"],
                              "root_status": (group.get("root_status_evidence") or {}).get("status")}
                             for group in correlation["groups"]]
        fingerprint = hashlib.sha256(json.dumps({"groups":fingerprint_input,"notices":correlation["notices"]}, sort_keys=True).encode()).hexdigest()
        changed = added > 0 or self.store.metadata("correlation_fingerprint") != fingerprint
        if changed:
            self.store.save_batch(correlation)
            self.store.metadata("correlation_fingerprint", fingerprint)
        return {"status": "CYCLE_COMPLETE", "started_at": started, "decision_time": now, "ingested_events": added,
                "api_pages": pages, "diagnostics": diagnostics, "correlation": correlation,
                "store_counts": self.store.counts(), "changed": changed,
                "scope": "Expert SQLite and correlation only; no ML training, remediation or alert deletion"}

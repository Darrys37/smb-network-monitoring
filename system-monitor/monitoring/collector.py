"""Label-free evidence collection using local Zabbix reads and restricted SSH probes."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import importlib
import ipaddress
import json
from pathlib import Path
import socket
import subprocess
import sys
import time

from . import probes


class NativeBackend:
    def __init__(self, engine_source, remote_config, *, clock=time.time):
        self.clock = clock
        self.remote_config = remote_config
        sys.path.insert(0, str(Path(engine_source).resolve()))
        self.client = importlib.import_module("zabbix_client")
        self.metric_module = importlib.import_module("roadmap_evidence")
        self.request_id = 50000

    def api(self, method, params):
        self.request_id += 1
        return self.client.call_api(method, params, self.request_id)

    def request_probe(self, observer, request):
        request = {**request, "expected_observer": observer}
        if observer == socket.gethostname().split(".")[0].lower():
            return probes.dispatch(request)
        host = self.remote_config[observer]
        ipaddress.IPv4Address(host["address"])
        command = ["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=4", "-o", "StrictHostKeyChecking=yes",
                   "-i", host["key_file"], "phat@" + host["address"]]
        response = subprocess.run(command, input=json.dumps(request), capture_output=True, text=True, timeout=12)
        if response.returncode or len(response.stdout) > 65536:
            raise RuntimeError("Remote read-only probe unavailable")
        result = json.loads(response.stdout)
        if isinstance(result, dict) and result.get("status") == "source_error":
            raise RuntimeError("Remote read-only probe failed")
        return result

    def metrics(self, profile):
        metric_host = profile.get("metrics_host_id", profile["host_id"])
        agent_host = profile.get("agent_host_id", profile["host_id"])
        rows = self.metric_module.collect_roadmap_metrics(metric_host)
        if agent_host != metric_host:
            rows = [row for row in rows if row.check_type != "agent_metric"]
            rows.append(self.metric_module.collect_agent_metric(agent_host))
        return [asdict(row) for row in rows]

    def collect(self, profile):
        started = int(self.clock())
        target = str(ipaddress.IPv4Address(profile["target_ip"]))
        rows = [probes.ping(target, "mon01"), probes.tcp(target, 80, "mon01"), probes.tcp(target, 10050, "mon01")]
        if profile.get("control_ip") and profile["control_ip"] != target:
            rows.append(probes.ping(profile["control_ip"], "mon01"))
        sources = {}
        tasks = {"monitor_metrics": lambda: self.metrics(profile),
                 "dns": lambda: self.request_probe(profile["dns_observer"], {"operation": "dns", "name": profile["dns_name"], "control_ip": profile["dns_control_ip"]})}
        if profile["http_service"] == "expected":
            tasks["local_http"] = lambda: self.request_probe(profile["http_observer"], {"operation": "http", "target": target})
        for key, task in tasks.items():
            try:
                result = task()
                if not isinstance(result, list):
                    raise ValueError("Invalid source response")
                rows.extend(result)
                sources[key] = {"status": "ok", "error_type": None}
            except Exception as error:
                sources[key] = {"status": "error", "error_type": type(error).__name__}
        return {"schema_version": 3, "profile": profile, "started_at": started, "decision_time": int(self.clock()),
                "evidence": rows, "sources": sources, "observer": "mon01"}

    def node_states(self, topology):
        def observe(item):
            name, node = item
            ping = probes.ping(node["address"], "mon01")
            tcp = probes.tcp(node["address"], 22, "mon01")
            positive = ping["result"]["status"] == "success" or tcp["result"]["status"] in {"success", "refused"}
            negative = ping["result"]["status"] == "no_reply" and tcp["result"]["status"] == "timeout"
            state = "up" if positive else "down" if negative else "unknown"
            details = {"ping": ping, "tcp22": tcp}
            if node["type"] == "gateway" and state == "up":
                try:
                    ready = self.request_probe(name, {"operation": "routing", "interface": node["backend_interface"], "target": node["backend_target"]})
                    details["routing"] = ready
                    state = "up" if ready["ready"] is True else "down"
                except Exception as error:
                    state = "unknown"
                    details["source_error"] = type(error).__name__
            return name, {"status": state, "observed_at": int(self.clock()), "evidence": details}
        nodes = [(key, value) for key, value in topology.nodes.items() if value["type"] in {"host", "gateway"}]
        with ThreadPoolExecutor(max_workers=3) as pool:
            return dict(pool.map(observe, nodes))

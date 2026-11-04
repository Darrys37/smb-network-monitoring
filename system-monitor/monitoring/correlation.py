"""Time-window correlation with auditable suppression and independent faults."""
import hashlib
import json


def event_order(event):
    identity = str(event["event_id"])
    return (event["clock"], event["source"], (0, int(identity)) if identity.isdigit() else (1, identity))


def normalize_event(event):
    required = {"source", "event_id", "clock", "node", "kind", "state", "key"}
    if not required <= set(event) or type(event["clock"]) is not int or event["clock"] < 0:
        raise ValueError("Invalid normalized event")
    if any(not isinstance(event[key], str) or not event[key] for key in required - {"clock"}):
        raise ValueError("Invalid event identifier")
    if event["state"] not in {"problem", "recovery"}:
        raise ValueError("Invalid event state")
    return {**event, "event_id": str(event["event_id"])}


def correlate(events, topology, node_states, now, *, window_seconds=30, max_age=180):
    if type(now) is not int or window_seconds <= 0:
        raise ValueError("Invalid correlation clock/window")
    unique = {}
    for item in events:
        event = normalize_event(item)
        if event["node"] not in topology.nodes or event["clock"] > now + 5:
            raise ValueError("Unknown topology node or future event")
        key = (event["source"], event["event_id"])
        immutable = {key: event[key] for key in ("clock", "node", "kind", "state", "key")}
        if key in unique and any(unique[key][field] != value for field, value in immutable.items()):
            raise ValueError("One event ID has conflicting immutable fields")
        unique[key] = event
    ordered = sorted(unique.values(), key=event_order)
    latest = {}
    for event in ordered:
        latest[(event["source"], event["key"])] = event
    all_active = [event for event in latest.values() if event["state"] == "problem"]
    notices = [event for event in all_active if topology.is_notice(event)]
    active = [event for event in all_active if not topology.is_notice(event)]
    local_http_failures = [event for event in active if event["kind"] == "http_service" and event.get("independent_fault") is True]

    def down(name):
        state = node_states.get(name, {})
        observed = state.get("observed_at")
        since = state.get("down_since")
        return (state.get("status") == "down" and type(observed) is int and 0 <= now - observed <= max_age
                and type(since) is int and 0 <= since <= observed)

    groups = {}
    for event in sorted(active, key=event_order):
        node = event["node"]
        root, cause = node, event["kind"]
        can_depend = event["kind"] in topology.dependent_kinds and event.get("independent_fault") is not True
        if can_depend:
            # The highest confirmed failed ancestor takes precedence. A much
            # older child incident is not retroactively blamed on a new outage.
            failed = [parent for parent in topology.ancestors(node)
                      if down(parent) and event["clock"] >= node_states[parent]["down_since"] - window_seconds]
            if failed:
                root, cause = failed[-1], "dependency"
            elif down(node):
                cause = "dependency"
            elif event["kind"] == "http_connectivity" and any(service["node"] == node and abs(service["clock"] - event["clock"]) <= window_seconds for service in local_http_failures):
                cause = "http_service"
        suppressed = root != node
        key = (root, cause)
        if key not in groups:
            identifier = hashlib.sha256((topology.version + "\0" + root + "\0" + cause).encode()).hexdigest()[:24]
            groups[key] = {"group_id": identifier, "root_node": root, "cause_group": cause,
                           "root_status_evidence": node_states.get(root), "members": [], "derived_root": True}
        groups[key]["members"].append({"source": event["source"], "event_id": event["event_id"], "node": node,
                                      "kind": event["kind"], "clock": event["clock"], "suppressed": suppressed,
                                      "reason": "Fresh parent-down evidence and a configured dependency path" if suppressed else "Independent/root alert retained",
                                      "dependency_path": topology.path(node, root) if suppressed else [node]})
        if node == root:
            groups[key]["derived_root"] = False
    problems = [event for event in ordered if event["state"] == "problem" and not topology.is_notice(event)]
    clocks = [event["clock"] for event in problems]
    left, peak = 0, 0
    for right, clock in enumerate(clocks):
        while clock - clocks[left] >= window_seconds:
            left += 1
        peak = max(peak, right - left + 1)
    output = sorted(groups.values(), key=lambda group: (group["root_node"], group["cause_group"]))
    return {"decision_time": now, "topology_version": topology.version, "window_seconds": window_seconds,
            "active_total_problem_events": len(all_active), "active_notice_events": len(notices),
            "notices": [{key: event.get(key) for key in ("source", "event_id", "node", "key", "name", "clock")} for event in notices],
            "raw_unique_events": len(ordered), "distinct_problem_events": len(problems), "active_problem_events": len(active),
            "recent_problem_events": sum(now - window_seconds < event["clock"] <= now for event in problems),
            "peak_window_event_count": peak, "emitted_groups": len(output),
            "suppressed_events": sum(member["suppressed"] for group in output for member in group["members"]), "groups": output,
            "raw_retained": True, "confidence_kind": "topology_and_fresh_evidence_correlation_not_proof_of_unique_physical_cause"}

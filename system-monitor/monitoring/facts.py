"""Normalize measurement quality; incident conditions belong in SQLite tables."""
import math


def latest(records, kind, target, now, max_age, **filters):
    rows = [row for row in records if row["check_type"] == kind and row["target"] == str(target)
            and all(row["result"].get(key) == value for key, value in filters.items())]
    if not rows:
        return None
    row = max(rows, key=lambda item: item["collected_at"])
    clock = row["collected_at"]
    return row["result"] if type(clock) is int and 0 <= now - clock <= max_age else None


def cpu_samples(history, now, policy):
    samples = history.get("samples", [])
    if len(samples) < policy["cpu_min_samples"]:
        raise ValueError("Too few CPU samples")
    clocks = [sample["clock"] for sample in samples]
    values = [sample["value"] for sample in samples]
    if any(type(clock) is not int or not now - policy["cpu_sample_max_age"] <= clock <= now for clock in clocks):
        raise ValueError("Invalid CPU sample clock")
    if any(type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 100 for value in values):
        raise ValueError("Invalid CPU percentage")
    if clocks != sorted(set(clocks)) or clocks[-1] - clocks[0] < policy["cpu_min_coverage"] or now - clocks[-1] > policy["max_age"]:
        raise ValueError("CPU samples unordered, sparse or stale")
    if any(b - a > policy["cpu_max_gap"] for a, b in zip(clocks, clocks[1:])):
        raise ValueError("CPU sample gap too large")
    return sum(values) / len(values), clocks[-1] - clocks[0]


def cpu_support(history, now, policy):
    items = history["support_items"]
    count_item, load_item = items["system.cpu.num"], items["system.cpu.load[all,avg1]"]
    for item, age in ((count_item, policy["cpu_count_max_age"]), (load_item, policy["max_age"])):
        if item["status"] != "0" or item["state"] != "0" or not 0 <= now - int(item["lastclock"]) <= age:
            raise ValueError("Invalid CPU corroboration freshness")
    count, load = float(count_item["lastvalue"]), float(load_item["lastvalue"])
    if not math.isfinite(count) or not count.is_integer() or count < 1 or not math.isfinite(load) or load < 0:
        raise ValueError("Invalid CPU count/load")
    return count, load


def extract(profile, records, now, policy, *, parent_status="unknown", window_alert_count=0):
    if profile.get("http_service", "unknown") not in {"expected", "absent", "unknown"}:
        raise ValueError("Invalid HTTP service scope")
    rows = [row if isinstance(row, dict) else {"check_type": row.check_type, "target": row.target,
            "collected_at": row.collected_at, "result": row.result} for row in records]
    get = lambda kind, target, **filters: latest(rows, kind, target, now, policy["max_age"], **filters)
    status = lambda row, allowed: row.get("status") if row and row.get("status") in allowed else None
    target, host = profile["target_ip"], profile["host_id"]
    ping = get("ping", target)
    tcp = get("tcp", target, port=80)
    tcp_agent = get("tcp", target, port=10050)
    control = get("ping", profile.get("control_ip")) if profile.get("control_ip") and profile["control_ip"] != target else None
    agent = get("agent_metric", profile.get("agent_host_id", host), key="agent.ping")
    service = get("service_state", target, observer=profile.get("http_observer", "srv01"), service="nginx")
    local_agent = get("service_state", target, observer=profile.get("http_observer", "srv01"), service="zabbix-agent2")
    local = get("local_http", target, observer=profile.get("http_observer", "srv01"), port=80, path="/")
    local_status = None
    if local and local.get("local_address_verified") is True:
        if local.get("status") == "success" and type(local.get("http_status")) is int and local["http_status"] == 200:
            local_status = "success"
        elif local.get("status") == "failed" and local.get("http_status") != 200:
            local_status = "failed"
    dns_name = profile.get("dns_name")
    dns_observer = profile.get("dns_observer", "cli01")
    dns_target = dns_name.lower().rstrip(".") if dns_name else None
    dns = get("dns", dns_target, observer=dns_observer, record_type="A") if dns_target else None
    dns_control = get("dns_control_ping", profile.get("dns_control_ip") or target, observer=dns_observer)
    dns_tcp = get("dns_control_tcp", profile.get("dns_control_ip") or target, observer=dns_observer, port=443)
    dns_connectivity = status(dns_control, {"success", "no_reply"})
    if dns_tcp and dns_tcp.get("status") in {"success", "refused"}:
        dns_connectivity = "success"
    metrics_host = profile.get("metrics_host_id", host)
    history = get("cpu_history", metrics_host, key="system.cpu.util")
    def metric(key):
        item = get("metric", metrics_host, key=key)
        if not item or item.get("status") != "success" or item.get("units") != "%":
            return None
        clock, value = item.get("sample_clock"), item.get("value")
        try:
            value = float(value)
        except (ValueError, TypeError):
            return None
        return value if type(clock) is int and 0 <= now-clock <= policy["max_age"] and math.isfinite(value) and 0 <= value <= 100 else None
    facts = {"target_ping": status(ping, {"success", "no_reply"}), "target_tcp80": status(tcp, {"success", "refused", "timeout"}),
             "agent_tcp": status(tcp_agent, {"success", "refused", "timeout"}),
             "control_ping": status(control, {"success", "no_reply"}), "local_http": local_status,
             "http_service": profile.get("http_service", "unknown"), "agent_present": agent is not None,
             "agent_status": agent.get("status") if agent else None,
             "dns_configured": bool(dns_name), "dns_present": dns is not None, "dns_status": dns.get("status") if dns else None,
             "dns_code": dns.get("dns_status") if dns else None, "dns_answers": bool(dns.get("addresses")) if dns else False,
             "dns_control": dns_connectivity, "dns_observer": dns_observer,
             "local_service_state": service.get("state") if service and service.get("status") == "success" else None,
             "local_agent_state": local_agent.get("state") if local_agent and local_agent.get("status") == "success" else None,
             "dns_response_time_ms": dns.get("response_time_ms") if dns else None,
             "http_status_code": local.get("http_status") if local else None,
             "cpu_history_present": history is not None, "cpu_history_status": history.get("status") if history else None,
             "cpu_units": history.get("units") if history else None, "cpu_samples_valid": False,
             "cpu_support_valid": False, "cpu_mean": None, "cpu_span": None, "cpu_count": None, "cpu_load": None,
             "cpu_percent": metric("system.cpu.util"), "ram_percent": metric("vm.memory.util"),
             "parent_status": parent_status, "window_alert_count": window_alert_count,
             "max_age": policy["max_age"], "cpu_min_coverage": policy["cpu_min_coverage"],
             "cpu_max_gap": policy["cpu_max_gap"], "cpu_high_percent": policy["cpu_high_percent"],
             "cpu_count_max_age": policy["cpu_count_max_age"]}
    if history:
        try:
            facts["cpu_mean"], facts["cpu_span"] = cpu_samples(history, now, policy)
            facts["cpu_samples_valid"] = True
        except (KeyError, TypeError, ValueError):
            pass
        try:
            facts["cpu_count"], facts["cpu_load"] = cpu_support(history, now, policy)
            facts["cpu_support_valid"] = True
        except (KeyError, TypeError, ValueError):
            pass
    return facts

"""Seven public feature groups; retain raw CPU/RAM and quality separately."""


def feature_vector(facts, policy):
    cpu, ram = facts["cpu_percent"], facts["ram_percent"]
    resource = "unknown"
    if cpu is not None and ram is not None:
        cpu_high, ram_high = cpu >= policy["cpu_high_percent"], ram >= policy.get("ram_high_percent", 90)
        resource = "cpu_ram_high" if cpu_high and ram_high else "cpu_high" if cpu_high else "ram_high" if ram_high else "normal"
    agent = "unavailable" if facts.get("local_agent_state") in {"inactive", "failed"} else "available" if facts.get("agent_status") == "success" else "unavailable" if facts.get("agent_status") == "no_data" and facts.get("agent_tcp") in {"refused", "timeout"} else "unknown"
    return {"schema": "system-vector-v3.0", "features": {
        "icmp_status": facts["target_ping"] or "unknown", "tcp80_status": facts["target_tcp80"] or "unknown",
        "http_status_code": facts["http_status_code"], "dns_response_time_ms": facts["dns_response_time_ms"],
        "resource_status": resource, "agent_availability": agent, "parent_status": facts["parent_status"]},
        "raw_resources": {"cpu_percent": cpu, "ram_percent": ram, "cpu_mean": facts["cpu_mean"], "cpu_samples_valid": facts["cpu_samples_valid"]},
        "note": "Resource status summarizes current CPU/RAM percentages; sustained overload is separately checked by the expert table. No old ML model is retrained or silently fed this new schema."}

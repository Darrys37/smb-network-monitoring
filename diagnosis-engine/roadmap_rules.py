"""Roadmap R1-R6. Suspicions are not assertions of a unique root cause.

Original rules.py remains available for reproducing previously saved dossiers.
"""
import math
import time
from models import DiagnosisRecord


def result(rule, matched=None, reason="", missing=(), actions=()):
    return DiagnosisRecord(rule,
        "insufficient_evidence" if matched is None else "matched" if matched else "not_matched",
        reason if matched else None, reason,
        tuple(missing), tuple(actions))


def latest(records, kind, target, now, **filters):
    candidates = [r for r in records if r.check_type == kind and r.target == str(target)
                  and all(r.result.get(k) == v for k, v in filters.items())]
    if not candidates:
        return None
    r = max(candidates, key=lambda r: r.collected_at)
    if type(r.collected_at) is not int or not 0 <= now - r.collected_at <= 180:
        return None
    return r.result


def ping(records, target, now):
    r = latest(records, "ping", target, now)
    return r.get("status") if r and r.get("status") in ("success", "no_reply") else None


def tcp(records, target, now, port=80):
    r = latest(records, "tcp", target, now, port=port)
    return r.get("status") if r and r.get("status") in ("success", "refused", "timeout") else None


def r1(target, control, records, now):
    rule = "R1_HOST_OR_LOCAL_CONNECTIVITY"
    p, t = ping(records, target, now), tcp(records, target, now)
    if p == "success" or t in ("success", "refused"):
        return result(rule, False, "Target responded to ICMP or TCP.")
    g = ping(records, control, now) if control and control != target else None
    if None in (p, t, g):
        return result(rule, reason="Cannot isolate target/local connectivity.",
                      missing=("Fresh target ping/TCP and a distinct same-subnet control host ping.",))
    matched = p == "no_reply" and t == "timeout" and g == "success"
    return result(rule, matched, f"Target ping={p}, TCP={t}; control host ping={g}.",
                  missing=("Target console, route and firewall state; compare from CLI01.",) if matched else (),
                  actions=("Inspect target console and local network path.",) if matched else ())


def local_http(records, target, observer, now):
    r = latest(records, "local_http", target, now, observer=observer, port=80, path="/")
    if not r or r.get("local_address_verified") is not True:
        return None
    if r.get("status") == "success" and type(r.get("http_status")) is int and r["http_status"] == 200:
        return "success"
    if r.get("status") == "failed" and r.get("http_status") != 200:
        return "failed"
    return None


def r2(target, records, now, observer="srv01"):
    rule = "R2_HTTP_SERVICE_SUSPECTED"
    p, t = ping(records, target, now), tcp(records, target, now)
    if None in (p, t):
        return result(rule, reason="Missing usable ping/TCP evidence.", missing=("Fresh ping and TCP port 80.",))
    if p != "success" or t == "success":
        return result(rule, False, f"Target ping={p}, TCP80={t}.")
    local = local_http(records, target, observer, now)
    if local == "success":
        return result(rule, False, "HTTP200 on the target's own service IP; a simple stopped-service hypothesis is not supported. Check R5.")
    if t == "timeout" and local is None:
        return result(rule, reason="Remote TCP timeout alone cannot distinguish service and access-path failure.",
                      missing=("Fresh local HTTP probe from the service host.",))
    return result(rule, True, f"Host ping works; TCP80={t}; local HTTP={local}. Service/listener or active rejection suspected.",
                  missing=("Service state, listening sockets and firewall policy; refusal alone does not prove nginx stopped.",),
                  actions=("On target inspect systemctl status nginx, ss -lntp and firewall rules.",))


def r3(host_id, target, records, now):
    rule = "R3_AGENT_UNAVAILABLE"
    p = ping(records, target, now)
    a = latest(records, "agent_metric", host_id, now, key="agent.ping")
    t = tcp(records, target, now, port=10050)
    if a and a.get("status") == "success":
        return result(rule, False, "A recent agent.ping sample exists.")
    if p is None or not a or a.get("status") != "no_data" or t is None:
        return result(rule, reason="Cannot establish agent unavailability.",
                      missing=("Enabled usable agent.ping with no recent data, target ping and passive TCP10050 probe.",))
    matched = p == "success" and t in ("refused", "timeout")
    return result(rule, matched, f"Host ping={p}, agent.ping has no recent data, TCP10050={t}.",
                  missing=("Agent mode, Server allow-list, service and firewall state.",) if matched else (),
                  actions=("Inspect zabbix-agent2 service and its logs; do not assume service stopped.",) if matched else ())


def r4(name, observer, control_ip, records, now):
    rule = "R4_DNS_RESOLVER_SUSPECTED"
    if not name:
        return result(rule, reason="DNS target not configured.", missing=("Actual application name and CLI01 DNS evidence.",))
    d = latest(records, "dns", name.lower().rstrip("."), now,
               observer=observer, record_type="A")
    p = latest(records, "dns_control_ping", control_ip, now, observer=observer)
    if not d or not p or p.get("status") not in ("success", "no_reply"):
        return result(rule, reason="DNS and IP control must be fresh and from the same intended observer.",
                      missing=("Run dns_probe.py on CLI01 for the configured name and control IP.",))
    status = d.get("status")
    code = d.get("dns_status")
    usable = ((status == "success" and code == "NOERROR" and bool(d.get("addresses")))
              or (status == "no_answer" and code == "NOERROR")
              or (status == "nxdomain" and code == "NXDOMAIN")
              or (status == "dns_error" and code in ("SERVFAIL", "REFUSED"))
              or status == "timeout")
    if not usable:
        return result(rule, reason="DNS collector did not produce an interpretable result.",
                      missing=("DNS response or timeout, not a missing executable/local command error.",))
    if status == "success":
        return result(rule, False, "DNS returned an A answer; this does not validate the expected IP.")
    if p["status"] != "success":
        return result(rule, reason="IP control also failed; DNS-specific failure is not isolated.",
                      missing=("Working IP connectivity from the same observer.",))
    return result(rule, True, f"IP control works on {observer}; DNS status={status}, rcode={code}.",
                  missing=("Expected name/IP, intended resolver and resolver configuration; NXDOMAIN may be a spelling/name issue.",),
                  actions=("Compare CLI01 resolver settings and query the intended resolver.",))


def r5(target, records, now, observer="srv01"):
    rule = "R5_HTTP_ACCESS_FILTER_SUSPECTED"
    p, t = ping(records, target, now), tcp(records, target, now)
    if t == "success" or p == "no_reply":
        return result(rule, False, "No isolated remote HTTP connection failure with working ICMP.")
    local = local_http(records, target, observer, now)
    if p is None or t is None or local is None:
        return result(rule, reason="Need remote ping/TCP and fresh HTTP evidence from the service host.",
                      missing=("Run http_probe.py on SRV01 and import its fresh JSON with --http-evidence.",))
    matched = p == "success" and t in ("timeout", "refused") and local == "success"
    reason = (
        f"Remote ping={p}, TCP80={t}; "
        f"HTTP on target's own service IP={local}. "
    )
    if matched:
        reason += (
            "Filtering/access-path failure is suspected, "
            "not proven firewall causation."
        )
    else:
        reason += (
            "The evidence does not meet R5 conditions "
            "for suspected filtering/access-path failure."
        )

    return result(
        rule, matched, reason,
        missing=(
            "Read firewall rules and relevant packet counters; "
            "compare another remote observer. Local HTTP does not "
            "traverse the same ingress path.",
        ) if matched else (),
        actions=(
            "Inspect SRV01 firewall and routes; compare HTTP from "
            "CLI01 before attributing cause.",
        ) if matched else (),
    )


def r6(host_id, records, now):
    rule = "R6_SUSTAINED_CPU_HIGH"
    h = latest(records, "cpu_history", host_id, now, key="system.cpu.util")
    if not h or h.get("status") != "success" or h.get("units") != "%":
        return result(rule, reason="No usable CPU history.", missing=("CPU percentage history over the last five minutes.",))
    samples = h.get("samples", [])
    try:
        if len(samples) < 3:
            raise ValueError()
        clocks = [s["clock"] for s in samples]
        values = [s["value"] for s in samples]
        if any(type(c) is not int or not now - 480 <= c <= now for c in clocks):
            raise ValueError()
        if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 100 for v in values):
            raise ValueError()
        if clocks != sorted(set(clocks)) or clocks[-1] - clocks[0] < 240 or now - clocks[-1] > 180:
            raise ValueError()
        if any(b-a > 120 for a, b in zip(clocks, clocks[1:])):
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        return result(rule, reason="CPU history is sparse, stale or invalid.",
                      missing=("At least 240s coverage, max 120s gap, latest sample <=180s old.",))
    mean = sum(values) / len(values)
    if mean < 90:
        return result(rule, False, f"Mean CPU={mean:.2f}%; below 90%.")
    try:
        support = h["support_items"]
        count_item, load_item = support["system.cpu.num"], support["system.cpu.load[all,avg1]"]
        # Lab: CPU count has a 1-day heartbeat; allow 180s grace.
        # CPU load changes rapidly and must remain fresh.
        for item, max_age in (
            (count_item, 86400 + 180),
            (load_item, 180),
        ):
            age = now - int(item["lastclock"])
            if (
                item["status"] != "0"
                or item["state"] != "0"
                or not 0 <= age <= max_age
            ):
                raise ValueError()
        count, load = float(count_item["lastvalue"]), float(load_item["lastvalue"])
        if not math.isfinite(count) or not count.is_integer() or count < 1 or not math.isfinite(load) or load < 0:
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        return result(rule, reason="CPU stays high, but load/cpu-count corroboration is missing.",
                      missing=("Usable CPU count <=86580s old (1d heartbeat + 180s grace) and CPU load <=180s old.",))
    matched = load >= count
    return result(rule, matched, f"Mean CPU={mean:.2f}% over {clocks[-1]-clocks[0]}s; threshold=90%; load={load:.2f}, CPUs={count:g}.",
                  missing=("Response-time baseline and top processes; CPU and load suggest but do not prove overload.",) if matched else (),
                  actions=("Compare load and response time; inspect top processes.",) if matched else ())


def diagnose_roadmap(host_id, target, records, control=None,
                     dns_name=None, dns_observer="cli01", control_ip=None, now=None,
                     http_observer="srv01"):
    now = int(time.time()) if now is None else now
    records = list(records)
    return [r1(target, control, records, now), r2(target, records, now, http_observer),
            r3(host_id, target, records, now),
            r4(dns_name, dns_observer, control_ip or target, records, now),
            r5(target, records, now, http_observer), r6(host_id, records, now)]

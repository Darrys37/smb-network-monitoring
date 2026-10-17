"""Roadmap R1-R6. Suspicions are not assertions of a unique root cause.

Original rules.py remains available for reproducing previously saved dossiers.
"""

import math
import time

from models import DiagnosisRecord
from policy import (
    CPU_COUNT_MAX_AGE_SECONDS,
    CPU_HIGH_PERCENT,
    CPU_MAX_GAP_SECONDS,
    CPU_MIN_COVERAGE_SECONDS,
    CPU_MIN_SAMPLES,
    CPU_SAMPLE_MAX_AGE_SECONDS,
    DEFAULT_HTTP_SERVICE,
    EVIDENCE_MAX_AGE_SECONDS,
    HTTP_SERVICE_SCOPES,
)


def result(rule, matched=None, reason="", missing=(), actions=()):
    """Build the same three-state output for every roadmap rule."""
    if matched is None:
        status = "insufficient_evidence"
    elif matched:
        status = "matched"
    else:
        status = "not_matched"
    return DiagnosisRecord(
        rule_id=rule,
        status=status,
        probable_cause=reason if matched else None,
        reasoning=reason,
        missing_info=tuple(missing),
        next_actions=tuple(actions),
    )


def latest(records, kind, target, now, **filters):
    """Select newest matching result, then check age; never hide a newer error."""
    candidates = [
        record
        for record in records
        if record.check_type == kind
        and record.target == str(target)
        and all((record.result.get(k) == v for k, v in filters.items()))
    ]
    if not candidates:
        return None
    record = max(candidates, key=lambda record: record.collected_at)
    if (
        type(record.collected_at) is not int
        or not 0 <= now - record.collected_at <= EVIDENCE_MAX_AGE_SECONDS
    ):
        return None
    return record.result


def ping(records, target, now):
    """Return only interpretable ICMP outcomes, otherwise None."""
    record = latest(records, "ping", target, now)
    return (
        record.get("status") if record and record.get("status") in ("success", "no_reply") else None
    )


def tcp(records, target, now, port=80):
    """Keep refusal distinct from timeout; other collector errors are unusable."""
    record = latest(records, "tcp", target, now, port=port)
    return (
        record.get("status")
        if record and record.get("status") in ("success", "refused", "timeout")
        else None
    )


def r1(target, control, records, now):
    """R1: isolate target connectivity using a distinct control host."""
    rule = "R1_HOST_OR_LOCAL_CONNECTIVITY"
    target_ping, target_tcp = (ping(records, target, now), tcp(records, target, now))
    if target_ping == "success" or target_tcp in ("success", "refused"):
        return result(rule, False, "Target responded to ICMP or TCP.")
    control_ping = ping(records, control, now) if control and control != target else None
    if None in (target_ping, target_tcp, control_ping):
        return result(
            rule,
            reason="Cannot isolate target/local connectivity.",
            missing=("Fresh target ping/TCP and a distinct same-subnet control host ping.",),
        )
    matched = target_ping == "no_reply" and target_tcp == "timeout" and (control_ping == "success")
    return result(
        rule,
        matched,
        f"Target ping={target_ping}, TCP={target_tcp}; control host ping={control_ping}.",
        missing=("Target console, route and firewall state; compare from CLI01.",)
        if matched
        else (),
        actions=("Inspect target console and local network path.",) if matched else (),
    )


def local_http(records, target, observer, now):
    """Interpret a verified probe of the host's own HTTP service address."""
    record = latest(records, "local_http", target, now, observer=observer, port=80, path="/")
    if not record or record.get("local_address_verified") is not True:
        return None
    if (
        record.get("status") == "success"
        and type(record.get("http_status")) is int
        and (record["http_status"] == 200)
    ):
        return "success"
    if record.get("status") == "failed" and record.get("http_status") != 200:
        return "failed"
    return None


def r2(target, records, now, observer="srv01"):
    """R2: suspect service/listener failure only when HTTP is applicable."""
    rule = "R2_HTTP_SERVICE_SUSPECTED"
    target_ping, target_tcp = (ping(records, target, now), tcp(records, target, now))
    if None in (target_ping, target_tcp):
        return result(
            rule,
            reason="Missing usable ping/TCP evidence.",
            missing=("Fresh ping and TCP port 80.",),
        )
    if target_ping != "success" or target_tcp == "success":
        return result(rule, False, f"Target ping={target_ping}, TCP80={target_tcp}.")
    local = local_http(records, target, observer, now)
    if local == "success":
        return result(
            rule,
            False,
            "HTTP200 on the target's own service IP; a simple stopped-service hypothesis is not supported. Check R5.",
        )
    if target_tcp == "timeout" and local is None:
        return result(
            rule,
            reason="Remote TCP timeout alone cannot distinguish service and access-path failure.",
            missing=("Fresh local HTTP probe from the service host.",),
        )
    return result(
        rule,
        True,
        f"Host ping works; TCP80={target_tcp}; local HTTP={local}. Service/listener or active rejection suspected.",
        missing=(
            "Service state, listening sockets and firewall policy; refusal alone does not prove nginx stopped.",
        ),
        actions=("On target inspect systemctl status nginx, ss -lntp and firewall rules.",),
    )


def r3(host_id, target, records, now):
    """R3: compare host reachability, stale agent data and passive agent TCP."""
    rule = "R3_AGENT_UNAVAILABLE"
    target_ping = ping(records, target, now)
    agent = latest(records, "agent_metric", host_id, now, key="agent.ping")
    agent_tcp = tcp(records, target, now, port=10050)
    if agent and agent.get("status") == "success":
        return result(rule, False, "A recent agent.ping sample exists.")
    if target_ping is None or not agent or agent.get("status") != "no_data" or (agent_tcp is None):
        return result(
            rule,
            reason="Cannot establish agent unavailability.",
            missing=(
                "Enabled usable agent.ping with no recent data, target ping and passive TCP10050 probe.",
            ),
        )
    matched = target_ping == "success" and agent_tcp in ("refused", "timeout")
    return result(
        rule,
        matched,
        f"Host ping={target_ping}, agent.ping has no recent data, TCP10050={agent_tcp}.",
        missing=("Agent mode, Server allow-list, service and firewall state.",) if matched else (),
        actions=("Inspect zabbix-agent2 service and its logs; do not assume service stopped.",)
        if matched
        else (),
    )


def r4(name, observer, control_ip, records, now):
    """R4: compare DNS with an IP control from the same observer."""
    rule = "R4_DNS_RESOLVER_SUSPECTED"
    if not name:
        return result(
            rule,
            reason="DNS target not configured.",
            missing=("Actual application name and CLI01 DNS evidence.",),
        )
    dns = latest(records, "dns", name.lower().rstrip("."), now, observer=observer, record_type="A")
    control_ping = latest(records, "dns_control_ping", control_ip, now, observer=observer)
    if not dns or not control_ping or control_ping.get("status") not in ("success", "no_reply"):
        return result(
            rule,
            reason="DNS and IP control must be fresh and from the same intended observer.",
            missing=("Run dns_probe.py on CLI01 for the configured name and control IP.",),
        )
    status = dns.get("status")
    code = dns.get("dns_status")
    usable = (
        status == "success"
        and code == "NOERROR"
        and bool(dns.get("addresses"))
        or (status == "no_answer" and code == "NOERROR")
        or (status == "nxdomain" and code == "NXDOMAIN")
        or (status == "dns_error" and code in ("SERVFAIL", "REFUSED"))
        or (status == "timeout")
    )
    if not usable:
        return result(
            rule,
            reason="DNS collector did not produce an interpretable result.",
            missing=("DNS response or timeout, not a missing executable/local command error.",),
        )
    if status == "success":
        return result(
            rule, False, "DNS returned an A answer; this does not validate the expected IP."
        )
    if control_ping["status"] != "success":
        return result(
            rule,
            reason="IP control also failed; DNS-specific failure is not isolated.",
            missing=("Working IP connectivity from the same observer.",),
        )
    return result(
        rule,
        True,
        f"IP control works on {observer}; DNS status={status}, rcode={code}.",
        missing=(
            "Expected name/IP, intended resolver and resolver configuration; NXDOMAIN may be a spelling/name issue.",
        ),
        actions=("Compare CLI01 resolver settings and query the intended resolver.",),
    )


def r5(target, records, now, observer="srv01"):
    """R5: remote HTTP fails while the service's own local probe works."""
    rule = "R5_HTTP_ACCESS_FILTER_SUSPECTED"
    target_ping, target_tcp = (ping(records, target, now), tcp(records, target, now))
    if target_tcp == "success" or target_ping == "no_reply":
        return result(rule, False, "No isolated remote HTTP connection failure with working ICMP.")
    local = local_http(records, target, observer, now)
    if target_ping is None or target_tcp is None or local is None:
        return result(
            rule,
            reason="Need remote ping/TCP and fresh HTTP evidence from the service host.",
            missing=("Run http_probe.py on SRV01 and import its fresh JSON with --http-evidence.",),
        )
    matched = (
        target_ping == "success" and target_tcp in ("timeout", "refused") and (local == "success")
    )
    reason = (
        f"Remote ping={target_ping}, TCP80={target_tcp}; HTTP on target's own service IP={local}. "
    )
    if matched:
        reason += "Filtering/access-path failure is suspected, not proven firewall causation."
    else:
        reason += (
            "The evidence does not meet R5 conditions for suspected filtering/access-path failure."
        )
    return result(
        rule,
        matched,
        reason,
        missing=(
            "Read firewall rules and relevant packet counters; compare another remote observer. Local HTTP does not traverse the same ingress path.",
        )
        if matched
        else (),
        actions=(
            "Inspect SRV01 firewall and routes; compare HTTP from CLI01 before attributing cause.",
        )
        if matched
        else (),
    )


def _validated_cpu_samples(history, now):
    """Validate values and time coverage before computing an arithmetic mean."""
    samples = history.get("samples", [])
    if len(samples) < CPU_MIN_SAMPLES:
        raise ValueError("Too few CPU samples")
    clocks = [sample["clock"] for sample in samples]
    values = [sample["value"] for sample in samples]
    if any(
        type(clock) is not int or not now - CPU_SAMPLE_MAX_AGE_SECONDS <= clock <= now
        for clock in clocks
    ):
        raise ValueError("CPU sample clock is invalid or outside the allowed age")
    if any(
        type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 100
        for value in values
    ):
        raise ValueError("CPU percentage is invalid")
    if (
        clocks != sorted(set(clocks))
        or clocks[-1] - clocks[0] < CPU_MIN_COVERAGE_SECONDS
        or now - clocks[-1] > EVIDENCE_MAX_AGE_SECONDS
    ):
        raise ValueError("CPU clocks are duplicated, unsorted, sparse or stale")
    if any(later - earlier > CPU_MAX_GAP_SECONDS for earlier, later in zip(clocks, clocks[1:])):
        raise ValueError("CPU sample gap exceeds the allowed limit")
    return clocks, values


def _validated_cpu_support(history, now):
    """CPU count allows its one-day heartbeat; load must remain recent."""
    support = history["support_items"]
    count_item, load_item = (support["system.cpu.num"], support["system.cpu.load[all,avg1]"])
    for item, max_age in (
        (count_item, CPU_COUNT_MAX_AGE_SECONDS),
        (load_item, EVIDENCE_MAX_AGE_SECONDS),
    ):
        age = now - int(item["lastclock"])
        if item["status"] != "0" or item["state"] != "0" or (not 0 <= age <= max_age):
            raise ValueError()
    count, load = (float(count_item["lastvalue"]), float(load_item["lastvalue"]))
    if (
        not math.isfinite(count)
        or not count.is_integer()
        or count < 1
        or (not math.isfinite(load))
        or (load < 0)
    ):
        raise ValueError("CPU count or load is invalid")
    return count, load


def r6(host_id, records, now):
    """R6: require sustained high CPU plus fresh load and CPU-count support."""
    rule = "R6_SUSTAINED_CPU_HIGH"
    history = latest(records, "cpu_history", host_id, now, key="system.cpu.util")
    if not history or history.get("status") != "success" or history.get("units") != "%":
        return result(
            rule,
            reason="No usable CPU history.",
            missing=("CPU percentage history over the last five minutes.",),
        )
    try:
        clocks, values = _validated_cpu_samples(history, now)
    except (KeyError, TypeError, ValueError):
        return result(
            rule,
            reason="CPU history is sparse, stale or invalid.",
            missing=(
                f"At least {CPU_MIN_COVERAGE_SECONDS}s coverage, max {CPU_MAX_GAP_SECONDS}s gap, "
                f"latest sample <={EVIDENCE_MAX_AGE_SECONDS}s old.",
            ),
        )
    mean = sum(values) / len(values)
    if mean < CPU_HIGH_PERCENT:
        return result(rule, False, f"Mean CPU={mean:.2f}%; below {CPU_HIGH_PERCENT}%.")
    try:
        count, load = _validated_cpu_support(history, now)
    except (KeyError, TypeError, ValueError):
        return result(
            rule,
            reason="CPU stays high, but load/cpu-count corroboration is missing.",
            missing=(
                f"Usable CPU count <={CPU_COUNT_MAX_AGE_SECONDS}s old "
                f"(1d heartbeat + {EVIDENCE_MAX_AGE_SECONDS}s grace) "
                f"and CPU load <={EVIDENCE_MAX_AGE_SECONDS}s old.",
            ),
        )
    matched = load >= count
    return result(
        rule,
        matched,
        f"Mean CPU={mean:.2f}% over {clocks[-1] - clocks[0]}s; "
        f"threshold={CPU_HIGH_PERCENT}%; load={load:.2f}, CPUs={count:g}.",
        missing=(
            "Response-time baseline and top processes; CPU and load suggest but do not prove overload.",
        )
        if matched
        else (),
        actions=("Compare load and response time; inspect top processes.",) if matched else (),
    )


def diagnose_roadmap(
    host_id,
    target,
    records,
    control=None,
    dns_name=None,
    dns_observer="cli01",
    control_ip=None,
    now=None,
    http_observer="srv01",
    http_service=DEFAULT_HTTP_SERVICE,
):
    """Evaluate R1-R6 independently, in stable output order.

    HTTP applicability defaults to unknown for both this API and the CLI.
    Callers targeting a web server must pass http_service="expected" explicitly.
    """
    if http_service not in HTTP_SERVICE_SCOPES:
        raise ValueError("Invalid HTTP service scope")

    now = int(time.time()) if now is None else now
    records = list(records)

    if http_service == "expected":
        http_r2 = r2(target, records, now, http_observer)
        http_r5 = r5(target, records, now, http_observer)
    elif http_service == "absent":
        reason = (
            "Not applicable: HTTP service is declared absent on this host. "
            "This does not establish overall host health."
        )
        http_r2 = result("R2_HTTP_SERVICE_SUSPECTED", False, reason)
        http_r5 = result("R5_HTTP_ACCESS_FILTER_SUSPECTED", False, reason)
    else:
        reason = "HTTP service applicability is unknown."
        missing = ("Declare whether this host is expected to provide HTTP.",)
        http_r2 = result("R2_HTTP_SERVICE_SUSPECTED", reason=reason, missing=missing)
        http_r5 = result("R5_HTTP_ACCESS_FILTER_SUSPECTED", reason=reason, missing=missing)

    return [
        r1(target, control, records, now),
        http_r2,
        r3(host_id, target, records, now),
        r4(dns_name, dns_observer, control_ip or target, records, now),
        http_r5,
        r6(host_id, records, now),
    ]

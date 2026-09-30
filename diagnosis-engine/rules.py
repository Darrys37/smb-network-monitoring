import time

from models import DiagnosisRecord


def diagnose_http_port(target, evidence, now=None, max_age=180):
    if type(max_age) is not int or max_age <= 0:
        raise ValueError("max_age must be a positive integer")

    if now is None:
        now = int(time.time())

    rule_id = "HTTP_PORT_REFUSED"
    selected = {}
    missing = []

    for check_type in ("ping", "tcp"):
        candidates = [
            record for record in evidence
            if record.check_type == check_type
            and record.target == target
            and (
                check_type != "tcp"
                or record.result.get("port") == 80
            )
        ]

        if not candidates:
            missing.append(f"Missing {check_type} evidence for {target}")
            continue

        latest = max(candidates, key=lambda record: record.collected_at)
        age = now - latest.collected_at

        if age < 0 or age > max_age:
            missing.append(f"{check_type} evidence has invalid age: {age}s")
            continue

        allowed = (
            {"success", "no_reply"}
            if check_type == "ping"
            else {"success", "refused", "timeout"}
        )

        if latest.result.get("status") not in allowed:
            missing.append(f"{check_type} check has no usable result")
            continue

        selected[check_type] = latest

    if missing:
        return DiagnosisRecord(
            rule_id=rule_id,
            status="insufficient_evidence",
            probable_cause=None,
            reasoning="Not enough recent evidence to evaluate this rule.",
            missing_info=tuple(missing),
            next_actions=(
                f"Repeat ping and TCP port 80 checks for {target}.",
            ),
        )

    ping_status = selected["ping"].result["status"]
    tcp_status = selected["tcp"].result["status"]

    if ping_status == "success" and tcp_status == "refused":
        return DiagnosisRecord(
            rule_id=rule_id,
            status="matched",
            probable_cause=(
                "No service listening on TCP port 80, "
                "or the connection is actively rejected."
            ),
            reasoning=(
                f"{target} responds to ping, but TCP port 80 "
                "refuses the connection."
            ),
            missing_info=(
                "Listening sockets and owning processes on the target.",
                "Web service status and firewall rules on the target.",
            ),
            next_actions=(
                "On the target: sudo ss -lntp",
                "On the target: systemctl status nginx --no-pager",
                "Inspect firewall rules for TCP port 80.",
            ),
        )

    return DiagnosisRecord(
        rule_id=rule_id,
        status="not_matched",
        probable_cause=None,
        reasoning=(
            f"Observed ping={ping_status}, TCP port 80={tcp_status}; "
            "this rule requires ping=success and TCP=refused."
        ),
        missing_info=(),
        next_actions=(),
    )
def diagnose_cpu(host_id, evidence, now=None, max_age=180):
    if type(max_age) is not int or max_age <= 0:
        raise ValueError("max_age must be a positive integer")

    if now is None:
        now = int(time.time())

    candidates = [
        record for record in evidence
        if record.check_type == "metric"
        and record.target == str(host_id)
        and record.result.get("key") == "system.cpu.util"
    ]

    problem = "Missing CPU metric for this host."
    value = None

    if candidates:
        latest = max(candidates, key=lambda record: record.collected_at)
        result = latest.result
        clock = result.get("sample_clock")
        value = result.get("value")

        if not 0 <= now - latest.collected_at <= max_age:
            problem = "CPU evidence collection time is stale or invalid."
        elif result.get("status") != "success":
            problem = "CPU metric is not usable."
        elif type(clock) is not int or not 0 < clock <= now:
            problem = "CPU sample timestamp is missing or invalid."
        elif now - clock > max_age:
            problem = "CPU sample is stale."
        elif result.get("units") != "%":
            problem = "CPU metric must use percent."
        elif type(value) not in (int, float) or not 0 <= value <= 100:
            problem = "CPU value is missing or invalid."
        else:
            problem = None

    if problem:
        return DiagnosisRecord(
            rule_id="CPU_HIGH",
            status="insufficient_evidence",
            probable_cause=None,
            reasoning="Cannot evaluate CPU usage reliably.",
            missing_info=(problem,),
            next_actions=("Collect a fresh CPU utilization sample.",),
        )

    high = value >= 90

    return DiagnosisRecord(
        rule_id="CPU_HIGH",
        status="matched" if high else "not_matched",
        probable_cause=(
            "High CPU demand at the sample time." if high else None
        ),
        reasoning=f"CPU utilization is {value:.2f}%; threshold is 90%.",
        missing_info=(
            "CPU history to determine whether high usage persists.",
            "Processes consuming CPU on the target.",
        ) if high else (),
        next_actions=(
            "Inspect CPU history in Zabbix.",
            "On the target: top",
        ) if high else (),
    )
def diagnose_dns_name(target, evidence, now=None, max_age=180):
    if type(max_age) is not int or max_age <= 0:
        raise ValueError("max_age must be a positive integer")

    if now is None:
        now = int(time.time())

    target = target.lower().rstrip(".")
    candidates = [
        record for record in evidence
        if record.check_type == "dns"
        and record.target.lower().rstrip(".") == target
        and record.result.get("record_type") == "A"
    ]

    problem = "Missing DNS A-query evidence for this name."
    matched = False
    observed = None

    if candidates:
        latest = max(candidates, key=lambda record: record.collected_at)
        age = now - latest.collected_at
        result = latest.result
        observed = result.get("dns_status")

        if not 0 <= age <= max_age:
            problem = "DNS evidence is stale or has a future timestamp."
        elif result.get("status") == "nxdomain" and observed == "NXDOMAIN":
            problem = None
            matched = True
        elif (
            result.get("status") in ("success", "no_answer")
            and observed == "NOERROR"
        ):
            problem = None
        else:
            problem = "No usable DNS response for evaluating name existence."

    if problem:
        return DiagnosisRecord(
            rule_id="DNS_NAME_NOT_FOUND",
            status="insufficient_evidence",
            probable_cause=None,
            reasoning="Cannot determine whether DNS reports this name absent.",
            missing_info=(problem,),
            next_actions=(f"Repeat the DNS A query for {target}.",),
        )

    return DiagnosisRecord(
        rule_id="DNS_NAME_NOT_FOUND",
        status="matched" if matched else "not_matched",
        probable_cause=(
            "Incorrect domain name or missing DNS name in the queried view."
            if matched else None
        ),
        reasoning=f"DNS query for {target} returned {observed}.",
        missing_info=(
            "Expected domain name and DNS records.",
            "Whether the query used the intended DNS resolver.",
        ) if matched else (),
        next_actions=(
            "Verify the domain spelling.",
            "Check the intended DNS resolver and authoritative records.",
        ) if matched else (),
    )
def diagnose_memory(host_id, evidence, now=None, max_age=180):
    if type(max_age) is not int or max_age <= 0:
        raise ValueError("max_age must be a positive integer")

    if now is None:
        now = int(time.time())

    candidates = [
        record for record in evidence
        if record.check_type == "metric"
        and record.target == str(host_id)
        and record.result.get("key") == "vm.memory.util"
    ]

    problem = "Missing memory utilization metric for this host."
    value = None

    if candidates:
        latest = max(candidates, key=lambda record: record.collected_at)
        result = latest.result
        clock = result.get("sample_clock")
        value = result.get("value")

        if not 0 <= now - latest.collected_at <= max_age:
            problem = "Memory evidence collection time is stale or invalid."
        elif result.get("status") != "success":
            problem = "Memory metric is not usable."
        elif type(clock) is not int or not 0 < clock <= now:
            problem = "Memory sample timestamp is missing or invalid."
        elif now - clock > max_age:
            problem = "Memory sample is stale."
        elif result.get("units") != "%":
            problem = "Memory metric must use percent."
        elif type(value) not in (int, float) or not 0 <= value <= 100:
            problem = "Memory value is missing or invalid."
        else:
            problem = None

    if problem:
        return DiagnosisRecord(
            rule_id="MEMORY_HIGH",
            status="insufficient_evidence",
            probable_cause=None,
            reasoning="Cannot evaluate memory usage reliably.",
            missing_info=(problem,),
            next_actions=("Collect a fresh memory utilization sample.",),
        )

    high = value >= 90

    return DiagnosisRecord(
        rule_id="MEMORY_HIGH",
        status="matched" if high else "not_matched",
        probable_cause=(
            "High memory usage at the sample time." if high else None
        ),
        reasoning=f"Memory utilization is {value:.2f}%; threshold is 90%.",
        missing_info=(
            "Memory history and available memory on the target.",
            "Swap activity and processes consuming memory.",
        ) if high else (),
        next_actions=(
            "Inspect memory history in Zabbix.",
            "On the target: free -h",
            "On the target: top",
        ) if high else (),
    )
def diagnose_reachability(target, evidence, now=None, max_age=180):
    if type(max_age) is not int or max_age <= 0:
        raise ValueError("max_age must be a positive integer")

    if now is None:
        now = int(time.time())

    selected = {}
    missing = []

    for check_type in ("ping", "tcp"):
        candidates = [
            record for record in evidence
            if record.check_type == check_type
            and record.target == target
            and (
                check_type != "tcp"
                or record.result.get("port") == 80
            )
        ]

        if not candidates:
            missing.append(f"Missing {check_type} evidence for {target}")
            continue

        latest = max(candidates, key=lambda record: record.collected_at)
        age = now - latest.collected_at
        status = latest.result.get("status")
        allowed = (
            {"success", "no_reply"}
            if check_type == "ping"
            else {"success", "refused", "timeout"}
        )

        if not 0 <= age <= max_age:
            missing.append(f"{check_type} evidence is stale or future-dated")
        elif status not in allowed:
            missing.append(f"{check_type} check has no usable result")
        else:
            selected[check_type] = status

    if missing:
        return DiagnosisRecord(
            rule_id="REACHABILITY_SUSPECTED",
            status="insufficient_evidence",
            probable_cause=None,
            reasoning="Cannot evaluate target reachability reliably.",
            missing_info=tuple(missing),
            next_actions=(
                f"Repeat ping and TCP port 80 checks for {target}.",
            ),
        )

    matched = (
        selected["ping"] == "no_reply"
        and selected["tcp"] == "timeout"
    )

    return DiagnosisRecord(
        rule_id="REACHABILITY_SUSPECTED",
        status="matched" if matched else "not_matched",
        probable_cause=(
            "Target unavailable, network path failure, or traffic filtering."
            if matched else None
        ),
        reasoning=(
            f"{target}: ping={selected['ping']}, "
            f"TCP port 80={selected['tcp']}."
        ),
        missing_info=(
            "Target power state and network interface configuration.",
            "Routing and firewall state.",
            "Connectivity results from another monitoring point.",
        ) if matched else (),
        next_actions=(
            "Inspect the target VM console and network interfaces.",
            "Check routing and firewall rules.",
            "Repeat connectivity checks from CLI01.",
        ) if matched else (),
    )
def diagnose_disk(host_id, evidence, now=None, max_age=180):
    if type(max_age) is not int or max_age <= 0:
        raise ValueError("max_age must be a positive integer")

    if now is None:
        now = int(time.time())

    candidates = [
        record for record in evidence
        if record.check_type == "metric"
        and record.target == str(host_id)
        and record.result.get("key") == "vfs.fs.dependent.size[/,pused]"
    ]

    problem = "Missing root filesystem utilization metric."
    value = None

    if candidates:
        latest = max(candidates, key=lambda record: record.collected_at)
        result = latest.result
        clock = result.get("sample_clock")
        value = result.get("value")

        if not 0 <= now - latest.collected_at <= max_age:
            problem = "Disk evidence collection time is stale or invalid."
        elif result.get("status") != "success":
            problem = "Disk metric is not usable."
        elif type(clock) is not int or not 0 < clock <= now:
            problem = "Disk sample timestamp is missing or invalid."
        elif now - clock > max_age:
            problem = "Disk sample is stale."
        elif result.get("units") != "%":
            problem = "Disk metric must use percent."
        elif type(value) not in (int, float) or not 0 <= value <= 100:
            problem = "Disk value is missing or invalid."
        else:
            problem = None

    if problem:
        return DiagnosisRecord(
            rule_id="ROOT_DISK_HIGH",
            status="insufficient_evidence",
            probable_cause=None,
            reasoning="Cannot evaluate root filesystem usage reliably.",
            missing_info=(problem,),
            next_actions=("Collect a fresh root filesystem usage sample.",),
        )

    high = value >= 90

    return DiagnosisRecord(
        rule_id="ROOT_DISK_HIGH",
        status="matched" if high else "not_matched",
        probable_cause=(
            "Root filesystem capacity is nearing exhaustion."
            if high else None
        ),
        reasoning=f"Filesystem / usage is {value:.2f}%; threshold is 90%.",
        missing_info=(
            "Available bytes and filesystem growth history.",
            "Directories consuming space and inode availability.",
        ) if high else (),
        next_actions=(
            "On the target: df -h /",
            "On the target: df -i /",
            "Inspect directory sizes and log retention before cleanup.",
        ) if high else (),
    )

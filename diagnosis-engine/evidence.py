import math
from zabbix_client import get_host_metrics
import re
import socket
import ipaddress
import subprocess
import time

from models import EvidenceRecord


def collect_ping(target: str, timeout: int = 2) -> EvidenceRecord:
    target = str(ipaddress.IPv4Address(target))
    if type(timeout) is not int or timeout <= 0:
        raise ValueError("timeout must be a positive integer")

    collected_at = int(time.time())
    started = time.monotonic()
    process_timeout = timeout + 1

    result = {
        "timeout_seconds": timeout,
        "process_timeout_seconds": process_timeout,
        "returncode": None,
        "stdout": "",
        "stderr": "",
    }

    try:
        completed = subprocess.run(
            ["ping", "-n", "-c", "1", "-W", str(timeout), target],
            capture_output=True,
            text=True,
            timeout=process_timeout,
            check=False,
        )

        result["returncode"] = completed.returncode
        result["stdout"] = completed.stdout.strip()
        result["stderr"] = completed.stderr.strip()

        if completed.returncode == 0:
            result["status"] = "success"
        elif completed.returncode == 1:
            result["status"] = "no_reply"
        else:
            result["status"] = "error"

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["stderr"] = "Ping process exceeded time limit"

    except OSError as exc:
        result["status"] = "error"
        result["stderr"] = str(exc)

    result["duration_ms"] = round(
        (time.monotonic() - started) * 1000, 2
    )

    return EvidenceRecord(
        check_type="ping",
        target=target,
        collected_at=collected_at,
        result=result,
    )
def collect_tcp(
    target: str, port: int, timeout: int = 2
) -> EvidenceRecord:
    target = str(ipaddress.IPv4Address(target))

    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("port must be an integer from 1 to 65535")
    if type(timeout) is not int or timeout <= 0:
        raise ValueError("timeout must be a positive integer")

    collected_at = int(time.time())
    started = time.monotonic()
    result = {
        "port": port,
        "timeout_seconds": timeout,
        "error": "",
        "errno": None,
    }

    try:
        with socket.create_connection(
            (target, port), timeout=timeout
        ):
            result["status"] = "success"

    except ConnectionRefusedError as exc:
        result["status"] = "refused"
        result["error"] = str(exc)
        result["errno"] = exc.errno

    except TimeoutError as exc:
        result["status"] = "timeout"
        result["error"] = str(exc)
        result["errno"] = exc.errno

    except OSError as exc:
        result["status"] = "error"
        result["error"] = str(exc)
        result["errno"] = exc.errno

    result["duration_ms"] = round(
        (time.monotonic() - started) * 1000, 2
    )

    return EvidenceRecord(
        check_type="tcp",
        target=target,
        collected_at=collected_at,
        result=result,
    )
def collect_dns(target: str, timeout: int = 2) -> EvidenceRecord:
    if not isinstance(target, str):
        raise ValueError("target must be a domain name")

    target = target.rstrip(".")
    labels = target.split(".")
    pattern = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"

    if (
        len(target) > 253
        or not all(re.fullmatch(pattern, label) for label in labels)
    ):
        raise ValueError("target must be a valid ASCII domain name")

    if type(timeout) is not int or timeout <= 0:
        raise ValueError("timeout must be a positive integer")

    collected_at = int(time.time())
    started = time.monotonic()
    result = {
        "record_type": "A",
        "timeout_seconds": timeout,
        "process_timeout_seconds": timeout + 1,
        "status": "error",
        "dns_status": None,
        "addresses": [],
        "returncode": None,
        "stdout": "",
        "stderr": "",
    }

    try:
        completed = subprocess.run(
            [
                "dig", "-r", f"+time={timeout}", "+tries=1",
                "-q", target + ".", "-t", "A",
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 1,
            check=False,
        )

        result["returncode"] = completed.returncode
        result["stdout"] = completed.stdout.strip()
        result["stderr"] = completed.stderr.strip()

        match = re.search(r"status:\s*(\w+)", completed.stdout)
        if match:
            result["dns_status"] = match.group(1)

        addresses = []
        in_answer = False
        for line in completed.stdout.splitlines():
            if line.startswith(";; ANSWER SECTION:"):
                in_answer = True
                continue
            if not line.strip() or line.startswith(";;"):
                in_answer = False
            if in_answer:
                fields = line.split()
                if len(fields) == 5 and fields[2:4] == ["IN", "A"]:
                    addresses.append(str(ipaddress.IPv4Address(fields[4])))

        result["addresses"] = sorted(set(addresses))

        if completed.returncode == 0 and match:
            if result["dns_status"] == "NOERROR":
                result["status"] = "success" if addresses else "no_answer"
            elif result["dns_status"] == "NXDOMAIN":
                result["status"] = "nxdomain"
            else:
                result["status"] = "dns_error"
        elif completed.returncode == 9 and "timed out" in (completed.stdout + completed.stderr).lower():
            result["status"] = "timeout"

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["stderr"] = "DNS process exceeded time limit"

    except (OSError, ValueError) as exc:
        result["status"] = "error"
        result["stderr"] = str(exc)

    result["duration_ms"] = round(
        (time.monotonic() - started) * 1000, 2
    )

    return EvidenceRecord(
        check_type="dns",
        target=target,
        collected_at=collected_at,
        result=result,
    )
def collect_metrics(host_id: str, max_age: int = 180):
    if type(max_age) is not int or max_age <= 0:
        raise ValueError("max_age must be a positive integer")

    expected = {
        "system.cpu.util": "%",
        "vm.memory.util": "%",
        "system.cpu.load[all,avg1]": "",
        "vfs.fs.dependent.size[/,pused]": "%",
    }

    items = get_host_metrics(host_id)
    collected_at = int(time.time())
    by_key = {item["key_"]: item for item in items}
    records = []

    for key, units in expected.items():
        item = by_key.get(key)
        result = {
            "key": key,
            "units": units,
            "max_age_seconds": max_age,
            "status": "missing",
            "value": None,
            "sample_clock": None,
            "age_seconds": None,
        }

        if item is not None:
            result["item_id"] = item.get("itemid")
            result["raw_value"] = item.get("lastvalue")
            result["error"] = item.get("error", "")

            try:
                clock = int(item["lastclock"])
                value = float(item["lastvalue"])

                if clock < 0 or not math.isfinite(value):
                    raise ValueError("Invalid timestamp or numeric value")
                if value < 0 or (units == "%" and value > 100):
                    raise ValueError("Metric value outside expected range")
                if item["units"] != units:
                    raise ValueError("Unexpected metric units")

                age = collected_at - clock
                result["value"] = value
                result["sample_clock"] = clock
                result["age_seconds"] = age

                if item["status"] != "0":
                    result["status"] = "disabled"
                elif item["state"] != "0":
                    result["status"] = "unsupported"
                elif clock == 0:
                    result["status"] = "no_data"
                elif age < 0:
                    result["status"] = "clock_error"
                elif age > max_age:
                    result["status"] = "stale"
                else:
                    result["status"] = "success"

            except (KeyError, TypeError, ValueError) as exc:
                result["status"] = "invalid"
                result["error"] = str(exc)

        records.append(EvidenceRecord(
            check_type="metric",
            target=str(host_id),
            collected_at=collected_at,
            result=result,
        ))

    return records

"""Import a DNS query and its IP control measured by the same observer."""

import ipaddress

from models import EvidenceRecord
from probe_evidence import load_probe_rows


def _validate_dns_result(result):
    """Reject inconsistent data; preserve genuine collector errors for R4."""
    if result.get("record_type") != "A":
        raise ValueError("DNS evidence must contain an A query")
    addresses = result.get("addresses")
    if not isinstance(addresses, list) or any(not isinstance(ip, str) for ip in addresses):
        raise ValueError("DNS addresses must be a list of IPv4 strings")
    for address in addresses:
        ipaddress.IPv4Address(address)
    status, code = result.get("status"), result.get("dns_status")
    if code is not None and (not isinstance(code, str) or not code):
        raise ValueError("Invalid DNS response code")
    if status == "success":
        consistent = code == "NOERROR" and bool(addresses)
    elif status == "no_answer":
        consistent = code == "NOERROR" and not addresses
    elif status == "nxdomain":
        consistent = code == "NXDOMAIN" and not addresses
    elif status == "dns_error":
        consistent = code is not None and code not in ("NOERROR", "NXDOMAIN") and not addresses
    elif status in ("timeout", "error"):
        consistent = True
    else:
        consistent = False
    if not consistent:
        raise ValueError("DNS status, response code and addresses are inconsistent")


def load_dns_evidence(path, name, control_ip, observer, now):
    """Require one fresh query and one control ping for configured targets.

    Original unversioned DNS files and schema_version=1 obey the same checks.
    The caller supplies intended targets, rather than trusting file contents.
    """
    if not isinstance(name, str) or not name.strip() or not control_ip:
        raise ValueError("DNS evidence requires a configured name and control IP")
    name = name.lower().rstrip(".")
    control_ip = str(ipaddress.IPv4Address(control_ip))
    rows = load_probe_rows(path, observer, now, label="DNS", allow_legacy_schema=True)
    if len(rows) != 2 or {row["check_type"] for row in rows} != {"dns", "dns_control_ping"}:
        raise ValueError("Expected one DNS query and one DNS control ping")
    for row in rows:
        result = row["result"]
        if row["check_type"] == "dns":
            if row["target"] != name:
                raise ValueError("DNS evidence name mismatch")
            _validate_dns_result(result)
        else:
            if row["target"] != control_ip:
                raise ValueError("DNS control IP mismatch")
            if result.get("status") not in ("success", "no_reply", "timeout", "error"):
                raise ValueError("Invalid DNS control ping status")
    return [EvidenceRecord(**row) for row in rows]

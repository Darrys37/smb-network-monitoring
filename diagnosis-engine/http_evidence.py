"""Validate operator-transferred local HTTP evidence; no remote execution."""

from models import EvidenceRecord
from probe_evidence import load_probe_rows


def load_http_evidence(path, target, observer, now):
    """Validate one fresh HTTP result for the target's own service IP."""
    rows = load_probe_rows(path, observer, now, label="HTTP")
    if len(rows) != 1:
        raise ValueError("Expected one local HTTP record")
    row = rows[0]
    if row["check_type"] != "local_http" or row["target"] != target:
        raise ValueError("HTTP evidence target mismatch")
    result = row["result"]
    if (
        result.get("local_address_verified") is not True
        or type(result.get("port")) is not int
        or result["port"] != 80
        or result.get("path") != "/"
    ):
        raise ValueError("HTTP evidence must check local target address, TCP80 and /")
    status, code = result.get("status"), result.get("http_status")
    if status not in ("success", "failed", "error"):
        raise ValueError("Invalid HTTP evidence status")
    if code is not None and (type(code) is not int or not 100 <= code <= 599):
        raise ValueError("Invalid HTTP response code")
    if (status == "success" and code != 200) or (status != "success" and code == 200):
        raise ValueError("HTTP status/code mismatch")
    return [EvidenceRecord(**row)]

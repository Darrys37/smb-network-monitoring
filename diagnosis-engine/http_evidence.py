"""Validate operator-transferred local HTTP evidence; no remote execution."""
import json
from models import EvidenceRecord


def load_http_evidence(path, target, observer, now):
    if path.stat().st_size > 65536:
        raise ValueError("HTTP evidence file exceeds 64 KiB")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1 or data.get("observer") != observer:
        raise ValueError("Invalid HTTP evidence envelope or observer")
    rows = data.get("evidence")
    if not isinstance(rows, list) or len(rows) != 1:
        raise ValueError("Expected one local HTTP record")
    row = rows[0]
    if not isinstance(row, dict) or set(row) != {"check_type", "target", "collected_at", "result"}:
        raise ValueError("Invalid HTTP record fields")
    if row["check_type"] != "local_http" or row["target"] != target:
        raise ValueError("HTTP evidence target mismatch")
    stamp, result = row["collected_at"], row["result"]
    if type(stamp) is not int or not 0 <= now - stamp <= 180:
        raise ValueError("HTTP evidence is stale or from the future; collect again")
    if not isinstance(result, dict) or result.get("observer") != observer:
        raise ValueError("HTTP record observer mismatch")
    if (result.get("local_address_verified") is not True or type(result.get("port")) is not int
            or result["port"] != 80 or result.get("path") != "/"):
        raise ValueError("HTTP evidence must check local target address, TCP80 and /")
    status, code = result.get("status"), result.get("http_status")
    if status not in ("success", "failed", "error"):
        raise ValueError("Invalid HTTP evidence status")
    if code is not None and (type(code) is not int or not 100 <= code <= 599):
        raise ValueError("Invalid HTTP response code")
    if (status == "success" and code != 200) or (status != "success" and code == 200):
        raise ValueError("HTTP status/code mismatch")
    return [EvidenceRecord(**row)]

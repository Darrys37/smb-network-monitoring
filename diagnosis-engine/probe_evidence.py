"""Validate common fields of operator-transferred HTTP/DNS evidence.

Only reads local files. Observer labels are not cryptographic authentication.
Protocol-specific validation belongs to the HTTP and DNS loaders.
"""

import json
from pathlib import Path

from policy import EVIDENCE_MAX_AGE_SECONDS, PROBE_MAX_BYTES, PROBE_SCHEMA_VERSION

RECORD_FIELDS = {"check_type", "target", "collected_at", "result"}


def load_probe_rows(path, observer, now, *, label, allow_legacy_schema=False):
    """Read bounded UTF-8 JSON and validate every row before returning any row.

    Original DNS files omitted schema_version; only DNS opts into accepting
    that envelope. An explicit unsupported version always fails.
    """
    with Path(path).open("rb") as stream:
        payload = stream.read(PROBE_MAX_BYTES + 1)
    if len(payload) > PROBE_MAX_BYTES:
        raise ValueError(f"{label} evidence file exceeds 64 KiB")
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} evidence must be valid UTF-8 JSON") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label} evidence envelope must be an object")
    if "schema_version" in data or not allow_legacy_schema:
        version = data.get("schema_version")
        if type(version) is not int or version != PROBE_SCHEMA_VERSION:
            raise ValueError(f"Invalid {label} evidence schema_version")
    if not isinstance(observer, str) or not observer or data.get("observer") != observer:
        raise ValueError(f"{label} observer mismatch")

    rows = data.get("evidence")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{label} evidence must be a non-empty list")
    for row in rows:
        if not isinstance(row, dict) or set(row) != RECORD_FIELDS:
            raise ValueError(f"Invalid {label} record fields")
        if any(not isinstance(row[key], str) or not row[key] for key in ("check_type", "target")):
            raise ValueError(f"Invalid {label} record check_type or target")
        stamp = row["collected_at"]
        if type(stamp) is not int or not 0 <= now - stamp <= EVIDENCE_MAX_AGE_SECONDS:
            raise ValueError(f"{label} evidence is stale or from the future; collect again")
        result = row["result"]
        if not isinstance(result, dict) or result.get("observer") != observer:
            raise ValueError(f"{label} record observer mismatch")
    return rows

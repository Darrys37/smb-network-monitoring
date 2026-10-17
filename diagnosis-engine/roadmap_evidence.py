"""Additional collectors for the roadmap; all remote actions are read-only."""

import math
import time

from evidence import METRIC_UNITS, metric_records_from_items
from models import EvidenceRecord
from policy import CPU_HISTORY_WINDOW_SECONDS, EVIDENCE_MAX_AGE_SECONDS
from zabbix_client import get_item_history, get_items_by_keys


def collect_roadmap_metrics(host_id):
    """Read item values once per run; history still needs its own API request.

    All six records share the time when item.get returned. Sample clocks stay
    unchanged, and CPU history ends at this time. No cache survives this call.
    """
    keys = [*METRIC_UNITS, "agent.ping", "system.cpu.num"]
    items = get_items_by_keys(host_id, keys)
    now = int(time.time())
    agent_items = [item for item in items if item["key_"] == "agent.ping"]
    return [
        *metric_records_from_items(host_id, items, now, EVIDENCE_MAX_AGE_SECONDS),
        _agent_metric_from_items(host_id, agent_items, now, EVIDENCE_MAX_AGE_SECONDS),
        _cpu_history_from_items(host_id, items, now),
    ]


def collect_agent_metric(host_id, max_age=EVIDENCE_MAX_AGE_SECONDS):
    """Stale enabled agent data is no_data, even if its current state is unsupported."""
    now = int(time.time())
    items = get_items_by_keys(host_id, ["agent.ping"])
    return _agent_metric_from_items(host_id, items, now, max_age)


def _agent_metric_from_items(host_id, items, now, max_age):
    result = {"key": "agent.ping", "status": "missing", "max_age_seconds": max_age}
    if len(items) == 1:
        item = items[0]
        result["item"] = item
        try:
            clock = int(item["lastclock"])
            result["sample_clock"] = clock
            if item["status"] != "0":
                result["status"] = "disabled"
            elif clock < 0 or clock > now:
                result["status"] = "invalid"
            elif clock == 0:
                result["status"] = "missing"
            elif now - clock > max_age:
                result["status"] = "no_data"
            elif item["state"] != "0":
                result["status"] = "unsupported"
            elif float(item["lastvalue"]) == 1:
                result["status"] = "success"
            else:
                result["status"] = "invalid"
        except (KeyError, ValueError, TypeError):
            result["status"] = "invalid"
    return EvidenceRecord("agent_metric", str(host_id), now, result)


def collect_cpu_history(host_id):
    """Collect the five-minute numeric history and raw corroborating items."""
    now = int(time.time())
    items = get_items_by_keys(
        host_id, ["system.cpu.util", "system.cpu.num", "system.cpu.load[all,avg1]"]
    )
    return _cpu_history_from_items(host_id, items, now)


def _cpu_history_from_items(host_id, items, now):
    result = {
        "key": "system.cpu.util",
        "units": "%",
        "status": "missing",
        "window_seconds": CPU_HISTORY_WINDOW_SECONDS,
        "samples": [],
    }
    by_key = {item["key_"]: item for item in items}
    result["support_items"] = {
        key: by_key[key] for key in ("system.cpu.num", "system.cpu.load[all,avg1]") if key in by_key
    }
    if "system.cpu.util" in by_key:
        item = by_key["system.cpu.util"]
        result["item_id"] = item["itemid"]
        if item.get("status") != "0" or item.get("state") != "0" or item.get("units") != "%":
            result["status"] = "unusable"
        else:
            try:
                rows = get_item_history(item, now - CPU_HISTORY_WINDOW_SECONDS, now)
                samples = [
                    {"clock": int(row["clock"]), "value": float(row["value"])} for row in rows
                ]
                if any(
                    not math.isfinite(s["value"])
                    or not 0 <= s["value"] <= 100
                    or not now - CPU_HISTORY_WINDOW_SECONDS <= s["clock"] <= now
                    for s in samples
                ):
                    raise ValueError("Invalid CPU history")
                if len({s["clock"] for s in samples}) != len(samples):
                    raise ValueError("Ambiguous duplicate CPU sample clocks")
                result.update(status="success", samples=sorted(samples, key=lambda s: s["clock"]))
            except (KeyError, TypeError, ValueError) as exc:
                result.update(status="invalid", error=str(exc))
    return EvidenceRecord("cpu_history", str(host_id), now, result)

"""One item read per assessment, without changing interpretation or DB safety."""

from copy import deepcopy
from unittest.mock import Mock

import pytest
from test_app_flow import EVENT

import app
import evidence
import roadmap_evidence as collectors
import zabbix_client
from models import EvidenceRecord

NOW = 1700000600
HOST = "10683"


def item_rows():
    values = {
        "system.cpu.util": ("95", "%"),
        "vm.memory.util": ("30", "%"),
        "system.cpu.load[all,avg1]": ("2", ""),
        "vfs.fs.dependent.size[/,pused]": ("20", "%"),
        "agent.ping": ("1", ""),
        "system.cpu.num": ("1", ""),
    }
    return [
        {
            "itemid": str(index),
            "key_": key,
            "lastclock": str(NOW),
            "lastvalue": value,
            "units": units,
            "status": "0",
            "state": "0",
            "value_type": "0",
            "error": "",
        }
        for index, (key, (value, units)) in enumerate(values.items(), start=1)
    ]


def mock_api(monkeypatch, rows=None, failure=None):
    rows = item_rows() if rows is None else rows
    calls = []

    def call(method, params, requests_id, use_token=True):
        calls.append((method, deepcopy(params)))
        if method == failure:
            raise RuntimeError("API unavailable")
        if method == "problem.get":
            return [{"eventid": EVENT["eventid"]}]
        if method == "event.get":
            return [deepcopy(EVENT)]
        if method == "item.get":
            keys = params["filter"]["key_"]
            return [deepcopy(row) for row in rows if row["key_"] in keys]
        if method == "history.get":
            return [{"clock": str(NOW - age), "value": "95"} for age in (240, 180, 120, 60, 0)]
        raise AssertionError(f"Unexpected API call: {method}")

    monkeypatch.setattr(zabbix_client, "call_api", call)
    monkeypatch.setattr(collectors.time, "time", lambda: NOW)
    return calls


@pytest.mark.parametrize(
    "case",
    ["healthy", "empty", "agent_stale", "agent_unsupported", "cpu_disabled", "cpu_missing"],
)
def test_batch_matches_individual_collectors(monkeypatch, case):
    rows = item_rows()
    if case == "empty":
        rows = []
    if case == "cpu_missing":
        rows = [row for row in rows if row["key_"] != "system.cpu.util"]
    for row in rows:
        if row["key_"] == "agent.ping" and case == "agent_stale":
            row.update(lastclock=str(NOW - 181), state="1")
        if row["key_"] == "agent.ping" and case == "agent_unsupported":
            row["state"] = "1"
        if row["key_"] == "system.cpu.util" and case == "cpu_disabled":
            row["status"] = "1"
    untouched = deepcopy(rows)
    calls = mock_api(monkeypatch, rows)
    expected = [
        *evidence.collect_metrics(HOST),
        collectors.collect_agent_metric(HOST),
        collectors.collect_cpu_history(HOST),
    ]
    assert [method for method, _ in calls].count("item.get") == 3
    calls.clear()
    assert collectors.collect_roadmap_metrics(HOST) == expected
    assert [method for method, _ in calls].count("item.get") == 1
    assert rows == untouched


def test_snapshot_uses_receive_time_and_preserves_sample_clocks(monkeypatch):
    rows = item_rows()
    rows[4]["lastclock"] = str(NOW - 180)
    clock = iter([NOW, NOW + 2])

    def fetch(*args):
        next(clock)  # API started earlier; receive time must follow it.
        return rows

    monkeypatch.setattr(collectors, "get_items_by_keys", fetch)
    monkeypatch.setattr(collectors.time, "time", lambda: next(clock))
    history = Mock(return_value=[])
    monkeypatch.setattr(collectors, "get_item_history", history)
    records = collectors.collect_roadmap_metrics(HOST)
    assert {record.collected_at for record in records} == {NOW + 2}
    assert records[4].result["sample_clock"] == NOW - 180
    assert records[4].result["status"] == "no_data"
    history.assert_called_once_with(rows[0], NOW + 2 - 300, NOW + 2)


def test_each_run_reads_its_own_host_and_fresh_values(monkeypatch):
    rows = item_rows()
    calls = mock_api(monkeypatch, rows)
    first = collectors.collect_roadmap_metrics(HOST)
    rows[0]["lastvalue"] = "10"
    second = collectors.collect_roadmap_metrics("10684")
    assert first[0].result["value"] == 95
    assert second[0].result["value"] == 10
    assert {record.target for record in second} == {"10684"}
    assert [params["hostids"] for method, params in calls if method == "item.get"] == [
        [HOST],
        ["10684"],
    ]


def mock_probes(monkeypatch):
    monkeypatch.setattr(
        app, "collect_ping", lambda ip: EvidenceRecord("ping", ip, NOW, {"status": "success"})
    )
    monkeypatch.setattr(
        app,
        "collect_tcp",
        lambda ip, port: EvidenceRecord("tcp", ip, NOW, {"status": "success", "port": port}),
    )


@pytest.mark.parametrize("ruleset,item_reads,total_calls", [("roadmap", 1, 6), ("legacy", 1, 5)])
def test_full_preview_request_budget_and_event_recheck(
    monkeypatch, tmp_path, ruleset, item_reads, total_calls
):
    calls = mock_api(monkeypatch)
    mock_probes(monkeypatch)
    db = tmp_path / "untouched.db"
    app.main(["--event-id", EVENT["eventid"], "--ruleset", ruleset, "--db", str(db)])
    methods = [method for method, _ in calls]
    assert len(methods) == total_calls
    assert methods.count("item.get") == item_reads
    assert methods[:2] == methods[-2:] == ["problem.get", "event.get"]
    assert not db.exists()


@pytest.mark.parametrize("failure", ["item.get", "history.get"])
@pytest.mark.parametrize("existing_db", [False, True])
def test_batch_api_failure_never_saves(monkeypatch, tmp_path, failure, existing_db):
    calls = mock_api(monkeypatch, failure=failure)
    mock_probes(monkeypatch)
    db = tmp_path / "unchanged.db"
    if existing_db:
        from repository import init_db

        init_db(db)
    before = db.read_bytes() if existing_db else None
    with pytest.raises(RuntimeError, match="API unavailable"):
        app.main(["--event-id", EVENT["eventid"], "--save", "--db", str(db)])
    assert (db.read_bytes() if db.exists() else None) == before
    assert calls[-1][0] == failure

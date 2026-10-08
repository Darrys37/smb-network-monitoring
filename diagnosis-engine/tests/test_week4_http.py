import json
from dataclasses import replace
from unittest.mock import Mock
import pytest
from models import EvidenceRecord
from roadmap_rules import diagnose_roadmap
from http_evidence import load_http_evidence
import http_probe
import app
from test_app_flow import setup
from report import load_report

NOW = 1700000086
TARGET = "192.168.56.20"


def local(status="success", code=200):
    return EvidenceRecord("local_http", TARGET, NOW, {
        "observer": "srv01", "port": 80, "path": "/",
        "local_address_verified": True, "status": status, "http_status": code})


def records(tcp="timeout", extra=None):
    return [EvidenceRecord("ping", TARGET, NOW, {"status": "success"}),
            EvidenceRecord("tcp", TARGET, NOW, {"status": tcp, "port": 80})] + ([] if extra is None else [extra])


@pytest.mark.parametrize("tcp", ["timeout", "refused"])
def test_local_success_is_not_stopped_service(tcp):
    out = diagnose_roadmap("10683", TARGET, records(tcp, local()), now=NOW)
    assert out[1].status == "not_matched"
    assert out[4].status == "matched"
    assert "not proven" in out[4].reasoning


@pytest.mark.parametrize("extra", [None, local("error", None),
    replace(local(), collected_at=NOW-181), replace(local(), collected_at=NOW+1),
    replace(local(), target="192.168.56.30"),
    replace(local(), result={**local().result, "observer": "mon01"}),
    replace(local(), result={**local().result, "local_address_verified": False})])
def test_timeout_cannot_guess_without_local_evidence(extra):
    out = diagnose_roadmap("10683", TARGET, records(extra=extra), now=NOW)
    assert out[1].status == out[4].status == "insufficient_evidence"


def test_local_failure_keeps_service_hypothesis():
    out = diagnose_roadmap("10683", TARGET, records(extra=local("failed", None)), now=NOW)
    assert out[1].status == "matched"
    assert out[4].status == "not_matched"


def write_probe(tmp_path, row=None):
    from dataclasses import asdict
    path = tmp_path / "probe.json"
    data = {"schema_version": 1, "observer": "srv01", "evidence": [asdict(row or local())]}
    path.write_text(json.dumps(data))
    return path


@pytest.mark.parametrize("field,value", [("observer", "mon01"), ("port", True),
    ("http_status", "200"), ("http_status", 503), ("local_address_verified", False)])
def test_import_rejects_wrong_or_inconsistent_result(tmp_path, field, value):
    path = write_probe(tmp_path, replace(local(), result={**local().result, field: value}))
    with pytest.raises(ValueError):
        load_http_evidence(path, TARGET, "srv01", NOW)


@pytest.mark.parametrize("delta", [-181, 1])
def test_import_rejects_bad_time(tmp_path, delta):
    path = write_probe(tmp_path, replace(local(), collected_at=NOW+delta))
    with pytest.raises(ValueError):
        load_http_evidence(path, TARGET, "srv01", NOW)


def test_http_import_persists_with_diagnosis(tmp_path, monkeypatch):
    setup(monkeypatch)
    path = write_probe(tmp_path)
    db = tmp_path / "case.db"
    monkeypatch.setattr("sys.argv", [
        "app.py", "--event-id", "458", "--save",
        "--db", str(db), "--http-evidence", str(path),
        "--http-service", "expected",
    ])
    app.main()
    report = load_report(1, db)
    assert report["diagnoses"][1]["status"] == "not_matched"
    assert report["diagnoses"][4]["status"] == "matched"
    assert any(r["check_type"] == "local_http" for r in report["evidence"])


def test_bad_http_import_never_creates_db(tmp_path, monkeypatch):
    setup(monkeypatch)
    path = write_probe(tmp_path, replace(local(), target="192.168.56.30"))
    db = tmp_path / "case.db"
    monkeypatch.setattr("sys.argv", ["app.py", "--event-id", "458", "--save",
        "--db", str(db), "--http-evidence", str(path)])
    with pytest.raises(ValueError):
        app.main()
    assert not db.exists()


def test_probe_refuses_wrong_host(monkeypatch):
    monkeypatch.setattr(http_probe.socket, "gethostname", lambda: "mon01")
    with pytest.raises(ValueError, match="Run this probe"):
        http_probe.collect_local_http(TARGET)


def test_probe_refuses_nonlocal_address(monkeypatch):
    monkeypatch.setattr(http_probe.socket, "gethostname", lambda: "srv01")
    monkeypatch.setattr(http_probe, "local_addresses", lambda: {"127.0.0.1"})
    with pytest.raises(ValueError, match="not assigned"):
        http_probe.collect_local_http(TARGET)


@pytest.mark.parametrize("outcome,expected", [(200,"success"), (503,"failed"),
    (ConnectionRefusedError("refused"),"failed"), (TimeoutError("timeout"),"failed"),
    (OSError("unknown"),"error")])
def test_probe_preserves_http_failure_and_collector_error(monkeypatch, outcome, expected):
    monkeypatch.setattr(http_probe.socket, "gethostname", lambda: "srv01")
    monkeypatch.setattr(http_probe, "local_addresses", lambda: {TARGET})
    conn = Mock()
    if isinstance(outcome, Exception):
        conn.request.side_effect = outcome
    else:
        conn.getresponse.return_value.status = outcome
    monkeypatch.setattr(http_probe.http.client, "HTTPConnection", lambda *a, **k: conn)
    assert http_probe.collect_local_http(TARGET)["result"]["status"] == expected
    conn.close.assert_called_once()

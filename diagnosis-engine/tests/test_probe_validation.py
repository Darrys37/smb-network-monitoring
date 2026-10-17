"""Boundary tests: malformed external data must fail before any DB write."""

import copy
import json
from unittest.mock import Mock

import pytest
from test_app_flow import setup

import app
import dns_probe
from dns_evidence import load_dns_evidence
from http_evidence import load_http_evidence
from models import EvidenceRecord
from policy import PROBE_MAX_BYTES
from roadmap_rules import diagnose_roadmap

NOW = 1700000086


def dns_payload(versioned=True):
    data = {
        "observer": "cli01",
        "evidence": [
            {
                "check_type": "dns",
                "target": "example.com",
                "collected_at": NOW,
                "result": {
                    "observer": "cli01",
                    "record_type": "A",
                    "status": "timeout",
                    "dns_status": None,
                    "addresses": [],
                },
            },
            {
                "check_type": "dns_control_ping",
                "target": "1.1.1.1",
                "collected_at": NOW,
                "result": {"observer": "cli01", "status": "success"},
            },
        ],
    }
    if versioned:
        data["schema_version"] = 1
    return data


def write_json(tmp_path, data):
    path = tmp_path / "probe.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def load_dns(path):
    return load_dns_evidence(path, "example.com", "1.1.1.1", "cli01", NOW)


@pytest.mark.parametrize("versioned", [False, True])
def test_dns_old_and_new_envelopes_have_identical_diagnosis(tmp_path, versioned):
    records = load_dns(write_json(tmp_path, dns_payload(versioned)))
    diagnoses = diagnose_roadmap(
        "10684",
        "192.168.56.30",
        records,
        dns_name="example.com",
        control_ip="1.1.1.1",
        http_service="absent",
        now=NOW,
    )
    assert diagnoses[3].status == "matched"
    assert diagnoses[1].status == diagnoses[4].status == "not_matched"


@pytest.mark.parametrize("protocol", ["DNS", "HTTP"])
@pytest.mark.parametrize(
    "data",
    [
        [],
        None,
        True,
        1,
        "text",
        {},
        {"evidence": None},
        {"schema_version": True, "observer": "cli01", "evidence": []},
    ],
)
def test_bad_envelope_is_value_error_not_attribute_error(tmp_path, protocol, data):
    path = write_json(tmp_path, data)
    with pytest.raises(ValueError):
        if protocol == "DNS":
            load_dns(path)
        else:
            load_http_evidence(path, "192.168.56.20", "srv01", NOW)


@pytest.mark.parametrize(
    "field,value",
    [
        ("target", "other.example"),
        ("check_type", "tcp"),
        ("collected_at", True),
        ("collected_at", NOW - 181),
        ("collected_at", NOW + 1),
        ("result", []),
        ("result", None),
        ("target", None),
        ("extra", "unexpected"),
    ],
)
def test_rejects_malformed_dns_record(tmp_path, field, value):
    data = dns_payload()
    data["evidence"][0][field] = value
    with pytest.raises(ValueError):
        load_dns(write_json(tmp_path, data))


@pytest.mark.parametrize(
    "field,value",
    [
        ("observer", "mon01"),
        ("record_type", "AAAA"),
        ("status", "unknown"),
        ("status", "success"),
        ("addresses", "1.1.1.1"),
        ("addresses", [True]),
        ("addresses", ["bad-ip"]),
        ("dns_status", []),
    ],
)
def test_rejects_inconsistent_dns_result(tmp_path, field, value):
    data = dns_payload()
    data["evidence"][0]["result"][field] = value
    with pytest.raises(ValueError):
        load_dns(write_json(tmp_path, data))


@pytest.mark.parametrize(
    "change",
    ["duplicate", "missing", "extra", "wrong_ip", "wrong_observer", "stale", "wrong_status"],
)
def test_dns_requires_one_fresh_control_from_same_observer(tmp_path, change):
    data = dns_payload()
    rows = data["evidence"]
    if change == "duplicate":
        rows[1] = copy.deepcopy(rows[0])
    elif change == "missing":
        rows.pop()
    elif change == "extra":
        rows.append(copy.deepcopy(rows[1]))
    elif change == "wrong_ip":
        rows[1]["target"] = "8.8.8.8"
    elif change == "wrong_observer":
        rows[1]["result"]["observer"] = "mon01"
    elif change == "stale":
        rows[1]["collected_at"] = NOW - 181
    else:
        rows[1]["result"]["status"] = "refused"
    with pytest.raises(ValueError):
        load_dns(write_json(tmp_path, data))


@pytest.mark.parametrize(
    "status,code,addresses,expected",
    [
        ("success", "NOERROR", ["192.168.56.20"], "not_matched"),
        ("no_answer", "NOERROR", [], "matched"),
        ("nxdomain", "NXDOMAIN", [], "matched"),
        ("dns_error", "SERVFAIL", [], "matched"),
        ("dns_error", "FORMERR", [], "insufficient_evidence"),
        ("timeout", None, [], "matched"),
        ("error", None, [], "insufficient_evidence"),
    ],
)
def test_dns_preserves_response_vs_collector_error(tmp_path, status, code, addresses, expected):
    data = dns_payload()
    data["evidence"][0]["result"].update(status=status, dns_status=code, addresses=addresses)
    records = load_dns(write_json(tmp_path, data))
    out = diagnose_roadmap(
        "10684", "192.168.56.30", records, dns_name="example.com", control_ip="1.1.1.1", now=NOW
    )
    assert out[3].status == expected


@pytest.mark.parametrize(
    "payload",
    [b"{broken", b"\xff", b" " * (PROBE_MAX_BYTES + 1)],
    ids=["invalid-json", "invalid-utf8", "oversized"],
)
@pytest.mark.parametrize("protocol", ["DNS", "HTTP"])
def test_encoding_json_and_size_fail_cleanly(tmp_path, payload, protocol):
    path = tmp_path / "probe.json"
    path.write_bytes(payload)
    with pytest.raises(ValueError):
        if protocol == "DNS":
            load_dns(path)
        else:
            load_http_evidence(path, "192.168.56.20", "srv01", NOW)


@pytest.mark.parametrize("age", [0, 180])
def test_dns_accepts_freshness_boundary(tmp_path, age):
    data = dns_payload()
    for row in data["evidence"]:
        row["collected_at"] = NOW - age
    assert len(load_dns(write_json(tmp_path, data))) == 2


def test_accepts_file_at_exact_size_limit(tmp_path):
    path = write_json(tmp_path, dns_payload())
    payload = path.read_bytes()
    path.write_bytes(payload + b" " * (PROBE_MAX_BYTES - len(payload)))
    assert len(load_dns(path)) == 2


def test_valid_dns_import_saves_complete_bundle(tmp_path, monkeypatch):
    from report import load_report

    setup(monkeypatch)
    path = write_json(tmp_path, dns_payload())
    db = tmp_path / "case.db"
    app.main(
        [
            "--event-id",
            "458",
            "--save",
            "--db",
            str(db),
            "--dns-evidence",
            str(path),
            "--dns-name",
            "example.com",
            "--dns-control-ip",
            "1.1.1.1",
        ]
    )
    report = load_report(1, db)
    assert len(report["diagnoses"]) == 6
    assert report["diagnoses"][3]["status"] == "matched"
    assert report["diagnoses"][1]["status"] == "insufficient_evidence"
    assert len([row for row in report["evidence"] if row["check_type"].startswith("dns")]) == 2


@pytest.mark.parametrize("version", [True, 0, 2, "1", None])
def test_explicit_bad_dns_version_is_rejected(tmp_path, version):
    data = dns_payload()
    data["schema_version"] = version
    with pytest.raises(ValueError, match="schema_version"):
        load_dns(write_json(tmp_path, data))


@pytest.mark.parametrize("existing", [False, True])
def test_bad_dns_import_never_changes_database(tmp_path, monkeypatch, existing):
    setup(monkeypatch)
    db = tmp_path / "case.db"
    if existing:
        from repository import init_db

        init_db(db)
    before = db.read_bytes() if existing else None
    path = write_json(tmp_path, [])
    with pytest.raises(ValueError, match="envelope"):
        app.main(
            [
                "--event-id",
                "458",
                "--save",
                "--db",
                str(db),
                "--dns-evidence",
                str(path),
                "--dns-name",
                "example.com",
                "--dns-control-ip",
                "1.1.1.1",
            ]
        )
    assert (db.read_bytes() if db.exists() else None) == before


@pytest.mark.parametrize(
    "options", [[], ["--dns-name", "example.com"], ["--dns-control-ip", "1.1.1.1"]]
)
def test_dns_intent_is_required_before_any_api_call(monkeypatch, options):
    api = Mock()
    monkeypatch.setattr(app, "get_open_problems", api)
    with pytest.raises(SystemExit) as error:
        app.main(["--event-id", "458", "--dns-evidence", "not-read.json", *options])
    assert error.value.code == 2
    api.assert_not_called()


def test_probe_output_round_trips_into_loader(tmp_path, monkeypatch):
    rows = dns_payload()["evidence"]
    monkeypatch.setattr(dns_probe.socket, "gethostname", lambda: "CLI01.lab")
    monkeypatch.setattr(dns_probe, "collect_dns", lambda _: EvidenceRecord(**rows[0]))
    monkeypatch.setattr(dns_probe, "collect_ping", lambda _: EvidenceRecord(**rows[1]))
    path = tmp_path / "probe.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "dns_probe.py",
            "--name",
            "EXAMPLE.COM.",
            "--control-ip",
            "1.1.1.1",
            "--output",
            str(path),
        ],
    )
    dns_probe.main()
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 1
    assert len(load_dns(path)) == 2

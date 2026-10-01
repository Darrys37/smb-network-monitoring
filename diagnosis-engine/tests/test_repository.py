import json
import sqlite3
from contextlib import closing
from repository import save_incident_bundle
import pytest

from models import EventRecord, HostRecord, EvidenceRecord, DiagnosisRecord
from repository import init_db, save_event, save_evidence, save_diagnosis

@pytest.fixture
def sample_event():
    return EventRecord(
        event_id="90001",
        clock=1700000000,
        name="TEST: HTTP check failed",
        severity=3,
        value=1,
        hosts=(
            HostRecord(
                host_id="10683",
                host="SRV01",
                name="SRV01",
            ),
        ),
    )


def test_save_event_persists_data(tmp_path, sample_event):
    db_path = tmp_path / "test.db"
    init_db(db_path)

    incident_id = save_event(sample_event, db_path)

    with closing(sqlite3.connect(db_path)) as connection:
        row = connection.execute(
            """
            SELECT event_id, clock, name, severity, value, hosts_json
            FROM incidents WHERE id = ?
            """,
            (incident_id,),
        ).fetchone()

    assert row is not None
    assert row[:5] == (
        "90001",
        1700000000,
        "TEST: HTTP check failed",
        3,
        1,
    )
    assert json.loads(row[5]) == [
        {
            "host_id": "10683",
            "host": "SRV01",
            "name": "SRV01",
        }
    ]


def test_save_same_event_twice_does_not_duplicate(tmp_path, sample_event):
    db_path = tmp_path / "test.db"
    init_db(db_path)

    first_id = save_event(sample_event, db_path)
    second_id = save_event(sample_event, db_path)

    with closing(sqlite3.connect(db_path)) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM incidents"
        ).fetchone()[0]

    assert first_id == second_id
    assert count == 1
@pytest.fixture
def sample_evidence():
    return EvidenceRecord(
        check_type="ping",
        target="192.168.56.20",
        collected_at=1700000010,
        result={"status": "success", "returncode": 0},
    )


def test_save_evidence_persists_data(
    tmp_path, sample_event, sample_evidence
):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    incident_id = save_event(sample_event, db_path)

    evidence_id = save_evidence(
        incident_id, sample_evidence, db_path
    )

    with closing(sqlite3.connect(db_path)) as connection:
        row = connection.execute(
            """
            SELECT incident_id, check_type, target,
                   collected_at, result_json
            FROM evidence WHERE id = ?
            """,
            (evidence_id,),
        ).fetchone()

    assert row is not None
    assert row[:4] == (
        incident_id, "ping", "192.168.56.20", 1700000010
    )
    assert json.loads(row[4]) == sample_evidence.result


def test_evidence_requires_existing_incident(tmp_path, sample_evidence):
    db_path = tmp_path / "test.db"
    init_db(db_path)

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        save_evidence(999, sample_evidence, db_path)

    with closing(sqlite3.connect(db_path)) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM evidence"
        ).fetchone()[0]

    assert count == 0
@pytest.mark.parametrize(
    "status, cause",
    [
        ("matched", "Possible service issue"),
        ("not_matched", None),
        ("insufficient_evidence", None),
    ],
)
def test_save_diagnosis_persists_data(tmp_path, sample_event, status, cause):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    incident_id = save_event(sample_event, db_path)

    diagnosis = DiagnosisRecord(
        rule_id="TEST_RULE",
        status=status,
        probable_cause=cause,
        reasoning="Test explanation",
        missing_info=("Need service status",),
        next_actions=("Inspect service",),
    )
    diagnosis_id = save_diagnosis(incident_id, diagnosis, db_path)

    with closing(sqlite3.connect(db_path)) as connection:
        row = connection.execute(
            """
            SELECT incident_id, rule_id, status, probable_cause,
                   reasoning, missing_info_json, next_actions_json
            FROM diagnoses WHERE id = ?
            """,
            (diagnosis_id,),
        ).fetchone()

    assert row is not None
    assert row[:5] == (
        incident_id, "TEST_RULE", status, cause, "Test explanation"
    )
    assert json.loads(row[5]) == ["Need service status"]
    assert json.loads(row[6]) == ["Inspect service"]


def test_diagnosis_requires_existing_incident(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    diagnosis = DiagnosisRecord(
        rule_id="TEST_RULE",
        status="insufficient_evidence",
        probable_cause=None,
        reasoning="No evidence",
        missing_info=("Need evidence",),
        next_actions=(),
    )

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        save_diagnosis(999, diagnosis, db_path)

    with closing(sqlite3.connect(db_path)) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM diagnoses"
        ).fetchone()[0]

    assert count == 0


def test_diagnosis_rejects_invalid_status(tmp_path, sample_event):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    incident_id = save_event(sample_event, db_path)
    diagnosis = DiagnosisRecord(
        rule_id="TEST_RULE",
        status="wrong_status",
        probable_cause=None,
        reasoning="Invalid status test",
        missing_info=(),
        next_actions=(),
    )

    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        save_diagnosis(incident_id, diagnosis, db_path)

    with closing(sqlite3.connect(db_path)) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM diagnoses"
        ).fetchone()[0]

    assert count == 0

def bundle_records():
    evidence = EvidenceRecord(
        check_type="tcp",
        target="192.168.56.20",
        collected_at=1700000200,
        result={"port": 80, "status": "refused"},
    )
    diagnosis = DiagnosisRecord(
        rule_id="HTTP_PORT_REFUSED",
        status="matched",
        probable_cause="Possible service issue",
        reasoning="TCP connection refused.",
        missing_info=("Need service status",),
        next_actions=("Inspect nginx",),
    )
    return evidence, diagnosis


def bundle_snapshot(db_path):
    with closing(sqlite3.connect(db_path)) as connection:
        return {
            table: connection.execute(
                f"SELECT * FROM {table} ORDER BY id"
            ).fetchall()
            for table in ("incidents", "evidence", "diagnoses")
        }


def test_bundle_saves_linked_records(tmp_path, sample_event):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    evidence, diagnosis = bundle_records()

    incident_id = save_incident_bundle(
        sample_event, [evidence], [diagnosis], db_path
    )

    with closing(sqlite3.connect(db_path)) as connection:
        event_row = connection.execute(
            "SELECT event_id FROM incidents WHERE id = ?",
            (incident_id,),
        ).fetchone()
        evidence_row = connection.execute(
            "SELECT incident_id, result_json FROM evidence"
        ).fetchone()
        diagnosis_row = connection.execute(
            "SELECT incident_id, rule_id, status FROM diagnoses"
        ).fetchone()

    assert event_row == (sample_event.event_id,)
    assert evidence_row[0] == incident_id
    assert json.loads(evidence_row[1]) == evidence.result
    assert diagnosis_row == (
        incident_id, "HTTP_PORT_REFUSED", "matched"
    )

    snapshot = bundle_snapshot(db_path)
    assert [len(snapshot[t]) for t in (
        "incidents", "evidence", "diagnoses"
    )] == [1, 1, 1]


def test_bundle_rejects_repeat_without_changes(tmp_path, sample_event):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    evidence, diagnosis = bundle_records()

    save_incident_bundle(
        sample_event, [evidence], [diagnosis], db_path
    )
    before = bundle_snapshot(db_path)

    with pytest.raises(ValueError, match="already has"):
        save_incident_bundle(
            sample_event, [evidence], [diagnosis], db_path
        )

    assert bundle_snapshot(db_path) == before


@pytest.mark.parametrize("existing_incident", [False, True])
def test_bundle_rolls_back_on_invalid_diagnosis(
    tmp_path, sample_event, existing_incident
):
    from dataclasses import replace

    db_path = tmp_path / "test.db"
    init_db(db_path)

    if existing_incident:
        save_event(sample_event, db_path)

    before = bundle_snapshot(db_path)
    evidence, diagnosis = bundle_records()
    invalid = replace(diagnosis, status="wrong_status")

    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        save_incident_bundle(
            sample_event,
            [evidence],
            [diagnosis, invalid],
            db_path,
        )

    assert bundle_snapshot(db_path) == before


def test_bundle_completes_existing_incident(tmp_path, sample_event):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    original_id = save_event(sample_event, db_path)
    evidence, diagnosis = bundle_records()

    incident_id = save_incident_bundle(
        sample_event, [evidence], [diagnosis], db_path
    )

    assert incident_id == original_id
    snapshot = bundle_snapshot(db_path)
    assert [len(snapshot[t]) for t in (
        "incidents", "evidence", "diagnoses"
    )] == [1, 1, 1]

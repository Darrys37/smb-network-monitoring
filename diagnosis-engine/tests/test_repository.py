import json
import sqlite3
from contextlib import closing

import pytest

from models import EventRecord, HostRecord, EvidenceRecord
from repository import init_db, save_event, save_evidence

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

import json
import sqlite3
from pathlib import Path
from dataclasses import asdict
from models import EventRecord, EvidenceRecord, DiagnosisRecord

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "diagnosis.db"

def init_db(db_path=DEFAULT_DB_PATH):
    connection = sqlite3.connect(db_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY,
                event_id TEXT NOT NULL UNIQUE,
                clock INTEGER NOT NULL CHECK (clock >=0),
                name TEXT NOT NULL,
                severity INTEGER NOT NULL
                    CHECK (severity BETWEEN 0 AND 5),
                value INTEGER NOT NULL
                    CHECK (value IN (0,1)),
                hosts_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY,
                incident_id INTEGER NOT NULL,
                check_type TEXT NOT NULL,
                target TEXT NOT NULL,
                collected_at INTEGER NOT NULL,
                result_json TEXT NOT NULL,
                FOREIGN KEY (incident_id) REFERENCES incidents(id)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS diagnoses (
                id INTEGER PRIMARY KEY,
                incident_id INTEGER NOT NULL,
                rule_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK (
                    status IN (
                        'matched',
                        'not_matched',
                        'insufficient_evidence'
                    )
                ),
                probable_cause TEXT,
                reasoning TEXT NOT NULL,
                missing_info_json TEXT NOT NULL,
                next_actions_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (incident_id) REFERENCES incidents(id)
            )
        """)
        connection.commit()
    finally:
        connection.close()
def save_event(event: EventRecord, db_path=DEFAULT_DB_PATH):
    hosts_json = json.dumps(
        [asdict(host) for host in event.hosts],
        ensure_ascii=False,
     )

    connection = sqlite3.connect(db_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("""
             INSERT INTO incidents (
                 event_id, clock, name, severity, value, hosts_json
             )
             VALUES (?, ?, ?, ?, ?, ?)
             ON CONFLICT(event_id) DO NOTHING
         """,(
             event.event_id,
             event.clock,
             event.name,
             event.severity,
             event.value,
             hosts_json,
         ))

        row = connection.execute(
             "SELECT id FROM incidents WHERE event_id = ?",
             (event.event_id,),
         ).fetchone()

        connection.commit()
        return row[0]
    finally:
        connection.close()          
def save_evidence(
    incident_id: int,
    evidence: EvidenceRecord,
    db_path=DEFAULT_DB_PATH,
):
    result_json = json.dumps(evidence.result, ensure_ascii=False)
    connection = sqlite3.connect(db_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        cursor = connection.execute("""
            INSERT INTO evidence (
                incident_id, check_type, target,
                collected_at, result_json
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            incident_id,
            evidence.check_type,
            evidence.target,
            evidence.collected_at,
            result_json,
        ))

        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()
def save_diagnosis(
    incident_id: int,
    diagnosis: DiagnosisRecord,
    db_path=DEFAULT_DB_PATH,
):
    missing_json = json.dumps(
        diagnosis.missing_info, ensure_ascii=False
    )
    actions_json = json.dumps(
        diagnosis.next_actions, ensure_ascii=False
    )
    connection = sqlite3.connect(db_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        cursor = connection.execute("""
            INSERT INTO diagnoses (
                incident_id, rule_id, status, probable_cause,
                reasoning, missing_info_json, next_actions_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            incident_id,
            diagnosis.rule_id,
            diagnosis.status,
            diagnosis.probable_cause,
            diagnosis.reasoning,
            missing_json,
            actions_json,
        ))

        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()
def save_incident_bundle(
    event: EventRecord,
    evidence,
    diagnoses,
    db_path=DEFAULT_DB_PATH,
):
    evidence = list(evidence)
    diagnoses = list(diagnoses)

    if not evidence or not diagnoses:
        raise ValueError("Evidence and diagnoses must not be empty")

    hosts_json = json.dumps(
        [asdict(host) for host in event.hosts],
        ensure_ascii=False,
    )

    connection = sqlite3.connect(db_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")

        connection.execute("""
            INSERT INTO incidents (
                event_id, clock, name, severity, value, hosts_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO NOTHING
        """, (
            event.event_id,
            event.clock,
            event.name,
            event.severity,
            event.value,
            hosts_json,
        ))

        incident_id = connection.execute(
            "SELECT id FROM incidents WHERE event_id = ?",
            (event.event_id,),
        ).fetchone()[0]

        for table in ("evidence", "diagnoses"):
            existing = connection.execute(
                f"SELECT 1 FROM {table} WHERE incident_id = ? LIMIT 1",
                (incident_id,),
            ).fetchone()

            if existing is not None:
                raise ValueError(
                    f"Incident {incident_id} already has {table}; "
                    "refusing to append a duplicate or mixed bundle"
                )

        connection.executemany("""
            INSERT INTO evidence (
                incident_id, check_type, target,
                collected_at, result_json
            )
            VALUES (?, ?, ?, ?, ?)
        """, [
            (
                incident_id,
                record.check_type,
                record.target,
                record.collected_at,
                json.dumps(record.result, ensure_ascii=False),
            )
            for record in evidence
        ])

        connection.executemany("""
            INSERT INTO diagnoses (
                incident_id, rule_id, status, probable_cause,
                reasoning, missing_info_json, next_actions_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            (
                incident_id,
                diagnosis.rule_id,
                diagnosis.status,
                diagnosis.probable_cause,
                diagnosis.reasoning,
                json.dumps(diagnosis.missing_info, ensure_ascii=False),
                json.dumps(diagnosis.next_actions, ensure_ascii=False),
            )
            for diagnosis in diagnoses
        ])

        connection.commit()
        return incident_id

    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_incident(event_id, db_path=DEFAULT_DB_PATH):
    """Read only: a missing database must never be silently created."""
    from contextlib import closing
    path = Path(db_path).resolve()
    if not path.is_file():
        raise ValueError("Database does not exist; save a problem first")
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM incidents WHERE event_id=?",
                           (str(event_id),)).fetchone()
        if row is None:
            raise ValueError("No stored incident for this event ID")
        return dict(row)


def save_recovery(problem, recovery, db_path=DEFAULT_DB_PATH):
    """Append verified recovery; never overwrite original evidence or event value.

    Additive migration inside a transaction also supports the original Week 3 DB.
    No connection is opened until all API event validation is complete.
    """
    import time
    from contextlib import closing
    event_id = str(problem.get("eventid", ""))
    stored = get_incident(event_id, db_path)
    recovery_id = str(recovery.get("eventid", ""))
    if not recovery_id.isdigit() or int(recovery_id) <= 0 or recovery_id == event_id:
        raise ValueError("Invalid recovery event ID")
    if str(problem.get("r_eventid")) != recovery_id:
        raise ValueError("Recovery event is not linked by the problem")
    if str(problem.get("value")) != "1" or str(recovery.get("value")) != "0":
        raise ValueError("Expected problem value=1 and recovery value=0")
    for item in (problem, recovery):
        if str(item.get("source")) != "0" or str(item.get("object")) != "0":
            raise ValueError("Expected trigger events")
    trigger_id = str(problem.get("objectid", ""))
    if not trigger_id.isdigit() or int(trigger_id) <= 0 or str(recovery.get("objectid")) != trigger_id:
        raise ValueError("Problem and recovery must reference the same trigger")
    expected_hosts = {h["host_id"] for h in json.loads(stored["hosts_json"])}
    for item in (problem, recovery):
        if {str(h["hostid"]) for h in item.get("hosts", [])} != expected_hosts:
            raise ValueError("Event host identity differs from stored incident")
    problem_clock = int(problem["clock"])
    recovery_clock = int(recovery["clock"])
    checked_at = int(time.time())
    if problem_clock != stored["clock"] or not problem_clock <= recovery_clock <= checked_at:
        raise ValueError("Invalid or mismatched event timestamps")
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("""CREATE TABLE IF NOT EXISTS recoveries (
                incident_id INTEGER PRIMARY KEY REFERENCES incidents(id),
                recovery_event_id TEXT NOT NULL,
                recovery_clock INTEGER NOT NULL,
                verified_at INTEGER NOT NULL,
                problem_json TEXT NOT NULL,
                recovery_json TEXT NOT NULL
            )""")
            old = conn.execute("SELECT recovery_event_id, recovery_clock FROM recoveries WHERE incident_id=?",
                               (stored["id"],)).fetchone()
            if old is not None:
                if old != (recovery_id, recovery_clock):
                    raise ValueError("Conflicting recovery already stored; refusing overwrite")
                return stored["id"]
            conn.execute("INSERT INTO recoveries VALUES (?, ?, ?, ?, ?, ?)", (
                stored["id"], recovery_id, recovery_clock, checked_at,
                json.dumps(problem, ensure_ascii=False),
                json.dumps(recovery, ensure_ascii=False),
            ))
    return stored["id"]

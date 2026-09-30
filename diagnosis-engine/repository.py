import json
import sqlite3
from pathlib import Path
from dataclasses import asdict
from models import EventRecord

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
                id ITEGER PRIMARY KEY,
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
                id  INTEGER PRIMARY KEY,
                incident_id INTEGER NOT NULL,
                rule_id TEXT NOT NULL,
                probable_cause TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                missing_info_json TEXT NOT NULL,
                next_actions_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CUREENT_TIMESTAMP,
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

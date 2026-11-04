"""Durable dedup, event cursors and append-only correlation/diagnosis audit."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid

from .correlation import event_order, normalize_event


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db, db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS events(source TEXT NOT NULL,event_id TEXT NOT NULL,clock INTEGER NOT NULL,node TEXT NOT NULL,kind TEXT NOT NULL,state TEXT NOT NULL,key TEXT NOT NULL,payload_json TEXT NOT NULL,received_at INTEGER NOT NULL,PRIMARY KEY(source,event_id));
            CREATE INDEX IF NOT EXISTS events_clock ON events(clock);
            CREATE TABLE IF NOT EXISTS cursors(stream TEXT PRIMARY KEY,cursor TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS diagnostics(id TEXT PRIMARY KEY,decision_clock INTEGER NOT NULL,profile_id TEXT NOT NULL,event_source TEXT,event_id TEXT,observation_json TEXT NOT NULL,assessment_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,decision_clock INTEGER NOT NULL,correlation_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS node_states(node TEXT PRIMARY KEY,status TEXT NOT NULL,observed_at INTEGER NOT NULL,down_since INTEGER,evidence_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS jobs(source TEXT NOT NULL,event_id TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'pending',attempts INTEGER NOT NULL DEFAULT 0,next_attempt_at INTEGER NOT NULL DEFAULT 0,last_error TEXT,diagnostic_id TEXT,PRIMARY KEY(source,event_id),FOREIGN KEY(source,event_id) REFERENCES events(source,event_id));
            CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            """)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def ingest(self, events, received_at, *, stream=None, cursor=None):
        added = 0
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            for item in events:
                event = normalize_event(item)
                old = db.execute("SELECT clock,node,kind,state,key FROM events WHERE source=? AND event_id=?", (event["source"], event["event_id"])).fetchone()
                immutable = (event["clock"], event["node"], event["kind"], event["state"], event["key"])
                if old is not None and old != immutable:
                    raise ValueError("Conflicting duplicate event; cursor unchanged")
                result = db.execute("INSERT OR IGNORE INTO events VALUES(?,?,?,?,?,?,?,?,?)", (event["source"], event["event_id"], *immutable, json.dumps(event, allow_nan=False), received_at))
                added += result.rowcount
                db.execute("INSERT OR IGNORE INTO jobs(source,event_id) VALUES(?,?)", (event["source"], event["event_id"]))
            if stream is not None and cursor is not None:
                previous = db.execute("SELECT cursor FROM cursors WHERE stream=?", (stream,)).fetchone()
                if previous and str(cursor).isdigit() and previous[0].isdigit():
                    cursor = str(max(int(cursor), int(previous[0])))
                db.execute("INSERT INTO cursors VALUES(?,?) ON CONFLICT(stream) DO UPDATE SET cursor=excluded.cursor", (stream, str(cursor)))
        return added

    def cursor(self, stream):
        with closing(self.connect()) as db:
            value = db.execute("SELECT cursor FROM cursors WHERE stream=?", (stream,)).fetchone()
            return value[0] if value else None

    def events(self):
        with closing(self.connect()) as db:
            return sorted([json.loads(row[0]) for row in db.execute("SELECT payload_json FROM events")], key=event_order)

    def set_node_state(self, node, status, observed_at, evidence):
        if status not in {"up", "down", "unknown"}:
            raise ValueError("Invalid node status")
        with closing(self.connect()) as db, db:
            old = db.execute("SELECT status,observed_at,down_since FROM node_states WHERE node=?", (node,)).fetchone()
            if old and observed_at < old[1]:
                raise ValueError("Node status cannot move backwards in time")
            since = old[2] if old and old[0] == "down" and status == "down" else observed_at if status == "down" else None
            db.execute("INSERT INTO node_states VALUES(?,?,?,?,?) ON CONFLICT(node) DO UPDATE SET status=excluded.status,observed_at=excluded.observed_at,down_since=excluded.down_since,evidence_json=excluded.evidence_json", (node, status, observed_at, since, json.dumps(evidence, allow_nan=False)))

    def node_states(self):
        with closing(self.connect()) as db:
            return {node: {"status": status, "observed_at": clock, "down_since": since, "evidence": json.loads(evidence)}
                    for node, status, clock, since, evidence in db.execute("SELECT * FROM node_states")}

    def save_diagnostic(self, profile_id, observation, assessment, *, event_source=None, event_id=None):
        identity = uuid.uuid4().hex
        with closing(self.connect()) as db, db:
            db.execute("INSERT INTO diagnostics VALUES(?,?,?,?,?,?,?)", (identity, observation["decision_time"], profile_id, event_source, event_id, json.dumps(observation, allow_nan=False), json.dumps(assessment, allow_nan=False)))
        return identity

    def save_batch(self, result):
        identity = uuid.uuid4().hex
        with closing(self.connect()) as db, db:
            db.execute("INSERT INTO batches VALUES(?,?,?)", (identity, result["decision_time"], json.dumps(result, allow_nan=False)))
        return identity

    def pending_jobs(self, now, limit=1000):
        with closing(self.connect()) as db:
            return [json.loads(row[0]) for row in db.execute("SELECT e.payload_json FROM jobs j JOIN events e USING(source,event_id) WHERE j.state='pending' AND j.next_attempt_at<=? ORDER BY e.clock,e.event_id LIMIT ?", (now, limit))]

    def complete_jobs(self, events, diagnostic_id):
        with closing(self.connect()) as db, db:
            db.executemany("UPDATE jobs SET state='done',diagnostic_id=?,last_error=NULL WHERE source=? AND event_id=?", [(diagnostic_id, event["source"], event["event_id"]) for event in events])

    def retry_jobs(self, events, now, error_type):
        with closing(self.connect()) as db, db:
            for event in events:
                row = db.execute("SELECT attempts FROM jobs WHERE source=? AND event_id=?", (event["source"], event["event_id"])).fetchone()
                attempts = row[0] + 1
                db.execute("UPDATE jobs SET attempts=?,next_attempt_at=?,last_error=? WHERE source=? AND event_id=?", (attempts, now + min(60, 5 * 2 ** min(attempts, 5)), error_type, event["source"], event["event_id"]))

    def metadata(self, key, value=None):
        with closing(self.connect()) as db, db:
            if value is not None:
                db.execute("INSERT INTO metadata VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
            result = db.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
            return result[0] if result else None

    def counts(self):
        with closing(self.connect()) as db:
            result = {table: db.execute("SELECT COUNT(*) FROM " + table).fetchone()[0] for table in ("events", "diagnostics", "batches")}
            result["pending_jobs"] = db.execute("SELECT COUNT(*) FROM jobs WHERE state='pending'").fetchone()[0]
            return result

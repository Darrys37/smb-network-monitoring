import json
import sqlite3
import tempfile
import time
from contextlib import closing
from pathlib import Path

from evidence import collect_ping, collect_tcp, collect_dns, collect_metrics
from models import EventRecord, HostRecord
from repository import init_db, save_event, save_evidence


def main():
    event = EventRecord(
        event_id="90001",
        clock=int(time.time()),
        name="TEST ONLY: evidence integration",
        severity=0,
        value=1,
        hosts=(HostRecord("10683", "SRV01", "SRV01"),),
    )

    records = [
        collect_ping("192.168.56.20"),
        collect_tcp("192.168.56.20", 80),
        collect_dns("example.com"),
        *collect_metrics("10683"),
    ]

    with tempfile.TemporaryDirectory() as folder:
        db_path = Path(folder) / "integration.db"
        init_db(db_path)
        incident_id = save_event(event, db_path)

        for record in records:
            save_evidence(incident_id, record, db_path)

        with closing(sqlite3.connect(db_path)) as connection:
            rows = connection.execute(
                """
                SELECT check_type, target, collected_at, result_json
                FROM evidence
                WHERE incident_id = ?
                ORDER BY id
                """,
                (incident_id,),
            ).fetchall()

        assert len(rows) == len(records) == 7

        for row, original in zip(rows, records):
            assert row[:3] == (
                original.check_type,
                original.target,
                original.collected_at,
            )
            result = json.loads(row[3])
            assert result == original.result
            label = result.get("key", "")
            print(row[0], row[1], label, result["status"])

        print("Evidence integration OK: 7 records verified")

if __name__ == "__main__":
    main()

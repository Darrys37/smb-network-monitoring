import sqlite3
from contextlib import closing

from event_parser import parse_event
from repository import DEFAULT_DB_PATH, init_db, save_event
from zabbix_client import get_recent_events


def count_incidents():
    with closing(sqlite3.connect(DEFAULT_DB_PATH)) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM incidents"
        ).fetchone()[0]


def main():
    init_db()
    raw_events = get_recent_events()
    events = [parse_event(raw) for raw in raw_events]

    print(f"Events received: {len(events)}")
    if not events:
        print("No events to test.")
        return

    before = count_incidents()

    first_ids = [save_event(event) for event in events]
    after_first = count_incidents()

    second_ids = [save_event(event) for event in events]
    after_second = count_incidents()

    print(f"Before: {before}")
    print(f"After first save: {after_first}")
    print(f"After second save: {after_second}")

    assert first_ids == second_ids, "Incident IDs changed"
    assert after_first == after_second, "Duplicate incidents created"
    print("Real-event duplicate check OK")


if __name__ == "__main__":
    main()

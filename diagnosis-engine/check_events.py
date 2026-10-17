"""Manual API/parser check. Importing this module performs no requests."""

from event_parser import parse_event
from zabbix_client import get_recent_events


def main():
    events = get_recent_events()
    print(f"Events received: {len(events)}")

    passed = 0
    failed = 0

    for raw in events:
        try:
            event = parse_event(raw)
        except ValueError as exc:
            failed += 1
            print(f"PARSE ERROR: {exc}")
            continue

        passed += 1
        print(event)

    print(f"Parsed: {passed}; Failed: {failed}")


if __name__ == "__main__":
    main()

"""Synchronize a known incident's recovery using read-only Zabbix API calls."""
import argparse
import sqlite3
from pathlib import Path
from repository import DEFAULT_DB_PATH, get_incident, save_recovery
from zabbix_client import get_event_by_id


def sync_recovery(event_id, db_path=DEFAULT_DB_PATH):
    get_incident(event_id, db_path)
    problem = get_event_by_id(event_id)
    if str(problem.get("eventid")) != str(event_id):
        raise ValueError("Returned problem ID mismatch")
    recovery_id = str(problem.get("r_eventid", ""))
    if not recovery_id.isdigit():
        raise ValueError("Missing or invalid r_eventid; status unknown")
    if recovery_id == "0":
        return None
    recovery = get_event_by_id(recovery_id)
    return save_recovery(problem, recovery, db_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()
    try:
        incident_id = sync_recovery(args.event_id, args.db)
        if incident_id is None:
            print("No linked recovery returned; stored records unchanged.")
        else:
            print(f"Incident {incident_id}: closed (verified Zabbix recovery stored).")
    except (RuntimeError, ValueError, KeyError, TypeError, sqlite3.Error, OSError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()

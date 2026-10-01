import argparse
import time
import json
import sqlite3
from pathlib import Path
from models import EvidenceRecord
from roadmap_rules import diagnose_roadmap
from roadmap_evidence import collect_agent_metric, collect_cpu_history
from repository import DEFAULT_DB_PATH

from event_parser import parse_event
from evidence import collect_ping, collect_tcp, collect_metrics
from repository import init_db, save_incident_bundle
from rules import diagnose_all
from zabbix_client import get_open_problems, get_event_by_id


HOST_ID = "10683"
TARGET_IP = "192.168.56.20"


def require_open_event(event_id, host_id=HOST_ID):
    problems = get_open_problems(host_id)
    open_ids = {str(problem["eventid"]) for problem in problems}

    if str(event_id) not in open_ids:
        raise ValueError(
            "Event is not an accessible open problem on the selected host."
        )

    raw = get_event_by_id(event_id)
    event = parse_event(raw)

    if event.event_id != str(event_id):
        raise ValueError("Returned event ID does not match.")

    if event.value != 1 or str(raw.get("r_eventid")) != "0":
        raise ValueError("Event is not an unresolved problem.")

    if str(host_id) not in {host.host_id for host in event.hosts}:
        raise ValueError("Event does not belong to the selected host.")

    return event


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate current evidence for an SRV01 problem."
    )
    parser.add_argument("--event-id")
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--host-id", default=HOST_ID)
    parser.add_argument("--target-ip", default=TARGET_IP)
    parser.add_argument("--ruleset", choices=("legacy", "roadmap"), default="roadmap")
    parser.add_argument("--gateway-ip")
    parser.add_argument("--peer-ip")
    parser.add_argument("--dns-name")
    parser.add_argument("--dns-observer", default="cli01")
    parser.add_argument("--dns-evidence", type=Path)

    args = parser.parse_args()

    if args.save and args.event_id is None:
        parser.error("--save requires --event-id")

    if args.event_id is None:
        problems = get_open_problems(args.host_id)
        print("Open problems on SRV01:", len(problems))

        for problem in problems:
            print(problem["eventid"], problem["name"])

        return

    event = require_open_event(args.event_id, args.host_id)
    started_at = int(time.time())

    records = [
        collect_ping(args.target_ip),
        collect_tcp(args.target_ip, 80),
        *collect_metrics(args.host_id),
    ]

    if args.ruleset == "legacy":
        diagnoses = diagnose_all(args.host_id, args.target_ip, records, now=int(time.time()))
    else:
        records += [collect_tcp(args.target_ip, 10050),
                    collect_agent_metric(args.host_id), collect_cpu_history(args.host_id)]
        for ip in dict.fromkeys([args.gateway_ip, args.peer_ip]):
            if ip and ip != args.target_ip:
                records.append(collect_ping(ip))
        if args.dns_evidence:
            data = json.loads(args.dns_evidence.read_text(encoding="utf-8"))
            if data.get("observer") != args.dns_observer:
                raise ValueError("DNS observer mismatch")
            for row in data["evidence"]:
                if row["check_type"] not in ("dns", "dns_control_ping"):
                    raise ValueError("Unexpected check type in DNS evidence")
                if row["result"].get("observer") != args.dns_observer:
                    raise ValueError("DNS record observer mismatch")
                if type(row["collected_at"]) is not int:
                    raise ValueError("Invalid DNS timestamp")
                records.append(EvidenceRecord(**row))
        diagnoses = diagnose_roadmap(
            args.host_id, args.target_ip, records,
            gateway=args.gateway_ip, peer=args.peer_ip,
            dns_name=args.dns_name, dns_observer=args.dns_observer,
            now=int(time.time()),
        )

    # Check again because recovery may occur during collection.
    require_open_event(event.event_id, args.host_id)

    print("Event:", event.event_id, event.name)
    print("Event timestamp:", event.clock)
    print("Collection started:", started_at)
    print("Evidence records:", len(records))
    print("Assessment uses current evidence.")

    for diagnosis in diagnoses:
        print(diagnosis.rule_id, diagnosis.status)
        print("  Reason:", diagnosis.reasoning)

        for item in diagnosis.missing_info:
            print("  Missing:", item)

        for action in diagnosis.next_actions:
            print("  Next:", action)

    if args.save:
        init_db(args.db)
        incident_id = save_incident_bundle(
            event, records, diagnoses, args.db
        )
        print("Saved incident ID:", incident_id)
    else:
        print("Preview only; database unchanged.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyError, TypeError, OSError, sqlite3.Error) as exc:
        raise SystemExit(f"Error: {exc}")

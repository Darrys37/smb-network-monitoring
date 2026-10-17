"""Validate event, collect, evaluate, recheck, display, then optionally save.

Rules do not perform I/O; collectors do not diagnose; repository owns SQLite.
Current evidence does not reconstruct the state at the original event time.
"""

import argparse
import sqlite3
import time
from pathlib import Path

from dns_evidence import load_dns_evidence
from event_parser import parse_event
from evidence import collect_metrics, collect_ping, collect_tcp
from http_evidence import load_http_evidence
from policy import DEFAULT_HTTP_SERVICE, HTTP_SERVICE_SCOPES
from repository import DEFAULT_DB_PATH, init_db, save_incident_bundle
from roadmap_evidence import collect_agent_metric, collect_cpu_history
from roadmap_rules import diagnose_roadmap
from rules import diagnose_all
from zabbix_client import get_event_by_id, get_open_problems

HOST_ID = "10683"
TARGET_IP = "192.168.56.20"


def require_open_event(event_id, host_id=HOST_ID):
    """Require an accessible unresolved problem belonging to the chosen host."""
    problems = get_open_problems(host_id)
    open_ids = {str(problem["eventid"]) for problem in problems}

    if str(event_id) not in open_ids:
        raise ValueError("Event is not an accessible open problem on the selected host.")

    raw = get_event_by_id(event_id)
    event = parse_event(raw)

    if event.event_id != str(event_id):
        raise ValueError("Returned event ID does not match.")

    if event.value != 1 or str(raw.get("r_eventid")) != "0":
        raise ValueError("Event is not an unresolved problem.")

    if str(host_id) not in {host.host_id for host in event.hosts}:
        raise ValueError("Event does not belong to the selected host.")

    return event


def build_parser():
    """Declare CLI options in one place, with the same scope default as rules."""
    parser = argparse.ArgumentParser(
        description="Evaluate current evidence for a selected host problem."
    )
    parser.add_argument("--event-id")
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--host-id", default=HOST_ID)
    parser.add_argument("--target-ip", default=TARGET_IP)
    parser.add_argument("--ruleset", choices=("legacy", "roadmap"), default="roadmap")
    parser.add_argument("--control-ip", help="Distinct same-subnet control host for R1")
    parser.add_argument("--http-evidence", type=Path)
    parser.add_argument("--http-observer", default="srv01")
    parser.add_argument(
        "--http-service",
        choices=HTTP_SERVICE_SCOPES,
        default=DEFAULT_HTTP_SERVICE,
        help="Unknown HTTP applicability leaves R2/R5 insufficient.",
    )
    parser.add_argument("--dns-name")
    parser.add_argument("--dns-control-ip", help="IP control probed from the DNS observer")
    parser.add_argument("--dns-observer", default="cli01")
    parser.add_argument("--dns-evidence", type=Path)

    return parser


def validate_args(parser, args):
    """Reject incomplete operator intent before calling APIs or probing."""
    if args.save and args.event_id is None:
        parser.error("--save requires --event-id")

    if args.ruleset == "roadmap" and args.dns_evidence:
        if not args.dns_name or not args.dns_control_ip:
            parser.error("--dns-evidence requires --dns-name and --dns-control-ip")


def collect_evidence(args):
    """Collect sequentially in the original order; failures abort the run."""
    records = [
        collect_ping(args.target_ip),
        collect_tcp(args.target_ip, 80),
        *collect_metrics(args.host_id),
    ]

    if args.ruleset == "legacy":
        return records
    records.extend(
        [
            collect_tcp(args.target_ip, 10050),
            collect_agent_metric(args.host_id),
            collect_cpu_history(args.host_id),
        ]
    )
    if args.control_ip and args.control_ip != args.target_ip:
        records.append(collect_ping(args.control_ip))
    if args.http_evidence:
        records.extend(
            load_http_evidence(
                args.http_evidence, args.target_ip, args.http_observer, int(time.time())
            )
        )
    if args.dns_evidence:
        records.extend(
            load_dns_evidence(
                args.dns_evidence,
                args.dns_name,
                args.dns_control_ip,
                args.dns_observer,
                int(time.time()),
            )
        )
    return records


def evaluate_evidence(args, records, now):
    """Select a ruleset. Evaluation itself has no API/network/SQLite writes."""
    if args.ruleset == "legacy":
        return diagnose_all(args.host_id, args.target_ip, records, now=now)
    return diagnose_roadmap(
        args.host_id,
        args.target_ip,
        records,
        control=args.control_ip,
        http_observer=args.http_observer,
        dns_name=args.dns_name,
        dns_observer=args.dns_observer,
        control_ip=args.dns_control_ip,
        http_service=args.http_service,
        now=now,
    )


def print_assessment(event, started_at, records, diagnoses):
    """Preserve the console format consumed by experiment scripts."""
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


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)
    if args.event_id is None:
        problems = get_open_problems(args.host_id)
        print(f"Open problems on host {args.host_id}:", len(problems))
        for problem in problems:
            print(problem["eventid"], problem["name"])
        return

    event = require_open_event(args.event_id, args.host_id)
    started_at = int(time.time())
    records = collect_evidence(args)
    diagnoses = evaluate_evidence(args, records, now=int(time.time()))

    # Recovery may occur during collection. This recheck is not a distributed lock.
    require_open_event(event.event_id, args.host_id)
    print_assessment(event, started_at, records, diagnoses)
    if args.save:
        init_db(args.db)
        incident_id = save_incident_bundle(event, records, diagnoses, args.db)
        print("Saved incident ID:", incident_id)
    else:
        print("Preview only; database unchanged.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyError, TypeError, OSError, sqlite3.Error) as exc:
        raise SystemExit(f"Error: {exc}")

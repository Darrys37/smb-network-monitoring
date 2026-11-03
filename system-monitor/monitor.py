"""SQLite expert and alert correlation CLI. Online mode runs on MON01."""
import argparse
import json
from pathlib import Path
import sys
import time

from monitoring.catalog import ExpertCatalog
from monitoring.correlation import correlate
from monitoring.store import Store
from monitoring.topology import Topology
from monitoring.vector import feature_vector


def save_new(path, value):
    data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(data)


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=root / "catalog/expert_rules.sqlite")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("rules")
    replay = sub.add_parser("replay")
    replay.add_argument("--observation", type=Path, required=True)
    replay.add_argument("--output", type=Path)
    grouped = sub.add_parser("correlate")
    grouped.add_argument("--events", type=Path, required=True)
    grouped.add_argument("--topology", type=Path, required=True)
    grouped.add_argument("--states", type=Path, required=True)
    grouped.add_argument("--now", type=int, required=True)
    grouped.add_argument("--output", type=Path)
    for name in ("once", "watch"):
        live = sub.add_parser(name)
        live.add_argument("--config", type=Path, default=root / "config/lab.json")
        live.add_argument("--state", type=Path, default=root / "runtime/monitoring.sqlite")
        live.add_argument("--engine-source", type=Path, default=root.parent / "diagnosis-engine")
        live.add_argument("--interval", type=float, default=5)
        live.add_argument("--output", type=Path)
        live.add_argument("--probe-all", action="store_true")
    args = parser.parse_args()
    if getattr(args, "interval", 5) < 1:
        parser.error("--interval must be at least one second")
    catalog = ExpertCatalog(args.catalog)
    if args.command == "rules":
        result = {"version": catalog.metadata["version"], "rules": [{key: row[key] for key in ("rule_id", "group", "title", "hypotheses")} for row in catalog.rules],
                  "condition_source": "SQLite decision_rows", "confidence_kind": catalog.metadata["confidence_kind"]}
    elif args.command == "replay":
        observation = read(args.observation)
        profile = dict(observation["profile"])
        profile.setdefault("http_observer", profile.get("observer", "srv01"))
        profile.setdefault("dns_observer", profile.get("observer", "cli01"))
        result = catalog.assess(profile, observation["evidence"], observation["decision_time"])
        result["feature_vector"] = feature_vector(result["facts"], catalog.metadata["policy"])
    elif args.command == "correlate":
        result = correlate(read(args.events), Topology(read(args.topology)), read(args.states), args.now,
                           window_seconds=catalog.metadata["correlation_window_seconds"])
    else:
        from monitoring.collector import NativeBackend
        from monitoring.worker import Worker
        config = read(args.config)
        # One live worker owns transitions/cursor. SQLite transactions alone
        # would not prevent duplicate measurements from two parallel workers.
        import fcntl
        args.state.parent.mkdir(parents=True, exist_ok=True)
        worker_lock = args.state.with_suffix(".lock").open("a")
        fcntl.flock(worker_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        backend = NativeBackend(args.engine_source, config["remote_probes"])
        worker = Worker(backend, catalog, Topology(config["topology"]), Store(args.state), config["profiles"], initial_lookback=config.get("initial_lookback_seconds", 60), probe_interval=config.get("probe_refresh_seconds", 30))
        while True:
            before = time.monotonic()
            result = worker.cycle(force_collect=args.probe_all)
            if args.command == "once":
                break
            if result["changed"]:
                print(json.dumps({"status": result["status"], "ingested_events": result["ingested_events"],
                                  "correlation": result["correlation"], "store_counts": result["store_counts"]}, ensure_ascii=True), flush=True)
            time.sleep(max(0, args.interval - (time.monotonic() - before)))
    if getattr(args, "output", None):
        save_new(args.output, result)
    print(json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as error:
        print(json.dumps({"status": "ERROR", "error_type": type(error).__name__}), file=sys.stderr)
        raise SystemExit(2)

"""Offline equivalence and warm comparison latency; never collects new data."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter_ns

from lab import PROJECT, read, sha, verify_release


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 100:
        parser.error("--repeats must be between 1 and 100")
    sys.path.insert(0, str(PROJECT / "ml-research"))
    from demo_v2 import assess
    from mlv2.core import save_new
    from shadow_runtime import CandidateRuntime
    started = perf_counter_ns()
    release, integrity = verify_release()
    runtime = CandidateRuntime(release["candidate_db"], PROJECT / "diagnosis-engine", expected_sha256=release["candidate_sha256"])
    startup_ms = (perf_counter_ns() - started) / 1e6
    freeze = read(PROJECT / "evidence/ml-v2/locked-test-v1/development-freeze.json")
    manifest = read(Path(release["evaluation"]) / "manifest.json")
    paths = [Path(row["path"]) for row in freeze["train"] + manifest["test_sources"]]
    paths += sorted((PROJECT / "evidence/ml-v2/demos/observations").glob("*/*/*.json"))
    observations = [read(path) for path in paths]
    failures = []
    for path, observation in zip(paths, observations):
        previous = sys.path[:]
        try:
            original = assess(observation, release["candidate_db"], PROJECT / "diagnosis-engine")
        finally:
            sys.path[:] = previous
        if original != runtime.assess(observation):
            failures.append(str(path))
    if failures:
        raise AssertionError("Full-output equivalence failed: " + json.dumps(failures))
    timings = {"original_reloads_sqlite": [], "cached_session_runtime": []}
    for repeat in range(args.repeats):
        # Alternate execution order to reduce systematic cache/order bias.
        order = list(timings) if repeat % 2 == 0 else list(reversed(timings))
        for observation in observations:
            for name in order:
                previous = sys.path[:]
                try:
                    before = perf_counter_ns()
                    if name == "original_reloads_sqlite":
                        assess(observation, release["candidate_db"], PROJECT / "diagnosis-engine")
                    else:
                        runtime.assess(observation)
                    timings[name].append((perf_counter_ns() - before) / 1e6)
                finally:
                    sys.path[:] = previous
    def summarize(values):
        return {"calls": len(values), "median_ms": statistics.median(values),
                "p95_ms": sorted(values)[max(0, int(len(values) * .95 + .999999) - 1)]}
    result = {"status": "OFFLINE_EQUIVALENCE_VERIFIED", "at": datetime.now(timezone.utc).isoformat(),
              "same_full_outputs": len(observations), "mismatches": failures,
              "input_observations_sha256": {str(path): sha(path) for path in paths},
              "integrity": integrity, "startup_including_release_hashes_ms": startup_ms,
              "latency": {name: summarize(values) for name, values in timings.items()},
              "measurement_scope": "Warm full expert+discrete ML comparison; same loaded observations, includes feature/gate/expert/rule evaluation. Original opens SQLite per call; new runtime loads once. Excludes CLI startup, observation disk reads, SSH/API/fault time. Existing historical data only; not new accuracy evidence.",
              "runtime_sha256": sha(PROJECT / "ml-research/shadow_runtime.py")}
    if args.output:
        save_new(args.output, result)
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()

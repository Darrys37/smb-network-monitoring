"""One entry point for release checks, offline replay and explicit lab demos."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
FAULTS = ("nginx_stopped", "agent_stopped", "interface_down", "remote_http_filtered", "dns_egress_blocked", "cpu_stress")


def read(path):
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object: " + Path(path).name)
    return value


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_release(project=PROJECT):
    project = Path(project).resolve()
    root = project / "evidence/ml-v2"
    release = read(root / "ML_RELEASE.json")
    if release.get("status") != "INITIAL_VM_ML_RELEASE_VERIFIED":
        raise ValueError("Release has not passed final review")
    checks = dict(release["source_hashes"])
    checks.update(release["known_limitation_evidence"])
    checks[str(root / "locked-test-v1/development-freeze.json")] = release["freeze_sha256"]
    checks[str(Path(release["evaluation"]) / "manifest.json")] = release["evaluation_manifest_sha256"]
    checks[release["candidate_db"]] = release["candidate_sha256"]
    for path, expected in checks.items():
        path = Path(path).resolve()
        if not path.is_relative_to(project):
            raise ValueError("Historical release references another project location; do not silently rewrite its paths")
        if sha(path) != expected:
            raise ValueError("Release hash mismatch: " + str(path.relative_to(project)))
    freeze = read(root / "locked-test-v1/development-freeze.json")
    manifest = read(Path(release["evaluation"]) / "manifest.json")
    observations = freeze["train"] + manifest["test_sources"]
    for row in observations:
        path = Path(row["path"]).resolve()
        if not path.is_relative_to(project) or sha(path) != row["sha256"]:
            raise ValueError("Frozen observation hash mismatch: " + path.name)
    return release, {"status": "RELEASE_HASHES_VERIFIED", "files_verified": len(checks),
                     "observations_verified": len(observations),
                     "candidate_sha256": release["candidate_sha256"],
                     "scope": release["scope"], "active_rules": release["active_rules"]}


def vm_states(diagnostics=None):
    diagnostics = diagnostics if diagnostics is not None else {}
    executable = shutil.which("VBoxManage")
    if not executable and os.name == "nt":
        guess = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Oracle/VirtualBox/VBoxManage.exe"
        executable = str(guess) if guess.is_file() else None
    if not executable:
        diagnostics["VirtualBox"] = "VBoxManageNotFound"
        return {name: "unavailable" for name in ("MON01", "SRV01", "CLI01")}
    states = {}
    for name in ("MON01", "SRV01", "CLI01"):
        try:
            result = subprocess.run([executable, "showvminfo", name, "--machinereadable"],
                                    capture_output=True, text=True, encoding="utf-8", timeout=10, check=True)
            values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
            states[name] = values["VMState"].strip('"')
        except (OSError, subprocess.SubprocessError, KeyError) as error:
            states[name] = "unavailable"
            diagnostics[name] = type(error).__name__
    return states


def settings(project=PROJECT):
    path = Path(project) / "tools/lab.local.json"
    value = read(path) if path.is_file() else {}
    if set(value) - {"coordination_root", "dependency_paths"}:
        raise ValueError("Only coordination_root and dependency_paths belong in lab.local.json")
    if value.get("coordination_root") is not None and not isinstance(value["coordination_root"], str):
        raise ValueError("coordination_root must be a path string")
    if not isinstance(value.get("dependency_paths", []), list) or any(not isinstance(p, str) for p in value.get("dependency_paths", [])):
        raise ValueError("dependency_paths must be a list of paths")
    return value


def dependency_path(value):
    paths = [str(Path(p).resolve()) for p in value.get("dependency_paths", [])]
    if any(not Path(p).is_dir() for p in paths):
        raise ValueError("Configured dependency directory is missing")
    previous = os.environ.get("PYTHONPATH")
    if previous:
        paths.append(previous)
    return os.pathsep.join(paths)


def demo(args, project=PROJECT):
    verify_release(project)
    config = settings(project)
    coordination = args.coordination_root or config.get("coordination_root")
    if not coordination:
        raise ValueError("Set --coordination-root to the existing coordinator workspace (or tools/lab.local.json)")
    coordination = Path(coordination).resolve()
    if not (coordination / "verification").is_dir():
        raise ValueError("Coordinator verification directory is missing; refusing to create separate demo locks")
    states = vm_states()
    if any(value != "running" for value in states.values()):
        raise ValueError("Demo requires all three VMs running: " + json.dumps(states))
    environment = os.environ.copy()
    environment["PYTHONPATH"] = dependency_path(config)
    environment["PYTHONIOENCODING"] = "utf-8"
    check = subprocess.run([sys.executable, "-c", "import paramiko"], env=environment, capture_output=True)
    if check.returncode:
        raise ValueError("Paramiko is unavailable in the chosen Python environment; install ml-research/requirements.txt")
    from lab_session import lab_session
    # The existing reviewed Pilot still owns preflight, fault timers and rollback.
    command = [sys.executable, str(Path(project) / "ml-research/run_demo_v2.py"),
               "--release", str(Path(project) / "evidence/ml-v2/ML_RELEASE.json"), "--fault", args.fault]
    with lab_session(coordination):
        return wait_for_demo(command, cwd=Path(project) / "ml-research", env=environment)


def wait_for_demo(command, **kwargs):
    """Retain the lab lock through Ctrl+C until the child's cleanup has ended."""
    with subprocess.Popen(command, **kwargs) as child:
        while True:
            try:
                return child.wait()
            except KeyboardInterrupt:
                print("Interrupted; waiting for the demo child to finish rollback before releasing lab locks.", file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="Read current release and VM states; never starts VMs")
    commands.add_parser("verify", help="Verify frozen source/evidence and candidate hashes")
    replay = commands.add_parser("replay", help="Reassess saved observations without VM/API/SSH")
    replay.add_argument("--observation", type=Path, nargs="+", required=True)
    replay.add_argument("--output", type=Path, help="Optional new JSON file, never overwritten")
    live = commands.add_parser("demo", help="Explicit fault injection; uses the reviewed Pilot and shared lab locks")
    live.add_argument("--fault", choices=FAULTS, default="nginx_stopped")
    live.add_argument("--coordination-root", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            release = read(PROJECT / "evidence/ml-v2/ML_RELEASE.json")
            diagnostics = {}
            result = {"status": release.get("status"), "hashes_checked": False, "project": str(PROJECT),
                      "python": sys.executable, "vms": vm_states(diagnostics), "vm_diagnostics": diagnostics,
                      "candidate_db": release.get("candidate_db"),
                      "presentation": release.get("presentation"), "scope": release.get("scope"),
                      "note": "Use verify to check integrity; no VM state was changed"}
        elif args.command == "verify":
            _, result = verify_release()
        elif args.command == "demo":
            return demo(args)
        else:
            release, receipt = verify_release()
            module = PROJECT / "ml-research"
            sys.path.insert(0, str(module))
            from mlv2.core import save_new
            from shadow_runtime import CandidateRuntime
            runtime = CandidateRuntime(release["candidate_db"], PROJECT / "diagnosis-engine",
                                       expected_sha256=release["candidate_sha256"])
            # Read raw bytes once so the recorded hash describes the assessed input.
            comparisons = []
            for path in args.observation:
                raw = path.read_bytes()
                comparisons.append({"observation": str(path.resolve()), "observation_sha256": hashlib.sha256(raw).hexdigest(),
                                    "assessment": runtime.assess(json.loads(raw.decode("utf-8-sig")))})
            result = {"status": "OFFLINE_REPLAY_COMPLETE", "at": datetime.now(timezone.utc).isoformat(),
                      "candidate_sha256": runtime.candidate_sha256, "release_verification": receipt,
                      "comparisons": comparisons, "note": "Replayed historical observations; no new fault experiment"}
            if args.output:
                save_new(args.output, result)
        print(json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(json.dumps({"status": "ERROR", "error_type": type(error).__name__, "message": str(error)}, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

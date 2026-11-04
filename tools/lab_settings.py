"""Local settings and read-only VirtualBox inventory for the worker lab."""
import json
import os
from pathlib import Path
import shutil
import subprocess
PROJECT = Path(__file__).resolve().parents[1]

def read(path):
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object: " + Path(path).name)
    return value

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

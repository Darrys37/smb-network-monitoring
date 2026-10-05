"""Read-only HTTP evidence, run on the service host. Standard library only."""
import argparse
import http.client
import ipaddress
import json
import socket
import subprocess
import time
from pathlib import Path


def local_addresses():
    completed = subprocess.run(["ip", "-j", "-4", "address", "show"],
                               capture_output=True, text=True, timeout=5, check=True)
    return {a["local"] for link in json.loads(completed.stdout)
            for a in link.get("addr_info", []) if a.get("family") == "inet"}


def collect_local_http(target, observer="srv01"):
    target = str(ipaddress.IPv4Address(target))
    actual = socket.gethostname().split(".")[0].lower()
    if actual != observer:
        raise ValueError(f"Run this probe on {observer}; actual hostname is {actual}")
    if target not in local_addresses():
        raise ValueError("Target IP is not assigned to this host")
    stamp = int(time.time())
    result = {"observer": actual, "port": 80, "path": "/",
              "local_address_verified": True, "status": "error",
              "http_status": None, "error": ""}
    # Numeric local address, no proxy, no redirects, no privileged commands.
    conn = http.client.HTTPConnection(target, 80, timeout=3)
    try:
        conn.request("HEAD", "/")
        response = conn.getresponse()
        result["http_status"] = response.status
        result["status"] = "success" if response.status == 200 else "failed"
    except (ConnectionRefusedError, TimeoutError) as exc:
        result.update(status="failed", error=str(exc))
    except (OSError, http.client.HTTPException) as exc:
        result.update(status="error", error=str(exc))
    finally:
        conn.close()
    return {"check_type": "local_http", "target": target,
            "collected_at": stamp, "result": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-ip", default="192.168.56.20")
    parser.add_argument("--observer", default="srv01")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    row = collect_local_http(args.target_ip, args.observer)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump({"schema_version": 1, "observer": args.observer,
                   "evidence": [row]}, handle, indent=2)
    print(f"Saved {args.output}: {row['result']['status']}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(f"Error: {exc}")

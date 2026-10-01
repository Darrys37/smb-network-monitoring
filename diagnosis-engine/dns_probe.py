"""Run on CLI01, not MON01, to observe CLI01's default DNS resolver."""
import argparse
import json
import socket
from dataclasses import asdict, replace
from pathlib import Path
from evidence import collect_dns, collect_ping


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--control-ip", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    observer = socket.gethostname().lower().split(".")[0]
    name = args.name.lower().rstrip(".")
    records = [collect_dns(name), replace(collect_ping(args.control_ip), check_type="dns_control_ping")]
    for record in records:
        record.result["observer"] = observer
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump({"observer": observer, "evidence": [asdict(r) for r in records]}, stream, indent=2)
    print("Saved:", args.output)


if __name__ == "__main__":
    main()

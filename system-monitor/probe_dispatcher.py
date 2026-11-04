"""Forced-command SSH entry point: one bounded JSON read-only probe per call."""
import json
import sys
from monitoring.probes import dispatch


def main():
    data = sys.stdin.buffer.read(8193)
    if len(data) > 8192:
        raise ValueError("Probe request too large")
    value = dispatch(json.loads(data))
    print(json.dumps(value, ensure_ascii=True, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"status": "source_error", "error_type": type(error).__name__}))
        raise SystemExit(2)

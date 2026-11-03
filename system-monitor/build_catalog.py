"""Build a new SQLite expert catalog from the reviewable seed JSON."""
import argparse
import json
from pathlib import Path
from monitoring.catalog import create_catalog


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=Path, default=root / "config/expert_seed.json")
    parser.add_argument("--output", type=Path, default=root / "catalog/expert_rules.sqlite")
    args = parser.parse_args()
    create_catalog(args.output, json.loads(args.seed.read_text(encoding="utf-8")))
    print(json.dumps({"status": "NEW_EXPERT_CATALOG_CREATED", "path": str(args.output)}, ensure_ascii=True))


if __name__ == "__main__":
    main()

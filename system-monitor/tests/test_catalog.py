from copy import deepcopy
from contextlib import closing
from dataclasses import asdict
import itertools
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = Path(os.environ.get("DIAGNOSIS_ENGINE_SOURCE", ROOT.parent / "diagnosis-engine"))
sys.path.insert(0, str(ENGINE))
from roadmap_rules import diagnose_roadmap
from monitoring.catalog import ExpertCatalog, create_catalog
from monitoring.expressions import validate, render


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "expert.sqlite"
        self.seed = json.loads((ROOT / "config/expert_seed.json").read_text(encoding="utf-8"))
        create_catalog(self.path, self.seed)
        self.catalog = ExpertCatalog(self.path)

    def compare(self, observation):
        p = observation["profile"]
        profile = {"host_id": p["host_id"], "target_ip": p["target_ip"], "control_ip": p["control_ip"],
                   "http_observer": p["observer"], "http_service": p["http_service"], "dns_name": p["dns_name"],
                   "dns_observer": p["observer"], "dns_control_ip": p["dns_control_ip"]}
        records = observation["evidence"]
        from models import EvidenceRecord
        expected = diagnose_roadmap(profile["host_id"], profile["target_ip"], [EvidenceRecord(**row) for row in records],
            control=profile["control_ip"], http_observer=profile["http_observer"], http_service=profile["http_service"],
            dns_name=profile["dns_name"], dns_observer=profile["dns_observer"], control_ip=profile["dns_control_ip"], now=observation["decision_time"])
        actual = self.catalog.assess(profile, records, observation["decision_time"])["diagnoses"][:6]
        # JSON conversion makes tuple/list formatting differences immaterial.
        expected = json.loads(json.dumps([asdict(row) for row in expected]))
        actual = [{key: row[key] for key in expected[index]} for index, row in enumerate(actual)]
        self.assertEqual(actual, expected)

    def test_all_88_historical_observations_match_legacy_full_six_diagnoses(self):
        fixtures = ROOT / "tests/fixtures"
        manifest = json.loads((fixtures / "manifest.json").read_text(encoding="utf-8"))
        paths = [fixtures / row["path"] for row in manifest["observations"]]
        self.assertGreaterEqual(len(paths), 88)
        for path in paths:
            with self.subTest(path=path.name):
                self.compare(json.loads(path.read_text(encoding="utf-8")))

    def test_missing_stale_unknown_and_http_scope_combinations_match_legacy(self):
        fixtures = ROOT / "tests/fixtures"
        manifest = json.loads((fixtures / "manifest.json").read_text(encoding="utf-8"))
        path = fixtures / manifest["baseline"]
        original = json.loads(path.read_text(encoding="utf-8"))
        for ping, tcp, local, scope in itertools.product([None, "success", "no_reply"], [None, "success", "timeout", "refused"], [None, "success", "failed"], ["expected", "absent", "unknown"]):
            obs = deepcopy(original)
            obs["profile"]["http_service"] = scope
            for row in obs["evidence"]:
                if row["check_type"] == "ping" and row["target"] == obs["profile"]["target_ip"]:
                    row["result"]["status"] = ping
                if row["check_type"] == "tcp" and row["result"].get("port") == 80:
                    row["result"]["status"] = tcp
                if row["check_type"] == "local_http":
                    row["result"].update(status=local, http_status=200 if local == "success" else None)
            self.compare(obs)
        stale = deepcopy(original)
        stale["decision_time"] += 500
        self.compare(stale)

    def test_rule_threshold_can_change_in_sqlite_without_python_change(self):
        fixtures = ROOT / "tests/fixtures"
        manifest = json.loads((fixtures / "manifest.json").read_text(encoding="utf-8"))
        path = fixtures / manifest["cpu"]
        observation = json.loads(path.read_text(encoding="utf-8"))
        for record in observation["evidence"]:
            if record["check_type"] == "cpu_history":
                for sample in record["result"]["samples"]:
                    sample["value"] = 92.
                record["result"]["support_items"] = {
                    key: {"status": "0", "state": "0", "lastclock": str(observation["decision_time"]), "lastvalue": value}
                    for key, value in (("system.cpu.num", "2"), ("system.cpu.load[all,avg1]", "3"))}
        profile = {"host_id": observation["profile"]["host_id"], "target_ip": observation["profile"]["target_ip"], "http_service": "expected"}
        self.assertEqual(self.catalog.assess(profile, observation["evidence"], observation["decision_time"])["diagnoses"][5]["status"], "matched")
        policy = self.seed["metadata"]["policy"]
        policy["cpu_high_percent"] = 95
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE metadata SET value_json=? WHERE key='policy'", (json.dumps(policy),))
        changed = ExpertCatalog(self.path)
        self.assertEqual(changed.assess(profile, observation["evidence"], observation["decision_time"])["diagnoses"][5]["status"], "not_matched")
        self.assertEqual(self.catalog.metadata["policy"]["cpu_high_percent"], 90)

    def test_unsafe_predicates_and_template_access_are_rejected(self):
        for expression in ({"op": "eval", "code": "unused"}, {"op": "eq", "field": "x.__class__", "value": 1}, {"op": "all", "args": []}):
            with self.assertRaises(ValueError):
                validate(expression)
        with self.assertRaises(ValueError):
            render("{value.__class__}", {"value": 1})

    def test_seven_groups_eight_independent_rules_and_three_hypotheses(self):
        self.assertEqual(len(self.catalog.rules), 8)
        self.assertEqual(len({row["group"] for row in self.catalog.rules}), 7)
        self.assertTrue(all(2 <= len(row["hypotheses"]) <= 3 for row in self.catalog.rules))

    def test_existing_catalog_not_overwritten(self):
        with self.assertRaises(FileExistsError):
            create_catalog(self.path, self.seed)

    def test_gateway_unknown_cannot_be_inferred_from_child_failures(self):
        profile = {"host_id": "10683", "target_ip": "192.168.56.20", "http_service": "expected"}
        result = self.catalog.assess(profile, [], 1000, parent_status="unknown")["diagnoses"]
        self.assertEqual(result[6]["status"], "insufficient_evidence")
        self.assertEqual(self.catalog.assess(profile, [], 1000, parent_status="down")["diagnoses"][6]["status"], "matched")

    def test_mutating_returned_hypotheses_cannot_change_the_catalog(self):
        profile = {"host_id": "10683", "target_ip": "192.168.56.20", "http_service": "expected"}
        first = self.catalog.assess(profile, [], 1000, parent_status="down")
        first["diagnoses"][6]["hypotheses"][0]["label"] = "modified"
        self.assertNotEqual(self.catalog.assess(profile, [], 1000, parent_status="down")["diagnoses"][6]["hypotheses"][0]["label"], "modified")


if __name__ == "__main__":
    unittest.main()

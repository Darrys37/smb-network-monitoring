from copy import deepcopy
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from candidate_v2 import load_database, write_database
from demo_v2 import assess
from mlv2.core import read, sha, save_new
from mlv2.features import CATEGORICAL, FEATURES, NUMERIC
from shadow_runtime import CandidateRuntime, load_expert

MODULE = Path(__file__).resolve().parents[1]
ENGINE = MODULE.parent / "diagnosis-engine"


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "candidate.sqlite"
        self.profile = read(MODULE / "config/srv01.json")
        write_database(self.database,
            [{"rule_id": "leaf", "conditions": [], "label": "healthy", "training_runs": 6, "leaf_class_fraction": 1.}],
            [{"conditions": ["ping_status=success"], "label": "healthy", "training_runs": 6, "support": 1., "confidence": 1., "lift": 1.}],
            {"profile": self.profile, "features": FEATURES, "categorical": CATEGORICAL, "numeric": NUMERIC})
        self.observation = {"schema_version": 2, "session_id": "s", "run_id": "r", "window_id": "w",
            "collector_version": "ml-observation-v2.0", "profile": deepcopy(self.profile), "started_at": 1000, "decision_time": 1000,
            "sources": {key: {"status": "ok", "error_type": None} for key in ("monitor", "local_http", "dns")},
            "evidence": [
                {"check_type": "ping", "target": target, "collected_at": 1000, "result": {"status": "success"}}
                for target in (self.profile["target_ip"], self.profile["control_ip"])] + [
                {"check_type": "tcp", "target": self.profile["target_ip"], "collected_at": 1000,
                 "result": {"port": port, "status": "success"}} for port in (80, 10050)]}

    def runtime(self, **kwargs):
        return CandidateRuntime(self.database, ENGINE, expected_sha256=kwargs.get("expected_sha256", sha(self.database)))

    def test_loads_database_once_and_does_not_grow_import_path(self):
        before = sys.path[:]
        with patch("shadow_runtime.load_database", wraps=load_database) as loader:
            runtime = self.runtime()
            runtime.assess(self.observation)
            runtime.assess(self.observation)
            self.assertEqual(loader.call_count, 1)
        self.assertEqual(before, sys.path)

    def test_full_output_matches_reference_for_known_missing_stale_and_other_profile(self):
        runtime = self.runtime()
        variants = [deepcopy(self.observation) for _ in range(4)]
        variants[1]["evidence"] = []
        variants[2]["decision_time"] = 1300
        variants[3]["profile"]["profile_id"] = "other-profile"
        for observation in variants:
            before = sys.path[:]
            try:
                expected = assess(observation, self.database, ENGINE)
            finally:
                sys.path[:] = before
            self.assertEqual(runtime.assess(observation), expected)

    def test_caller_cannot_mutate_cached_rules_through_result(self):
        runtime = self.runtime()
        first = runtime.assess(self.observation)
        first["ml_suggestions"]["CART"]["matched_rule"]["label"] = "tampered"
        self.assertEqual(runtime.assess(self.observation)["ml_suggestions"]["CART"]["label"], "healthy")

    def test_model_hash_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "artifact changed"):
            self.runtime(expected_sha256="0" * 64)

    def test_model_modified_during_load_rejected(self):
        with patch("shadow_runtime.sha", side_effect=["a", "b"]):
            with self.assertRaisesRegex(ValueError, "while it was being loaded"):
                self.runtime(expected_sha256="a")

    def test_another_cached_engine_is_rejected_without_changing_import_path(self):
        load_expert(ENGINE)
        before = sys.path[:]
        with patch.dict(sys.modules, {"models": type("Other", (), {"__file__": str(ENGINE / "another.py")})()}):
            with self.assertRaisesRegex(ValueError, "Another engine"):
                load_expert(ENGINE)
        self.assertEqual(before, sys.path)

    def test_demo_snapshots_reuse_runtime_and_preserve_provenance(self):
        from mlv2.pilot import Pilot
        from run_demo_v2 import DemoPilot
        root = Path(self.temp.name) / "demo"
        second = deepcopy(self.observation)
        second["window_id"] = "w2"
        for observation in (self.observation, second):
            save_new(root / "observations/s/r" / (observation["window_id"] + ".json"), observation)
        with patch("shadow_runtime.load_database", wraps=load_database) as loader, \
             patch.object(Pilot, "snapshot", side_effect=[self.observation, second]), redirect_stdout(io.StringIO()):
            pilot = DemoPilot(None, root, ENGINE, self.profile, candidate_db=self.database)
            pilot.snapshot({"session_id": "s", "run_id": "r"})
            pilot.snapshot({"session_id": "s", "run_id": "r"})
            self.assertEqual(loader.call_count, 1)
        comparison = read(root / "comparisons/s/r/w2.json")
        self.assertEqual(comparison["candidate_sha256"], sha(self.database))
        self.assertEqual(comparison["observation_sha256"], sha(root / "observations/s/r/w2.json"))
        self.assertEqual(comparison["mode"], "explicit_lab_demo_shadow")


if __name__ == "__main__":
    unittest.main()

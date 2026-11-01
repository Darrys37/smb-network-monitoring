import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, call, patch

TOOLS = Path(__file__).resolve().parents[2] / "tools"
sys.path.insert(0, str(TOOLS))
import lab
from lab_session import byte_lock, keep_awake, lab_session


class WorkflowTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows wake API")
    def test_failed_wake_thread_start_clears_main_thread_request(self):
        kernel = MagicMock()
        kernel.SetThreadExecutionState.return_value = 1
        worker = MagicMock()
        worker.ident = None
        worker.start.side_effect = RuntimeError("cannot start thread")
        with patch("ctypes.WinDLL", return_value=kernel), patch("lab_session.threading.Thread", return_value=worker):
            with self.assertRaisesRegex(RuntimeError, "cannot start thread"):
                with keep_awake():
                    pass
        self.assertEqual(kernel.SetThreadExecutionState.call_args_list, [call(0x80000003), call(0x80000000)])

    @unittest.skipUnless(os.name == "nt", "Windows wake API")
    def test_body_error_clears_wake_and_joins_refresher(self):
        kernel = MagicMock()
        kernel.SetThreadExecutionState.return_value = 1
        worker = MagicMock()
        worker.ident = 1
        with patch("ctypes.WinDLL", return_value=kernel), patch("lab_session.threading.Thread", return_value=worker):
            with self.assertRaisesRegex(ValueError, "body"):
                with keep_awake():
                    raise ValueError("body")
        worker.join.assert_called_once_with(timeout=2)
        self.assertEqual(kernel.SetThreadExecutionState.call_args_list[-1], call(0x80000000))

    def test_child_waits_after_interrupt_before_returning(self):
        child = MagicMock()
        child.__enter__.return_value = child
        child.wait.side_effect = [KeyboardInterrupt(), 130]
        with patch.object(lab.subprocess, "Popen", return_value=child), patch.object(lab.sys, "stderr"):
            self.assertEqual(lab.wait_for_demo(["unused"]), 130)
        self.assertEqual(child.wait.call_count, 2)

    def test_frozen_observation_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            evidence = root / "evidence/ml-v2"
            locked = evidence / "locked-test-v1"
            evaluation = locked / "evaluation"
            evaluation.mkdir(parents=True)
            observation = locked / "observation.json"
            observation.write_text('{}')
            freeze = locked / "development-freeze.json"
            freeze.write_text(json.dumps({"train": [{"path": str(observation), "sha256": lab.sha(observation)}]}))
            manifest = evaluation / "manifest.json"
            manifest.write_text(json.dumps({"test_sources": []}))
            candidate = evaluation / "candidate.sqlite"
            candidate.write_bytes(b"hash-only fixture")
            (evidence / "ML_RELEASE.json").write_text(json.dumps({
                "status": "INITIAL_VM_ML_RELEASE_VERIFIED", "source_hashes": {}, "known_limitation_evidence": {},
                "evaluation": str(evaluation), "evaluation_manifest_sha256": lab.sha(manifest), "freeze_sha256": lab.sha(freeze),
                "candidate_db": str(candidate), "candidate_sha256": lab.sha(candidate), "scope": "fixture", "active_rules": 0}))
            self.assertEqual(lab.verify_release(root)[1]["observations_verified"], 1)
            observation.write_text('{"changed":true}')
            with self.assertRaisesRegex(ValueError, "observation hash mismatch"):
                lab.verify_release(root)

    def test_live_demo_refuses_stopped_vms_before_opening_transport(self):
        with patch.object(lab, "verify_release", return_value=({}, {})), \
             patch.object(lab, "settings", return_value={}), \
             tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "verification").mkdir()
            args = argparse.Namespace(coordination_root=Path(folder), fault="nginx_stopped")
            with patch.object(lab, "vm_states", return_value={"MON01": "poweroff"}), \
                 patch.object(lab.subprocess, "run") as child:
                with self.assertRaisesRegex(ValueError, "all three VMs"):
                    lab.demo(args)
                child.assert_not_called()

    def test_unknown_settings_cannot_silently_include_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "tools").mkdir()
            (root / "tools/lab.local.json").write_text(json.dumps({"password": "not-a-real-password"}))
            with self.assertRaisesRegex(ValueError, "Only coordination"):
                lab.settings(root)

    def test_missing_dependency_directory_is_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "dependency directory"):
                lab.dependency_path({"dependency_paths": [str(Path(folder) / "missing")]})

    def test_guard_releases_locks_after_body_error(self):
        @contextmanager
        def no_wake():
            yield
        with tempfile.TemporaryDirectory() as folder, patch("lab_session.keep_awake", no_wake):
            with self.assertRaisesRegex(ValueError, "body"):
                with lab_session(folder):
                    raise ValueError("body")
            with lab_session(folder):
                pass

    def test_second_process_cannot_acquire_shared_byte_then_can_after_release(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "coordinator.lock"
            code = "import sys;sys.path.insert(0,sys.argv[1]);from lab_session import byte_lock\nwith byte_lock(sys.argv[2]): pass"
            command = [sys.executable, "-c", code, str(TOOLS), str(path)]
            with byte_lock(path):
                blocked = subprocess.run(command, capture_output=True, text=True)
                self.assertNotEqual(blocked.returncode, 0)
                self.assertIn("Lab is busy", blocked.stderr)
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)

    def test_guard_rolls_back_first_lock_when_second_is_busy(self):
        with tempfile.TemporaryDirectory() as folder:
            verification = Path(folder) / "verification"
            # A separate holder is needed: POSIX locks are per-process.
            code = "import sys;sys.path.insert(0,sys.argv[1]);from lab_session import byte_lock\nwith byte_lock(sys.argv[2]):\n print('locked',flush=True);sys.stdin.readline()"
            child = subprocess.Popen([sys.executable, "-c", code, str(TOOLS), str(verification / "ml-acceptance.lock")],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                self.assertEqual(child.stdout.readline().strip(), "locked")
                with self.assertRaisesRegex(RuntimeError, "Lab is busy"):
                    with lab_session(folder):
                        pass
                with byte_lock(verification / "ml-supervisor.lock"):
                    pass
            finally:
                child.communicate("\n", timeout=5)


if __name__ == "__main__":
    unittest.main()

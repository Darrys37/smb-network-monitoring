"""The operator status command must work without a research checkout or live SSH."""
from contextlib import redirect_stdout
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "tools"))
import lab_settings
import lab_transport


class OperatorTests(unittest.TestCase):
    def test_local_config_does_not_require_historical_release_files(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            self.assertEqual(lab_settings.settings(folder), {})
            tools = Path(folder) / "tools"
            tools.mkdir()
            (tools / "lab.local.json").write_text('{"dependency_paths": 42}', encoding="utf-8")
            with self.assertRaises(ValueError):
                lab_settings.settings(folder)

    def test_status_imports_neutral_helpers_and_never_connects_to_ssh(self):
        spec = importlib.util.spec_from_file_location("worker_operator", ROOT / "system_lab.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = {"worker_service": "active", "counts": {"pending_jobs": 0},
                  "correlation": {"active_problem_events": 0, "emitted_groups": 0,
                                  "suppressed_events": 0, "groups": []}}
        output = io.StringIO()
        with patch.object(sys, "argv", ["system_lab.py", "status"]), \
             patch.object(lab_settings, "settings", return_value={}), \
             patch.object(lab_settings, "vm_states", return_value={name: "running" for name in ("MON01", "SRV01", "CLI01")}), \
             patch.object(lab_transport, "LabTransport") as transport, \
             patch("getpass.getpass", return_value=""), \
             patch.object(module, "snapshot", return_value=report), redirect_stdout(output):
            module.main()
        self.assertIn('"active_events": 0', output.getvalue())
        transport.return_value.close.assert_called_once()
        transport.return_value.command.assert_not_called()


if __name__ == "__main__":
    unittest.main()

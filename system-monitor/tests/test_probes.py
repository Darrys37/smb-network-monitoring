from pathlib import Path
import unittest
from unittest.mock import patch

from monitoring.probes import parse_dns, dispatch
from monitoring.catalog import ExpertCatalog, create_catalog
import json
import tempfile


class ProbeTests(unittest.TestCase):
    def test_dns_response_time_comes_from_response_stats_not_process_timeout(self):
        output = ";; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 1\nexample.com. 100 IN A 93.184.216.34\n;; Query time: 17 msec\n"
        result = parse_dns(output, 0)
        self.assertEqual(result["response_time_ms"], 17)
        self.assertEqual(result["status"], "success")
        timeout = parse_dns(";; no servers could be reached", 9)
        self.assertEqual(timeout["status"], "timeout")
        self.assertIsNone(timeout["response_time_ms"])

    def test_nxdomain_and_command_errors_do_not_become_normal_answers(self):
        self.assertEqual(parse_dns("status: NXDOMAIN\n;; Query time: 4 msec", 0)["status"], "nxdomain")
        self.assertEqual(parse_dns("", 127)["status"], "error")

    def test_wrong_observer_is_rejected_before_any_probe(self):
        with patch("monitoring.probes.socket.gethostname", return_value="cli01"):
            with self.assertRaises(ValueError):
                dispatch({"operation": "http", "expected_observer": "srv01", "target": "192.168.56.20"})

    def test_local_service_fault_and_parent_failure_both_remain_visible(self):
        root = Path(__file__).resolve().parents[1]
        seed = json.loads((root / "config/expert_seed.json").read_text())
        with tempfile.TemporaryDirectory(dir=root) as folder:
            path = Path(folder) / "rules.sqlite"
            create_catalog(path, seed)
            profile = {"host_id": "10683", "target_ip": "172.30.20.20", "http_service": "expected", "http_observer": "srv01"}
            evidence = [{"check_type": "service_state", "target": "172.30.20.20", "collected_at": 1000,
                         "result": {"service": "nginx", "observer": "srv01", "status": "success", "state": "inactive"}}]
            result = ExpertCatalog(path).assess(profile, evidence, 1000, parent_status="down")
            self.assertEqual(result["diagnoses"][1]["status"], "matched")
            self.assertEqual(result["diagnoses"][6]["status"], "matched")


if __name__ == "__main__":
    unittest.main()

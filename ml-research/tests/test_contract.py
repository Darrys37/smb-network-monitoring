import copy
from pathlib import Path
import tempfile
import unittest

from mlv2.core import read, register, review, save_new, validate_profile, validate_observation
from mlv2.collector import collect

ROOT = Path(__file__).resolve().parents[1]
ENGINE = Path(r'C:\Users\Darrys\do-an\diagnosis-engine')


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.profile = read(ROOT/'config/srv01.json')

    def test_fault_label_cannot_enter_profile(self):
        self.profile['label'] = 'nginx_stopped'
        with self.assertRaises(ValueError): validate_profile(self.profile)

    def test_equal_target_control_rejected(self):
        self.profile['control_ip'] = self.profile['target_ip']
        with self.assertRaises(ValueError): validate_profile(self.profile)

    def test_schedule_identical_with_or_without_registry(self):
        calls = []
        def runner(host, code):
            calls.append((host, code))
            return []
        collect(self.profile, ENGINE, 'session1', 'run1', runner, clock=lambda:1000)
        before = list(calls); calls.clear()
        collect(self.profile, ENGINE, 'session1', 'run2', runner, clock=lambda:1000)
        self.assertEqual(before, calls)
        self.assertEqual([c[0] for c in calls], ['mon01','srv01','srv01'])
        self.assertFalse(any(label in source for _,source in calls
                             for label in ['nginx_stopped', 'cpu_stress', 'planned_labels']))

    def test_failed_source_preserved_without_stderr_secret(self):
        def runner(host, code): raise RuntimeError('secret-token-must-never-appear')
        result = collect(self.profile, ENGINE, 's', 'r', runner, clock=lambda:1000)
        self.assertTrue(all(v['status']=='error' for v in result['sources'].values()))
        self.assertNotIn('secret-token', str(result))

    def test_absent_http_is_context_not_fault_label(self):
        calls = []
        profile = read(ROOT/'config/cli01.json')
        result = collect(profile, ENGINE, 's', 'r', lambda h,c: calls.append(h) or [], clock=lambda:1000)
        self.assertEqual(calls, ['mon01','cli01'])
        self.assertEqual(result['sources']['local_http']['status'], 'not_applicable')

    def test_future_record_rejected(self):
        row = {'check_type':'ping','target':'ip','collected_at':1001,'result':{}}
        with self.assertRaises(ValueError):
            collect(self.profile, ENGINE, 's', 'r', lambda h,c:[row], clock=lambda:1000)

    def test_labels_forbidden_in_observation(self):
        value = collect(self.profile, ENGINE, 's', 'r', lambda h,c:[], clock=lambda:1000)
        value['label'] = 'healthy'
        with self.assertRaises(ValueError): validate_observation(value)

    def test_registration_immutable_and_review_requires_evidence(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            register(directory, 's', 'r', ['healthy'])
            with self.assertRaises(FileExistsError): register(directory, 's', 'r', ['nginx_stopped'])
            with self.assertRaises(ValueError): review(directory,'s','r','valid',['healthy'],[])
            log = Path(directory)/'independent.log'; log.write_text('services active')
            value = review(directory,'s','r','valid',['healthy'],[log])
            log.write_text('source changed later')
            archived = Path(directory)/'review-evidence'/value['references'][0]['sha256']
            self.assertEqual(archived.read_text(), 'services active')

    def test_failed_json_write_does_not_publish_partial_file(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            target=Path(directory)/'bad.json'
            with self.assertRaises(ValueError):save_new(target,{'bad':float('nan')})
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(directory).iterdir()),[])


if __name__ == '__main__': unittest.main(verbosity=2)

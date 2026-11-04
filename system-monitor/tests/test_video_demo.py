import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
if not (HERE/'video_demo.py').exists():HERE=HERE.parent


def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class VideoTests(unittest.TestCase):
    def test_all_eight_cases_require_real_matching_rule_and_current_trial(self):
        view=load('video_demo')
        for case in view.CASES:
            node='cli01' if case=='R4' else 'srv01'
            r={'correlation':{'suppressed_events':1},'latest_diagnostics':[{'node':node,'observation':{'decision_time':100},'assessment':{'diagnoses':[{'rule_id':case+'_FIXTURE','status':'matched'}]}}]}
            self.assertTrue(view.detected(r,case,100))
            self.assertFalse(view.detected(r,case,101))
            r['latest_diagnostics'][0]['assessment']['diagnoses'][0]['status']='insufficient_evidence'
            self.assertFalse(view.detected(r,case,100))

    def test_failed_timer_never_stops_service(self):
        faults=load('video_faults');calls=[]
        with tempfile.TemporaryDirectory(dir=HERE) as folder, patch.object(faults,'ROOT',Path(folder)), \
             patch.object(faults.os,'geteuid',return_value=0,create=True), \
             patch.object(faults.socket,'gethostname',return_value='srv01'), \
             patch.object(faults,'active',side_effect=lambda unit:unit=='nginx'), \
             patch.object(faults,'run',side_effect=lambda args,**kwargs:calls.append(args)):
            with self.assertRaises(RuntimeError):faults.control('arm','R2','a'*12,'# fixture')
        self.assertFalse(any(call[:2]==['systemctl','stop'] for call in calls))
        self.assertTrue(any(call[0]=='systemd-run' for call in calls))

    def test_wrong_host_cannot_create_fault(self):
        faults=load('video_faults')
        with patch.object(faults.os,'geteuid',return_value=0,create=True), \
             patch.object(faults.socket,'gethostname',return_value='mon01'),patch.object(faults,'run') as run:
            with self.assertRaises(ValueError):faults.control('arm','R2','a'*12,'# fixture')
            run.assert_not_called()

    def test_recovery_only_removes_owned_firewall_table(self):
        faults=load('video_faults');calls=[]
        class Result:returncode=0
        with tempfile.TemporaryDirectory(dir=HERE) as folder, patch.object(faults,'ROOT',Path(folder)), \
             patch.object(faults.os,'geteuid',return_value=0,create=True), \
             patch.object(faults.socket,'gethostname',return_value='srv01'), \
             patch.object(faults,'run',side_effect=lambda args,*a,**kw:(calls.append(args) or Result())):
            trial=Path(folder)/('b'*12);trial.mkdir()
            (trial/'state.json').write_text('{"case":"R5","token":"bbbbbbbbbbbb","table":"doan_video_bbbbbbbbbbbb","unit":"fixture"}')
            self.assertTrue(faults.control('recover','R5','b'*12)['restored'])
        self.assertIn(['nft','delete','table','inet','doan_video_bbbbbbbbbbbb'],calls)
        self.assertFalse(any('flush' in call for call in calls))

    def test_presenter_has_no_raw_json(self):
        view=load('video_demo');out=io.StringIO()
        with patch('sys.stdout',out):view.panel('R5',3,'ĐÃ PHÁT HIỆN',['Web tại máy chủ: ĐẠT','Truy cập từ xa: KHÔNG ĐẠT'])
        self.assertIn('BƯỚC 3/4',out.getvalue())
        self.assertNotIn('{',out.getvalue())


if __name__=='__main__':unittest.main()

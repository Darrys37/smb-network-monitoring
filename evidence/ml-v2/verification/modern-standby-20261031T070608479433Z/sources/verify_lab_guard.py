"""Verify temporary wake requests and cleanup with Windows calls mocked."""
from datetime import datetime,timezone
import io,json
from pathlib import Path
import unittest
from unittest.mock import MagicMock,patch
import lab_host_guard


class WakeGuardTests(unittest.TestCase):
    def kernel(self):
        value=MagicMock();value.SetThreadExecutionState.return_value=0x80000000
        return value

    def test_display_and_system_request_is_cleared_on_normal_exit(self):
        kernel=self.kernel()
        with patch('lab_host_guard.ctypes.WinDLL',return_value=kernel),patch('lab_host_guard.cpu_sets',return_value=[{'group':0,'efficiency_class':1,'logical_index':0}]):
            with lab_host_guard.lab_host_guard() as profile:
                self.assertEqual(profile['mode'],'display_and_system_awake')
                self.assertIn('ES_DISPLAY_REQUIRED',profile['power_request'])
                self.assertEqual(profile['vm_affinity'],[])
        self.assertEqual(kernel.SetThreadExecutionState.call_args_list[0].args,(0x80000003,))
        self.assertEqual(kernel.SetThreadExecutionState.call_args_list[-1].args,(0x80000000,))

    def test_request_is_cleared_on_exception(self):
        kernel=self.kernel()
        with patch('lab_host_guard.ctypes.WinDLL',return_value=kernel),patch('lab_host_guard.cpu_sets',return_value=[{'group':0,'efficiency_class':1,'logical_index':0}]):
            with self.assertRaisesRegex(RuntimeError,'experiment failed'):
                with lab_host_guard.lab_host_guard():raise RuntimeError('experiment failed')
        self.assertEqual(kernel.SetThreadExecutionState.call_args_list[-1].args,(0x80000000,))

    def test_worker_renews_request_after_idle_resume(self):
        kernel=self.kernel();event=MagicMock();event.wait.side_effect=[False,True]
        fake_threading=MagicMock();fake_threading.Event.return_value=event
        import threading
        fake_threading.Thread=threading.Thread
        with patch('lab_host_guard.ctypes.WinDLL',return_value=kernel),patch('lab_host_guard.cpu_sets',return_value=[{'group':0,'efficiency_class':1,'logical_index':0}]),patch('lab_host_guard.threading',fake_threading):
            with lab_host_guard.lab_host_guard():pass
        requests=[call.args[0] for call in kernel.SetThreadExecutionState.call_args_list]
        self.assertGreaterEqual(requests.count(0x80000003),2)
        self.assertEqual(requests[-1],0x80000000)


if __name__=='__main__':
    output=io.StringIO()
    result=unittest.TextTestRunner(stream=output,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(WakeGuardTests))
    record={'at':datetime.now(timezone.utc).isoformat(),'success':result.wasSuccessful(),
            'tests_run':result.testsRun,'output':output.getvalue()}
    path=Path(__file__).resolve().parent/'verification'/('lab-wake-tests-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    path.write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record),flush=True)
    raise SystemExit(not result.wasSuccessful())

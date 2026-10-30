from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from mlv2.core import save_new
from mlv2.pilot import Pilot


class Clock:
    def __init__(self):self.value=1000
    def monotonic(self):return self.value
    def sleep(self,seconds):self.value+=seconds


class Transport:
    def runner(self,host,source):
        if "print(json.dumps({n:" in source:
            return {'fault.log':'FAULT_VERIFIED 1233\n',
                    'rollback.log':'ROLLBACK_BEFORE 1234\nROLLBACK_AFTER 1234\n'}
        return None
    def sudo(self,*args):return ''
    def command(self,*args):return 0,'loaded'


class TimingPilot(Pilot):
    def __init__(self,root,clock,late):
        super().__init__(Transport(),root,'.',{},log=lambda *a,**k:None)
        self.clock,self.late,self.count=clock,late,0
    def wait_baseline(self,limit=480):return {'verified':True}
    def snapshot(self,item):
        self.count+=1
        if self.late and self.count==2:self.clock.value+=200
        # Integer remote clocks appear to put rollback one second earlier.
        value={'started_at':1234,'decision_time':1235}
        save_new(self.root/'observations'/item['session_id']/item['run_id']/(str(self.count)+'.json'),value)
        return value


class TimingTests(unittest.TestCase):
    def run_case(self,late):
        clock=Clock()
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root) as directory:
            pilot=TimingPilot(directory,clock,late)
            with patch('mlv2.pilot.time.monotonic',clock.monotonic),patch('mlv2.pilot.time.sleep',clock.sleep):
                return pilot.run({'session_id':'s','run_id':'r','label':'nginx_stopped'})
    def test_coordinator_order_handles_remote_integer_clock_offset(self):
        self.assertTrue(self.run_case(False)['valid'])
    def test_window_after_possible_failsafe_cannot_use_causal_override(self):
        self.assertFalse(self.run_case(True)['valid'])


if __name__=='__main__':unittest.main(verbosity=2)

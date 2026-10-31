from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from test_timing import Clock,TimingPilot
from mlv2.core import read


class InterruptPilot(TimingPilot):
    def snapshot(self,item):
        if self.count==1:raise KeyboardInterrupt
        return super().snapshot(item)


class InterruptedScheduleTests(unittest.TestCase):
    def test_keyboard_interrupt_before_second_window_is_not_a_valid_completed_trial(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root) as directory:
            clock=Clock();pilot=InterruptPilot(directory,clock,False)
            with patch('mlv2.pilot.time.monotonic',clock.monotonic),patch('mlv2.pilot.time.sleep',clock.sleep):
                with self.assertRaises(KeyboardInterrupt):
                    pilot.run({'session_id':'s','run_id':'r','label':'nginx_stopped'})
            receipt=read(Path(directory)/'trial-logs/s/r/RESULT.json')
            self.assertFalse(receipt['valid'])
            self.assertEqual(receipt['error_type'],'IncompleteObservationSchedule')


if __name__=='__main__':unittest.main()

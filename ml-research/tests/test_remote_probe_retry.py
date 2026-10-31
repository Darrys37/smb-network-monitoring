import unittest
from unittest.mock import MagicMock,patch
from mlv2.pilot import Pilot
from mlv2.transport import RemoteProbeError
from test_resilience import Clock


class RemoteControlRetryTests(unittest.TestCase):
    def test_remote_control_program_failure_cannot_certify_healthy_and_is_retried(self):
        transport=MagicMock()
        transport.runner.side_effect=[RemoteProbeError('command timeout'),{'service':'healthy'},{'monitor':'healthy'}]
        clock=Clock();pilot=Pilot(transport,'.','.',{},log=MagicMock())
        with patch('mlv2.pilot.time.monotonic',clock.now),patch('mlv2.pilot.time.sleep',clock.sleep),patch('mlv2.pilot.baseline_ok',return_value=True) as baseline:
            result=pilot.wait_baseline()
        baseline.assert_called_once_with({'service':'healthy'},{'monitor':'healthy'})
        self.assertEqual(clock.value,15)
        self.assertEqual(result['service'],{'service':'healthy'})


if __name__=='__main__':unittest.main()

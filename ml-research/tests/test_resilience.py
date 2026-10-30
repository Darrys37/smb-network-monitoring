import unittest
from unittest.mock import MagicMock,patch
from paramiko import SSHException,AuthenticationException
from mlv2.pilot import Pilot
from mlv2.transport import SSHTransport


class Clock:
    value=0
    def now(self):return self.value
    def sleep(self,seconds):self.value+=seconds


class ResilienceTests(unittest.TestCase):
    def test_transient_control_error_retries_without_declaring_healthy(self):
        transport=MagicMock()
        transport.runner.side_effect=[SSHException('temporary'),{'service':'good'},{'monitor':'good'}]
        pilot=Pilot(transport,'.','.',{},log=MagicMock());clock=Clock()
        with patch('mlv2.pilot.baseline_ok',return_value=True) as baseline,patch('mlv2.pilot.time.sleep',clock.sleep),patch('mlv2.pilot.time.monotonic',clock.now):
            result=pilot.wait_baseline()
        baseline.assert_called_once_with({'service':'good'},{'monitor':'good'})
        self.assertEqual(clock.value,15)
        self.assertEqual(result['monitor'],{'monitor':'good'})

    def test_repeated_control_errors_stop_at_deadline(self):
        transport=MagicMock();transport.runner.side_effect=SSHException('temporary')
        pilot=Pilot(transport,'.','.',{},log=MagicMock());clock=Clock()
        with patch('mlv2.pilot.time.sleep',clock.sleep),patch('mlv2.pilot.time.monotonic',clock.now):
            with self.assertRaisesRegex(RuntimeError,'Baseline did not stabilize'):pilot.wait_baseline(limit=1)
        self.assertEqual(transport.runner.call_count,2)

    def test_authentication_failure_does_not_get_retried(self):
        transport=MagicMock();transport.runner.side_effect=AuthenticationException('rejected')
        with patch('mlv2.pilot.time.sleep') as sleep:
            with self.assertRaises(AuthenticationException):Pilot(transport,'.','.',{}).wait_baseline()
        sleep.assert_not_called()

    def test_failed_connection_is_closed_and_not_cached(self):
        client=MagicMock();client.connect.side_effect=SSHException('failed')
        with patch('mlv2.transport.paramiko.SSHClient',return_value=client):
            transport=SSHTransport('test-only-fake-credential')
            with self.assertRaises(SSHException):transport.command('srv01','true')
        client.close.assert_called_once()
        self.assertFalse(transport.clients)


if __name__=='__main__':unittest.main()

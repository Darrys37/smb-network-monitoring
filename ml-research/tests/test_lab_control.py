import copy
import unittest
from unittest.mock import MagicMock,patch
from mlv2.transport import SSHTransport,LabTransport
from mlv2.pilot import Pilot,platform_ready,platform_stable


def stable_health():
    return {'status':'ok','schema_version':2,'nodes':{host:{'boot_id':host,'stall_count':0,'recent_stall':False,
        'package_jobs_active':False,'dpkg_lock_held':False,'package_audit_clean':True,'package_status_sha256':'a'*64}
        for host in ['mon01','srv01','cli01']}}


class ControlTests(unittest.TestCase):
    def test_probe_transport_retains_original_timeouts(self):
        client=MagicMock();stdout=MagicMock();stderr=MagicMock();stdin=MagicMock()
        stdout.read.return_value=b'null';stderr.read.return_value=b''
        stdout.channel.recv_exit_status.return_value=0
        client.exec_command.return_value=(stdin,stdout,stderr)
        with patch('mlv2.transport.paramiko.SSHClient',return_value=client):
            transport=SSHTransport('synthetic-test-only')
            self.assertIsNone(transport.runner('srv01',"print('null')"))
        self.assertEqual(client.connect.call_args.kwargs['timeout'],8)
        self.assertEqual(client.exec_command.call_args.kwargs['timeout'],12)

    def test_long_control_and_short_probes_are_separate(self):
        control=MagicMock();probes=MagicMock()
        with patch('mlv2.transport.SSHTransport',side_effect=[control,probes]) as factory:
            transport=LabTransport('synthetic-test-only')
            transport.runner('srv01','control');transport.probe_runner('srv01','measurement')
            transport.close()
        self.assertEqual(factory.call_args_list[0].kwargs['connect_timeout'],30)
        self.assertEqual(factory.call_args_list[1].kwargs,{})
        control.runner.assert_called_once_with('srv01','control')
        probes.runner.assert_called_once_with('srv01','measurement')
        control.close.assert_called_once();probes.close.assert_called_once()

    def test_pilot_measurement_uses_probe_runner(self):
        transport=MagicMock()
        with patch('mlv2.pilot.collect',return_value={'window_id':'w'}) as collect,patch('mlv2.pilot.save_new'):
            Pilot(transport,'.','.',{}).snapshot({'session_id':'s','run_id':'r'})
        self.assertIs(collect.call_args.args[-1],transport.probe_runner)

    def test_new_kernel_stall_or_boot_change_invalidates_single_fault_assumption(self):
        before=stable_health()
        self.assertTrue(platform_ready(before));self.assertTrue(platform_stable(before,before))
        after=copy.deepcopy(before);after['nodes']['srv01']['stall_count']=1
        self.assertFalse(platform_stable(before,after))
        after=copy.deepcopy(before);after['nodes']['srv01']['boot_id']='new-boot'
        self.assertFalse(platform_stable(before,after))
        after=copy.deepcopy(before);after['nodes']['mon01']['recent_stall']=True
        self.assertFalse(platform_ready(after))
        self.assertFalse(platform_ready({'status':'error'}))


    def test_package_jobs_locks_audit_and_missing_schema_cannot_certify_baseline(self):
        for key,value in [('package_jobs_active',True),('dpkg_lock_held',True),('package_audit_clean',False)]:
            state=stable_health();state['nodes']['mon01'][key]=value
            self.assertFalse(platform_ready(state))
        state=stable_health();del state['schema_version']
        self.assertFalse(platform_ready(state))

    def test_package_change_invalidates_trial_after_package_jobs_have_finished(self):
        before=stable_health();after=copy.deepcopy(before)
        after['nodes']['mon01']['package_status_sha256']='b'*64
        self.assertTrue(platform_ready(after))
        self.assertFalse(platform_stable(before,after))

    def test_platform_authentication_failure_propagates_immediately(self):
        import paramiko
        with patch('mlv2.transport.SSHTransport'):
            transport=LabTransport('synthetic-test-only')
            transport.control.sudo.side_effect=paramiko.AuthenticationException('synthetic')
            with self.assertRaises(paramiko.AuthenticationException):transport.platform_health()


if __name__=='__main__':unittest.main()

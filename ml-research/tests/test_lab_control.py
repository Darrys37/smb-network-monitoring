import copy
import unittest
from unittest.mock import MagicMock,patch
from mlv2.transport import SSHTransport,LabTransport
from mlv2.pilot import Pilot,platform_ready,platform_stable


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
        before={'status':'ok','nodes':{host:{'boot_id':host,'stall_count':0,'recent_stall':False}
                                    for host in ['mon01','srv01','cli01']}}
        self.assertTrue(platform_ready(before));self.assertTrue(platform_stable(before,before))
        after=copy.deepcopy(before);after['nodes']['srv01']['stall_count']=1
        self.assertFalse(platform_stable(before,after))
        after=copy.deepcopy(before);after['nodes']['srv01']['boot_id']='new-boot'
        self.assertFalse(platform_stable(before,after))
        after=copy.deepcopy(before);after['nodes']['mon01']['recent_stall']=True
        self.assertFalse(platform_ready(after))
        self.assertFalse(platform_ready({'status':'error'}))


if __name__=='__main__':unittest.main()

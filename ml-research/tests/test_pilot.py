import unittest
from mlv2.faults import plan,scripts
from mlv2.pilot import Pilot,baseline_ok,schedule


class PilotTests(unittest.TestCase):
    def test_schedule_42_unique_runs_and_three_per_label_session(self):
        items=schedule()
        self.assertEqual(len(items),42)
        self.assertEqual(len({(x['session_id'],x['run_id']) for x in items}),42)
        from collections import Counter
        self.assertTrue(all(n==3 for n in Counter((x['session_id'],x['label']) for x in items).values()))
        self.assertEqual(items,schedule())

    def test_rollback_does_not_flush_unrelated_firewall(self):
        for label in ['remote_http_filtered','dns_egress_blocked']:
            spec=plan(label,'a123456789ab')
            self.assertIn('nft delete table inet mlv2_a123456789ab',spec.rollback)
            self.assertNotIn('flush',spec.rollback)

    def test_cpu_has_timeout_and_owned_unit(self):
        spec=plan('cpu_stress','a123456789ab')
        self.assertIn('--timeout 420s',spec.inject)
        self.assertIn('RuntimeMaxSec=450s',spec.inject)
        self.assertIn('systemctl stop mlv2-stress-a123456789ab.service',spec.rollback)

    def test_paths_and_shell_tokens_are_validated(self):
        with self.assertRaises(ValueError):plan('cpu_stress',';id')
        with self.assertRaises(ValueError):scripts(plan('healthy','a123456789ab'),'/tmp/../../root')

    def test_stress_history_requires_washout(self):
        s={'nginx':{'stdout':'active'},'agent':{'stdout':'active'},'http':{'stdout':'200'},
           'clock':{'stdout':'yes'},'stress':{'code':1},'dns':{'stdout':'1.2.3.4','code':0},'control':{'code':0}}
        m={'problems':[],'metrics':[{'check_type':'cpu_history','result':{'status':'success',
            'samples':[{'value':20},{'value':20},{'value':100}]}}]}
        self.assertFalse(baseline_ok(s,m))
        m['metrics'][0]['result']['samples'][-1]['value']=20
        self.assertTrue(baseline_ok(s,m))
        s['dns']['stdout']=';; timed out'
        self.assertFalse(baseline_ok(s,m))

    def test_expired_timer_does_not_break_completed_trial(self):
        class Transport:
            def command(self,*args):return 1,'not-found\n'
            def sudo(self,*args):raise AssertionError('Do not stop absent timer')
        pilot=Pilot(Transport(),'.','. ',{})
        self.assertEqual(pilot.cancel_timer('mlv2-123'),'already_collected')


if __name__=='__main__':unittest.main(verbosity=2)

from copy import deepcopy
import unittest

from monitoring.correlation import correlate
from monitoring.topology import Topology


class BootNoticeTests(unittest.TestCase):
    def setUp(self):
        self.config={'version':'notice-fixture','nodes':{'server':{'type':'host','parents':[]}},'informational_triggers':[
            {'node':'server','trigger_id':'42','expected_name':'Server restarted (uptime < 10m)','expected_severity':'2'}]}
        self.event={'source':'zabbix','event_id':'1','clock':1000,'node':'server','kind':'unknown','state':'problem','key':'42',
                    'name':'Server restarted (uptime < 10m)','raw':{'name':'Server restarted (uptime < 10m)','severity':'2'}}

    def test_configured_notice_is_visible_and_retained_but_does_not_block_healthy_baseline(self):
        before=deepcopy(self.event)
        result=correlate([self.event],Topology(self.config),{},1010)
        self.assertEqual((result['raw_unique_events'],result['active_total_problem_events'],result['active_notice_events'],result['active_problem_events'],result['emitted_groups']),(1,1,1,0,0))
        self.assertEqual(self.event,before)

    def test_any_changed_identity_or_content_keeps_the_event_actionable(self):
        for field,value in [('key','43'),('name','CPU warning'),('severity','3')]:
            event=deepcopy(self.event)
            if field=='key':event[field]=value
            else:event['raw'][field]=value
            result=correlate([event],Topology(self.config),{},1010)
            self.assertEqual((result['active_notice_events'],result['active_problem_events']),(0,1))

    def test_recovery_clears_notice_and_other_warning_remains_actionable(self):
        recovery={**self.event,'event_id':'2','clock':1005,'state':'recovery'}
        fault={**self.event,'event_id':'3','key':'99','kind':'cpu','raw':{'name':'CPU warning','severity':'2'}}
        result=correlate([self.event,recovery,fault],Topology(self.config),{},1010)
        self.assertEqual((result['raw_unique_events'],result['active_notice_events'],result['active_problem_events']),(3,0,1))

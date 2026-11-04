from pathlib import Path
import json
import unittest
import test_worker
from monitoring.correlation import correlate
from monitoring.topology import Topology


class ProbeRecoveryTests(unittest.TestCase):
    def setup_worker(self):
        fixture=test_worker.WorkerTests('test_one_snapshot_covers_one_hundred_distinct_alerts_for_same_node')
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        return fixture,fixture.worker()

    def test_down_unknown_up_recovers_once_and_preserves_raw_problem(self):
        f,w=self.setup_worker()
        for clock,state in [(1000,'down'),(1001,'unknown'),(1002,'up')]:
            f.backend.now=clock;f.backend.gateway=state;w.observe_nodes(clock)
        events=w.store.events()
        self.assertEqual([e['state'] for e in events if e['node']=='gateway'],['problem','recovery'])
        self.assertEqual(correlate(events,f.graph,w.store.node_states(),1002)['active_problem_events'],0)
        self.assertEqual(w.observe_nodes(1002),0)

    def test_open_problem_is_recovered_even_if_cached_node_is_already_up(self):
        f,w=self.setup_worker();f.backend.gateway='down';w.observe_nodes(1000)
        w.store.set_node_state('gateway','up',1001,{})
        f.backend.now=1002;f.backend.gateway='up';w.observe_nodes(1002)
        self.assertEqual([e['state'] for e in w.store.events() if e['node']=='gateway'],['problem','recovery'])

    def test_os_notice_requires_exact_identity_and_severity(self):
        root=Path(__file__).resolve().parents[1]
        topology=Topology(json.loads((root/'config/lab.json').read_text())['topology'])
        event={'source':'zabbix','node':'cli01','key':'25297','raw':{'name':'Linux: Operating system description has changed','severity':'1'}}
        self.assertTrue(topology.is_notice(event))
        event['raw']['severity']='2';self.assertFalse(topology.is_notice(event))

from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest

from monitoring.catalog import ExpertCatalog, create_catalog
from monitoring.store import Store
from monitoring.topology import Topology
from monitoring.worker import Worker

ROOT = Path(__file__).resolve().parents[1]


class Backend:
    def __init__(self):
        self.now = 1000
        self.events = []
        self.failed = False
        self.collections = []
        self.gateway = 'up'
        self.nginx = 'active'

    def api(self, method, params):
        if method=='problem.get':return []
        if method != 'event.get':raise AssertionError(method)
        if 'eventids' in params:return deepcopy([row for row in self.events if row['eventid'] in params['eventids']])
        return deepcopy([row for row in self.events if int(row['eventid']) >= int(params.get('eventid_from', 0)) and int(row['clock']) >= params.get('time_from', 0)][:params['limit']])

    def node_states(self, topology):
        return {node: {'status': self.gateway if node == 'gateway' else 'up', 'observed_at': self.now, 'evidence': {}}
                for node in topology.nodes}

    def collect(self, profile):
        self.collections.append(profile['node'])
        if self.failed:raise TimeoutError('no fabricated measurement')
        evidence = [{'check_type': 'service_state', 'target': profile['target_ip'], 'collected_at': self.now,
                     'result': {'observer':'srv01','service':'nginx','status':'success','state':self.nginx}}] if profile['node']=='server' else []
        return {'decision_time':self.now,'evidence':evidence,'sources':{'fixture':{'status':'ok'}}}


def raw(identity, value=1, host='2', key='500', kind='http_connectivity', clock=1000):
    return {'eventid':str(identity),'value':str(value),'clock':str(clock),'objectid':key,'hosts':[{'hostid':host}],
            'tags':[{'tag':'diag.kind','value':kind}]}


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        path=Path(self.temp.name)
        create_catalog(path/'catalog.sqlite',json.loads((ROOT/'config/expert_seed.json').read_text()))
        self.catalog=ExpertCatalog(path/'catalog.sqlite')
        self.state=path/'state.sqlite'
        self.backend=Backend()
        self.graph=Topology({'version':'worker-fixture','nodes':{'gateway':{'type':'gateway','parents':[]},
                     'server':{'type':'host','parents':['gateway'],'dependency_basis':'fixture routed network'}}})
        self.profiles=[{'node':node,'host_id':host,'profile_id':node,'target_ip':ip,'http_observer':'srv01','http_service':scope}
                       for node,host,ip,scope in [('gateway','1','192.168.56.30','absent'),('server','2','172.30.20.20','expected')]]

    def worker(self, **options):
        return Worker(self.backend,self.catalog,self.graph,Store(self.state),self.profiles,clock=lambda:self.backend.now,probe_interval=0,**options)

    def test_pagination_and_recovery_survive_restart_without_duplicate_jobs(self):
        self.backend.events=[raw(10),raw(11,0),raw(12,key='501')]
        first=self.worker(page_limit=2).cycle()
        self.assertEqual((first['api_pages'],first['store_counts']['events'],first['store_counts']['pending_jobs']),(2,3,0))
        self.assertEqual(self.backend.collections,['server'])
        self.assertEqual(first['correlation']['active_problem_events'],1)
        self.backend.now+=1
        second=self.worker(page_limit=2).cycle()
        self.assertEqual(second['ingested_events'],0)
        self.assertEqual(second['diagnostics'],[])
        self.assertFalse(second['changed'])

    def test_failure_does_not_lose_cursor_or_pending_jobs_and_retries_after_restart(self):
        self.backend.events=[raw(10)];self.backend.failed=True
        failed=self.worker().cycle()
        self.assertEqual(failed['store_counts']['pending_jobs'],1)
        self.assertEqual(Store(self.state).cursor('zabbix'),'10')
        self.backend.failed=False;self.backend.now+=20
        retried=self.worker().cycle()
        self.assertEqual(retried['store_counts']['pending_jobs'],0)
        self.assertEqual(retried['ingested_events'],0)
        self.assertEqual(retried['diagnostics'][0]['jobs'],1)

    def test_one_snapshot_covers_one_hundred_distinct_alerts_for_same_node(self):
        self.backend.events=[raw(i+1,key=str(i+500)) for i in range(100)]
        result=self.worker(page_limit=20).cycle()
        self.assertEqual((len(self.backend.collections),result['store_counts']['events'],result['store_counts']['pending_jobs']),(1,100,0))
        self.assertEqual(result['diagnostics'][0]['assessment']['diagnoses'][-1]['status'],'matched')

    def test_ambiguous_host_does_not_advance_cursor(self):
        self.backend.events=[raw(10,host='999')]
        with self.assertRaises(ValueError):self.worker().cycle()
        self.assertIsNone(Store(self.state).cursor('zabbix'))
        self.assertEqual(Store(self.state).counts()['events'],0)

    def test_periodic_probe_collects_healthy_features_without_waiting_for_an_alert(self):
        worker=self.worker();worker.probe_interval=30
        result=worker.cycle()
        self.assertEqual(len(result['diagnostics']),2)
        self.assertEqual(result['ingested_events'],0)
        self.backend.now+=5
        self.assertEqual(worker.cycle()['diagnostics'],[])
        self.backend.now+=30
        self.assertEqual(len(worker.cycle()['diagnostics']),2)

    def test_independent_service_fault_is_retained_with_gateway_fault_and_recovers(self):
        self.backend.gateway='down';self.backend.nginx='inactive'
        result=self.worker().cycle(force_collect=True)
        self.assertEqual(result['correlation']['emitted_groups'],2)
        self.assertTrue(any(group['root_node']=='server' for group in result['correlation']['groups']))
        self.backend.now+=10;self.backend.gateway='up';self.backend.nginx='active'
        recovered=self.worker().cycle(force_collect=True)
        self.assertEqual(recovered['correlation']['active_problem_events'],0)
        self.assertEqual(recovered['store_counts']['pending_jobs'],0)

    def test_same_host_cannot_be_mapped_twice_even_when_integer(self):
        self.profiles[0]['host_id']=2
        with self.assertRaises(ValueError):self.worker()

    def test_first_start_backfills_an_old_open_problem_outside_recent_lookback(self):
        self.backend.events=[raw(3,clock=100)]
        original=self.backend.api
        self.backend.api=lambda method,params: [{'eventid':'3'}] if method=='problem.get' else original(method,params)
        result=self.worker().cycle()
        self.assertEqual((result['store_counts']['events'],result['correlation']['active_problem_events']),(1,1))
        self.assertIsNone(Store(self.state).cursor('zabbix'))
        self.assertEqual(Store(self.state).counts()['pending_jobs'],0)


if __name__=='__main__':unittest.main()

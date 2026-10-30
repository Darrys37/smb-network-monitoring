import copy,unittest
from pathlib import Path
from mlv2.core import read,VERSION
from mlv2.features import extract,FEATURES


class FeatureTests(unittest.TestCase):
    def sample(self):
        return {'schema_version':2,'session_id':'s','run_id':'r','window_id':'w','collector_version':VERSION,
                'profile':read(Path(__file__).resolve().parents[1]/'config/srv01.json'),
                'started_at':1000,'decision_time':1000,
                'sources':{s:{'status':'ok','error_type':None} for s in ['monitor','local_http','dns']},'evidence':[]}

    def test_whitelist_never_contains_metadata(self):
        row=extract(self.sample())
        self.assertEqual(set(row),set(FEATURES))
        self.assertFalse(set(row)&{'run_id','session_id','label','host_id','event_id'})

    def test_stale_metric_not_filled_with_zero_or_old_number(self):
        sample=self.sample()
        sample['evidence']=[{'check_type':'metric','target':'10683','collected_at':1000,
                            'result':{'key':'system.cpu.util','units':'%','status':'success','sample_clock':700,'value':99}}]
        self.assertIsNone(extract(sample)['cpu_percent'])

    def test_cpu_history_mean_requires_coverage(self):
        sample=self.sample()
        result={'key':'system.cpu.util','status':'success','units':'%',
                'samples':[{'clock':800,'value':100},{'clock':900,'value':100},{'clock':1000,'value':100}]}
        sample['evidence']=[{'check_type':'cpu_history','target':'10683','collected_at':1000,'result':result}]
        self.assertIsNone(extract(sample)['cpu_mean'])
        result['samples'][0]['clock']=760;result['samples'][1]['clock']=880
        self.assertEqual(extract(sample)['cpu_mean'],100)


if __name__=='__main__':unittest.main(verbosity=2)

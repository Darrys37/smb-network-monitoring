import sqlite3
import tempfile
from pathlib import Path
import unittest
import json,time
from unittest.mock import patch
import pandas as pd

from candidate_v2 import write_database
from mlv2.core import LABELS,VERSION,register,review,save_new,sha,read
from mlv2.features import FEATURES,CATEGORICAL,NUMERIC
from locked_test_v2 import test_schedule,fit_methods,predict_methods,verify_split,validate_test_observation,shadow_gate,freeze_development,evaluate_locked,latency,CONFIG,ABSTAIN
from registry_v2 import write_registry


def fixture(prefix):
    return pd.DataFrame([{'session_id':prefix+str(s),'run_id':'r'+str(i)+label,'label':label,
        **{key:'synthetic_'+label for key in CATEGORICAL},**{key:10. for key in NUMERIC}}
        for s in range(2) for label in sorted(LABELS) for i in range(3)])


class LockedTests(unittest.TestCase):
    def test_test_schedule_is_fresh_balanced_and_deterministic(self):
        plan=test_schedule()
        self.assertEqual(len(plan),42)
        self.assertEqual(plan,test_schedule())
        self.assertTrue(all(row['session_id'].startswith('test-v2-') for row in plan))
        self.assertEqual(len({(row['session_id'],row['run_id']) for row in plan}),42)

    def test_fitting_never_learns_test_categories_or_numeric_statistics(self):
        train=fixture('dev');test=fixture('test')
        model=fit_methods(train)
        numeric=model['cart_numeric']['encode'].named_transformers_['numeric']
        before=numeric.statistics_.copy()
        test.loc[:,'cpu_percent']=9999.
        test.loc[:,'ping_status']='NEVER_SEEN_TEST_CATEGORY'
        result=predict_methods(model,test)
        self.assertEqual(len(result),42)
        self.assertEqual(numeric.statistics_.tolist(),before.tolist())
        categories=model['cart_numeric']['encode'].named_transformers_['cat'].categories_
        self.assertNotIn('NEVER_SEEN_TEST_CATEGORY',categories[0])

    def test_split_rejects_shared_sessions_or_changed_frozen_parameters(self):
        train=fixture('dev');test=fixture('test')
        verify_split(train,test,{'config':CONFIG})
        with self.assertRaisesRegex(ValueError,'Session leakage'):verify_split(train,train,{'config':CONFIG})
        with self.assertRaisesRegex(ValueError,'hyperparameters'):verify_split(train,test,{'config':{}})

    def test_temporal_embargo_and_profile_are_required(self):
        frozen={'profile':{'id':'srv'},'earliest_test_time':1000}
        with self.assertRaisesRegex(ValueError,'embargo'):
            validate_test_observation({'profile':{'id':'srv'},'started_at':999},frozen)
        with self.assertRaisesRegex(ValueError,'profile'):
            validate_test_observation({'profile':{'id':'other'},'started_at':1001},frozen)
        validate_test_observation({'profile':{'id':'srv'},'started_at':1000},frozen)

    def test_serving_gate_keeps_unknown_core_as_abstention(self):
        frame=fixture('test').iloc[:2].copy()
        frame.iloc[0,frame.columns.get_loc('ping_status')]='unknown'
        self.assertEqual(shadow_gate(frame,['healthy','healthy']),[ABSTAIN,'healthy'])

    def test_registry_records_research_validation_without_activation_and_preserves_audit(self):
        root=Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory(dir=root) as directory:
            candidate=Path(directory)/'candidates.sqlite'
            registry=Path(directory)/'registry.sqlite'
            cart=[{'rule_id':'leaf0','conditions':[],'label':'healthy','training_runs':6,'leaf_class_fraction':1.}]
            fp=[{'conditions':['ping_status=success'],'label':'healthy','training_runs':6,'confidence':1.,'support':.2,'lift':2.}]
            write_database(candidate,cart,fp,{})
            freeze={'train':[],'config':dict(CONFIG),'scope':'synthetic test fixture only'}
            write_registry(registry,candidate,freeze,[],{'cart_discrete':{},'fp_classifier':{}},
                           {'test_rows':1,'CART':True,'FP-Growth':True})
            db=sqlite3.connect(registry)
            try:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM rule_lifecycle WHERE state='active'").fetchone()[0],0)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM rule_lifecycle WHERE state='validated'").fetchone()[0],2)
                with self.assertRaises(sqlite3.IntegrityError):db.execute('DELETE FROM rule_lifecycle')
                db.rollback()
                with self.assertRaises(sqlite3.IntegrityError):db.execute("UPDATE rules SET label='cpu_stress'")
                db.rollback()
                self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            finally:db.close()

    def test_end_to_end_on_synthetic_schema_fixture_not_lab_data(self):
        project=Path(__file__).resolve().parents[2]
        profile=read(project/'ml-research/config/srv01.json')
        root=Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-M5-',dir=root) as directory:
            base=Path(directory);trainroot=base/'development';testroot=base/'test'
            fake_benchmark=base/'fake-pilot-output';fake_benchmark.mkdir()
            source_rows=[];csv_rows=[]
            def record(data,item,stamp):
                session,run=item['session_id'],item['run_id']
                register(data,session,run,[item['label']])
                value={'schema_version':2,'collector_version':VERSION,'session_id':session,'run_id':run,
                    'window_id':'synthetic-window','profile':profile,'started_at':stamp,'decision_time':stamp,
                    'sources':{key:{'status':'error','error_type':'SyntheticUnitFixture'} for key in ['monitor','local_http','dns']},'evidence':[]}
                path=data/'observations'/session/run/'synthetic-window.json';save_new(path,value)
                evidence=data/'synthetic-logs'/session/(run+'.json');save_new(evidence,{'synthetic_only':True})
                reviewed=review(data,session,run,'valid',[item['label']],[evidence])
                review_path=next((data/'registry'/session/run).glob('review-*.json'))
                save_new(data/'trial-logs'/session/run/'RESULT.json',{**item,'valid':True,'review':reviewed})
                return {'session_id':session,'run_id':run,'path':str(path),'sha256':sha(path),'review_sha256':sha(review_path)}
            for index,item in enumerate(test_schedule()):
                dev={**item,'session_id':item['session_id'].replace('test-v2','synthetic-dev')}
                source_rows.append(record(trainroot,dev,int(time.time())-1000))
                csv_rows.append({key:dev[key] for key in ['session_id','run_id','label']})
            pd.DataFrame(csv_rows).to_csv(fake_benchmark/'dataset_used.csv',index=False)
            save_new(fake_benchmark/'manifest.json',{'sources':source_rows})
            write_database(fake_benchmark/'candidate_rules.sqlite',[],[],{})
            frozen=base/'freeze.json';freeze=freeze_development(project,fake_benchmark,frozen)
            for item in freeze['test_schedule']:record(testroot,item,freeze['earliest_test_time']+1)
            with patch('locked_test_v2.latency',return_value={'scope':'Synthetic fixture; timing not measured'}):
                output=evaluate_locked(project,testroot,frozen,base/'evaluation')
            manifest=read(output/'manifest.json')
            self.assertEqual(manifest['train_rows'],42);self.assertEqual(manifest['test_rows'],42)
            self.assertTrue(read(output/'held_out_serialization_equivalence.json')['CART'])
            self.assertEqual(read(output/'metrics.json')['cart_discrete']['coverage'],0.)
            self.assertTrue((output/'research_registry.sqlite').is_file())
            timing=latency(project,fit_methods(fixture('dev')),[source_rows[0]],repeats=1)
            self.assertEqual(timing['methods']['expert']['calls'],1)


if __name__=='__main__':unittest.main()

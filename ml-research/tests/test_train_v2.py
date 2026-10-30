import unittest
import numpy as np
import pandas as pd
import tempfile
from pathlib import Path
from train_v2 import tree_model,grouped_folds,learn_rules,rules_predict,metrics,family_comparison,evaluate,quality_analysis,ABSTAIN
from candidate_v2 import export_cart,cart_predict,fp_predict,write_database,load_database,discrete_row


class TrainingTests(unittest.TestCase):
    def test_imputer_and_encoder_fit_only_train(self):
        train=pd.DataFrame({'signal':['a','a','b','b'],'cpu':[10.,20.,np.nan,30.]})
        model=tree_model(['signal'],['cpu']).fit(train,['x','x','y','y'])
        numeric=model['encode'].named_transformers_['numeric']
        before=numeric.statistics_.copy()
        model.predict(pd.DataFrame({'signal':['never_seen'],'cpu':[99999.]}))
        np.testing.assert_equal(numeric.statistics_,before)
        self.assertEqual(before.tolist(),[20.])

    def test_session_split_keeps_all_related_runs_together(self):
        frame=pd.DataFrame([{'session_id':s,'run_id':s+y+str(i),'label':y}
              for s in ['session1','session2'] for y in ['fault_a','fault_b'] for i in range(3)])
        for train,test in grouped_folds(frame):
            self.assertFalse(set(frame.iloc[train].session_id)&set(frame.iloc[test].session_id))
        with self.assertRaises(ValueError):grouped_folds(frame.iloc[:6])

    def test_rule_statistics_and_unseen_case_abstain(self):
        x=pd.DataFrame({'signal':['up']*3+['down']*3});labels=['a']*3+['b']*3
        rules=learn_rules(x,labels)
        self.assertEqual(len(rules),2)
        for rule in rules:
            self.assertAlmostEqual(rule['support'],.5)
            self.assertAlmostEqual(rule['confidence'],1.)
            self.assertAlmostEqual(rule['lift'],2.)
            self.assertEqual(rule['training_runs'],3)
        self.assertEqual(rules_predict(rules,x),labels)
        self.assertEqual(rules_predict(rules,pd.DataFrame({'signal':['unknown']})),[ABSTAIN])

    def test_conflicting_equal_rules_do_not_pick_arbitrary_label(self):
        rules=[{'conditions':['signal=up'],'label':y,'confidence':1.,'support':.5} for y in ['a','b']]
        self.assertEqual(rules_predict(rules,pd.DataFrame({'signal':['up']})),[ABSTAIN])

    def test_abstention_remains_in_full_accuracy_denominator(self):
        result=metrics(['a','b'],['a',ABSTAIN])
        self.assertEqual(result['accuracy_all_runs'],.5)
        self.assertEqual(result['coverage'],.5)
        self.assertEqual(result['accuracy_covered'],1.)

    def test_expert_insufficient_is_not_counted_as_healthy_clearance(self):
        expert=[{'diagnostic_family':'nginx_stopped','injected_label':y,'expert_status':status}
                for y,status in [('healthy','insufficient_evidence'),('nginx_stopped','matched')]]
        predictions=pd.DataFrame({name:['healthy','nginx_stopped']
                                  for name in ['cart_numeric','cart_discrete','fp_classifier']})
        result=next(r for r in family_comparison(expert,predictions) if r['method']=='expert')
        self.assertEqual(result['coverage'],.5)
        self.assertEqual(result['healthy_abstentions'],1)
        self.assertEqual(result['healthy_false_alarms'],0)

    def test_sqlite_cart_and_fp_preserve_predictions_including_unseen_category(self):
        x=pd.DataFrame({'signal':['up']*3+['down']*3,'other':['yes']*6});labels=['a']*3+['b']*3
        tree=tree_model(list(x),[]).fit(x,labels)
        cart=export_cart(tree,list(x));fp=learn_rules(x,labels)
        probe=pd.DataFrame({'signal':['up','down','never_seen'],'other':['yes']*3})
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'rules.sqlite'
            write_database(path,cart,fp,{'features':list(x)})
            _,restored=load_database(path)
            self.assertEqual([cart_predict(restored['CART'],row)['label'] for row in probe.to_dict('records')],tree.predict(probe).tolist())
            self.assertEqual([fp_predict(restored['FP-Growth'],row)['label'] for row in probe.to_dict('records')],rules_predict(fp,probe))
            with self.assertRaises(FileExistsError):write_database(path,cart,fp,{})

    def test_candidate_conditions_are_data_and_unknown_operator_is_rejected(self):
        rule={'conditions':[{'feature':'signal','op':'exec','value':'unsafe'}],'label':'a'}
        with self.assertRaises(ValueError):cart_predict([rule],{'signal':'up'})
        self.assertEqual(cart_predict([],{'signal':'up'})['label'],ABSTAIN)

    def test_discretization_keeps_missing_values_and_boundary_semantics(self):
        row=discrete_row({'a':'unknown','cpu_percent':None,'ram_percent':90.,'cpu_coverage_seconds':240.,'cpu_max_gap_seconds':120.},
            ['a'],['cpu_percent','ram_percent','cpu_coverage_seconds','cpu_max_gap_seconds'])
        self.assertEqual(row,{'a':'unknown','cpu_percent':'unknown','ram_percent':'high_ge90',
                             'cpu_coverage_seconds':'sufficient','cpu_max_gap_seconds':'gap_ok'})

    def test_all_benchmarks_run_on_grouped_synthetic_fixture(self):
        frame=pd.DataFrame([{'session_id':s,'run_id':s+y+str(i),'label':y,'signal':y,'cpu_percent':10.}
            for s in ['session1','session2'] for y in ['a','b'] for i in range(3)])
        summary,folds,predictions=evaluate(frame,['signal','cpu_percent'],['signal'],['cpu_percent'])
        self.assertEqual(summary['cart_numeric']['correct'],12)
        self.assertEqual(summary['fp_classifier']['correct'],12)
        self.assertEqual(summary['cart_missingness']['correct'],6)
        self.assertEqual(len(predictions),12)
        self.assertEqual(len(folds),2)
        self.assertEqual(quality_analysis(frame,['signal','cpu_percent'],['signal'],['cpu_percent'])['empirical_discrete_deterministic_ceiling'],1.)


if __name__=='__main__':unittest.main(verbosity=2)

"""Fixed-configuration pilot benchmark; no live rule activation or API calls.

Configuration uses knowledge of the initial pilot. Held-out pilot sessions are
internal validation, not a claim of blind evaluation or cross-host generalization.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.metadata,json,math,sqlite3,sys,time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import fpgrowth
from mlxtend.preprocessing import TransactionEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score,f1_score,confusion_matrix
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier,export_text
from candidate_v2 import discrete_row,export_cart,cart_predict,fp_predict,write_database,load_database

ABSTAIN='ABSTAIN'
CONFIG={'tree_max_depth':6,'tree_min_samples_leaf':2,'random_state':37,
        'fp_min_run_count':2,'fp_min_confidence':0.8,'fp_min_lift':1.1,
        'fp_max_conditions':4,'numeric_high_percent':90}


def dump(path,value):
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def discrete(frame,categorical,numeric):
    return pd.DataFrame([discrete_row(row,categorical,numeric) for row in frame.to_dict('records')],index=frame.index)


def tree_model(categorical,numeric):
    transforms=[('cat',OneHotEncoder(handle_unknown='ignore',sparse_output=False),categorical)]
    if numeric:
        transforms.append(('numeric',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True),numeric))
    return Pipeline([('encode',ColumnTransformer(transforms)),
        ('tree',DecisionTreeClassifier(max_depth=CONFIG['tree_max_depth'],
             min_samples_leaf=CONFIG['tree_min_samples_leaf'],random_state=CONFIG['random_state']))])


def baskets(frame):
    return [{str(key)+'='+str(value) for key,value in row.items() if value not in ['unknown','not_applicable']}
            for row in frame.to_dict('records')]


def learn_rules(frame,labels):
    data=[x|{'label='+str(y)} for x,y in zip(baskets(frame),labels)]
    encoder=TransactionEncoder();matrix=encoder.fit(data).transform(data)
    itemsets=fpgrowth(pd.DataFrame(matrix,columns=encoder.columns_),
                     min_support=CONFIG['fp_min_run_count']/len(data),use_colnames=True,
                     max_len=CONFIG['fp_max_conditions']+1)
    supports=dict(zip(itemsets.itemsets,itemsets.support))
    candidates=[]
    for items,support in supports.items():
        outcomes=[v for v in items if v.startswith('label=')]
        if len(outcomes)!=1 or len(items)<2:continue
        condition=items-frozenset(outcomes)
        confidence=float(support/supports[condition])
        lift=float(confidence/supports[frozenset(outcomes)])
        if confidence<CONFIG['fp_min_confidence'] or lift<CONFIG['fp_min_lift']:continue
        candidates.append({'conditions':sorted(condition),'label':outcomes[0][6:],
             'support':float(support),'confidence':confidence,'lift':lift,
             'training_runs':int(round(support*len(data)))})
    # Train-only dominance pruning. Equal-quality longer rules do not add evidence.
    candidates.sort(key=lambda r:(len(r['conditions']),-r['confidence'],-r['support'],r['conditions']))
    kept=[]
    for rule in candidates:
        dominated=any(other['label']==rule['label'] and set(other['conditions'])<=set(rule['conditions'])
             and other['confidence']>=rule['confidence'] and other['support']>=rule['support'] for other in kept)
        if not dominated:kept.append(rule)
    return kept


def rules_predict(rules,frame):
    predicted=[]
    for basket in baskets(frame):
        matched=[r for r in rules if set(r['conditions'])<=basket]
        if not matched:predicted.append(ABSTAIN);continue
        score=lambda r:(r['confidence'],r['support'],-len(r['conditions']))
        best=max(score(r) for r in matched)
        winners={r['label'] for r in matched if score(r)==best}
        predicted.append(next(iter(winners)) if len(winners)==1 else ABSTAIN)
    return predicted


def grouped_folds(frame):
    if frame.session_id.nunique()<2:raise ValueError('At least two completed sessions are required')
    splits=list(LeaveOneGroupOut().split(frame,frame.label,frame.session_id))
    classes=set(frame.label)
    for train,test in splits:
        if set(frame.iloc[train].session_id)&set(frame.iloc[test].session_id):raise AssertionError('Session leakage')
        if set(frame.iloc[train].label)!=classes or set(frame.iloc[test].label)!=classes:
            raise ValueError('Every train/test session must contain all diagnostic labels')
    return splits


def metrics(truth,predicted):
    classes=sorted(set(truth));covered=[i for i,x in enumerate(predicted) if x!=ABSTAIN]
    return {'accuracy_all_runs':float(accuracy_score(truth,predicted)),
            'macro_f1':float(f1_score(truth,predicted,labels=classes,average='macro',zero_division=0)),
            'coverage':len(covered)/len(truth),
            'accuracy_covered':float(accuracy_score([truth[i] for i in covered],[predicted[i] for i in covered])) if covered else None,
            'correct':sum(a==b for a,b in zip(truth,predicted)),'runs':len(truth),
            'confusion_labels':classes+[ABSTAIN],
            'confusion_matrix':confusion_matrix(truth,predicted,labels=classes+[ABSTAIN]).tolist()}


def load_data(project,root):
    sys.path.insert(0,str(project/'ml-research'))
    from mlv2.core import read,sha
    from mlv2.features import extract,FEATURES,CATEGORICAL,NUMERIC
    from mlv2.pilot import schedule
    from mlv2.quality import audit
    # Require results for every original scheduled attempt; uncertain attempts stay visible.
    for item in schedule():
        if not (root/'trial-logs'/item['session_id']/item['run_id']/'RESULT.json').exists():
            raise ValueError('Pilot schedule is incomplete; no benchmark produced')
    records=[];provenance=[]
    for registration in sorted((root/'registry').glob('pilot-v2-*/*/registration.json')):
        item=read(registration);session,run=item['session_id'],item['run_id']
        revisions=list(registration.parent.glob('review-*.json'))
        if len(revisions)!=1:raise ValueError('Explicit review revision required: '+run)
        review=read(revisions[0])
        if review['validity']!='valid':continue
        if review['registration_sha256']!=sha(registration):raise ValueError('Registration hash mismatch')
        for reference in review['references']:
            evidence=root/'review-evidence'/reference['sha256']
            if sha(evidence)!=reference['sha256']:raise ValueError('Ground-truth provenance mismatch')
        if len(review['labels'])!=1:raise ValueError('Single-fault pilot benchmark requires one label')
        windows=list((root/'observations'/session/run).glob('*.json'))
        path=max(windows,key=lambda p:read(p)['decision_time'])
        observation=read(path)
        if observation['profile']!=read(project/'ml-research/config/srv01.json'):
            raise ValueError('Pilot benchmark requires the declared common SRV01 profile')
        records.append({'session_id':session,'run_id':run,'label':review['labels'][0],**extract(observation)})
        provenance.append({'session_id':session,'run_id':run,'path':str(path),'sha256':sha(path),'review_sha256':sha(revisions[0])})
    frame=pd.DataFrame(records)
    if frame.empty:raise ValueError('No valid data')
    counts=frame.groupby(['session_id','label']).size()
    if len(counts)!=14 or counts.min()<3:raise ValueError('Need three valid independent run IDs per label/session')
    for key in NUMERIC:frame[key]=pd.to_numeric(frame[key],errors='raise')
    return frame,provenance,FEATURES,CATEGORICAL,NUMERIC


def evaluate(frame,features,categorical,numeric):
    indices=grouped_folds(frame)
    predictions={n:[None]*len(frame) for n in ['majority','cart_numeric','cart_discrete','fp_classifier','cart_no_quality','cart_missingness','cart_common']}
    log=[]
    x_discrete=discrete(frame[features],categorical,numeric) # fixed domain bins; no dataset fit
    measured_numeric=[key for key in numeric if key not in ['cpu_coverage_seconds','cpu_max_gap_seconds']]
    common_categorical=[key for key in categorical if key not in ['local_http_status','dns_status']]
    presence=x_discrete.map(lambda value:'missing' if value=='unknown' else ('not_applicable' if value=='not_applicable' else 'available'))
    for train_idx,test_idx in indices:
        train,test=frame.iloc[train_idx],frame.iloc[test_idx]
        fold={'train_sessions':sorted(set(train.session_id)),'test_sessions':sorted(set(test.session_id)),
              'train_runs':train.run_id.tolist(),'test_runs':test.run_id.tolist()}
        for name,x,cat,num in [('cart_numeric',frame[features],categorical,numeric),
                              ('cart_discrete',x_discrete,features,[]),
                              ('cart_no_quality',frame[categorical+measured_numeric],categorical,measured_numeric),
                              ('cart_missingness',presence,features,[]),
                              ('cart_common',frame[common_categorical+numeric],common_categorical,numeric)]:
            model=tree_model(cat,num).fit(x.iloc[train_idx],train.label)
            start=time.perf_counter();values=model.predict(x.iloc[test_idx]).tolist()
            fold[name+'_batch_ms_per_run']=1000*(time.perf_counter()-start)/len(test)
            for i,value in zip(test_idx,values):predictions[name][i]=value
        rules=learn_rules(x_discrete.iloc[train_idx],train.label)
        values=rules_predict(rules,x_discrete.iloc[test_idx]);fold['fp_rules_train']=len(rules)
        for i,value in zip(test_idx,values):predictions['fp_classifier'][i]=value
        majority=sorted(Counter(train.label).items(),key=lambda item:(-item[1],item[0]))[0][0]
        for i in test_idx:predictions['majority'][i]=majority
        log.append(fold)
    summary={name:metrics(frame.label.tolist(),values) for name,values in predictions.items()}
    table=frame[['session_id','run_id','label']].copy()
    for name,values in predictions.items():table[name]=values
    return summary,log,table


def quality_analysis(frame,features,categorical,numeric):
    x=discrete(frame[features],categorical,numeric)
    missing=[]
    for label,group in x.assign(label=frame.label).groupby('label'):
        for feature in features:
            missing.append({'label':label,'feature':feature,'runs':len(group),
                            'unknown':int((group[feature]=='unknown').sum()),
                            'not_applicable':int((group[feature]=='not_applicable').sum())})
    groups=frame[['session_id','run_id','label']].join(x).groupby(features,dropna=False)
    collisions=[];correct_bound=0
    for vector,group in groups:
        counts=Counter(group.label)
        correct_bound+=max(counts.values())
        if len(counts)>1:
            collisions.append({'vector':dict(zip(features,vector)),'labels':dict(counts),
                               'runs':group[['session_id','run_id','label']].to_dict('records')})
    return {'missingness_by_label':missing,'distinct_discrete_vectors':len(groups),
            'conflicting_vectors':collisions,'empirical_discrete_deterministic_ceiling':correct_bound/len(frame),
            'note':'Descriptive in-sample identifiability bound; not expected test accuracy. Missingness-only CART is an explicit shortcut check.'}


def compare_expert(project,provenance,predictions):
    sys.path.insert(0,str(project/'diagnosis-engine'))
    from models import EvidenceRecord
    from roadmap_rules import diagnose_roadmap
    from mlv2.core import read
    mapping={'R1':'interface_down','R2':'nginx_stopped','R3':'agent_stopped','R4':'dns_egress_blocked',
             'R5':'remote_http_filtered','R6':'cpu_stress'}
    rows=[]
    for i,source in enumerate(provenance):
        observation=read(source['path']);p=observation['profile']
        diagnoses=diagnose_roadmap(p['host_id'],p['target_ip'],[EvidenceRecord(**e) for e in observation['evidence']],
            control=p['control_ip'],http_observer=p['observer'],dns_name=p['dns_name'],dns_observer=p['observer'],
            control_ip=p['dns_control_ip'],http_service=p['http_service'],now=observation['decision_time'])
        for diagnosis in diagnoses:
            family=mapping[diagnosis.rule_id.split('_')[0]]
            rows.append({'session_id':source['session_id'],'run_id':source['run_id'],
                         'injected_label':predictions.iloc[i]['label'],'diagnostic_family':family,
                         'expert_status':diagnosis.status,'reasoning':diagnosis.reasoning})
    return rows


def family_comparison(expert,predictions):
    """Compare six independent questions; never call all not_matched 'healthy'."""
    output=[]
    families=sorted({r['diagnostic_family'] for r in expert})
    for family in families:
        assessments=[r for r in expert if r['diagnostic_family']==family]
        truth=[r['injected_label']==family for r in assessments]
        healthy=[r['injected_label']=='healthy' for r in assessments]
        methods={'expert':[{'matched':True,'not_matched':False,'insufficient_evidence':None}[r['expert_status']] for r in assessments]}
        for method in ['cart_numeric','cart_discrete','fp_classifier']:
            methods[method]=[None if value==ABSTAIN else value==family for value in predictions[method]]
        for method,values in methods.items():
            tp=sum(t and v is True for t,v in zip(truth,values))
            fp=sum(not t and v is True for t,v in zip(truth,values))
            fn=sum(t and v is not True for t,v in zip(truth,values))
            healthy_n=sum(healthy)
            output.append({'diagnostic_family':family,'method':method,'tp':tp,'fp':fp,'fn_including_abstention':fn,
                'precision':tp/(tp+fp) if tp+fp else 0.,'recall_including_abstention':tp/(tp+fn) if tp+fn else 0.,
                'f1_including_abstention':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.,
                'coverage':sum(v is not None for v in values)/len(values),
                'healthy_false_alarms':sum(h and v is True for h,v in zip(healthy,values)),
                'healthy_abstentions':sum(h and v is None for h,v in zip(healthy,values)),
                'healthy_runs':healthy_n})
    return output


def candidates(frame,features,categorical,numeric,out,profile):
    x=discrete(frame[features],categorical,numeric)
    rules=learn_rules(x,frame.label)
    dump(out/'fp_candidates_training_only.json',rules)
    model=tree_model(features,[]).fit(x,frame.label)
    names=model['encode'].get_feature_names_out().tolist()
    (out/'cart_discrete_training_only.txt').write_text(export_text(model['tree'],feature_names=names,max_depth=10),encoding='utf-8')
    cart=export_cart(model,features)
    dump(out/'cart_candidates_training_only.json',cart)
    write_database(out/'candidate_rules.sqlite',cart,rules,
        {'features':features,'categorical':categorical,'numeric':numeric,'config':CONFIG,
         'scope':'pilot same-profile candidate suggestions only; not active or calibrated',
         'profile':profile,
         'training_runs':len(frame),'training_sessions':sorted(set(frame.session_id))})
    _,restored=load_database(out/'candidate_rules.sqlite')
    rows=x.to_dict('records')
    expected=model.predict(x).tolist()
    actual=[cart_predict(restored['CART'],row)['label'] for row in rows]
    if actual!=expected:raise AssertionError('CART/SQLite prediction mismatch')
    if [fp_predict(restored['FP-Growth'],row)['label'] for row in rows]!=rules_predict(rules,x):
        raise AssertionError('FP/SQLite prediction mismatch')
    dump(out/'candidate_equivalence.json',{'rows':len(rows),'CART_discrete':True,'FP_classifier':True,
         'scope':'all fitted pilot feature rows; independent unseen-category tests are in unit suite'})
    return len(rules)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',type=Path,required=True)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--output-root',type=Path,required=True)
    args=parser.parse_args()
    frame,sources,features,categorical,numeric=load_data(args.project_root,args.data_root)
    out=args.output_root/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
    frame.to_csv(out/'dataset_used.csv',index=False,encoding='utf-8-sig')
    summary,folds,predictions=evaluate(frame,features,categorical,numeric)
    dump(out/'metrics.json',summary);dump(out/'folds.json',folds)
    dump(out/'quality_and_identifiability.json',quality_analysis(frame,features,categorical,numeric))
    later=sorted(set(frame.session_id))[-1]
    forward=predictions[predictions.session_id==later]
    forward_metrics={name:metrics(forward.label.tolist(),forward[name].tolist()) for name in summary}
    dump(out/'forward_block_metrics.json',{'test_session':later,'metrics':forward_metrics})
    predictions.to_csv(out/'held_out_predictions.csv',index=False,encoding='utf-8-sig')
    expert=compare_expert(args.project_root,sources,predictions)
    dump(out/'expert_assessments_same_evidence.json',expert)
    comparison=family_comparison(expert,predictions)
    dump(out/'family_comparison.json',comparison)
    pd.DataFrame(comparison).to_csv(out/'family_comparison.csv',index=False,encoding='utf-8-sig')
    count=candidates(frame,features,categorical,numeric,out,
        json.loads((args.project_root/'ml-research/config/srv01.json').read_text(encoding='utf-8')))
    lines=['# ML v2 internal pilot benchmark','',
        f"{len(frame)} valid runs across {frame.session_id.nunique()} blocks; last observation per run.",'',
        '| Method | Correct / runs | Macro-F1 | Coverage |','|---|---:|---:|---:|']
    for name,value in summary.items():lines.append(f"| {name} | {value['correct']}/{value['runs']} | {value['macro_f1']:.3f} | {value['coverage']:.1%} |")
    lines+=['','## Later-block holdout','',f'Train on earlier block; test on {later}. This is the forward-in-time internal comparison.',
            '', '| Method | Correct / runs | Macro-F1 | Coverage |','|---|---:|---:|---:|']
    for name,value in forward_metrics.items():lines.append(f"| {name} | {value['correct']}/{value['runs']} | {value['macro_f1']:.3f} | {value['coverage']:.1%} |")
    lines+=['','Leave-one-session-out; preprocessing/mining/pruning fits training sessions only. Domain bins are fixed.',
        '', 'This is internal pilot validation: same host, same lab, same day and only two collection blocks. The initial pilot was seen during method design. No untouched final test, cross-host accuracy, production FPR or calibrated diagnosis probability is claimed.',
        '', 'Expert output remains six independent matched/not_matched/insufficient assessments. It is not forced into a single class or treated as healthy when no rule matches. Read the same-evidence JSON before any per-family evaluation.',
        '', 'Unknown metric values and history coverage can reveal data availability. Evaluate missingness ablation on new data before deployment. CPU/RAM discretization at 90% is a fixed benchmark choice, not a learned optimal threshold.',
        '', 'Predefined ablations use the same held-out sessions: cart_no_quality removes CPU coverage/gap columns; cart_missingness sees availability only and no measured values; cart_common removes local HTTP and DNS probes. Strong missingness-only results reveal a shortcut in this controlled dataset, not fault diagnosis from symptoms.',
        '', f'{count} FP candidates fitted on all pilot rows are training-only artifacts, distinct from fold models. Confidence/lift are not calibrated causal probabilities. No candidate is activated.',
        '', 'Prediction timings are tiny offline batches and exclude evidence collection/API time.','']
    (out/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    code_files=[Path(__file__),Path(__file__).with_name('candidate_v2.py'),
                args.project_root/'ml-research/mlv2/features.py',
                *[args.project_root/'diagnosis-engine'/name for name in ['models.py','policy.py','roadmap_rules.py']]]
    dump(out/'manifest.json',{'config':CONFIG,'features':features,'sources':sources,'code_sha256':digest(__file__),
         'code_files_sha256':{str(path):digest(path) for path in code_files},
         'packages':{p:importlib.metadata.version(p) for p in ['numpy','pandas','scikit-learn','mlxtend']},
         'scope':'pilot-only internal validation; no runtime activation'})
    dump(args.output_root/'latest.json',{'output_dir':str(out)})
    print(json.dumps({'status':'PILOT_BENCHMARK_OK','rows':len(frame),'output_dir':str(out),'metrics':summary},ensure_ascii=True))


if __name__=='__main__':main()

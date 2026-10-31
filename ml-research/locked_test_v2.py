"""Freeze development data before fresh collection; evaluate the sealed test once."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report

from mlv2.core import LABELS,read,save_new,sha
from mlv2.features import FEATURES,CATEGORICAL,NUMERIC,extract
from mlv2.pilot import schedule
from candidate_v2 import load_database,cart_predict,fp_predict
from registry_v2 import write_registry
from train_v2 import (CONFIG,ABSTAIN,tree_model,discrete,learn_rules,rules_predict,
    metrics,compare_expert,family_comparison,quality_analysis,candidates)


def dump(path,value):
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')


def test_schedule():
    return [{**item,'session_id':item['session_id'].replace('pilot-v2-','test-v2-')}
            for item in schedule(seed=101,sessions=2,repeats=3)]


def method_inputs(frame):
    x=frame[FEATURES]
    xd=discrete(x,CATEGORICAL,NUMERIC)
    numeric=[key for key in NUMERIC if key not in ['cpu_coverage_seconds','cpu_max_gap_seconds']]
    common=[key for key in CATEGORICAL if key not in ['local_http_status','dns_status']]
    presence=xd.map(lambda value:'missing' if value=='unknown' else ('not_applicable' if value=='not_applicable' else 'available'))
    return {'cart_numeric':(x,CATEGORICAL,NUMERIC),'cart_discrete':(xd,FEATURES,[]),
            'cart_no_quality':(frame[CATEGORICAL+numeric],CATEGORICAL,numeric),
            'cart_missingness':(presence,FEATURES,[]),
            'cart_common':(frame[common+NUMERIC],common,NUMERIC)}


def fit_methods(train):
    output={}
    for name,(x,cat,num) in method_inputs(train).items():
        output[name]=tree_model(cat,num).fit(x,train.label)
    output['fp_classifier']=learn_rules(discrete(train[FEATURES],CATEGORICAL,NUMERIC),train.label)
    output['majority']=sorted(Counter(train.label).items(),key=lambda pair:(-pair[1],pair[0]))[0][0]
    return output


def predict_methods(models,test):
    result=test[['session_id','run_id','label']].copy()
    for name,(x,_,_) in method_inputs(test).items():result[name]=models[name].predict(x).tolist()
    result['fp_classifier']=rules_predict(models['fp_classifier'],discrete(test[FEATURES],CATEGORICAL,NUMERIC))
    for method in ['cart_discrete','fp_classifier']:
        result[method]=shadow_gate(test,result[method].tolist())
    result['majority']=models['majority']
    return result


def shadow_gate(frame,values):
    core=['ping_status','tcp80_status','tcp10050_status','control_ping_status']
    missing=frame[core].eq('unknown').any(axis=1).tolist()
    return [ABSTAIN if absent else value for value,absent in zip(values,missing)]


def verify_split(train,test,freeze):
    if set(train.session_id)&set(test.session_id):raise ValueError('Session leakage')
    if set(zip(train.session_id,train.run_id))&set(zip(test.session_id,test.run_id)):
        raise ValueError('Run leakage')
    if set(test.label)!=LABELS or set(train.label)!=LABELS:raise ValueError('Label coverage incomplete')
    if min(test.groupby(['session_id','label']).size())<3:raise ValueError('Test needs three valid runs per label/block')
    if len(test.groupby(['session_id','label']).size())!=14:raise ValueError('Expected two complete locked test blocks')
    if CONFIG!=freeze['config']:raise ValueError('Frozen hyperparameters changed')


def freeze_development(project,pilot_output,target):
    if target.exists():raise FileExistsError(target)
    source=read(pilot_output/'manifest.json')
    metadata=pd.read_csv(pilot_output/'dataset_used.csv',encoding='utf-8-sig',keep_default_na=False)
    labels={(row.session_id,row.run_id):row.label for row in metadata.itertuples()}
    rows=[];last=0
    for item in source['sources']:
        path=Path(item['path'])
        if sha(path)!=item['sha256']:raise ValueError('Development observation changed')
        observation=read(path);extract(observation)
        label=labels[item['session_id'],item['run_id']]
        registry=path.parents[3]/'registry'/item['session_id']/item['run_id']
        reviews=[p for p in registry.glob('review-*.json') if sha(p)==item['review_sha256']]
        if len(reviews)!=1:raise ValueError('Development review differs from benchmark')
        review=read(reviews[0])
        if review['labels']!=[label] or review['validity']!='valid':raise ValueError('Development label changed')
        if review['registration_sha256']!=sha(registry/'registration.json'):raise ValueError('Development registry changed')
        for reference in review['references']:
            if sha(path.parents[3]/'review-evidence'/reference['sha256'])!=reference['sha256']:
                raise ValueError('Development ground truth changed')
        rows.append({**item,'label':label})
        last=max(last,observation['decision_time'])
    if len(rows)<42:raise ValueError('Pilot development data is incomplete')
    files=[Path(__file__),Path(__file__).with_name('registry_v2.py'),
           *[project/'ml-research'/name for name in ['train_v2.py','candidate_v2.py','demo_v2.py','mlv2/features.py']],
           *[project/'diagnosis-engine'/name for name in ['models.py','policy.py','roadmap_rules.py']]]
    files.extend(sorted((project/'ml-research/mlv2').glob('*.py')))
    files.append(project/'ml-research/config/srv01.json')
    value={'schema_version':1,'frozen_at':int(time.time()),'config':dict(CONFIG),'features':FEATURES,
           'profile':read(project/'ml-research/config/srv01.json'),'train':rows,
           'earliest_test_time':max(last+600,int(time.time())),
           'embargo_seconds':600,'test_schedule':test_schedule(),
           'code_sha256':{str(path):sha(path) for path in files},
           'package_versions':{name:importlib.metadata.version(name) for name in ['numpy','pandas','scikit-learn','mlxtend']},
           'scope':'Fixed-configuration pilot development -> two fresh same-host test blocks; no cross-host or IID claim',
           'budget':'42 new test runs (2 blocks x 3 repeats x 7 labels); smaller initial acceptance study than the provisional 210-run proposal',
           'test_policy':'No model scores viewed until both test blocks complete; retry only independent intervention validity; no tuning after opening test'}
    value['shadow_policy']='CART discrete and FP abstain if any core ping/TCP80/TCP10050/control probe is unknown; profile must match exactly'
    value['pilot_candidate_sha256']=sha(pilot_output/'candidate_rules.sqlite')
    value['pilot_manifest_sha256']=sha(pilot_output/'manifest.json')
    save_new(target,value)
    return value


def load_development(freeze):
    records=[]
    for source in freeze['train']:
        if sha(source['path'])!=source['sha256']:raise ValueError('Frozen training observation changed')
        observation=read(source['path'])
        records.append({'session_id':source['session_id'],'run_id':source['run_id'],'label':source['label'],**extract(observation)})
    frame=pd.DataFrame(records)
    for key in NUMERIC:frame[key]=pd.to_numeric(frame[key])
    return frame


def load_test(root,freeze):
    records=[];sources=[]
    for item in freeze['test_schedule']:
        original=root/'trial-logs'/item['session_id']/item['run_id']/'RESULT.json'
        if not original.exists():raise ValueError('Locked test collection is incomplete')
        choices=[original,*sorted(original.parent.parent.glob(item['run_id']+'-retry*/RESULT.json'))]
        valid=[path for path in choices if read(path)['valid']]
        if len(valid)!=1:raise ValueError('Each scheduled test needs exactly one valid attempt')
        result=read(valid[0]);session,run=result['session_id'],result['run_id']
        registration=root/'registry'/session/run/'registration.json'
        reviews=list(registration.parent.glob('review-*.json'))
        if len(reviews)!=1:raise ValueError('Test needs one unambiguous independent review')
        review=read(reviews[0])
        if review['validity']!='valid' or review['labels']!=[item['label']]:raise ValueError('Test review/label mismatch')
        if read(registration)['registered_at']<freeze['frozen_at']:raise ValueError('Test registered before freeze')
        if review['registration_sha256']!=sha(registration):raise ValueError('Test registration changed')
        for reference in review['references']:
            if sha(root/'review-evidence'/reference['sha256'])!=reference['sha256']:raise ValueError('Independent test evidence changed')
        path=max((root/'observations'/session/run).glob('*.json'),key=lambda p:read(p)['decision_time'])
        observation=read(path)
        validate_test_observation(observation,freeze)
        records.append({'session_id':session,'run_id':run,'label':item['label'],**extract(observation)})
        sources.append({'session_id':session,'run_id':run,'path':str(path),'sha256':sha(path),
                        'review_sha256':sha(reviews[0]),'result_sha256':sha(valid[0])})
    frame=pd.DataFrame(records)
    for key in NUMERIC:frame[key]=pd.to_numeric(frame[key])
    return frame,sources


def validate_test_observation(observation,freeze):
    if observation['profile']!=freeze['profile']:raise ValueError('Test profile differs from frozen scope')
    if observation['started_at']<freeze['earliest_test_time']:raise ValueError('Test violates temporal embargo')


def latency(project,models,sources,repeats=20):
    sys.path.insert(0,str(project/'diagnosis-engine'))
    from models import EvidenceRecord
    from roadmap_rules import diagnose_roadmap
    observations=[read(source['path']) for source in sources]
    times={name:[] for name in ['expert','cart_numeric','cart_discrete','fp_classifier']}
    for _ in range(repeats):
        for observation in observations:
            p=observation['profile']
            start=time.perf_counter_ns()
            diagnose_roadmap(p['host_id'],p['target_ip'],[EvidenceRecord(**row) for row in observation['evidence']],
                control=p['control_ip'],http_observer=p['observer'],dns_name=p['dns_name'],dns_observer=p['observer'],
                control_ip=p['dns_control_ip'],http_service=p['http_service'],now=observation['decision_time'])
            times['expert'].append((time.perf_counter_ns()-start)/1e6)
            for name in ['cart_numeric','cart_discrete','fp_classifier']:
                start=time.perf_counter_ns()
                frame=pd.DataFrame([extract(observation)])
                missing=any(frame.iloc[0][key]=='unknown' for key in ['ping_status','tcp80_status','tcp10050_status','control_ping_status'])
                if name=='cart_numeric':models[name].predict(frame[FEATURES])
                elif missing:pass # Shadow serving policy returns ABSTAIN before model.
                else:
                    frame=discrete(frame[FEATURES],CATEGORICAL,NUMERIC)
                    if name=='cart_discrete':models[name].predict(frame)
                    else:rules_predict(models[name],frame)
                times[name].append((time.perf_counter_ns()-start)/1e6)
    return {'scope':'Same raw observations preloaded; includes feature construction/inference, excludes SSH/API/disk/model loading; warm offline microbenchmark',
            'repeats_per_observation':repeats,'methods':{name:{'median_ms':float(np.median(values)),
                'p95_ms':float(np.percentile(values,95)),'calls':len(values)} for name,values in times.items()}}


def evaluate_locked(project,root,freeze_file,output_root):
    freeze=read(freeze_file)
    for name,checksum in freeze['code_sha256'].items():
        if sha(name)!=checksum:raise ValueError('Code changed after test freeze: '+name)
    for name,version in freeze['package_versions'].items():
        if importlib.metadata.version(name)!=version:raise ValueError('Package changed after test freeze: '+name)
    train=load_development(freeze);test,sources=load_test(root,freeze);verify_split(train,test,freeze)
    if {source['sha256'] for source in freeze['train']}&{source['sha256'] for source in sources}:
        raise ValueError('Raw observation duplicated across train/test')
    # No reads from test enter fit_methods. Evaluation occurs only after collection.
    models=fit_methods(train);prediction=predict_methods(models,test)
    summary={name:metrics(test.label.tolist(),prediction[name].tolist()) for name in models}
    out=output_root/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True,exist_ok=False)
    train.to_csv(out/'development_used.csv',index=False,encoding='utf-8-sig')
    test.to_csv(out/'locked_test_used.csv',index=False,encoding='utf-8-sig')
    prediction.to_csv(out/'locked_test_predictions.csv',index=False,encoding='utf-8-sig')
    dump(out/'metrics.json',summary)
    dump(out/'per_class.json',{name:classification_report(test.label.tolist(),prediction[name].tolist(),labels=sorted(LABELS),output_dict=True,zero_division=0) for name in models})
    expert=compare_expert(project,sources,prediction)
    dump(out/'expert_same_observations.json',expert)
    comparison=family_comparison(expert,prediction)
    pd.DataFrame(comparison).to_csv(out/'family_comparison.csv',index=False,encoding='utf-8-sig')
    dump(out/'test_quality_and_identifiability.json',quality_analysis(test,FEATURES,CATEGORICAL,NUMERIC))
    candidates(train,FEATURES,CATEGORICAL,NUMERIC,out,freeze['profile'])
    _,rules=load_database(out/'candidate_rules.sqlite')
    xd=discrete(test[FEATURES],CATEGORICAL,NUMERIC);rows=xd.to_dict('records')
    serialized_cart=[cart_predict(rules['CART'],row)['label'] for row in rows]
    serialized_fp=[fp_predict(rules['FP-Growth'],row)['label'] for row in rows]
    equivalent={'test_rows':len(test),
        'CART':serialized_cart==models['cart_discrete'].predict(xd).tolist() and shadow_gate(test,serialized_cart)==prediction.cart_discrete.tolist(),
        'FP-Growth':serialized_fp==rules_predict(models['fp_classifier'],xd) and shadow_gate(test,serialized_fp)==prediction.fp_classifier.tolist()}
    if not equivalent['CART'] or not equivalent['FP-Growth']:raise AssertionError('SQLite/test model mismatch')
    dump(out/'held_out_serialization_equivalence.json',equivalent)
    timings=latency(project,models,sources);dump(out/'same_input_latency.json',timings)
    write_registry(out/'research_registry.sqlite',out/'candidate_rules.sqlite',freeze,sources,summary,equivalent)
    dump(out/'manifest.json',{'freeze_sha256':sha(freeze_file),'freeze':freeze,'test_sources':sources,
         'candidate_sha256':sha(out/'candidate_rules.sqlite'),'train_rows':len(train),'test_rows':len(test),
         'test_sessions':sorted(set(test.session_id)),'scope':freeze['scope']})
    lines=['# Kết quả test mới đã khóa trước khi thu','',
        f'Train: {len(train)} lượt pilot; test mới: {len(test)} lượt, hai block trên cùng SRV01. Không fit lại trên test.',
        '', '| Phương pháp | Đúng / tổng | Macro-F1 | Coverage |','|---|---:|---:|---:|']
    for name,value in summary.items():lines.append(f"| {name} | {value['correct']}/{value['runs']} | {value['macro_f1']:.3f} | {value['coverage']:.1%} |")
    lines+=['','Đây là test giữ riêng theo thời gian, trong phạm vi cùng host/lab. Hai block không đủ để ước lượng CI theo phiên đáng tin cậy hoặc chứng minh chuyển host. Các phiên pilot đã được nhìn trong thiết kế phương pháp.',
        '', 'Tập cân bằng bảy lớp có tỷ lệ lỗi khác production. Confidence/lift và tỷ lệ lớp tại lá cây không phải xác suất nguyên nhân đúng đã hiệu chỉnh.',
        '', 'Đã đối chiếu cùng raw observations với sáu nhận định chuyên gia; insufficient_evidence giữ riêng. Đọc family_comparison.csv thay vì ép expert thành nhãn healthy.',
        '', 'Các cột accuracy bao gồm ABSTAIN trong mẫu số. Per-class metrics, missingness-only/common/no-quality ablations và toàn bộ dự đoán đều được lưu; không bỏ ca khó theo điểm mô hình.',
        '', 'Serving policy đã khóa: CART discrete/FP abstain khi thiếu bất kỳ core ping/TCP80/TCP10050/control probe; các CART khác là đối chứng nghiên cứu. Đã kiểm tra cả raw model serialization và policy này với kết quả live.',
        '', 'SQLite chỉ chứa luật fit trên train; registry ghi validated theo nghĩa kiểm chứng serialization và lưu đánh giá cho nghiên cứu shadow, không phê duyệt production. Không có luật active.',
        '', 'Latency là warm offline cùng đầu vào, gồm dựng feature và inference; không bao gồm API/SSH hoặc thời gian Zabbix phát hiện. Không suy scalability production từ phép đo này.',
        '', 'M8 (máy thật, multi-fault, topology/suppression) chưa được chứng minh bởi tập lỗi đơn này.','']
    (out/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    dump(output_root/'latest.json',{'output_dir':str(out)})
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['freeze','evaluate'])
    parser.add_argument('--project-root',type=Path,required=True)
    parser.add_argument('--freeze',type=Path,required=True)
    parser.add_argument('--pilot-output',type=Path)
    parser.add_argument('--test-root',type=Path)
    parser.add_argument('--output-root',type=Path)
    args=parser.parse_args()
    if args.action=='freeze':
        if args.pilot_output is None:parser.error('freeze requires pilot-output')
        value=freeze_development(args.project_root,args.pilot_output,args.freeze)
        print(json.dumps({'status':'DEVELOPMENT_FROZEN','train_rows':len(value['train']),'test_runs':len(value['test_schedule'])}))
    else:
        if args.test_root is None or args.output_root is None:parser.error('evaluate requires test-root and output-root')
        output=evaluate_locked(args.project_root,args.test_root,args.freeze,args.output_root)
        print(json.dumps({'status':'LOCKED_TEST_EVALUATED','output_dir':str(output)},ensure_ascii=True))


if __name__=='__main__':main()

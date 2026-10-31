"""Review completed, sealed VM results and release a candidate for the bounded lab demo."""
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sqlite3
import sys

WORK=Path(__file__).resolve().parent
PROJECT=Path(r'C:\Users\Darrys\do-an')
ROOT=PROJECT/'evidence/ml-v2'
sys.path[:0]=[str(WORK/'.ssh-deps'),str(PROJECT/'ml-research')]
from mlv2.core import read,save_new,sha


def csv_rows(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))


def integrity(path):
    db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
    assert db.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
    return db


def main():
    state=read(WORK/'verification/full-ml-status.json')
    if state['phase']!='COMPLETE_INITIAL_VM_ML':
        raise RuntimeError('Full experiment/report/postflight must finish before results are opened for release review')
    result=Path(state['result']).resolve();assert result.is_relative_to(ROOT.resolve())
    manifest=read(result/'manifest.json');freeze=manifest['freeze']
    assert manifest['train_rows']==manifest['test_rows']==42
    assert manifest['freeze_sha256']==sha(ROOT/'locked-test-v1/development-freeze.json')
    for name,value in freeze['code_sha256'].items():assert sha(name)==value
    for name,value in freeze['package_versions'].items():assert importlib.metadata.version(name)==value
    train=freeze['train'];test=manifest['test_sources']
    assert len(train)==len(test)==42
    assert not {x['sha256'] for x in train}&{x['sha256'] for x in test}
    assert not {x['session_id'] for x in train}&{x['session_id'] for x in test}
    for source in [*train,*test]:assert sha(source['path'])==source['sha256']
    predictions=csv_rows(result/'locked_test_predictions.csv')
    assert len(predictions)==42
    assert len({(r['session_id'],r['run_id']) for r in predictions})==42
    counts=Counter(r['label'] for r in predictions)
    assert len(counts)==7 and set(counts.values())=={6}
    summary=read(result/'metrics.json');checked={}
    assert len(summary)==7
    for method,expected in summary.items():
        correct=sum(r[method]==r['label'] for r in predictions)
        covered=sum(r[method]!='ABSTAIN' for r in predictions)
        f1=[]
        for label in counts:
            tp=sum(r['label']==r[method]==label for r in predictions)
            fp=sum(r['label']!=label and r[method]==label for r in predictions)
            fn=sum(r['label']==label and r[method]!=label for r in predictions)
            f1.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0)
        assert expected['runs']==42 and expected['correct']==correct
        assert abs(expected['accuracy_all_runs']-correct/42)<1e-12
        assert abs(expected['coverage']-covered/42)<1e-12
        assert abs(expected['macro_f1']-sum(f1)/7)<1e-12
        labels=expected['confusion_labels'];positions={label:i for i,label in enumerate(labels)}
        matrix=[[0 for _ in labels] for _ in labels]
        for row in predictions:matrix[positions[row['label']]][positions[row[method]]]+=1
        assert expected['confusion_matrix']==matrix
        checked[method]={'correct':correct,'runs':42,'covered':covered,'macro_f1':sum(f1)/7}
    equivalent=read(result/'held_out_serialization_equivalence.json')
    assert equivalent['test_rows']==42 and equivalent['CART'] and equivalent['FP-Growth']
    live=read(result/'live_shadow_equivalence.json')
    assert live['all_equal'] and len(live['cases'])==42 and all(r['equivalent'] for r in live['cases'])
    system_environment=read(result/'lab-environment-freeze.json')
    system_validation=read(result/'lab-environment-validation.json')
    assert system_validation['all_equal']
    assert system_environment['packages']==system_validation['before_packages']==system_validation['after_packages']
    assert sha(ROOT/'locked-test-v1/lab-environment-freeze.json')==system_validation['reference_sha256']
    assert system_environment==read(ROOT/'locked-test-v1/lab-environment-freeze.json')
    assert all(read(source['path'])['started_at']>=system_environment['frozen_at'] for source in test)
    post=read(result/'final-postflight.json')
    assert post['status']=='PILOT_POSTFLIGHT_OK'
    assert post['source_engine_unchanged'] and post['runtime_counts_unchanged']
    assert post['runtime']['counts']=={'incidents':39,'evidence':301,'diagnoses':172,'recoveries':29}
    candidate=result/'candidate_rules.sqlite';assert sha(candidate)==manifest['candidate_sha256']
    db=integrity(candidate)
    try:
        assert db.execute("SELECT COUNT(*) FROM candidates WHERE status!='candidate'").fetchone()[0]==0
        rules=dict(db.execute('SELECT algorithm,COUNT(*) FROM candidates GROUP BY algorithm'))
        metadata={k:json.loads(v) for k,v in db.execute('SELECT key,value_json FROM metadata')}
        assert metadata['training_runs']==42 and metadata['profile']==freeze['profile']
        assert metadata['features']==freeze['features'] and rules.get('CART',0)>0
    finally:db.close()
    db=integrity(result/'research_registry.sqlite')
    try:
        assert db.execute("SELECT COUNT(*) FROM rule_lifecycle WHERE state='active'").fetchone()[0]==0
        assert db.execute("SELECT COUNT(*) FROM rule_lifecycle WHERE state='validated'").fetchone()[0]==2
        assert db.execute('SELECT COUNT(*) FROM models').fetchone()[0]==2
    finally:db.close()
    presentation=Path(read(result/'presentation-latest.json')['output_dir'])
    figures=read(presentation/'FIGURES.json')
    for name,value in figures['input_sha256'].items():assert sha(result/name)==value
    for name,value in figures['output_sha256'].items():assert sha(presentation/name)==value
    assert list((result/'detection-audit').glob('*')), 'Monitoring detection audit is required'
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    qa=ROOT/'verification'/('final-release-review-'+stamp)/'QA.json'
    record={'status':'INITIAL_VM_ML_RELEASE_VERIFIED','at':datetime.now(timezone.utc).isoformat(),
            'candidate_db':str(candidate),'candidate_sha256':sha(candidate),'evaluation':str(result),
            'evaluation_manifest_sha256':sha(result/'manifest.json'),'freeze_sha256':manifest['freeze_sha256'],
            'presentation':str(presentation),'qa_receipt':str(qa),'metrics_recomputed_from_csv':checked,
            'candidate_rule_counts':rules,'sqlite_integrity_and_foreign_keys':True,'active_rules':0,
            'source_hashes':freeze['code_sha256'],'scope':'Initial same-host, known single-fault VM research demo; no production/cross-host/multi-fault claim',
            'release_meaning':'Serialization, sealed evaluation and evidence consistency verified; no minimum accuracy or production approval is implied'}
    save_new(qa,record)
    release=ROOT/'ML_RELEASE.json'
    if release.exists():
        previous=read(release)
        assert previous['candidate_sha256']==record['candidate_sha256'] and previous['status']==record['status']
    else:save_new(release,record)
    print(json.dumps(record,ensure_ascii=True),flush=True)


if __name__=='__main__':main()

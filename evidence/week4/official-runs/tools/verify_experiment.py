"""Cross-check exported files, CSV joins, summary counts, and transfer hashes."""
import csv
import hashlib
import json
from pathlib import Path
import sys

project=Path(sys.argv[1])
root=project/'evidence/week4/official-runs'
summary=json.loads((root/'experiment-summary.json').read_text())
rows=list(csv.DictReader((root/'all-trials.csv').open(encoding='utf-8')))
assert len(rows)==18 and summary['complete_18_valid_faults']
assert len({r['run_id'] for r in rows})==18
event_ids=[]
incident_ids=[]
extra_events=[]
for row in rows:
    folder=root/row['run_id']
    run=json.loads((folder/'run.json').read_text())
    assert run['run_id']==row['run_id']
    assert str(run.get('problem_event_id',''))==row['problem_event_id']
    assert str(run.get('recovery_event_id',''))==row['recovery_event_id']
    if row['problem_event_id']:
        problem=json.loads((folder/'problem-after-recovery.json').read_text())
        recovery=json.loads((folder/'recovery.json').read_text())
        assert problem['eventid']==row['problem_event_id']
        assert problem['r_eventid']==recovery['eventid']==row['recovery_event_id']
        assert problem['objectid']==recovery['objectid'] and problem['value']=='1' and recovery['value']=='0'
        event_ids.append(problem['eventid'])
    if row['incident_id']:
        report=json.loads((folder/'incident.json').read_text())
        assert str(report['incident']['id'])==row['incident_id']
        assert report['incident']['event_id']==row['problem_event_id']
        assert report['lifecycle_status']==row['lifecycle']=='closed'
        assert report['recovery']['recovery_event_id']==row['recovery_event_id']
        target=[d for d in report['diagnoses'] if d['rule_id'].startswith(row['scenario']+'_')]
        assert len(target)==1 and target[0]['status']==row['target_diagnosis_status']
        assert len(report['diagnoses'])==6
        incident_ids.append(row['incident_id'])
    history=list(csv.DictReader((folder/'window-history.csv').open()))
    assert history and len({(r['itemid'],r['clock'],r['ns']) for r in history})==len(history)
    events=json.loads((folder/'all-trigger-events.json').read_text())
    extras=[e['eventid'] for e in events if e['eventid'] not in (row['problem_event_id'],row['recovery_event_id'])]
    if extras: extra_events.append({'run_id':row['run_id'],'event_ids':extras})
for scenario,data in summary['scenarios'].items():
    group=[r for r in rows if r['scenario']==scenario]
    assert len(group)==data['valid_faults']==3
    assert sum(r['detected']=='True' for r in group)==data['detected']
    assert sum(r['target_success_end_to_end']=='True' for r in group)==data['target_success_end_to_end']
assert len(set(event_ids))==len(event_ids) and len(set(incident_ids))==len(incident_ids)
assert json.loads((root/'R5-03/adjudication.json').read_text())['classification']=='aborted_before_fault'
assert not (root/'R5-03/fault.log').exists()
verified={}
for base,name in [(root,'checksums-final.json'),(project/'evidence/week4/baseline-20261016T162549Z','checksums.json')]:
    manifest=json.loads((base/name).read_text())
    # Manifests use relative pathname -> SHA256 maps.
    for relative,digest in manifest.items():
        actual=hashlib.sha256((base/relative).read_bytes()).hexdigest()
        assert actual==digest,relative
    verified[name]=len(manifest)
result={'rows':len(rows),'unique_problem_ids':len(event_ids),'unique_incident_ids':len(incident_ids),
 'checksum_files_verified':verified,'additional_trigger_events_requiring_review':extra_events,
 'result':'PASS'}
assert not extra_events,extra_events
print(json.dumps(result,indent=2))

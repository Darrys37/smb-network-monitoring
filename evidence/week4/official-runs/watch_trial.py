"""Record one official trial using existing diagnosis/recovery/report CLIs.

No fault injection here. Fault ground truth is collected separately on SRV01.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import hashlib

ENGINE = Path('/home/phat/do-an/diagnosis-engine')
sys.path.insert(0, str(ENGINE))
os.chdir(ENGINE)
from zabbix_client import get_open_problems, get_event_by_id
from report import load_report, render_markdown, render_csv

def utc():
    return datetime.now(timezone.utc).isoformat()

def write(path, data):
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n')
    tmp.replace(path)

def command(folder, name, args, timeout=90):
    before, tick = utc(), time.monotonic()
    try:
        result = subprocess.run(args, cwd=ENGINE, capture_output=True, text=True, timeout=timeout)
        text, rc = result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        text, rc = str(exc), 124
    (folder/(name+'.log')).write_text(text)
    return {'start_utc': before, 'end_utc': utc(), 'elapsed_seconds': time.monotonic()-tick,
            'exit_code': rc, 'args': [str(a) for a in args]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--root', type=Path, required=True)
    args = ap.parse_args()
    scenario=args.run_id.split('-')[0]
    if scenario not in ('R1','R2','R3'):
        raise ValueError('This recorder supports only R1-R3')
    folder = args.root/args.run_id
    folder.mkdir(parents=True, exist_ok=False)
    manifest = {'run_id': args.run_id, 'scenario': scenario, 'source_commit':'ca04071',
        'config_commit':'978b4f9', 'docs_commit':'4cabeb0', 'host_id':'10683',
        'target_ip':'192.168.56.20','control_ip':'192.168.56.30','http_scope':'expected',
        'observer':'mon01','watch_start_utc':utc(), 'status':'preflight',
        'measurement_note':'Fault/rollback timestamps come from independent SRV01 log; watch start is not fault time.'}
    state = folder/'run.json'
    write(state, manifest)
    baseline = Path('/home/phat/do-an/evidence/week4/baseline-20261016T162549Z')
    hashes=json.loads((baseline/'source-hashes-start.json').read_text())
    changed=[name for name, value in hashes.items() if hashlib.sha256((ENGINE/name).read_bytes()).hexdigest()!=value]
    if changed:
        raise RuntimeError('Source differs from freeze: '+repr(changed))
    opened = get_open_problems('10683')
    write(folder/'problems-before.json', opened)
    if opened:
        raise RuntimeError('SRV01 has open background problems; classify before starting')
    pre = command(folder,'preflight',['bash','-c',
        'date -u -Is; ping -c 2 -W 2 192.168.56.20 && ping -c 2 -W 2 192.168.56.30 && '
        'curl --fail --max-time 5 -s -o /dev/null -w "HTTP %{http_code}\\n" http://192.168.56.20/'])
    manifest['preflight'] = pre
    if pre['exit_code']:
        raise RuntimeError('Connectivity preflight failed')
    manifest.update(status='waiting_for_fault_and_event', ready_at_utc=utc())
    write(state, manifest)
    print('READY', args.run_id, flush=True)
    # The ready marker is written before the independently controlled fault starts.
    deadline = time.monotonic()+(600 if scenario=='R3' else 300)
    trigger='25260' if scenario=='R3' else '25334'
    event = None
    with (folder/'polls.jsonl').open('x') as log:
        while time.monotonic()<deadline:
            opened = get_open_problems('10683')
            log.write(json.dumps({'at_utc':utc(), 'problems':opened})+'\n'); log.flush()
            matches=[x for x in opened if str(x['objectid'])==trigger]
            if matches:
                if len(matches)!=1:
                    raise RuntimeError('Ambiguous HTTP events')
                event=get_event_by_id(matches[0]['eventid'])
                break
            time.sleep(5)
    if event is None:
        manifest.update(status='no_detection', detection=False, finished_at_utc=utc())
        write(state,manifest)
        return
    write(folder/'problem.json', event)
    manifest.update(status='diagnosing', problem_event_id=event['eventid'],
                    problem_clock=int(event['clock']), detection=True)
    write(state,manifest)
    extra=[]
    if scenario=='R2':
        manifest['status']='waiting_external_http_probe'
        write(state,manifest)
        probe=folder/'local-http.json'
        deadline=time.monotonic()+180
        while not probe.exists() and time.monotonic()<deadline:
            time.sleep(2)
        if probe.exists():
            extra=['--http-observer','srv01','--http-evidence',str(probe)]
        else:
            manifest['external_probe_error']='No local HTTP JSON received before deadline'
    manifest['cli']=command(folder,'diagnosis',[sys.executable,'app.py',
        '--event-id',event['eventid'],'--host-id','10683','--target-ip','192.168.56.20',
        '--ruleset','roadmap','--control-ip','192.168.56.30','--http-service','expected','--save',*extra])
    with sqlite3.connect('file:'+str(ENGINE/'diagnosis.db')+'?mode=ro',uri=True) as db:
        found=db.execute('SELECT id FROM incidents WHERE event_id=?',(event['eventid'],)).fetchone()
    incident_id=found[0] if found else None
    manifest.update(status='waiting_recovery',incident_id=incident_id)
    if incident_id:
        report=load_report(incident_id, ENGINE/'diagnosis.db')
        write(folder/'incident-before-recovery.json',report)
        manifest['diagnoses']=[{'rule_id':d['rule_id'],'status':d['status']} for d in report['diagnoses']]
    write(state,manifest)
    deadline=time.monotonic()+600
    while time.monotonic()<deadline:
        problem=get_event_by_id(event['eventid'])
        if problem.get('r_eventid') not in ('0',0,None,''):
            write(folder/'problem-after-recovery.json',problem)
            recovery=get_event_by_id(problem['r_eventid'])
            write(folder/'recovery.json',recovery)
            manifest.update(recovery_event_id=recovery['eventid'],recovery_clock=int(recovery['clock']))
            break
        time.sleep(5)
    manifest['postflight']=command(folder,'postflight',['bash','-c',
        'date -u -Is; ping -c 2 -W 2 192.168.56.20 && ping -c 2 -W 2 192.168.56.30 && '
        'curl --fail --max-time 5 -s -o /dev/null -w "HTTP %{http_code}\\n" http://192.168.56.20/'])
    if incident_id:
        manifest['recovery_sync']=command(folder,'recovery-sync',[sys.executable,'recovery.py','--event-id',event['eventid']])
        report=load_report(incident_id, ENGINE/'diagnosis.db')
        write(folder/'incident.json',report)
        (folder/'incident.md').write_text(render_markdown(report))
        (folder/'incident.csv').write_text(render_csv(report))
        manifest['lifecycle_status']=report['lifecycle_status']
    manifest.update(status='recorded_pending_ground_truth_review',finished_at_utc=utc())
    write(state,manifest)
    print(json.dumps(manifest,indent=2),flush=True)

if __name__=='__main__':
    main()

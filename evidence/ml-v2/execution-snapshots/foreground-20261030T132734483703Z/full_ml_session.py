"""Foreground authorized session: pilot -> sealed test -> detection/report/backup."""
from datetime import datetime,timezone
import getpass,io,json,os,subprocess,sys
from pathlib import Path

WORK=Path(__file__).resolve().parent
PROJECT=Path(r'C:\Users\Darrys\do-an')
MODULE=PROJECT/'ml-research'
ROOT=PROJECT/'evidence/ml-v2'
sys.path.insert(0,str(WORK/'.ssh-deps'));sys.path.insert(0,str(MODULE))
from mlv2.core import read,save_new,sha
from mlv2.transport import LabTransport
from lab_host_guard import lab_host_guard
import ml_supervisor


def state(phase,**extra):
    result={'phase':phase,'pid':os.getpid(),'at':datetime.now(timezone.utc).isoformat(),**extra}
    path=WORK/'verification/full-ml-status.json';temp=path.with_suffix('.pending.json')
    temp.write_text(json.dumps(result,indent=2),encoding='utf-8');os.replace(temp,path)
    print(json.dumps(result,ensure_ascii=True),flush=True)


def invoke(function,password):
    original_stdin,original_args=sys.stdin,sys.argv
    stream=io.StringIO(password+'\n')
    try:
        sys.stdin=stream;sys.argv=[function.__module__,'0'];function()
    finally:
        sys.stdin=original_stdin;sys.argv=original_args;stream.close()


def offline(*args):
    result=subprocess.run([sys.executable,*map(str,args)],cwd=MODULE,
        env={**os.environ,'PYTHONPATH':str(WORK/'.ssh-deps'),'PYTHONIOENCODING':'utf-8'},
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
    print(result.stdout,flush=True)
    if result.returncode:raise RuntimeError('Postprocessing failed: '+str(args[0]))


def definitions(value):
    rows=json.loads(json.dumps(value['triggers']))
    for row in rows:
        row['items']=sorted(row.get('items',[]),key=lambda item:int(item['itemid']))
        row['dependencies']=sorted(row.get('dependencies',[]),key=lambda item:int(item['triggerid']))
    return sorted(rows,key=lambda item:int(item['triggerid']))


def main():
    password=getpass.getpass('VM SSH password (not logged): ')
    stage='pilot'
    try:
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        snapshot=ROOT/'execution-snapshots'/('foreground-'+stamp)
        snapshot.mkdir(parents=True)
        (snapshot/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
        save_new(snapshot/'manifest.json',{Path(__file__).name:sha(__file__)})
        prior=read(WORK/'verification/ml-supervisor-status.json')
        if prior['phase']!='COMPLETE_PILOT_M4':
            state('running_pilot_foreground')
            with lab_host_guard() as profile:
                save_new(snapshot/'host-execution.json',profile)
                invoke(ml_supervisor.main,password)
        if read(WORK/'verification/ml-supervisor-status.json')['phase']!='COMPLETE_PILOT_M4':
            raise RuntimeError('Pilot not complete')
        stage='holdout';state('running_sealed_holdout_foreground')
        import ml_acceptance
        previous=WORK/'verification/ml-acceptance-status.json'
        if not previous.exists() or read(previous)['phase']!='COMPLETE_INITIAL_VM_ML_ACCEPTANCE':
            invoke(ml_acceptance.main,password)
        completed=read(previous)
        if completed['phase']!='COMPLETE_INITIAL_VM_ML_ACCEPTANCE':raise RuntimeError('Holdout not complete')
        result=Path(completed['output_dir'])
        stage='postprocessing';state('auditing_monitoring_detection',result=str(result))
        from detection_audit_v2 import build_intervals
        intervals=build_intervals(result)
        params={'output':['eventid','clock','name','severity','value','objectid','r_eventid'],
                'hostids':['10683'],'source':0,'object':0,'value':1,
                'time_from':min(row['start'] for row in intervals)-1,'time_till':max(row['end'] for row in intervals)+1,
                'sortfield':['clock','eventid'],'sortorder':'ASC','limit':10001}
        source="import json,time\nfrom zabbix_client import call_api\nparams="+repr(params)+"\n"+"""
events=call_api('event.get',params,9911)
inventory=call_api('trigger.get',{'hostids':['10683'],'output':['triggerid','description','expression','priority','status'],
 'selectItems':['itemid','name','key_','status'],'selectDependencies':['triggerid','description']},9912)
print(json.dumps({'host_id':'10683','time_from':params['time_from'],'time_till':params['time_till'],
 'events':events,'truncated':len(events)>=params['limit'],'triggers':inventory,'queried_at':int(time.time())}))
"""
        transport=LabTransport(password)
        try:export=transport.runner('mon01',source)
        finally:transport.close()
        inventory=ROOT/'verification/trigger-inventory-20261030T110354793414Z.json'
        save_new(result/'monitoring-events-export.json',export)
        if definitions(export)!=definitions(read(inventory)):
            raise ValueError('Trigger definitions changed since pre-test inventory; detection needs review')
        offline('detection_audit_v2.py','--evaluation',result,'--events',result/'monitoring-events-export.json',
                '--inventory',inventory,'--mapping',MODULE/'config/detection_map_srv01_v1.json','--output',result/'detection-audit')
        state('rendering_actual_results',result=str(result))
        offline('render_acceptance_v2.py','--result',result)
        presentation=Path(read(result/'presentation-latest.json')['output_dir'])
        save_new(result/'final-postflight.json',ml_supervisor.postflight(password))
        from resume_ml_pilot import backup
        checkpoint=backup('full-ml-evidence-complete-')
        state('COMPLETE_INITIAL_VM_ML',result=str(result),presentation=str(presentation),backup=str(checkpoint),
              remaining_scope=['physical-host transfer','multi-fault datasets','topology/correlation/suppression experiments'])
    except BaseException as exc:
        if stage=='pilot':ml_supervisor.status('STOPPED_REQUIRES_REVIEW',error_type=type(exc).__name__,error_message=str(exc))
        elif stage=='holdout':
            import ml_acceptance
            ml_acceptance.status('STOPPED_REQUIRES_REVIEW',error_type=type(exc).__name__,error_message=str(exc))
        state('STOPPED_REQUIRES_REVIEW',stage=stage,error_type=type(exc).__name__,error_message=str(exc))
        raise
    finally:password=None


if __name__=='__main__':main()

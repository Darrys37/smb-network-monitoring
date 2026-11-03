"""Windows/operator CLI for the three-VM system; no ML prediction or training."""
import argparse
from contextlib import nullcontext
from datetime import datetime,timezone
import getpass
import json
from pathlib import Path
import shlex
import sys
import time

PROJECT=Path(__file__).resolve().parents[1]
REMOTE='/home/phat/do-an/system-monitor'


def snapshot(transport):
    source="import sys,json,subprocess;from pathlib import Path;sys.path.insert(0,"+repr(REMOTE)+");from report import report;r=report(Path("+repr(REMOTE)+"));r['worker_service']=subprocess.run(['systemctl','is-active','do-an-monitor-v3.service'],capture_output=True,text=True).stdout.strip();print(json.dumps(r))"
    return transport.runner('mon01',source)


def fault(transport,kind,action):
    host={'nginx':'srv01','gateway':'cli01'}[kind]
    source="import sys,json;sys.path.insert(0,"+repr(REMOTE)+");from fault_control import control;print(json.dumps(control("+repr(action)+","+repr(kind)+",120)))"
    return json.loads(transport.sudo(host,'python3 -c '+shlex.quote(source)))


def storm(transport,value):
    source="import sys,json;sys.path.insert(0,"+repr(REMOTE)+");from storm_control import set_value;print(json.dumps(set_value("+str(value)+")))"
    return transport.runner('mon01',source)


def show(result):
    corr=result['correlation']
    print(json.dumps({'worker':result['worker_service'],'active_events':corr['active_problem_events'],'groups':corr['emitted_groups'],
                      'suppressed':corr['suppressed_events'],'pending_jobs':result['counts']['pending_jobs'],
                      'roots':[{'node':g['root_node'],'kind':g['cause_group'],'alerts':len(g['members'])} for g in corr['groups']]},ensure_ascii=True),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['status','demo','recover'])
    parser.add_argument('--fault',choices=['nginx','gateway','multi','storm'],default='nginx')
    args=parser.parse_args()
    sys.path.insert(0,str(PROJECT/'tools'))
    from lab import settings,vm_states
    config=settings(PROJECT)
    for path in config.get('dependency_paths',[]):sys.path.insert(0,path)
    sys.path.insert(0,str(PROJECT/'ml-research'))
    # Reuse only the host-key-checked SSH transport. No ML model is loaded.
    from mlv2.transport import LabTransport
    from lab_session import lab_session
    coordination=config.get('coordination_root')
    if args.command!='status' and not coordination:raise ValueError('Configure tools/lab.local.json coordination_root first')
    if any(state!='running' for state in vm_states().values()):raise ValueError('Start all three lab VMs first')
    guard=lab_session(coordination) if args.command!='status' else nullcontext()
    with guard:
        transport=LabTransport(getpass.getpass('VM SSH password (never saved): '))
        try:
            if args.command=='status':show(snapshot(transport));return
            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            destination=PROJECT/'evidence/system-v3/demos'/stamp
            destination.mkdir(parents=True)
            def save(name,data):
                (destination/(name+'.json')).write_text(json.dumps(data,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
            if args.command=='recover':
                errors=[]
                for kind in ['nginx','gateway']:
                    try:save('recover-'+kind,fault(transport,kind,'recover'))
                    except Exception as error:errors.append(type(error).__name__)
                try:save('recover-storm',storm(transport,0))
                except Exception as error:errors.append(type(error).__name__)
                show(snapshot(transport))
                if errors:raise RuntimeError('Some recovery actions failed; independent timers remain in effect')
                return
            before=snapshot(transport);save('before',before);show(before)
            if before['worker_service']!='active' or before['correlation']['active_problem_events'] or before['counts']['pending_jobs']:
                raise ValueError('Worker/baseline not ready; no fault applied')
            if any(state['status']!='up' or not 0<=before['report_clock']-state['observed_at']<=30 for state in before['node_states'].values()):
                raise ValueError('Fresh healthy node states required; no fault applied')
            if any(value['status']!='ok' for row in before['latest_diagnostics'] for value in row['observation']['sources'].values()):
                raise ValueError('All baseline evidence sources must be available; no fault applied')
            srv=next(row for row in before['latest_diagnostics'] if row['node']=='srv01')
            features=srv['assessment']['feature_vector']['features']
            if features['http_status_code']!=200 or features['parent_status']!='up' or before['report_clock']-srv['observation']['decision_time']>60:
                raise ValueError('Fresh routed HTTP and gateway baseline required; no fault applied')
            selected=['nginx'] if args.fault=='nginx' else ['gateway'] if args.fault in {'gateway','storm'} else ['gateway','nginx']
            armed=[];storm_started=False;detected=False
            try:
                for kind in selected:
                    # Add before arm: even an interrupted SSH reply gets cleanup.
                    armed.append(kind);save('arm-'+kind,fault(transport,kind,'arm'))
                if args.fault=='storm':
                    command=['systemd-run','--unit=do-an-v3-rollback-storm','--on-active=100s','--uid=phat','--gid=phat',
                             '--property=WorkingDirectory=/home/phat/do-an/diagnosis-engine',
                             '/home/phat/do-an/diagnosis-engine/.venv/bin/python',REMOTE+'/storm_control.py','0']
                    transport.sudo('mon01',shlex.join(command))
                    storm_started=True;save('inject-storm',storm(transport,1))
                deadline=time.monotonic()+70
                while time.monotonic()<deadline:
                    result=snapshot(transport);show(result)
                    corr=result['correlation'];roots={(g['root_node'],g['cause_group']) for g in corr['groups']}
                    accepted=(('srv01','http_service') in roots if args.fault=='nginx' else ('cli01','dependency') in roots and corr['suppressed_events']>=1)
                    if args.fault=='multi':accepted=accepted and ('srv01','http_service') in roots
                    if args.fault=='storm':accepted=accepted and sum(e['state']=='problem' and e.get('name','').startswith('V3 SYNTHETIC') for e in result['events'])>=20 and corr['suppressed_events']>=20
                    if accepted and result['counts']['pending_jobs']==0:
                        save('detected',result);detected=True;break
                    time.sleep(3)
                if not detected:raise TimeoutError('Expected observed system behavior was not verified before timeout')
            finally:
                errors=[]
                if storm_started:
                    try:save('clear-storm',storm(transport,0))
                    except Exception as error:errors.append(type(error).__name__)
                for kind in reversed(armed):
                    try:save('recover-'+kind,fault(transport,kind,'recover'))
                    except Exception as error:errors.append(type(error).__name__)
                if errors:print(json.dumps({'recovery_errors':errors,'independent_rollback_timers':'retained'}),flush=True)
                deadline=time.monotonic()+65
                while time.monotonic()<deadline:
                    recovered=snapshot(transport)
                    if recovered['correlation']['active_problem_events']==0 and recovered['counts']['pending_jobs']==0:
                        save('recovered',recovered);show(recovered);break
                    time.sleep(3)
                else:raise RuntimeError('Recovery not fully verified; inspect saved evidence and use recover command')
            print(json.dumps({'status':'SYSTEM_DEMO_VERIFIED','fault':args.fault,'evidence':str(destination)},ensure_ascii=True))
        finally:transport.close()


if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:raise SystemExit(130)
    except Exception as error:
        print(json.dumps({'status':'ERROR','error_type':type(error).__name__}),file=sys.stderr);raise SystemExit(2)

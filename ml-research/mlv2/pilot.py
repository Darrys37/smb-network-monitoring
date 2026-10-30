"""Resumable multi-session pilot; raw evidence survives invalid trials."""
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import shlex
import time
import uuid

from paramiko import SSHException, AuthenticationException, BadHostKeyException

from .collector import collect
from .core import LABELS, read, register, review, save_new
from .faults import plan, scripts

MON_STATUS = '''import json
from zabbix_client import get_open_problems
from roadmap_evidence import collect_roadmap_metrics
from dataclasses import asdict
print(json.dumps({'problems':get_open_problems('10683'),'metrics':[asdict(x) for x in collect_roadmap_metrics('10683')]}))
'''
SERVICE_STATUS = '''import json,subprocess,time
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=5)
 return {'code':p.returncode,'stdout':p.stdout.strip()}
print(json.dumps({'time':int(time.time()),'nginx':run(['systemctl','is-active','nginx']),
 'agent':run(['systemctl','is-active','zabbix-agent2']),
 'http':run(['curl','--max-time','3','-s','-o','/dev/null','-w','%{http_code}','http://192.168.56.20/']),
 'clock':run(['timedatectl','show','-p','NTPSynchronized','--value']),
 'stress':run(['pgrep','-x','stress-ng']),
 'dns':run(['dig','+time=2','+tries=1','+short','example.com','A']),
 'control':run(['ping','-c','1','-W','2','1.1.1.1'])}))
'''


def schedule(seed=37, sessions=2, repeats=3):
    rng = random.Random(seed)
    result = []
    for session in range(1, sessions+1):
        for repeat in range(1, repeats+1):
            labels = sorted(LABELS)
            rng.shuffle(labels)
            for index, label in enumerate(labels):
                result.append({'session_id':f'pilot-v2-s{session:02}',
                               'run_id':f'r{repeat:02}-{index+1:02}-{label}', 'label':label})
    return result


def baseline_ok(service, monitor):
    import ipaddress
    addresses=[]
    for line in service['dns']['stdout'].splitlines():
        try: addresses.append(ipaddress.IPv4Address(line.strip()))
        except ValueError: pass
    services = (service['nginx']['stdout']=='active' and service['agent']['stdout']=='active'
                and service['http']['stdout']=='200' and service['clock']['stdout']=='yes'
                and service['stress']['code']==1 and service['dns']['code']==0 and bool(addresses)
                and service['control']['code']==0)
    history = [m for m in monitor['metrics'] if m['check_type']=='cpu_history']
    if not services or not history or history[0]['result'].get('status')!='success':
        return False
    samples = history[0]['result'].get('samples',[])
    if len(samples)<3 or any(float(s['value'])>=80 for s in samples):
        return False
    # OS-description informational notices are recorded, not silently resolved.
    return not any(p['severity'] not in ['0','1'] for p in monitor['problems'])


class Pilot:
    def __init__(self, transport, root, engine, profile, log=print):
        self.transport,self.root,self.engine,self.profile,self.log = transport,Path(root),Path(engine),profile,log

    def wait_baseline(self, limit=1200):
        deadline=time.monotonic()+limit
        while True:
            try:
                service=self.transport.runner('srv01', SERVICE_STATUS)
                monitor=self.transport.runner('mon01', MON_STATUS)
            except (AuthenticationException, BadHostKeyException):
                raise
            except (SSHException, OSError, TimeoutError) as exc:
                # A control-channel timeout does not certify a healthy baseline.
                self.transport.drop('srv01');self.transport.drop('mon01')
                self.log(json.dumps({'state':'baseline_probe_error','error_type':type(exc).__name__}),flush=True)
            else:
                if baseline_ok(service,monitor): return {'service':service,'monitor':monitor}
            if time.monotonic()>=deadline: raise RuntimeError('Baseline did not stabilize')
            self.log(json.dumps({'state':'waiting_baseline','at':int(time.time())}),flush=True)
            time.sleep(15)

    def snapshot(self, item):
        value=collect(self.profile,self.engine,item['session_id'],item['run_id'],self.transport.runner)
        path=self.root/'observations'/item['session_id']/item['run_id']/(value['window_id']+'.json')
        save_new(path,value)
        return value

    def cancel_timer(self,unit):
        code,state=self.transport.command('srv01',f'systemctl show --property=LoadState --value {unit}-rollback.timer')
        if state.strip()=='not-found':return 'already_collected'
        if code:raise RuntimeError('Cannot inspect rollback timer')
        self.transport.sudo('srv01',f'systemctl stop {unit}-rollback.timer')
        return 'stopped'

    def run(self,item):
        folder=self.root/'trial-logs'/item['session_id']/item['run_id']
        if (folder/'RESULT.json').exists(): return read(folder/'RESULT.json')
        if (self.root/'registry'/item['session_id']/item['run_id']/'registration.json').exists():
            raise RuntimeError('Incomplete registered run requires explicit review before resume')
        before=self.wait_baseline()
        folder.mkdir(parents=True,exist_ok=False)
        save_new(folder/'preflight.json',before)
        register(self.root,item['session_id'],item['run_id'],[item['label']])
        token=uuid.uuid4().hex[:12]
        spec=plan(item['label'],token)
        remote='/home/phat/ml-experiments/'+token
        fault,rollback=scripts(spec,remote)
        unit='mlv2-'+token
        save_new(folder/'control.json',{'remote_directory':remote,'unit':unit,
                 'hold_seconds':spec.hold_seconds,'fault_script':fault,'rollback_script':rollback})
        armed=False;valid=False;error=None
        timeline={'timer_earliest_deadline_monotonic':None,'windows':[],'manual_rollback_requested_monotonic':None}
        self.log(json.dumps({'state':'run_started',**item,'hold_seconds':spec.hold_seconds}),flush=True)
        try:
            # Remote artifacts are exclusive, user-owned; scripts run with least needed sudo.
            source=f"from pathlib import Path\np=Path({remote!r});p.mkdir(parents=True,exist_ok=False)\n"+''.join(
                f"(p/{name!r}).write_text({value!r})\n" for name,value in [('fault.sh',fault),('rollback.sh',rollback),('fault.log',''),('rollback.log','')])
            self.transport.runner('srv01',source+"print('null')\n")
            if item['label']!='healthy':
                timeline['timer_earliest_deadline_monotonic']=time.monotonic()+spec.hold_seconds+90
                self.transport.sudo('srv01',f'systemd-run --unit={unit}-rollback --on-active={spec.hold_seconds+90}s --timer-property=AccuracySec=1s /bin/bash {remote}/rollback.sh')
                armed=True
            self.transport.sudo('srv01',f'systemd-run --unit={unit}-fault /bin/bash {remote}/fault.sh')
            time.sleep(5 if item['label']=='interface_down' else 2)
            self.snapshot(item)
            timeline['windows'].append({'completed_monotonic':time.monotonic()})
            started=time.monotonic()
            while time.monotonic()-started<spec.hold_seconds:
                time.sleep(max(0,min(10,spec.hold_seconds-(time.monotonic()-started))))
            self.snapshot(item)
            timeline['windows'].append({'completed_monotonic':time.monotonic()})
        except Exception as exc:
            error=type(exc).__name__
        finally:
            # A down link can interrupt SSH; its independent timer brings it back.
            if armed:
                try:
                    timeline['manual_rollback_requested_monotonic']=time.monotonic()
                    self.transport.sudo('srv01',f'/bin/bash {remote}/rollback.sh')
                    self.cancel_timer(unit)
                except Exception:
                    self.transport.drop('srv01')
                    for _ in range(24):
                        time.sleep(5)
                        try:
                            self.transport.runner('srv01',"print('null')\n")
                            break
                        except Exception:self.transport.drop('srv01')
                    else:raise RuntimeError('Cannot verify failsafe rollback')
            after=self.wait_baseline()
            save_new(folder/'postflight.json',after)
            raw=self.transport.runner('srv01',f"import json\nfrom pathlib import Path\np=Path({remote!r})\nprint(json.dumps({{n:(p/n).read_text() for n in ['fault.log','rollback.log']}}))\n")
            save_new(folder/'independent-logs.json',raw)
            save_new(folder/'coordinator-timeline.json',timeline)
            # Timer cannot fire later during another run. Remove only this run's timer.
            if armed:self.cancel_timer(unit)
            valid=error is None and 'FAULT_VERIFIED ' in raw['fault.log']
            if armed: valid=valid and 'ROLLBACK_AFTER ' in raw['rollback.log']
            verified=[int(line.split()[1]) for line in raw['fault.log'].splitlines() if line.startswith('FAULT_VERIFIED ')]
            restored=[int(line.split()[1]) for line in raw['rollback.log'].splitlines() if line.startswith('ROLLBACK_BEFORE ')]
            windows=list((self.root/'observations'/item['session_id']/item['run_id']).glob('*.json'))
            if verified:
                valid=valid and bool(windows) and all(read(p)['started_at']>=verified[0] for p in windows)
            if restored:
                # Across-host integer clocks can differ by a second. Use coordinator
                # causality for the end boundary when its timer could not yet fire.
                completion=max((w['completed_monotonic'] for w in timeline['windows']),default=float('inf'))
                requested=timeline['manual_rollback_requested_monotonic']
                deadline=timeline['timer_earliest_deadline_monotonic']
                causal_end=(requested is not None and deadline is not None and completion<=requested and completion<deadline-1)
                valid=valid and (causal_end or all(read(p)['decision_time']<=min(restored) for p in windows))
            result=review(self.root,item['session_id'],item['run_id'],'valid' if valid else 'uncertain',
                          [item['label']],[folder/'preflight.json',folder/'postflight.json',folder/'independent-logs.json'])
            receipt={**item,'valid':valid,'error_type':error,'review':result,'remote_log_directory':remote}
            save_new(folder/'RESULT.json',receipt)
            self.log(json.dumps({'state':'run_finished','run_id':item['run_id'],'valid':valid,'error_type':error}),flush=True)
        return receipt

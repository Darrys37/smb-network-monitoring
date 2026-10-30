"""One guarded Nginx data trial, with independent service logs and rollback."""
from datetime import datetime,timezone
import getpass,json,sys,time,uuid
from pathlib import Path
WORK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(WORK/'ml-research'))
from mlv2.core import read,register,review,save_new
from mlv2.collector import collect
from mlv2.transport import SSHTransport

DATA=WORK/'ml-research/outputs'
ENGINE=Path(r'C:\Users\Darrys\do-an\diagnosis-engine')
session='pilot-session-01'
run='nginx-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
profile=read(WORK/'ml-research/config/srv01.json')
transport=SSHTransport(getpass.getpass('VM SSH password (not logged): '))
directory=DATA/'trial-logs'/session/run
directory.mkdir(parents=True,exist_ok=False)
log=[];armed=False;restored=False

def state(stage):
 code,output=transport.command('srv01',"date -u +%s; systemctl is-active nginx; systemctl is-active zabbix-agent2; curl --max-time 3 -s -o /dev/null -w '%{http_code}' http://192.168.56.20/; true")
 row={'stage':stage,'observed_at':int(time.time()),'output':output.strip(),'exit':code}
 log.append(row)
 return output.strip().splitlines()

try:
 before=state('preflight')
 if before[1:3]!=['active','active'] or before[-1]!='200':
  raise RuntimeError('Baseline services not normal')
 register(DATA,session,run,['nginx_stopped'])
 unit='ml-nginx-'+uuid.uuid4().hex[:12]
 transport.sudo('srv01','systemd-run --unit='+unit+' --on-active=90s /usr/bin/systemctl start nginx')
 armed=True
 transport.sudo('srv01','systemctl stop nginx')
 fault=state('fault_verified')
 if fault[1]!='inactive': raise RuntimeError('Nginx stop not verified')
 observation=collect(profile,ENGINE,session,run,transport.runner)
 path=DATA/'observations'/session/run/(observation['window_id']+'.json')
 save_new(path,observation)
 # Keep the fault across a web-scenario polling interval, without training on the event name.
 for _ in range(3):
  time.sleep(10)
  check=state('fault_hold')
  if check[1]!='inactive': raise RuntimeError('Fault ended unexpectedly')
 observation=collect(profile,ENGINE,session,run,transport.runner)
 save_new(DATA/'observations'/session/run/(observation['window_id']+'.json'),observation)
 problems=transport.runner('mon01',"import json\nfrom zabbix_client import get_open_problems\nprint(json.dumps(get_open_problems('10683')))\n")
 save_new(directory/'problems-during-fault.json',problems)
finally:
 try:
  if armed:
   transport.sudo('srv01','systemctl start nginx')
   after=state('rollback_verified')
   restored=after[1:3]==['active','active'] and after[-1]=='200'
  save_new(directory/'independent-service-log.json',log)
 finally: transport.close()

if not restored: raise RuntimeError('Rollback not verified; timer remains as failsafe')
refs=[directory/'independent-service-log.json']
result=review(DATA,session,run,'valid',['nginx_stopped'],refs)
save_new(directory/'RESULT.json',{'run_id':run,'session_id':session,'rollback_verified':True,
                                'review':result,'note':'First pilot trial only, not a complete dataset'})
print(json.dumps({'status':'FIRST_FAULT_TRIAL_OK','run_id':run,'rollback_verified':restored,
                  'log_dir':str(directory)},ensure_ascii=True))

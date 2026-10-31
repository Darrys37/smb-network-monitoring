"""One-off lab rescue for the observed apt/Zabbix/MySQL stop/start ordering wait."""
from datetime import datetime,timezone
import getpass,json,shlex,sys
from pathlib import Path

WORK=Path(__file__).resolve().parent
PROJECT=Path(r'C:\Users\Darrys\do-an')
sys.path[:0]=[str(WORK/'.ssh-deps'),str(PROJECT/'ml-research')]
from mlv2.transport import LabTransport
from mlv2.core import save_new,sha

BACKUP=r'''import gzip,hashlib,json,os,shutil,subprocess,tarfile
from datetime import datetime,timezone
from pathlib import Path
def call(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=20)
 if p.returncode:raise RuntimeError('Backup precondition command failed')
 return p.stdout.strip()
state=call(['systemctl','show','mysql.service','-p','ActiveState','-p','MainPID','-p','StateChangeTimestamp'])
assert 'ActiveState=inactive' in state and 'MainPID=0' in state
assert subprocess.run(['pgrep','-x','mysqld'],capture_output=True).returncode==1
size=int(call(['du','-sb','/var/lib/mysql']).split()[0])
assert shutil.disk_usage('/home/phat').free>size*2+512*1024**2
out=Path('/home/phat/ml-checkpoints')/('mysql-ordering-rescue-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
out.mkdir(mode=0o700);os.chmod(out,0o700)
archive=out/'mysql-cold-and-config.tar.gz'
with tarfile.open(archive,'x:gz',compresslevel=3) as stream:
 for name in ['/var/lib/mysql','/etc/mysql','/etc/zabbix/zabbix_server.conf','/etc/zabbix/web/zabbix.conf.php']:
  if Path(name).exists():stream.add(name,arcname=name.lstrip('/'))
os.chmod(archive,0o600)
assert call(['systemctl','show','mysql.service','-p','ActiveState','-p','MainPID','-p','StateChangeTimestamp'])==state
with gzip.open(archive,'rb') as stream:
 for block in iter(lambda:stream.read(1024*1024),b''):pass
digest=hashlib.sha256()
with archive.open('rb') as stream:
 for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
result={'status':'MYSQL_COLD_BACKUP_VERIFIED','directory':str(out),'archive':str(archive),
 'sha256':digest.hexdigest(),'mysql_data_bytes':size,'mysql_state_before_and_after':state,
 'scope':'Private VM-only cold MySQL/config backup; not exported or printed contents'}
(out/'VERIFICATION.json').write_text(json.dumps(result,indent=2));os.chmod(out/'VERIFICATION.json',0o600)
print(json.dumps(result))
'''

RECOVER=r'''import json,subprocess,time
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=20)
 return {'code':p.returncode,'stdout':p.stdout.strip()}
before=run(['systemctl','list-jobs','--no-legend','--no-pager'])
assert 'mysql.service' in before['stdout'] and 'waiting' in before['stdout']
assert 'zabbix-server.service' in before['stdout']
dependency=run(['systemctl','show','mysql.service','-p','Before'])
assert 'zabbix-server.service' in dependency['stdout']
assert run(['systemctl','is-active','mysql.service'])['stdout']=='inactive'
action=run(['systemctl','start','--job-mode=ignore-dependencies','--no-block','mysql.service'])
assert action['code']==0
deadline=time.monotonic()+100
while time.monotonic()<deadline:
 mysql=run(['systemctl','is-active','mysql.service'])
 zabbix=run(['systemctl','is-active','zabbix-server.service'])
 if mysql['stdout']=='active' and zabbix['stdout']=='active':break
 time.sleep(2)
else:raise TimeoutError('Rescue request sent; services require further inspection')
result={'status':'MYSQL_AND_ZABBIX_SERVICES_RECOVERED','before_jobs':before,'ordering':dependency,
 'action':'One-off systemctl start mysql with ignore-dependencies; no unit/policy/package configuration changed',
 'after_jobs':run(['systemctl','list-jobs','--no-legend','--no-pager']),
 'mysql':mysql,'zabbix':zabbix,'mysql_query':run(['mysql','--batch','--skip-column-names','-e','SELECT 1'])}
assert result['mysql_query']['code']==0
print(json.dumps(result))
'''

password=getpass.getpass('VM SSH password (not logged): ')
transport=LabTransport(password);transport.control.command_timeout=240
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
out=PROJECT/'evidence/ml-v2/verification'/('mysql-ordering-recovery-'+stamp)
try:
    cold=json.loads(transport.sudo('mon01','python3 -c '+shlex.quote(BACKUP)))
    save_new(out/'cold-backup.json',cold)
    print(json.dumps(cold),flush=True)
    result=json.loads(transport.sudo('mon01','python3 -c '+shlex.quote(RECOVER)))
    save_new(out/'recovery.json',result)
    (out/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    save_new(out/'source-sha256.json',{Path(__file__).name:sha(__file__)})
    print(json.dumps(result),flush=True)
finally:transport.close();password=None

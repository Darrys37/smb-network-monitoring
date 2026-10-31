"""Authenticate without logging credentials; back up VM runtime before ML work."""
import getpass
import json
from pathlib import Path
import shlex
import sys
from datetime import datetime, timezone

WORK = Path(__file__).resolve().parent
sys.path.insert(0, str(WORK / '.ssh-deps'))
import paramiko

REMOTE = r'''
import hashlib,json,os,shutil,socket,sqlite3,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
host=socket.gethostname().split('.')[0].lower()
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out=Path.home()/'ml-checkpoints'/('pre-integration-'+stamp)
out.mkdir(parents=True,exist_ok=False);out.chmod(0o700)
result={'hostname':host,'backup_dir':str(out),'created_at_utc':stamp}
def command(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=15)
 return {'code':p.returncode,'stdout':p.stdout.strip()}
result['clock_sync']=command(['timedatectl','show','-p','NTPSynchronized','--value'])
services=['zabbix-agent2']+(['zabbix-server','mysql'] if host=='mon01' else ['nginx'] if host=='srv01' else [])
result['services']={name:command(['systemctl','is-active',name]) for name in services}
if host=='mon01':
 root=Path('/home/phat/do-an/diagnosis-engine')
 dest=out/'engine-source';dest.mkdir()
 for p in list(root.glob('*.py'))+list(root.glob('*.txt'))+list(root.glob('*.ini'))+list(root.glob('*.toml')):
  shutil.copy2(p,dest/p.name)
 if (root/'tests').exists(): shutil.copytree(root/'tests',dest/'tests',ignore=shutil.ignore_patterns('__pycache__'))
 if (root/'.env').exists():
  shutil.copyfile(root/'.env',out/'runtime.env');(out/'runtime.env').chmod(0o600)
 src=sqlite3.connect((root/'diagnosis.db').as_uri()+'?mode=ro',uri=True)
 target=sqlite3.connect(out/'diagnosis-consistent.db')
 try:
  src.backup(target)
  result['sqlite_integrity']=target.execute('PRAGMA integrity_check').fetchall()
  result['sqlite_foreign_keys']=target.execute('PRAGMA foreign_key_check').fetchall()
  result['sqlite_counts']={t:target.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['incidents','evidence','diagnoses','recoveries']}
 finally: target.close();src.close()
 (out/'diagnosis-consistent.db').chmod(0o600)
 os.chdir(root);sys.path.insert(0,str(root))
 from zabbix_client import get_open_problems
 result['open_problems']={h:len(get_open_problems(h)) for h in ['10084','10683','10684']}
 result['engine_source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.py')}
else:
 for p in [Path('/home/phat/http_probe.py'),Path('/home/phat/week4-dns-probe')]:
  if p.is_file(): shutil.copy2(p,out/p.name)
  elif p.is_dir(): shutil.copytree(p,out/p.name,ignore=shutil.ignore_patterns('__pycache__','.venv'))
result['backup_files']=sum(p.is_file() for p in out.rglob('*'))
(out/'VERIFICATION.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
'''


def main():
    password = getpass.getpass('VM SSH password (not logged): ')
    results = []
    for ip in ['192.168.56.10', '192.168.56.20', '192.168.56.30']:
        client = paramiko.SSHClient()
        client.load_host_keys(str(Path.home() / '.ssh/known_hosts'))
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        try:
            client.connect(ip, username='phat', password=password, look_for_keys=False,
                           allow_agent=False, timeout=8, auth_timeout=8)
            command = '/home/phat/do-an/diagnosis-engine/.venv/bin/python' if ip.endswith('.10') else 'python3'
            _, stdout, stderr = client.exec_command(command+' -c '+shlex.quote(REMOTE), timeout=60)
            data = stdout.read().decode()
            error = stderr.read().decode()
            if stdout.channel.recv_exit_status():
                # Never forward arbitrary remote stderr (may include config).
                raise RuntimeError('Remote preflight failed on '+ip+'; error class only: '+error.splitlines()[-1].split(':')[0])
            results.append(json.loads(data))
        finally:
            client.close()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = WORK/'verification'/('ml-vm-preflight-'+stamp+'.json')
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps({'status':'VM_PREFLIGHT_OK','receipt':str(output),'hosts':results},ensure_ascii=True))


if __name__ == '__main__':
    main()

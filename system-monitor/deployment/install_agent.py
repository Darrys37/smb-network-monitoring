import json
import os
from pathlib import Path
import shutil
import socket
import subprocess

host=socket.gethostname().split('.')[0].lower()
if host not in {'cli01','srv01'}:raise ValueError('Unexpected VM')
source=Path('/home/phat/do-an/system-monitor/monitoring/probes.py')
root=Path('/usr/local/lib/do-an-system-v3');root.mkdir(exist_ok=True,parents=True)
shutil.copyfile(source,root/'probes.py')
helper=root/'agent_probe.py'
helper.write_text('''import json,sys,subprocess
from probes import dns,routing
if sys.argv[1]=='router':
 print(int(routing('enp0s9','172.30.20.20','cli01')['ready']))
elif sys.argv[1]=='dns':
 print(json.dumps(dns('example.com','cli01')['result']))
elif sys.argv[1]=='nginx':
 print(int(subprocess.run(['systemctl','is-active','--quiet','nginx']).returncode==0))
else:raise ValueError('Unsupported check')
''')
for path in (root/'probes.py',helper):os.chown(path,0,0);path.chmod(0o644)
config=Path('/etc/zabbix/zabbix_agent2.d/do-an-system-v3.conf')
config.write_text(('UserParameter=diag.router.ready,/usr/bin/python3 '+str(helper)+' router\nUserParameter=diag.dns.json,/usr/bin/python3 '+str(helper)+' dns\n') if host=='cli01' else 'UserParameter=diag.service.nginx,/usr/bin/python3 '+str(helper)+' nginx\n')
config.chmod(0o644);os.chown(config,0,0)
subprocess.run(['systemctl','restart','zabbix-agent2'],capture_output=True,check=True,timeout=20)
value=subprocess.run(['systemctl','is-active','zabbix-agent2'],capture_output=True,text=True,timeout=5)
checks={}
for name in (['router','dns'] if host=='cli01' else ['nginx']):
 p=subprocess.run(['runuser','-u','zabbix','--','python3',str(helper),name],capture_output=True,text=True,timeout=10)
 checks[name]={'code':p.returncode,'value':p.stdout.strip()}
print(json.dumps({'host':host,'agent_service':value.stdout.strip(),'checks':checks}))

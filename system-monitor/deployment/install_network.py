import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
host = socket.gethostname().split('.')[0].lower()
if host not in {'mon01','srv01','cli01'}:raise ValueError('Unexpected VM')
source = Path('/home/phat/do-an/system-monitor/lab_network.py')
destination = Path('/usr/local/lib/do-an-system-v3')
destination.mkdir(parents=True, exist_ok=True)
destination.chmod(0o755)
target = destination/'lab_network.py'
shutil.copyfile(source,target);target.chmod(0o755);os.chown(target,0,0)
unit = Path('/etc/systemd/system/do-an-network-v3.service')
unit.write_text('''[Unit]
Description=Owned routed overlay for the three-VM diagnosis lab
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/python3 /usr/local/lib/do-an-system-v3/lab_network.py apply
ExecStop=/usr/bin/python3 /usr/local/lib/do-an-system-v3/lab_network.py remove

[Install]
WantedBy=multi-user.target
''')
unit.chmod(0o644);os.chown(unit,0,0)
subprocess.run(['systemctl','daemon-reload'],check=True,timeout=15)
subprocess.run(['systemctl','enable','do-an-network-v3.service'],check=True,capture_output=True,timeout=15)
run = subprocess.run(['systemctl','restart','do-an-network-v3.service'],capture_output=True,text=True,timeout=30)
status = subprocess.run(['systemctl','is-active','do-an-network-v3.service'],capture_output=True,text=True,timeout=5)
detail = subprocess.run(['python3',str(target),'status'],capture_output=True,text=True,timeout=10)
print(json.dumps({'host':host,'restart_exit':run.returncode,'service':status.stdout.strip(),'network':json.loads(detail.stdout) if detail.returncode==0 else None,'source_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))

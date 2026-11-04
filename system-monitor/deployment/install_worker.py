import json
import os
from pathlib import Path
import subprocess
root=Path('/home/phat/do-an/system-monitor')
runtime=root/'runtime';runtime.mkdir(exist_ok=True)
import pwd
owner=pwd.getpwnam('phat')
os.chown(runtime,owner.pw_uid,owner.pw_gid)
unit=Path('/etc/systemd/system/do-an-monitor-v3.service')
unit.write_text('''[Unit]
Description=Zabbix evidence, SQLite expert diagnosis and topology correlation
After=network-online.target do-an-network-v3.service zabbix-server.service
Wants=network-online.target

[Service]
Type=simple
User=phat
Group=phat
WorkingDirectory=/home/phat/do-an/diagnosis-engine
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/phat/do-an/diagnosis-engine/.venv/bin/python /home/phat/do-an/system-monitor/monitor.py watch --interval 5
Restart=on-failure
RestartSec=10
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/home/phat/do-an/system-monitor/runtime
PrivateTmp=true
UMask=0077

[Install]
WantedBy=multi-user.target
''')
unit.chmod(0o644);os.chown(unit,0,0)
subprocess.run(['systemctl','daemon-reload'],capture_output=True,check=True,timeout=15)
subprocess.run(['systemctl','enable','--now','do-an-monitor-v3.service'],capture_output=True,check=True,timeout=15)
subprocess.run(['zabbix_server','-R','config_cache_reload'],capture_output=True,timeout=10)
print(json.dumps({'worker_service':subprocess.run(['systemctl','is-active','do-an-monitor-v3.service'],capture_output=True,text=True).stdout.strip(),'runtime_user':'phat','runtime_uses_admin_token':False}))

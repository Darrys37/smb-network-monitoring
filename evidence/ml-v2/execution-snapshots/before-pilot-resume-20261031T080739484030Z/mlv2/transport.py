"""Password stays in memory; arbitrary remote errors never reach experiment logs."""
import json
from pathlib import Path
import paramiko


class RemoteProbeError(RuntimeError):
    """Remote program unavailable; no failed measurement is fabricated."""


class SSHTransport:
    def __init__(self, password, connect_timeout=8, command_timeout=12, banner_timeout=15, auth_timeout=8):
        self.password, self.clients = password, {}
        self.connect_timeout,self.command_timeout=connect_timeout,command_timeout
        self.banner_timeout,self.auth_timeout=banner_timeout,auth_timeout

    def command(self, host, command, stdin_data=None):
        if host in self.clients:
            active=self.clients[host].get_transport()
            if active is None or not active.is_active():self.drop(host)
        if host not in self.clients:
            ip = {'mon01':'192.168.56.10','srv01':'192.168.56.20','cli01':'192.168.56.30'}[host]
            client = paramiko.SSHClient()
            client.load_host_keys(str(Path.home()/'.ssh/known_hosts'))
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
            try:
                client.connect(ip, username='phat', password=self.password, look_for_keys=False,
                               allow_agent=False, timeout=self.connect_timeout, auth_timeout=self.auth_timeout, banner_timeout=self.banner_timeout)
            except Exception:
                client.close()
                raise
            self.clients[host] = client
        try:
            stdin, stdout, stderr = self.clients[host].exec_command(command, timeout=self.command_timeout)
            if stdin_data is not None:
                stdin.write(stdin_data);stdin.flush();stdin.channel.shutdown_write()
            data = stdout.read(4*1024*1024)
            stderr.read(65536)
            code = stdout.channel.recv_exit_status()
            return code, data.decode('utf-8')
        except Exception:
            self.drop(host)
            raise

    def drop(self, host):
        client = self.clients.pop(host, None)
        if client is not None:
            client.close()

    def runner(self, host, source):
        command = 'cd /home/phat/do-an/diagnosis-engine && .venv/bin/python -' if host=='mon01' else 'python3 -'
        code, output = self.command(host, command, source)
        if code: raise RemoteProbeError('Remote probe failed')
        return json.loads(output)

    def sudo(self, host, command):
        code, output = self.command(host, "sudo -S -p '' "+command, self.password+'\n')
        if code: raise RuntimeError('Privileged operation failed')
        return output

    def close(self):
        for client in self.clients.values(): client.close()
        self.password = None


PLATFORM_SOURCE = r"""import hashlib,json,os,re,subprocess,time
from pathlib import Path
result=subprocess.run(['journalctl','-k','-b','--no-pager','-o','json'],capture_output=True,text=True,timeout=15)
if result.returncode:raise RuntimeError('Kernel journal unavailable')
matches=[]
for line in result.stdout.splitlines():
 row=json.loads(line);message=row.get('MESSAGE','')
 if isinstance(message,str) and (('rcu:' in message and ('detected stalls' in message or 'kthread starved' in message)) or 'BUG: soft lockup' in message):
  matches.append({'monotonic_us':int(row['__MONOTONIC_TIMESTAMP']),'realtime_us':int(row['__REALTIME_TIMESTAMP']),'message':message[:512]})
now=int(time.monotonic()*1000000)
latest=max((row['monotonic_us'] for row in matches),default=0)
jobs=subprocess.run(['systemctl','list-jobs','--no-legend','--no-pager'],capture_output=True,text=True,timeout=5)
if jobs.returncode:raise RuntimeError('Package job inventory unavailable')
package_jobs=[line.split()[1] for line in jobs.stdout.splitlines() if any(name in line for name in ['apt-daily.service','apt-daily-upgrade.service','unattended-upgrades.service'])]
lock_files=[]
for name in ['/var/lib/dpkg/lock','/var/lib/dpkg/lock-frontend']:
 p=Path(name)
 if p.exists():
  value=p.stat();lock_files.append((os.major(value.st_dev),os.minor(value.st_dev),value.st_ino))
held=[]
for line in Path('/proc/locks').read_text().splitlines():
 match=re.search(r'\b([0-9a-f]+):([0-9a-f]+):(\d+)\b',line,re.I)
 if match and (int(match[1],16),int(match[2],16),int(match[3])) in lock_files:held.append(True)
audit=subprocess.run(['dpkg','--audit'],capture_output=True,text=True,timeout=10)
package_sha=hashlib.sha256(Path('/var/lib/dpkg/status').read_bytes()).hexdigest()
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 'stall_count':len(matches),'recent_stall':bool(matches and now-latest<=120000000),
 'last_stalls':matches[-20:],'package_jobs_active':bool(package_jobs),'package_jobs':package_jobs,
 'dpkg_lock_held':bool(held),'package_audit_clean':audit.returncode==0 and not audit.stdout.strip(),
 'package_status_sha256':package_sha}))
"""


class LabTransport:
    """Control may wait longer; collection keeps the original 8/12-second limits."""
    audit_platform=True

    def __init__(self,password):
        self.control=SSHTransport(password,connect_timeout=30,command_timeout=60,banner_timeout=60,auth_timeout=30)
        self.probes=SSHTransport(password)

    def runner(self,*args):return self.control.runner(*args)
    def probe_runner(self,*args):return self.probes.runner(*args)
    def command(self,*args):return self.control.command(*args)
    def sudo(self,*args):return self.control.sudo(*args)
    def drop(self,host):self.control.drop(host);self.probes.drop(host)
    def close(self):self.control.close();self.probes.close()

    def platform_health(self):
        import shlex
        try:
            nodes={host:json.loads(self.control.sudo(host,'python3 -c '+shlex.quote(PLATFORM_SOURCE)))
                   for host in ['mon01','srv01','cli01']}
            return {'status':'ok','schema_version':2,'nodes':nodes}
        except (paramiko.AuthenticationException,paramiko.BadHostKeyException):
            raise
        except Exception as exc:
            return {'status':'error','error_type':type(exc).__name__}

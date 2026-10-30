"""Password stays in memory; arbitrary remote errors never reach experiment logs."""
import json
from pathlib import Path
import paramiko


class SSHTransport:
    def __init__(self, password):
        self.password, self.clients = password, {}

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
                               allow_agent=False, timeout=8, auth_timeout=8)
            except Exception:
                client.close()
                raise
            self.clients[host] = client
        try:
            stdin, stdout, stderr = self.clients[host].exec_command(command, timeout=12)
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
        if code: raise RuntimeError('Remote probe failed')
        return json.loads(output)

    def sudo(self, host, command):
        code, output = self.command(host, "sudo -S -p '' "+command, self.password+'\n')
        if code: raise RuntimeError('Privileged operation failed')
        return output

    def close(self):
        for client in self.clients.values(): client.close()
        self.password = None

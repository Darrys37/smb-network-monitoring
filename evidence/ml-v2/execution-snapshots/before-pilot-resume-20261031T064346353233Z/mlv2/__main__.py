import argparse
import getpass
import json
from pathlib import Path
import shlex

from .core import read, register, review, save_new, validate_observation
from .collector import collect


def main():
    parser = argparse.ArgumentParser(description='ML data collection/registry; no fault injection')
    parser.add_argument('--data-root', type=Path, required=True)
    sub = parser.add_subparsers(dest='action', required=True)
    for action in ['register', 'review', 'collect']:
        command = sub.add_parser(action)
        command.add_argument('--session', required=True)
        command.add_argument('--run', required=True)
        if action in ['register', 'review']:
            command.add_argument('--labels', nargs='+', required=True)
        if action == 'review':
            command.add_argument('--validity', choices=['valid','invalid','uncertain'], required=True)
            command.add_argument('--evidence', type=Path, nargs='+', required=True)
        if action == 'collect':
            command.add_argument('--profile', type=Path, required=True)
            command.add_argument('--engine-source', type=Path, required=True)
    args = parser.parse_args()
    if args.action == 'register':
        value = register(args.data_root, args.session, args.run, args.labels)
    elif args.action == 'review':
        value = review(args.data_root, args.session, args.run, args.validity, args.labels, args.evidence)
    else:
        from .core import identifier
        identifier(args.session); identifier(args.run)
        if not (args.data_root/'registry'/args.session/args.run/'registration.json').exists():
            parser.error('Register the run before collecting; label contents are never passed to collector')
        import paramiko
        password = getpass.getpass('VM SSH password (not logged): ')
        clients = {}

        def runner(host, program):
            if host not in clients:
                ip = {'mon01':'192.168.56.10','srv01':'192.168.56.20','cli01':'192.168.56.30'}[host]
                client = paramiko.SSHClient()
                client.load_host_keys(str(Path.home()/'.ssh/known_hosts'))
                client.set_missing_host_key_policy(paramiko.RejectPolicy())
                client.connect(ip, username='phat', password=password, look_for_keys=False,
                               allow_agent=False, timeout=8, auth_timeout=8)
                clients[host] = client
            python = '/home/phat/do-an/diagnosis-engine/.venv/bin/python' if host == 'mon01' else 'python3'
            stdin, stdout, stderr = clients[host].exec_command('cd /home/phat/do-an/diagnosis-engine && '+python+' -' if host=='mon01' else python+' -', timeout=60)
            stdin.write(program);stdin.flush();stdin.channel.shutdown_write()
            output = stdout.read(4*1024*1024)
            stderr.read(65536)
            if stdout.channel.recv_exit_status():
                raise RuntimeError('Remote probe failed')
            return json.loads(output)
        try:
            value = collect(read(args.profile), args.engine_source, args.session, args.run, runner)
        finally:
            for client in clients.values(): client.close()
        target = args.data_root/'observations'/args.session/args.run/(value['window_id']+'.json')
        save_new(target, value)
        print(json.dumps({'path':str(target),'sources':value['sources'],'evidence_count':len(value['evidence'])},ensure_ascii=True))
        if any(v['status']=='error' for v in value['sources'].values()):
            raise SystemExit(2)
        return
    print(json.dumps(value,ensure_ascii=True))


if __name__ == '__main__':
    main()

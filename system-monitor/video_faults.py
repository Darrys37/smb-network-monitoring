"""Bounded interventions for isolated video trials. No worker or access-policy changes."""
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time

HOST = {'R1':'srv01','R2':'srv01','R3':'srv01','R4':'cli01','R5':'srv01','R6':'srv01','R7':'cli01','R8':'mon01'}
ROOT = Path('/var/lib/do-an-video')


def run(args, check=True, text=None):
    result = subprocess.run(args, input=text, text=True, capture_output=True, timeout=20)
    if check and result.returncode:
        raise RuntimeError('Lab operation failed: ' + args[0])
    return result


def active(unit):
    return run(['systemctl','is-active','--quiet',unit], False).returncode == 0


def push(value):
    run(['runuser','-u','phat','--','/home/phat/do-an/diagnosis-engine/.venv/bin/python',
         '/home/phat/do-an/system-monitor/storm_control.py',str(value)])


def control(action, case, token, source=None):
    if os.geteuid() != 0 or case not in HOST or socket.gethostname().split('.')[0].lower() != HOST[case]:
        raise ValueError('Wrong privilege, host or case')
    if not re.fullmatch('[a-f0-9]{12}',token):
        raise ValueError('Invalid trial identity')
    folder = ROOT / token
    state_file = folder / 'state.json'
    if action == 'recover':
        if not state_file.exists():
            return {'restored':True,'state_absent':True}
        state = json.loads(state_file.read_text())
        if state['case'] != case or state['token'] != token:
            raise ValueError('Foreign trial state')
        if case in {'R1','R4','R5'}:
            if run(['nft','list','table','inet',state['table']],False).returncode == 0:
                run(['nft','delete','table','inet',state['table']])
        elif case in {'R2','R3'}:
            service = 'nginx' if case == 'R2' else 'zabbix-agent2'
            run(['systemctl','start',service])
            if not active(service):
                raise RuntimeError('Service recovery not verified')
        elif case == 'R6':
            run(['systemctl','stop',state['stress']],False)
            if active(state['stress']):
                raise RuntimeError('Stress still running')
        elif case == 'R7':
            run(['sysctl','-w','net.ipv4.ip_forward=1'])
            if Path('/proc/sys/net/ipv4/ip_forward').read_text().strip() != '1':
                raise RuntimeError('Forwarding recovery failed')
        else:
            push(0)
        state['recovered_at'] = int(time.time())
        state_file.write_text(json.dumps(state))
        run(['systemctl','stop',state['unit']+'.timer'],False)
        return {'restored':True,'case':case}
    if action != 'arm' or not source or folder.exists():
        raise ValueError('Invalid arm or reused trial')
    if case in {'R2','R3','R6'} and not active('nginx' if case=='R2' else 'zabbix-agent2'):
        raise ValueError('Service baseline unhealthy')
    if case == 'R6' and not Path('/usr/bin/stress-ng').is_file():
        raise ValueError('stress-ng missing')
    if case == 'R7' and Path('/proc/sys/net/ipv4/ip_forward').read_text().strip() != '1':
        raise ValueError('Gateway baseline unhealthy')
    if case in {'R1','R4','R5'} and run(['nft','list','table','inet','doan_video_'+token],False).returncode == 0:
        raise ValueError('Table already exists; nothing changed')
    ROOT.mkdir(mode=0o700,exist_ok=True)
    folder.mkdir(mode=0o700)
    lifetime = 480 if case=='R6' else 180
    state = {'case':case,'token':token,'table':'doan_video_'+token,'unit':'doan-video-'+token,
             'stress':'doan-video-cpu-'+token,'recovered_at':None}
    state_file.write_text(json.dumps(state)); state_file.chmod(0o600)
    rollback = folder/'rollback.py'
    rollback.write_text(source); rollback.chmod(0o700)
    # No intervention precedes a confirmed independent rollback timer.
    run(['systemd-run','--unit='+state['unit'],'--on-active='+str(lifetime)+'s',
         '--timer-property=AccuracySec=1s','/usr/bin/python3',str(rollback),'recover',case,token])
    if not active(state['unit']+'.timer'):
        raise RuntimeError('Rollback timer not active; no fault applied')
    try:
        if case in {'R1','R4','R5'}:
            if run(['nft','list','table','inet',state['table']],False).returncode == 0:
                raise ValueError('Owned table already exists')
            direction='output' if case=='R4' else 'input'
            rules = ('udp dport 53 counter drop\ntcp dport 53 counter drop' if case=='R4' else
                     'ip saddr 192.168.56.10 ip daddr 172.30.20.20 tcp dport 80 counter drop' if case=='R5' else
                     'ip saddr 192.168.56.10 ip daddr 172.30.20.20 ip protocol icmp counter drop\nip saddr 192.168.56.10 ip daddr 172.30.20.20 ip protocol tcp counter drop')
            run(['nft','-f','-'],text='table inet '+state['table']+' {\nchain '+direction+' {\ntype filter hook '+direction+' priority -10; policy accept;\n'+rules+'\n}\n}\n')
            if case=='R4':run(['resolvectl','flush-caches'])
        elif case in {'R2','R3'}:
            service='nginx' if case=='R2' else 'zabbix-agent2'
            run(['systemctl','stop',service])
            if active(service):raise RuntimeError('Service not stopped')
        elif case=='R6':
            count=len(os.sched_getaffinity(0))+1
            run(['systemd-run','--unit='+state['stress'],'--property=RuntimeMaxSec=440s',
                 '--property=KillMode=control-group','/usr/bin/stress-ng','--cpu',str(count),'--cpu-load','100','--timeout','420s','--quiet'])
            if not active(state['stress']):raise RuntimeError('Stress not running')
        elif case=='R7':run(['sysctl','-w','net.ipv4.ip_forward=0'])
        else:push(1)
        state['fault_at']=int(time.time());state_file.write_text(json.dumps(state))
        return {'case':case,'fault_at':state['fault_at'],'rollback_seconds':lifetime,'timer_active':True}
    except BaseException:
        control('recover',case,token)
        raise


if __name__=='__main__':
    print(json.dumps(control(*sys.argv[1:4])))

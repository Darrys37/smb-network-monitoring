"""Bounded lab faults, each armed behind an independent systemd rollback timer."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import time


def command(args):
    value=subprocess.run(args,capture_output=True,text=True,timeout=10)
    if value.returncode:raise RuntimeError('Lab command failed: '+args[0])
    return value.stdout.strip()


def control(action, kind, seconds=120):
    if os.geteuid()!=0:raise PermissionError('Run via sudo on the designated VM')
    host=socket.gethostname().split('.')[0].lower()
    if kind not in {'nginx','gateway'} or host!=({'nginx':'srv01','gateway':'cli01'}[kind]):raise ValueError('Wrong VM/fault')
    if not 45<=seconds<=180:raise ValueError('Rollback must be 45..180 seconds')
    unit='do-an-v3-rollback-'+kind
    restore=['/usr/bin/systemctl','start','nginx'] if kind=='nginx' else ['/usr/sbin/sysctl','-w','net.ipv4.ip_forward=1']
    def baseline():
        if kind=='nginx':return subprocess.run(['systemctl','is-active','--quiet','nginx']).returncode==0
        return Path('/proc/sys/net/ipv4/ip_forward').read_text().strip()=='1'
    if action=='arm':
        if not baseline():raise ValueError('Fault baseline is not healthy; nothing changed')
        active=subprocess.run(['systemctl','is-active','--quiet',unit+'.timer']).returncode==0
        if active:raise ValueError('Previous rollback timer still active')
        subprocess.run(['systemctl','reset-failed',unit+'.service'],capture_output=True)
        command(['systemd-run','--unit='+unit,'--on-active='+str(seconds)+'s',*restore])
        command(['systemctl','is-active',unit+'.timer'])
        # No fault occurs before a verified independent rollback timer exists.
        command(['systemctl','stop','nginx'] if kind=='nginx' else ['sysctl','-w','net.ipv4.ip_forward=0'])
        return {'host':host,'fault':kind,'action':action,'fault_clock':int(time.time()),'rollback_seconds':seconds,
                'rollback_timer':unit+'.timer','timer_active':True,'fault_applied':not baseline()}
    if action=='recover':
        command(restore)
        if not baseline():raise RuntimeError('Recovery verification failed; rollback timer retained')
        subprocess.run(['systemctl','stop',unit+'.timer'],capture_output=True)
        return {'host':host,'fault':kind,'action':action,'recovered_clock':int(time.time()),'baseline_restored':True}
    raise ValueError('Unknown fault action')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['arm','recover'])
    parser.add_argument('kind',choices=['nginx','gateway'])
    parser.add_argument('--seconds',type=int,default=120)
    args=parser.parse_args()
    print(json.dumps(control(args.action,args.kind,args.seconds)))

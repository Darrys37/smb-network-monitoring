"""One-off supervisor; credentials arrive through an anonymous stdin pipe only."""
import ctypes
import csv
from ctypes import wintypes
from datetime import datetime,timezone
import hashlib
import json
import msvcrt
import os
from pathlib import Path
import subprocess
import sys
import time

WORK=Path(__file__).resolve().parent
PROJECT=Path(r'C:\Users\Darrys\do-an')
MODULE=PROJECT/'ml-research'
ROOT=PROJECT/'evidence/ml-v2'
sys.path.insert(0,str(WORK/'.ssh-deps'))
sys.path.insert(0,str(MODULE))
from resume_ml_pilot import main as resume,backup
from mlv2.core import read,save_new
from mlv2.pilot import schedule,baseline_ok,SERVICE_STATUS,MON_STATUS
from mlv2.transport import SSHTransport
from mlv2.collector import collect


def status(phase,**extra):
    result_files=list((ROOT/'trial-logs').glob('pilot-v2-*/*/RESULT.json'))
    results=[read(path) for path in result_files]
    value={'phase':phase,'pid':os.getpid(),'updated_at':datetime.now(timezone.utc).isoformat(),
           'attempts_finished':len(results),'valid_attempts':sum(bool(row['valid']) for row in results),**extra}
    target=WORK/'verification/ml-supervisor-status.json'
    temp=target.with_suffix('.pending.json')
    temp.write_text(json.dumps(value,indent=2),encoding='utf-8')
    os.replace(temp,target)
    print(json.dumps(value,ensure_ascii=True),flush=True)


def wait_original(pid):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
    kernel.WaitForSingleObject.restype=wintypes.DWORD
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x100000,False,pid)
    if not handle:
        raise OSError('Cannot safely acquire original process handle')
    try:
        deadline=time.monotonic()+3*3600
        while True:
            result=kernel.WaitForSingleObject(handle,15000)
            if result==0:return
            if result!=258:raise OSError('Original-process wait failed')
            if time.monotonic()>deadline:raise TimeoutError('Original process still active; no second coordinator started')
            status('waiting_original_coordinator',original_pid=pid)
    finally:
        kernel.CloseHandle(handle)


def postflight(password):
    transport=SSHTransport(password)
    try:
        service=transport.runner('srv01',SERVICE_STATUS)
        monitor=transport.runner('mon01',MON_STATUS)
        assert baseline_ok(service,monitor),'Baseline not restored'
        code,interfaces=transport.command('srv01','ip -j -4 address show dev enp0s8')
        assert code==0 and any('UP' in row['flags'] and any(a.get('local')=='192.168.56.20' for a in row.get('addr_info',[])) for row in json.loads(interfaces))
        assert 'mlv2_' not in transport.sudo('srv01','nft list tables')
        code,timers=transport.command('srv01',"systemctl list-timers 'mlv2-*' --no-legend --no-pager")
        assert code==0 and not timers.strip()
        state=transport.runner('mon01',"""import hashlib,json,sqlite3
from pathlib import Path
p=Path('/home/phat/do-an/diagnosis-engine')
db=sqlite3.connect((p/'diagnosis.db').as_uri()+'?mode=ro',uri=True)
try:
 result={'source':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in p.glob('*.py')},
 'counts':{t:db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['incidents','evidence','diagnoses','recoveries']},
 'integrity':db.execute('PRAGMA integrity_check').fetchall()}
finally:db.close()
print(json.dumps(result))
""")
        previous=read(sorted((WORK/'verification').glob('ml-vm-preflight-*.json'))[-1])[0]
        assert state['source']==previous['engine_source_sha256']
        assert state['counts']==previous['sqlite_counts']
        assert state['integrity']==[['ok']]
        return {'status':'PILOT_POSTFLIGHT_OK','service':service,'monitor':monitor,'runtime':state,
                'source_engine_unchanged':True,'runtime_counts_unchanged':True,
                'pilot_firewall_tables_remaining':False,'pilot_timers_remaining':False}
    finally:
        transport.close()


def command(*args):
    result=subprocess.run([sys.executable,*map(str,args)],cwd=MODULE,env={**os.environ,'PYTHONIOENCODING':'utf-8','PYTHONPATH':str(WORK/'.ssh-deps')},
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
    print(result.stdout,flush=True)
    if result.returncode:raise RuntimeError('Offline command failed: '+str(args[0]))


def main():
    password=sys.stdin.readline().rstrip('\r\n')
    if not password:raise ValueError('No credential received')
    lock=(WORK/'verification/ml-supervisor.lock').open('a+b')
    lock.seek(0)
    if not lock.read(1):lock.write(b'0');lock.flush()
    lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    sources=[MODULE/name for name in ['train_v2.py','candidate_v2.py','demo_v2.py','demo_live_v2.py']]
    source_hashes={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    try:
        snapshot=ROOT/'execution-snapshots'/('supervisor-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        helper_hashes={}
        for path in [Path(__file__),WORK/'resume_ml_pilot.py',WORK/'launch_ml_supervisor.py']:
            target=snapshot/path.name
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(path.read_bytes())
            helper_hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        save_new(snapshot/'manifest.json',helper_hashes)
        status('supervisor_started',original_pid=int(sys.argv[1]))
        wait_original(int(sys.argv[1]))
        if source_hashes!={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}:
            raise RuntimeError('Research source changed while collecting; explicit review needed')
        status('checking_and_resuming_remaining_runs')
        resume(password)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        verification=ROOT/'verification'/('completed-pilot-'+stamp)
        status('postflight')
        save_new(verification/'postflight.json',postflight(password))
        command('export_dataset.py','--data-root',ROOT,'--output',ROOT/'quality')
        command('-m','unittest','discover','-s','tests','-v')
        status('training_pilot_benchmark')
        command('train_v2.py','--project-root',PROJECT,'--data-root',ROOT,'--output-root',ROOT/'benchmark')
        output=Path(read(ROOT/'benchmark/latest.json')['output_dir'])
        from demo_v2 import assess
        manifest=read(output/'manifest.json')
        with (output/'dataset_used.csv').open(encoding='utf-8-sig') as stream:
            labels={(row['session_id'],row['run_id']):row['label'] for row in csv.DictReader(stream)}
        selected={}
        for item in manifest['sources']:
            label=labels[item['session_id'],item['run_id']]
            if label not in selected:selected[label]=item
        for label,item in selected.items():
            save_new(output/'replay-demo'/f'{label}.json',assess(read(item['path']),output/'candidate_rules.sqlite',PROJECT/'diagnosis-engine'))
        status('healthy_live_shadow_demo')
        transport=SSHTransport(password)
        try:
            observation=collect(read(MODULE/'config/srv01.json'),PROJECT/'diagnosis-engine','shadow-v2','demo-'+stamp,transport.runner)
        finally:transport.close()
        save_new(output/'healthy-live-demo/observation.json',observation)
        save_new(output/'healthy-live-demo/comparison.json',assess(observation,output/'candidate_rules.sqlite',PROJECT/'diagnosis-engine'))
        save_new(verification/'post-demo-postflight.json',postflight(password))
        save_new(output/'supervisor-source-hashes.json',source_hashes)
        note=['# Kết quả tiếp tục tự động','',f'Hoàn tất lúc {datetime.now(timezone.utc).isoformat()} UTC.',
              '',f'Benchmark: `{output.relative_to(PROJECT).as_posix()}`.',
              '', 'Lịch 42 lượt đã có attempt hợp lệ; nguyên bản uncertain và retry được giữ riêng. Đã chạy tests, kiểm tra postflight trước/sau demo và so cùng evidence.',
              '', 'Đây là pilot nội bộ; M5 test độc lập và đánh giá chuyển host chưa hoàn tất. Luật SQLite chỉ ở trạng thái candidate. Wrapper shadow riêng, chưa thay engine vận hành.','']
        save_new(verification/'completion.json',{'benchmark':str(output),'pilot_schedule_has_valid_attempts':True,'verified_postflight':True})
        (MODULE/'AUTORUN_RESULT.md').write_text('\n'.join(note),encoding='utf-8')
        final_backup=backup('after-pilot-benchmark-')
        status('COMPLETE_PILOT_M4',benchmark=str(output),backup=str(final_backup),verification=str(verification))
    finally:
        password=None
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()


if __name__=='__main__':
    try:main()
    except BaseException as exc:
        status('STOPPED_REQUIRES_REVIEW',error_type=type(exc).__name__,error_message=str(exc))
        raise

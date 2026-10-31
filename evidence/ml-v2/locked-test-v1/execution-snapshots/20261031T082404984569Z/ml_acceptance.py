"""Complete a sealed holdout, versioned rule registry and fault-time shadow checks."""
import ctypes
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
PARENT=PROJECT/'evidence/ml-v2'
ROOT=PARENT/'locked-test-v1'
sys.path.insert(0,str(WORK/'.ssh-deps'));sys.path.insert(0,str(MODULE))
from mlv2.core import read,save_new,sha
from mlv2.pilot import Pilot,platform_ready
from mlv2.transport import LabTransport as SSHTransport
from mlv2.quality import audit
from locked_test_v2 import freeze_development,evaluate_locked
from demo_v2 import assess
from ml_supervisor import postflight
from ml_vm_preflight import REMOTE as REMOTE_BACKUP
from resume_ml_pilot import finish_interrupted,backup
from lab_host_guard import lab_host_guard


def status(phase,**extra):
    results=[read(path) for path in ROOT.glob('trial-logs/*/*/RESULT.json')]
    value={'phase':phase,'pid':os.getpid(),'at':datetime.now(timezone.utc).isoformat(),
           'finished_attempts':len(results),'valid_attempts':sum(row['valid'] for row in results),**extra}
    path=WORK/'verification/ml-acceptance-status.json';temp=path.with_suffix('.pending.json')
    temp.write_text(json.dumps(value,indent=2),encoding='utf-8');os.replace(temp,path)
    print(json.dumps(value,ensure_ascii=True),flush=True)


def wait_original(pid):
    if pid==0:return
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD];kernel.WaitForSingleObject.restype=wintypes.DWORD
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x100000,False,pid)
    if not handle:raise OSError('Cannot acquire current worker handle; review state before resuming')
    try:
        while True:
            result=kernel.WaitForSingleObject(handle,30000)
            if result==0:return
            if result!=258:raise OSError('Worker wait failed')
            status('waiting_pilot_worker',pilot_pid=pid)
    finally:kernel.CloseHandle(handle)


def run_tests(receipt):
    result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=MODULE,
        env={**os.environ,'PYTHONPATH':str(WORK/'.ssh-deps'),'PYTHONIOENCODING':'utf-8'},
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
    save_new(receipt,{'returncode':result.returncode,'output':result.stdout})
    if result.returncode:raise RuntimeError('ML tests failed; no further fault injection')


def package_fingerprint(platform):
    if not platform_ready(platform):raise RuntimeError('System package/platform audit is not ready')
    return {name:row['package_status_sha256'] for name,row in platform['nodes'].items()}


class ShadowPilot(Pilot):
    def __init__(self,*args,candidate_db,expected_candidate_sha,expected_packages=None,**kwargs):
        super().__init__(*args,**kwargs);self.candidate_db=candidate_db;self.expected_candidate_sha=expected_candidate_sha
        self.expected_packages=expected_packages

    def wait_baseline(self,limit=1200):
        value=super().wait_baseline(limit)
        if self.expected_packages is not None and package_fingerprint(value['platform'])!=self.expected_packages:
            raise ValueError('Frozen system package environment changed; do not continue the sealed test')
        return value

    def snapshot(self,item):
        value=super().snapshot(item)
        # The candidate receives no planned label. Errors in shadow inference do
        # not redefine the validity of an independently verified intervention.
        try:
            if sha(self.candidate_db)!=self.expected_candidate_sha:raise ValueError('Frozen candidate artifact changed')
            comparison=assess(value,self.candidate_db,self.engine)
            comparison['mode']='live_shadow_sealed_holdout'
            comparison['candidate_sha256']=sha(self.candidate_db)
            comparison['observation_sha256']=sha(self.root/'observations'/item['session_id']/item['run_id']/(value['window_id']+'.json'))
        except Exception as exc:
            comparison={'mode':'live_shadow_sealed_holdout','error_type':type(exc).__name__}
        save_new(self.root/'sealed-shadow'/item['session_id']/item['run_id']/(value['window_id']+'.json'),comparison)
        return value


def collect_schedule(pilot,planned):
    for item in planned:
        result=ROOT/'trial-logs'/item['session_id']/item['run_id']/'RESULT.json'
        if not result.exists():
            registration=ROOT/'registry'/item['session_id']/item['run_id']/'registration.json'
            if registration.exists():finish_interrupted(pilot,item)
            else:pilot.run(item)
        if read(result)['valid']:continue
        for index in range(1,4):
            attempt={**item,'run_id':item['run_id']+f'-retry{index}'}
            receipt=ROOT/'trial-logs'/attempt['session_id']/attempt['run_id']/'RESULT.json'
            if not receipt.exists():
                registration=ROOT/'registry'/attempt['session_id']/attempt['run_id']/'registration.json'
                if registration.exists():finish_interrupted(pilot,attempt)
                else:
                    plan=ROOT/'retry-plans'/(attempt['session_id']+'--'+attempt['run_id']+'.json')
                    if not plan.exists():save_new(plan,{'parent_run_id':item['run_id'],'attempt':attempt})
                    pilot.run(attempt)
            if read(receipt)['valid']:break
        else:raise RuntimeError('Three validity retries exhausted: '+item['run_id'])


def shadow_equivalence(output):
    import csv
    manifest=read(output/'manifest.json')
    with (output/'locked_test_predictions.csv').open(encoding='utf-8-sig') as stream:
        expected={(row['session_id'],row['run_id']):row for row in csv.DictReader(stream)}
    findings=[]
    for source in manifest['test_sources']:
        observation=read(source['path'])
        sealed=read(ROOT/'sealed-shadow'/source['session_id']/source['run_id']/(observation['window_id']+'.json'))
        if sealed.get('error_type'):raise RuntimeError('Fault-time shadow inference failed: '+sealed['error_type'])
        if sealed['observation_sha256']!=source['sha256']:raise ValueError('Shadow/evaluation observation differs')
        row=expected[source['session_id'],source['run_id']]
        same=(sealed['ml_suggestions']['CART']['label']==row['cart_discrete'] and
              sealed['ml_suggestions']['FP-Growth']['label']==row['fp_classifier'])
        findings.append({'session_id':source['session_id'],'run_id':source['run_id'],'equivalent':same})
    save_new(output/'live_shadow_equivalence.json',{'cases':findings,'all_equal':all(row['equivalent'] for row in findings),
        'scope':'Live predictions were saved during fault before rollback and not used to tune or retry; comparison opened after all collection'})
    if not all(row['equivalent'] for row in findings):raise AssertionError('Live shadow and frozen offline predictions differ')


def _worker_main():
    password=sys.stdin.readline().rstrip('\r\n')
    if not password:raise ValueError('No credential supplied')
    own=(WORK/'verification/ml-acceptance.lock').open('a+b');own.seek(0)
    if not own.read(1):own.write(b'0');own.flush()
    own.seek(0);msvcrt.locking(own.fileno(),msvcrt.LK_NBLCK,1)
    lab=None;lab_locked=False;transport=None;host_guard=None
    try:
        helper_files=[Path(__file__),WORK/'resume_ml_pilot.py',WORK/'ml_supervisor.py',WORK/'ml_vm_preflight.py',WORK/'lab_host_guard.py']
        helper_bytes={str(path):path.read_bytes() for path in helper_files}
        status('waiting_pilot_worker',pilot_pid=int(sys.argv[1]))
        wait_original(int(sys.argv[1]))
        previous=read(WORK/'verification/ml-supervisor-status.json')
        if previous['phase']!='COMPLETE_PILOT_M4':raise RuntimeError('Pilot worker did not finish successfully; review before holdout')
        if any(path.read_bytes()!=helper_bytes[str(path)] for path in helper_files):
            raise ValueError('Coordinator helper changed while waiting; review before collecting test')
        lab=(WORK/'verification/ml-supervisor.lock').open('a+b');lab.seek(0)
        msvcrt.locking(lab.fileno(),msvcrt.LK_NBLCK,1)
        lab_locked=True
        host_guard=lab_host_guard();host_profile=host_guard.__enter__()
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        verification=ROOT/'verification'/stamp
        save_new(verification/'host-execution-profile.json',host_profile)
        pilot_output=Path(read(PARENT/'benchmark/latest.json')['output_dir'])
        freeze_file=ROOT/'development-freeze.json'
        if not freeze_file.exists():freeze_development(PROJECT,pilot_output,freeze_file)
        freeze=read(freeze_file)
        if sha(pilot_output/'candidate_rules.sqlite')!=freeze['pilot_candidate_sha256']:
            raise ValueError('Pilot candidate changed after freeze')
        for name,checksum in freeze['code_sha256'].items():
            if sha(name)!=checksum:raise ValueError('Source changed after holdout freeze')
        run_tests(verification/'preflight-tests.json')
        backup('before-locked-test-')
        status('fresh_vm_backup')
        transport=SSHTransport(password)
        vm=[]
        for host in ['mon01','srv01','cli01']:vm.append(transport.runner(host,REMOTE_BACKUP))
        assert vm[0]['sqlite_integrity']==[['ok']] and not vm[0]['sqlite_foreign_keys']
        save_new(verification/'vm-backup.json',vm)
        save_new(verification/'preflight.json',postflight(password))
        environment_file=ROOT/'lab-environment-freeze.json'
        environment=Pilot(transport,ROOT,PROJECT/'diagnosis-engine',freeze['profile']).wait_baseline()['platform']
        packages=package_fingerprint(environment)
        if not environment_file.exists():
            save_new(environment_file,{'schema_version':1,'frozen_at':int(time.time()),'packages':packages,
                'platform':environment,'scope':'Fixed package state on the three lab nodes during the fresh heldout collection'})
        environment_reference=read(environment_file)
        if packages!=environment_reference['packages']:raise ValueError('System packages differ from the pre-test environment freeze')
        status('temporal_embargo',earliest_test_time=freeze['earliest_test_time'])
        while time.time()<freeze['earliest_test_time']:
            time.sleep(min(30,freeze['earliest_test_time']-time.time()))
        snapshot=ROOT/'execution-snapshots'/stamp
        helpers=helper_files
        for source in helpers:
            target=snapshot/source.name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
        save_new(snapshot/'manifest.json',{source.name:sha(source) for source in helpers})
        def progress(message,**kwargs):
            print(message,**kwargs)
            status('collecting_sealed_holdout',latest_event=json.loads(message))
        pilot=ShadowPilot(transport,ROOT,PROJECT/'diagnosis-engine',freeze['profile'],log=progress,
                          candidate_db=pilot_output/'candidate_rules.sqlite',expected_candidate_sha=freeze['pilot_candidate_sha256'],
                          expected_packages=environment_reference['packages'])
        collect_schedule(pilot,freeze['test_schedule'])
        after_packages=package_fingerprint(transport.platform_health())
        if after_packages!=environment_reference['packages']:raise ValueError('System packages changed during heldout collection')
        environment_validation={'all_equal':True,'before_packages':environment_reference['packages'],
            'after_packages':after_packages,'reference_sha256':sha(environment_file),
            'scope':'Package update jobs/locks audited before and after each trial; hashes checked against a pre-test reference'}
        transport.close();transport=None
        status('holdout_collected_postflight')
        save_new(verification/'postflight.json',postflight(password))
        audit(ROOT,ROOT/'quality')
        run_tests(verification/'postflight-tests.json')
        status('opening_sealed_evaluation')
        output=evaluate_locked(PROJECT,ROOT,freeze_file,ROOT/'evaluation')
        save_new(output/'lab-environment-freeze.json',environment_reference)
        save_new(output/'lab-environment-validation.json',environment_validation)
        shadow_equivalence(output)
        save_new(verification/'after-evaluation-postflight.json',postflight(password))
        save_new(verification/'completion.json',{'locked_test_output':str(output),'live_shadow_verified':True,
            'baseline_runtime_preserved':True,'no_rules_active':True,'scope':'Initial same-host ML acceptance; physical/multi-fault/topology excluded'})
        (MODULE/'ACCEPTANCE_RESULT.md').write_text('# Nghiệm thu ML trên lab VM\n\n'+
            f'Báo cáo thật: `{output.relative_to(PROJECT).as_posix()}/REPORT.md`.\n\n'+
            'Đã khóa train/config trước khi thu test mới; kiểm tra SQLite, so luật chuyên gia, đo latency cùng đầu vào và đối chiếu shadow live trong fault. Mọi luật vẫn không active trong engine vận hành.\n\n'+
            'Đây là nghiệm thu ban đầu trong cùng host/lab. Không đại diện đầy đủ ngân sách 210 lượt đề xuất; chưa chứng minh khả năng chuyển máy thật, multi-fault hoặc topology/suppression.\n',encoding='utf-8')
        final_backup=backup('after-locked-test-acceptance-')
        status('COMPLETE_INITIAL_VM_ML_ACCEPTANCE',output_dir=str(output),backup=str(final_backup),verification=str(verification))
    finally:
        if transport is not None:transport.close()
        password=None
        if host_guard is not None:host_guard.__exit__(None,None,None)
        if lab is not None:
            if lab_locked:
                lab.seek(0);msvcrt.locking(lab.fileno(),msvcrt.LK_UNLCK,1)
            lab.close()
        own.seek(0);msvcrt.locking(own.fileno(),msvcrt.LK_UNLCK,1);own.close()


def main():
    if os.environ.get('ML_ACCEPTANCE_DIRECT')=='1':return _worker_main()
    # Use a fresh foreground interpreter after the development stage. Its
    # executed modules then match the hashes frozen before test collection.
    password=sys.stdin.readline().rstrip('\r\n')
    if not password:raise ValueError('No credential supplied')
    try:
        result=subprocess.run([sys.executable,'-u',str(Path(__file__)),sys.argv[1]],
            cwd=WORK,input=(password+'\n').encode('utf-8'),
            env={**os.environ,'ML_ACCEPTANCE_DIRECT':'1','PYTHONIOENCODING':'utf-8'})
        if result.returncode:raise RuntimeError('Fresh acceptance interpreter failed; inspect its recorded status')
    finally:password=None


if __name__=='__main__':
    try:main()
    except BaseException as exc:
        status('STOPPED_REQUIRES_REVIEW',error_type=type(exc).__name__,error_message=str(exc))
        raise

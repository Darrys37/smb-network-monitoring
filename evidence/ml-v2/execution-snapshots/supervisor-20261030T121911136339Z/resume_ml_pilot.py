"""Audit interrupted trials, then resume the registered pilot without overwrite."""
import getpass
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
import zipfile

WORK = Path(__file__).resolve().parent
PROJECT = Path(r'C:\Users\Darrys\do-an')
MODULE = PROJECT / 'ml-research'
ROOT = PROJECT / 'evidence/ml-v2'
sys.path.insert(0, str(WORK / '.ssh-deps'))
sys.path.insert(0, str(MODULE))
from mlv2.core import read, review, save_new
from mlv2.pilot import Pilot, schedule
from mlv2.transport import LabTransport as SSHTransport


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def backup(prefix='before-pilot-resume-'):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = WORK / 'deliverables' / (prefix + stamp)
    out.mkdir()
    archive = out / 'current-ml-evidence.zip'
    hashes = {}
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as stream:
        for base in [MODULE, ROOT]:
            for source in sorted(base.rglob('*')):
                if not source.is_file() or '__pycache__' in source.parts:
                    continue
                relative = source.relative_to(PROJECT).as_posix()
                hashes[relative] = checksum(source)
                stream.write(source, relative)
    with zipfile.ZipFile(archive) as stream:
        assert stream.testzip() is None
        assert all(hashlib.sha256(stream.read(name)).hexdigest() == value for name, value in hashes.items())
    save_new(out / 'files.json', hashes)
    head = subprocess.check_output(['git', '-C', str(PROJECT), 'rev-parse', 'HEAD'], text=True).strip()
    second = Path(r'D:\Study\network-monitoring-project\backups') / out.name
    second.mkdir()
    for path in [archive, out / 'files.json']:
        shutil.copyfile(path, second / path.name)
        assert checksum(path) == checksum(second / path.name)
    receipt = {'status':'DIRTY_ML_BACKUP_VERIFIED', 'head':head, 'primary':str(out),
               'secondary':str(second), 'sha256':checksum(archive), 'files':len(hashes),
               'scope':'Current ML source and evidence, including uncommitted interrupted trial; full Git backup retained separately'}
    save_new(out / 'VERIFICATION.json', receipt)
    print(json.dumps(receipt, ensure_ascii=True), flush=True)
    return out


def finish_interrupted(pilot, item):
    root = Path(pilot.root)
    folder = root / 'trial-logs' / item['session_id'] / item['run_id']
    control = read(folder / 'control.json')
    remote, unit = control['remote_directory'], control['unit']
    assert re.fullmatch(r'/home/phat/ml-experiments/[0-9a-f]{12}', remote)
    assert re.fullmatch(r'mlv2-[0-9a-f]{12}', unit)
    # Replay only the exact recorded idempotent rollback. Never touch other units.
    pilot.transport.sudo('srv01', '/bin/bash ' + remote + '/rollback.sh')
    pilot.cancel_timer(unit)
    after = pilot.wait_baseline()
    save_new(folder / 'interruption-postflight.json', after)
    logs = pilot.transport.runner('srv01', "import json\nfrom pathlib import Path\np=Path(" + repr(remote) + ")\nprint(json.dumps({n:(p/n).read_text() for n in ['fault.log','rollback.log']}))\n")
    save_new(folder / 'interruption-independent-logs.json', logs)
    audit = {'reason':'Coordinator process no longer running; missing completion timeline and end observation are not reconstructed',
             'interrupted_run_retained':True, 'baseline_restored':True, 'timer_cancelled':True}
    save_new(folder / 'interruption-audit.json', audit)
    result = review(root, item['session_id'], item['run_id'], 'uncertain', [item['label']],
                    [folder/'preflight.json', folder/'interruption-postflight.json', folder/'interruption-independent-logs.json', folder/'interruption-audit.json'])
    save_new(folder / 'RESULT.json', {**item, 'valid':False, 'error_type':'CoordinatorInterrupted',
                                    'review':result, 'remote_log_directory':remote})
    print(json.dumps({'state':'interrupted_run_audited', **item}), flush=True)


def main(password=None):
    out = backup()
    transport = SSHTransport(getpass.getpass('VM SSH password (not logged): ') if password is None else password)
    pilot = Pilot(transport, ROOT, PROJECT/'diagnosis-engine', read(MODULE/'config/srv01.json'))
    # Snapshot the executed source separately from previous batches.
    snapshot = ROOT/'execution-snapshots'/out.name
    manifest = {}
    for source in [Path(__file__), MODULE/'run_pilot.py', *sorted((MODULE/'mlv2').glob('*.py'))]:
        relative = 'coordinator/'+source.name if source.parent == WORK else source.relative_to(MODULE).as_posix()
        target = snapshot/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        manifest[relative] = checksum(source)
    save_new(snapshot/'manifest.json', manifest)
    try:
        for item in schedule():
            folder = ROOT/'trial-logs'/item['session_id']/item['run_id']
            result_path = folder/'RESULT.json'
            if not result_path.exists():
                registration = ROOT/'registry'/item['session_id']/item['run_id']/'registration.json'
                if registration.exists():
                    finish_interrupted(pilot, item)
                else:
                    pilot.run(item)
            if read(result_path)['valid']:
                continue
            valid_retry = False
            for attempt in range(1, 4):
                retry = {**item, 'run_id':item['run_id']+f'-retry{attempt}'}
                retry_result = ROOT/'trial-logs'/retry['session_id']/retry['run_id']/'RESULT.json'
                if retry_result.exists():
                    if read(retry_result)['valid']:
                        valid_retry = True
                        break
                    continue
                registration = ROOT/'registry'/retry['session_id']/retry['run_id']/'registration.json'
                if registration.exists():
                    finish_interrupted(pilot, retry)
                    continue
                plan = ROOT/'retry-plans'/(retry['session_id']+'--'+retry['run_id']+'.json')
                if not plan.exists():
                    save_new(plan, {'parent_run_id':item['run_id'], 'attempt':retry})
                if pilot.run(retry)['valid']:
                    valid_retry = True
                    break
            if not valid_retry:
                raise RuntimeError('Three retry attempts exhausted: '+item['run_id'])
        print(json.dumps({'state':'ALL_42_SCHEDULED_RUNS_HAVE_VALID_ATTEMPTS'}), flush=True)
    finally:
        transport.close()


if __name__ == '__main__':
    main()

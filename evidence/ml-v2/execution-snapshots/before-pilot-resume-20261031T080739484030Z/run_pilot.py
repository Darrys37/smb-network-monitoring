"""Resume the registered 42-run pilot in bounded batches, without storing passwords."""
import argparse
import getpass
import json
import hashlib
from datetime import datetime,timezone
from pathlib import Path

from mlv2.core import read,save_new
from mlv2.pilot import Pilot,schedule
from mlv2.transport import LabTransport as SSHTransport


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--engine-source',type=Path,required=True)
    p.add_argument('--max-runs',type=int,default=7)
    p.add_argument('--retry-run',help='Explicit uncertain run to retry with a new ID; original evidence stays intact')
    p.add_argument('--retry-session',help='Session of the uncertain parent run')
    args=p.parse_args()
    if args.max_runs<1:p.error('max-runs must be positive')
    planned=schedule()
    if args.retry_run:
        if not args.retry_session:p.error('retry-run requires retry-session')
        matches=[item for item in planned if item['run_id']==args.retry_run and item['session_id']==args.retry_session]
        if len(matches)!=1:p.error('Retry run must identify exactly one scheduled run')
        original=matches[0]
        result=read(args.data_root/'trial-logs'/original['session_id']/original['run_id']/'RESULT.json')
        if result['valid']:p.error('Valid runs cannot be silently replaced')
        attempt=1
        while (args.data_root/'registry'/original['session_id']/(original['run_id']+f'-retry{attempt}')).exists():attempt+=1
        planned=[{**original,'run_id':original['run_id']+f'-retry{attempt}'}]
    file=args.data_root/'pilot-schedule.json'
    if args.retry_run:
        save_new(args.data_root/'retry-plans'/(planned[0]['run_id']+'.json'),
                 {'parent_run_id':args.retry_run,'attempt':planned[0]})
    elif file.exists():
        if read(file)!=planned:raise ValueError('Saved schedule differs')
    else:save_new(file,planned)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    source_root=Path(__file__).parent
    snapshot=args.data_root/'execution-snapshots'/stamp
    snapshot.mkdir(parents=True,exist_ok=False)
    manifest={}
    for source in [Path(__file__),*sorted((source_root/'mlv2').glob('*.py'))]:
        relative=source.relative_to(source_root)
        target=snapshot/relative;target.parent.mkdir(parents=True,exist_ok=True)
        data=source.read_bytes();target.write_bytes(data)
        manifest[relative.as_posix()]=hashlib.sha256(data).hexdigest()
    save_new(snapshot/'manifest.json',manifest)
    profile=read(Path(__file__).parent/'config/srv01.json')
    transport=SSHTransport(getpass.getpass('VM SSH password (not logged): '))
    pilot=Pilot(transport,args.data_root,args.engine_source,profile)
    completed=0
    try:
        for item in planned:
            result=args.data_root/'trial-logs'/item['session_id']/item['run_id']/'RESULT.json'
            if result.exists():continue
            pilot.run(item)
            completed+=1
            if completed>=args.max_runs:break
    finally:transport.close()
    print(json.dumps({'state':'batch_finished','new_runs':completed,'planned_runs':len(planned)}),flush=True)


if __name__=='__main__':main()

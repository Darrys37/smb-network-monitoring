"""Retry uncertain first-pass runs under new IDs; preserve original attempts."""
import argparse,getpass,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from mlv2.core import read,save_new
from mlv2.pilot import Pilot,schedule
from mlv2.transport import SSHTransport


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--engine-source',type=Path,required=True)
    args=parser.parse_args()
    source_root=Path(__file__).parent
    items=schedule()[:7]
    results=[read(args.data_root/'trial-logs'/x['session_id']/x['run_id']/'RESULT.json') for x in items]
    pending=[x for x,r in zip(items,results) if not r['valid']]
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    snapshot=args.data_root/'execution-snapshots'/('retry-'+stamp)
    snapshot.mkdir(parents=True,exist_ok=False)
    hashes={}
    for p in [Path(__file__),*sorted((source_root/'mlv2').glob('*.py'))]:
        relative=p.relative_to(source_root);target=snapshot/relative;target.parent.mkdir(parents=True,exist_ok=True)
        data=p.read_bytes();target.write_bytes(data);hashes[relative.as_posix()]=hashlib.sha256(data).hexdigest()
    save_new(snapshot/'manifest.json',hashes)
    if not pending:
        print('No uncertain first-pass trials');return
    transport=SSHTransport(getpass.getpass('VM SSH password (not logged): '))
    pilot=Pilot(transport,args.data_root,args.engine_source,read(source_root/'config/srv01.json'))
    try:
        for item in pending:
            parent=item['run_id'];attempt=1
            while (args.data_root/'registry'/item['session_id']/(parent+f'-retry{attempt}')).exists():attempt+=1
            retry={**item,'run_id':parent+f'-retry{attempt}'}
            save_new(args.data_root/'retry-plans'/(retry['session_id']+'-'+retry['run_id']+'.json'),
                     {'parent_run_id':parent,'attempt':retry,'reason':'Original timing/operation uncertainty; no raw data replaced'})
            pilot.run(retry)
    finally:transport.close()
    print(json.dumps({'state':'retry_batch_finished','attempted':len(pending)}),flush=True)


if __name__=='__main__':main()

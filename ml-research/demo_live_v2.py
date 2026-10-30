"""Collect one label-free observation and display expert + candidate suggestions."""
import argparse
from datetime import datetime,timezone
import getpass
import hashlib
import json
from pathlib import Path

from demo_v2 import assess
from mlv2.collector import collect
from mlv2.core import read,save_new
from mlv2.transport import SSHTransport


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',type=Path,default=Path(__file__).parent/'config/srv01.json')
    parser.add_argument('--engine-source',type=Path,required=True)
    parser.add_argument('--candidate-db',type=Path,required=True)
    parser.add_argument('--output-root',type=Path,required=True)
    args=parser.parse_args()
    # Fail before collection if the model path is wrong. No training occurs here.
    if not args.candidate_db.is_file():parser.error('Candidate database is missing')
    run='demo-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    transport=SSHTransport(getpass.getpass('VM SSH password (not logged): '))
    try:
        observation=collect(read(args.profile),args.engine_source,'shadow-v2',run,transport.runner)
    finally:
        transport.close()
    out=args.output_root/run
    save_new(out/'observation.json',observation)
    comparison=assess(observation,args.candidate_db,args.engine_source)
    comparison['mode']='live_shadow_candidate_comparison'
    comparison['candidate_sha256']=hashlib.sha256(args.candidate_db.read_bytes()).hexdigest()
    comparison['observation_sha256']=hashlib.sha256((out/'observation.json').read_bytes()).hexdigest()
    save_new(out/'comparison.json',comparison)
    print(json.dumps({'output_dir':str(out),'expert':comparison['expert_diagnoses'],
                      'ml_suggestions':comparison['ml_suggestions'],
                      'scope_gate_passed':comparison['scope_gate_passed']},indent=2,ensure_ascii=False))


if __name__=='__main__':main()

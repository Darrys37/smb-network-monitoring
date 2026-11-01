"""Bounded lab demo: healthy -> injected fault -> recovery, expert + ML side by side."""
import argparse
from datetime import datetime,timezone
import getpass,hashlib,json,os
from pathlib import Path

from candidate_v2 import load_database
from shadow_runtime import CandidateRuntime
from mlv2.core import LABELS,read,save_new,sha
from mlv2.features import FEATURES,CATEGORICAL,NUMERIC
from mlv2.pilot import Pilot
from mlv2.transport import LabTransport


def validate_release(release_file,profile):
    release=read(release_file)
    if release.get('status')!='INITIAL_VM_ML_RELEASE_VERIFIED':raise ValueError('Release has not passed final review')
    candidate=Path(release['candidate_db'])
    if sha(candidate)!=release['candidate_sha256']:raise ValueError('Released model artifact changed')
    metadata,rules=load_database(candidate)
    if metadata['profile']!=profile or profile['target_ip']!='192.168.56.20' or profile['host_id']!='10683':
        raise ValueError('Demo is limited to the reviewed SRV01 lab profile')
    if metadata['features']!=FEATURES or metadata['categorical']!=CATEGORICAL or metadata['numeric']!=NUMERIC:
        raise ValueError('Model feature contract differs')
    if not rules['CART']:raise ValueError('Released CART model is empty')
    return candidate


class DemoPilot(Pilot):
    def __init__(self,*args,candidate_db,**kwargs):
        super().__init__(*args,**kwargs);self.candidate_db=candidate_db
        # One verified read-only candidate snapshot for the whole demo session.
        self.runtime=CandidateRuntime(candidate_db,self.engine,expected_sha256=sha(candidate_db))

    def snapshot(self,item):
        observation=super().snapshot(item)
        output=self.runtime.assess(observation)
        output['mode']='explicit_lab_demo_shadow'
        output['candidate_sha256']=self.runtime.candidate_sha256
        output['observation_sha256']=sha(self.root/'observations'/item['session_id']/item['run_id']/(observation['window_id']+'.json'))
        save_new(self.root/'comparisons'/item['session_id']/item['run_id']/(observation['window_id']+'.json'),output)
        print(json.dumps({'run_id':item['run_id'],'expert':[{key:row[key] for key in ['rule_id','status','reasoning']} for row in output['expert_diagnoses']],
            'ml_suggestions':output['ml_suggestions']},indent=2,ensure_ascii=True),flush=True)
        return observation


def main():
    module=Path(__file__).resolve().parent;project=module.parent
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release',type=Path,default=project/'evidence/ml-v2/ML_RELEASE.json')
    parser.add_argument('--profile',type=Path,default=module/'config/srv01.json')
    parser.add_argument('--engine-source',type=Path,default=project/'diagnosis-engine')
    parser.add_argument('--fault',choices=sorted(LABELS-{'healthy'}),default='nginx_stopped')
    parser.add_argument('--output-root',type=Path,default=project/'evidence/ml-v2/demos')
    args=parser.parse_args()
    profile=read(args.profile);candidate=validate_release(args.release,profile)
    transport=LabTransport(getpass.getpass('VM SSH password (not logged): '))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    session='demo-'+stamp
    awake=None
    if os.name=='nt':
        import ctypes
        awake=ctypes.windll.kernel32.SetThreadExecutionState
        awake(0x80000001)
    try:
        pilot=DemoPilot(transport,args.output_root,args.engine_source,profile,candidate_db=candidate)
        baseline=pilot.wait_baseline()
        save_new(args.output_root/'checks'/session/'before.json',baseline)
        pilot.snapshot({'session_id':session,'run_id':'before'})
        result=pilot.run({'session_id':session,'run_id':'fault','label':args.fault})
        pilot.snapshot({'session_id':session,'run_id':'after'})
        save_new(args.output_root/'checks'/session/'result.json',result)
        print(json.dumps({'status':'DEMO_VERIFIED' if result['valid'] else 'DEMO_REQUIRES_REVIEW',
                          'session_id':session,'output_root':str(args.output_root)},ensure_ascii=True))
        if not result['valid']:raise SystemExit(2)
    finally:
        transport.close()
        if awake is not None:awake(0x80000000)


if __name__=='__main__':main()

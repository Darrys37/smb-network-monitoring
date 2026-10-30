"""Compare expert diagnoses and candidate ML suggestions on one saved observation."""
import argparse
import dataclasses
import hashlib
import json
from pathlib import Path
import sys

from candidate_v2 import ABSTAIN,cart_predict,fp_predict,discrete_row,load_database
from mlv2.core import read,save_new
from mlv2.features import extract,CATEGORICAL,NUMERIC,FEATURES


def assess(observation, database, engine_source):
    metadata,rules=load_database(database)
    if metadata['features']!=FEATURES or metadata['categorical']!=CATEGORICAL or metadata['numeric']!=NUMERIC:
        raise ValueError('Candidate feature contract mismatch')
    features=extract(observation)
    row=discrete_row(features,CATEGORICAL,NUMERIC)
    sys.path.insert(0,str(engine_source))
    from models import EvidenceRecord
    from roadmap_rules import diagnose_roadmap
    p=observation['profile']
    expert=diagnose_roadmap(p['host_id'],p['target_ip'],[EvidenceRecord(**e) for e in observation['evidence']],
        control=p['control_ip'],http_observer=p['observer'],dns_name=p['dns_name'],
        dns_observer=p['observer'],control_ip=p['dns_control_ip'],http_service=p['http_service'],now=observation['decision_time'])
    # Explicit scope gate for the current single-host candidate dataset. Further
    # hosts and simultaneous faults require separate data and evaluation.
    scope=(p==metadata['profile'])
    missing_core=[key for key in ['ping_status','tcp80_status','tcp10050_status','control_ping_status'] if row[key]=='unknown']
    if scope and not missing_core:
        ml={'CART':cart_predict(rules['CART'],row),'FP-Growth':fp_predict(rules['FP-Growth'],row)}
    else:
        ml={name:{'label':ABSTAIN,'reason':'Outside pilot profile or incomplete core probes'} for name in rules}
    return {'mode':'offline_candidate_comparison','decision_time':observation['decision_time'],
            'expert_diagnoses':[dataclasses.asdict(value) for value in expert],
            'features':features,'discrete_features':row,'ml_suggestions':ml,
            'scope_gate_passed':scope and not missing_core,
            'limitations':['Single-fault pilot on SRV01; no generalization claim',
                          'Association confidence and leaf fraction describe training data',
                          'No automatic remediation, alert mutation or rule activation']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observation',type=Path,required=True)
    parser.add_argument('--candidate-db',type=Path,required=True)
    parser.add_argument('--engine-source',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    output=assess(read(args.observation),args.candidate_db,args.engine_source)
    output['provenance']={key:{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        for key,path in [('observation',args.observation),('candidate_db',args.candidate_db)]}
    if args.output:
        save_new(args.output,output)
    print(json.dumps(output,indent=2,ensure_ascii=False,allow_nan=False))


if __name__=='__main__':main()

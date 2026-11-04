"""Read the current system state without starting a second worker or changing events."""
from contextlib import closing
import argparse
import json
from pathlib import Path
import time

from monitoring.correlation import correlate
from monitoring.store import Store
from monitoring.topology import Topology


def report(root):
    config=json.loads((root/'config/lab.json').read_text())
    store=Store(root/'runtime/monitoring.sqlite')
    with closing(store.connect()) as db:
        latest=[]
        for profile in config['profiles']:
            row=db.execute('SELECT observation_json,assessment_json FROM diagnostics WHERE profile_id=? ORDER BY decision_clock DESC,rowid DESC LIMIT 1',(profile['profile_id'],)).fetchone()
            if row:latest.append({'node':profile['node'],'observation':json.loads(row[0]),'assessment':json.loads(row[1])})
    now=int(time.time())
    return {'report_clock':now,'counts':store.counts(),'zabbix_cursor':store.cursor('zabbix'),'node_states':store.node_states(),
            'correlation':correlate(store.events(),Topology(config['topology']),store.node_states(),now,
                                    window_seconds=30,max_age=180),'latest_diagnostics':latest,'events':store.events()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json',action='store_true')
    args=parser.parse_args()
    result=report(Path(__file__).resolve().parent)
    if args.json:print(json.dumps(result,ensure_ascii=True,indent=2))
    else:
        corr=result['correlation']
        print(f"Active events: {corr['active_problem_events']} | Incident groups: {corr['emitted_groups']} | Suppressed dependent alerts: {corr['suppressed_events']}")
        print('Informational notices retained:',corr.get('active_notice_events',0))
        print('Raw events retained:',result['counts']['events'],'| Pending diagnosis jobs:',result['counts']['pending_jobs'])
        for group in corr['groups']:
            print('ROOT',group['root_node'],'|',group['cause_group'],'| alerts:',len(group['members']))
        for row in result['latest_diagnostics']:
            print(row['node'],json.dumps(row['assessment']['feature_vector']['features']))
            for diagnosis in row['assessment']['diagnoses']:
                if diagnosis['status']=='matched':print(' ',diagnosis['rule_id'],diagnosis['reasoning'])

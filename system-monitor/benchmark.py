"""Synthetic algorithm replay benchmark; this does not emulate real host/network load."""
import argparse
import json
from pathlib import Path
import platform
import statistics
import sys
import time

from monitoring.correlation import correlate
from monitoring.topology import Topology


def benchmark():
    rows=[]
    for size in (100,1000,10000):
        nodes={'gateway':{'type':'gateway','parents':[]}}
        nodes.update({f'host-{i}':{'type':'host','parents':['gateway'],'dependency_basis':'synthetic direct dependency'} for i in range(size)})
        events=[{'source':'benchmark','event_id':'0','clock':1000,'node':'gateway','kind':'reachability','state':'problem','key':'gateway'}]
        events.extend({'source':'benchmark','event_id':str(i+1),'clock':1001+i%8,'node':f'host-{i}','kind':'http_connectivity','state':'problem','key':f'host-{i}'} for i in range(size))
        states={'gateway':{'status':'down','observed_at':1010,'down_since':1000}}
        for mode in ('without_topology_suppression','with_topology_suppression'):
            graph=Topology({'version':'synthetic-'+mode,'nodes':nodes,**({'dependent_kinds':[]} if mode.startswith('without') else {})})
            durations=[]
            for _ in range(5):
                start=time.perf_counter();result=correlate(events,graph,states,1010);durations.append((time.perf_counter()-start)*1000)
            assert result['raw_unique_events']==size+1
            assert result['emitted_groups']==(size+1 if mode.startswith('without') else 1)
            rows.append({'child_nodes':size,'events':size+1,'mode':mode,'groups':result['emitted_groups'],
                         'suppressed':result['suppressed_events'],'median_ms':statistics.median(durations),'min_ms':min(durations),'max_ms':max(durations)})
    return {'scope':'Synthetic in-process correlation replay only; no Zabbix, SSH, SQLite ingestion, live network throughput or production accuracy claim',
            'python':sys.version,'platform':platform.platform(),'repetitions':5,'rows':rows}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=benchmark();args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as out:json.dump(result,out,indent=2)
    print(json.dumps(result,indent=2))

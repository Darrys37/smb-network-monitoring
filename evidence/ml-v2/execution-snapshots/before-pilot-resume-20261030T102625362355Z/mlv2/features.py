"""Whitelist features from observations; labels/IDs/times never become predictors."""
import math

from .core import validate_observation

CATEGORICAL=['ping_status','tcp80_status','tcp10050_status','local_http_status',
             'dns_status','agent_status','control_ping_status']
NUMERIC=['cpu_percent','ram_percent','cpu_mean','cpu_coverage_seconds','cpu_max_gap_seconds']
FEATURES=CATEGORICAL+NUMERIC


def finite(value):
    if isinstance(value,bool):return None
    try:result=float(value)
    except (TypeError,ValueError):return None
    return result if math.isfinite(result) else None


def extract(observation):
    validate_observation(observation)
    p=observation['profile'];now=observation['decision_time']

    def latest(kind,target,**filters):
        rows=[e for e in observation['evidence'] if e['check_type']==kind and e['target']==target
              and all(e['result'].get(k)==v for k,v in filters.items())]
        if not rows:return None
        row=max(rows,key=lambda r:r['collected_at'])
        return row['result'] if 0<=now-row['collected_at']<=180 else None

    def status(result,allowed):
        return result['status'] if result and result.get('status') in allowed else 'unknown'

    def metric(key):
        result=latest('metric',p['host_id'],key=key)
        if not result or result.get('status')!='success' or result.get('units')!='%':return None
        clock=result.get('sample_clock');value=finite(result.get('value'))
        if type(clock) is not int or not 0<=now-clock<=180 or value is None or not 0<=value<=100:return None
        return value

    local=latest('local_http',p['target_ip'],observer=p['observer'],port=80,path='/')
    local_status='unknown'
    if p['http_service']=='absent':local_status='not_applicable'
    elif local and local.get('local_address_verified') is True:
        if local.get('status')=='success' and local.get('http_status')==200:local_status='http_200'
        elif local.get('status')=='failed' and local.get('http_status')!=200:local_status='failed'
    agent=latest('agent_metric',p['host_id'],key='agent.ping')
    agent_status=status(agent,{'success','no_data'})
    if agent_status=='success' and (type(agent.get('sample_clock')) is not int or not 0<=now-agent['sample_clock']<=180):
        agent_status='unknown'
    row={
        'ping_status':status(latest('ping',p['target_ip']),{'success','no_reply'}),
        'tcp80_status':status(latest('tcp',p['target_ip'],port=80),{'success','refused','timeout'}),
        'tcp10050_status':status(latest('tcp',p['target_ip'],port=10050),{'success','refused','timeout'}),
        'local_http_status':local_status,
        'dns_status':status(latest('dns',p['dns_name'],observer=p['observer']),{'success','timeout','nxdomain','no_answer','dns_error'}),
        'agent_status':agent_status,
        'control_ping_status':status(latest('ping',p['control_ip']),{'success','no_reply'}),
        'cpu_percent':metric('system.cpu.util'),'ram_percent':metric('vm.memory.util'),
        'cpu_mean':None,'cpu_coverage_seconds':None,'cpu_max_gap_seconds':None,
    }
    history=latest('cpu_history',p['host_id'],key='system.cpu.util')
    if history and history.get('status')=='success' and history.get('units')=='%':
        samples=history.get('samples',[])
        if not isinstance(samples,list) or any(not isinstance(s,dict) for s in samples):return row
        clocks=[s.get('clock') for s in samples];values=[finite(s.get('value')) for s in samples]
        valid=(len(samples)>=3 and all(type(c) is int and 0<=now-c<=480 for c in clocks)
               and all(v is not None and 0<=v<=100 for v in values)
               and all(b>a for a,b in zip(clocks,clocks[1:])))
        if valid:
            span=clocks[-1]-clocks[0];gap=max(b-a for a,b in zip(clocks,clocks[1:]))
            row['cpu_coverage_seconds']=span;row['cpu_max_gap_seconds']=gap
            if span>=240 and gap<=120 and now-clocks[-1]<=180:row['cpu_mean']=sum(values)/len(values)
    return row

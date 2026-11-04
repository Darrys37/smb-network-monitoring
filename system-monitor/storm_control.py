"""Admin-only synthetic alert channels; these represent injected alerts, not extra VMs."""
import argparse
import json
from pathlib import Path
import requests
import time
from dotenv import dotenv_values


def set_value(value):
    if type(value) is not int or value not in {0,1}:raise ValueError('Expected 0 or 1')
    root=Path(__file__).resolve().parent
    provisioned=json.loads((root/'config/provisioned.json').read_text())
    engine=root.parent/'diagnosis-engine'
    url=dotenv_values(engine/'.env')['ZABBIX_URL']
    token=dotenv_values(engine/'.env.admin')['ZABBIX_ADMIN_API_TOKEN']
    items=[identity for key,identity in provisioned['items'].items() if key.startswith('SRV01-Routed:diag.storm[')]
    if len(items)!=20:raise ValueError('Unexpected synthetic channel count')
    started=int(time.time())
    response=requests.post(url,headers={'Authorization':'Bearer '+token},json={'jsonrpc':'2.0','method':'history.push',
        'params':[{'itemid':identity,'value':value} for identity in items],'id':90001},timeout=8)
    response.raise_for_status();data=response.json()
    result=data.get('result',{})
    accepted=sum('error' not in row for row in result.get('data',[]))
    if result.get('response')!='success' or accepted!=20:raise RuntimeError('Some synthetic values were rejected')
    return {'synthetic_channels':20,'value':value,'accepted':accepted,'started_clock':started,'completed_clock':int(time.time()),'label':'Injected alerts only; not 20 independent physical faults'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('value',type=int,choices=[0,1]);args=parser.parse_args()
    print(json.dumps(set_value(args.value)))

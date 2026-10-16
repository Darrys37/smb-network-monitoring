"""Export numeric history and all accessible trigger events for recorded trial windows."""
import csv
from datetime import datetime
import json
from pathlib import Path
import sys
sys.path.insert(0,'/home/phat/do-an/diagnosis-engine')
from zabbix_client import call_api

root=Path(sys.argv[1])
baseline=Path('/home/phat/do-an/evidence/week4/baseline-20261016T162549Z')
config=json.loads((baseline/'effective-config-start.json').read_text())
for folder in sorted(root.glob('R[1-6]-0[123]*')):
    if not (folder/'fault.log').exists() or not (folder/'run.json').exists():
        continue
    run=json.loads((folder/'run.json').read_text())
    if run['status'] in ('preflight','waiting_for_fault_and_event','diagnosing',
        'waiting_external_http_probe','waiting_external_dns_probe','waiting_recovery'):
        continue
    start=int(datetime.fromisoformat(run['watch_start_utc']).timestamp())
    end=int(datetime.fromisoformat(run['finished_at_utc']).timestamp())
    if (folder/'window-history.csv').exists():
        continue
    events=call_api('event.get',{'hostids':['10084','10683','10684'],
        'source':0,'object':0,'time_from':start,'time_till':end,
        'output':'extend','selectHosts':['hostid','host','name'],
        'sortfield':['eventid'],'sortorder':'ASC','limit':10000},150)
    if len(events)>=10000: raise RuntimeError('Event export may be truncated')
    (folder/'all-trigger-events.json').write_text(json.dumps(events,indent=2)+'\n')
    with (folder/'window-history.csv').open('x',newline='') as out:
        w=csv.DictWriter(out,fieldnames=['hostid','key','itemid','clock','ns','value'])
        w.writeheader()
        count=0
        for item in config['items']:
            if item['value_type'] not in ('0','3'): continue
            for lower in range(start,end+1,3600):
                rows=call_api('history.get',{'itemids':[item['itemid']],
                    'history':int(item['value_type']),'time_from':lower,
                    'time_till':min(end,lower+3599),'output':'extend',
                    'sortfield':['clock','ns'],'sortorder':'ASC','limit':10000},151)
                if len(rows)>=10000: raise RuntimeError('History export may be truncated')
                for row in rows:
                    w.writerow({'hostid':item['hostid'],'key':item['key_'],
                        'itemid':item['itemid'],'clock':row['clock'],
                        'ns':row['ns'],'value':row['value']})
                count+=len(rows)
    (folder/'window-export.json').write_text(json.dumps({'start_epoch':start,'end_epoch':end,
        'history_rows':count,'trigger_events':len(events),
        'note':'Watch window includes preflight; independent fault/rollback timestamps define measurement intervals.'},indent=2)+'\n')
    print(folder.name,count,'history rows',len(events),'trigger events',flush=True)

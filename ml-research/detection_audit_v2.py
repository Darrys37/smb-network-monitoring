"""Audit Zabbix problem-event coverage separately from classifier accuracy."""
import argparse,csv,json
from pathlib import Path
from collections import defaultdict
from statistics import mean
from mlv2.core import read,sha


def markers(log,prefix):
    return [int(line.split()[1]) for line in log.splitlines() if line.startswith(prefix+' ')]


def build_intervals(evaluation):
    manifest=read(evaluation/'manifest.json');output=[]
    for source in manifest['test_sources']:
        path=Path(source['path']);root=path.parents[3]
        if sha(path)!=source['sha256']:raise ValueError('Test observation changed before detection audit')
        reviews=[p for p in (root/'registry'/source['session_id']/source['run_id']).glob('review-*.json') if sha(p)==source['review_sha256']]
        if len(reviews)!=1:raise ValueError('Test review changed')
        review=read(reviews[0])
        if review['validity']!='valid' or len(review['labels'])!=1:raise ValueError('Single-fault independent test labels required')
        raw=root/'trial-logs'/source['session_id']/source['run_id']/'independent-logs.json'
        signatures=[r['sha256'] for r in review['references'] if r['original_name']=='independent-logs.json']
        if signatures!=[sha(raw)]:raise ValueError('Intervention logs changed')
        logs=read(raw);observation=read(path)
        starts=markers(logs['fault.log'],'FAULT_BEFORE')
        ends=markers(logs['rollback.log'],'ROLLBACK_BEFORE')
        if len(starts)!=1:raise ValueError('Ambiguous intervention start')
        end=min(ends) if ends else observation['decision_time']
        if end<starts[0]:raise ValueError('Invalid intervention interval')
        output.append({'session_id':source['session_id'],'run_id':source['run_id'],'label':review['labels'][0],
                       'start':starts[0],'end':end,'decision_time':observation['decision_time']})
    ordered=sorted(output,key=lambda row:row['start'])
    if any(a['end']>b['start'] for a,b in zip(ordered,ordered[1:])):raise ValueError('Interventions overlap')
    return output


def audit_events(intervals,events,mapping):
    rows=[]
    for interval in intervals:
        label=interval['label']
        if label not in mapping['related_trigger_ids']:raise ValueError('Unmapped diagnostic label')
        expected=set(mapping['related_trigger_ids'][label])
        significant=[event for event in events if int(event['value'])==1 and int(event['severity'])>=2]
        strict=[event for event in significant if interval['start']<=int(event['clock'])<=interval['end']]
        related=[event for event in strict if event['objectid'] in expected]
        by_observation=[event for event in related if int(event['clock'])<=interval['decision_time']]
        tolerant=[event for event in significant if event['objectid'] in expected and interval['start']-1<=int(event['clock'])<=interval['end']+1]
        delta=min((int(event['clock'])-interval['start'] for event in related),default=None)
        rows.append({**interval,'configured_related_triggers':len(expected),
            'related_detected_strict':bool(related),'related_detected_by_selected_observation':bool(by_observation),
            'related_detected_with_1s_boundary_tolerance':bool(tolerant),
            'first_related_event_clock_delta_seconds':delta,
            'related_event_ids':[event['eventid'] for event in related],
            'significant_event_ids':[event['eventid'] for event in strict],
            'boundary_ambiguous_event_ids':[event['eventid'] for event in tolerant if event not in related]})
    groups=defaultdict(list)
    for row in rows:groups[row['label']].append(row)
    summary={}
    for label,group in groups.items():
        delays=[row['first_related_event_clock_delta_seconds'] for row in group if row['first_related_event_clock_delta_seconds'] is not None]
        summary[label]={'runs':len(group),'configured_related_triggers':group[0]['configured_related_triggers'],
            'related_detected_strict':sum(row['related_detected_strict'] for row in group),
            'related_detected_by_selected_observation':sum(row['related_detected_by_selected_observation'] for row in group),
            'mean_first_related_event_clock_delta_seconds':mean(delays) if delays else None,
            'runs_with_any_significant_problem_event':sum(bool(row['significant_event_ids']) for row in group)}
    return rows,summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evaluation',type=Path,required=True);p.add_argument('--events',type=Path,required=True)
    p.add_argument('--inventory',type=Path,required=True);p.add_argument('--mapping',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    mapping=read(args.mapping);inventory=read(args.inventory);export=read(args.events)
    if mapping['inventory_sha256']!=sha(args.inventory):raise ValueError('Trigger inventory mapping changed')
    enabled={trigger['triggerid'] for trigger in inventory['triggers'] if trigger['status']=='0'}
    if not set(trigger for ids in mapping['related_trigger_ids'].values() for trigger in ids)<=enabled:
        raise ValueError('Mapping references a disabled or absent trigger')
    intervals=build_intervals(args.evaluation)
    if export['host_id']!=mapping['host_id'] or export.get('truncated'):raise ValueError('Incomplete event export')
    if export['time_from']>min(row['start'] for row in intervals)-1 or export['time_till']<max(row['end'] for row in intervals)+1:
        raise ValueError('Event export does not cover all interventions')
    rows,summary=audit_events(intervals,export['events'],mapping)
    args.output.mkdir(parents=True,exist_ok=False)
    payload={'summary':summary,'rows':rows,'source_sha256':{name:sha(path) for name,path in [('events',args.events),('inventory',args.inventory),('mapping',args.mapping)]}}
    (args.output/'detection.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    with (args.output/'detection.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader()
        writer.writerows({key:';'.join(value) if isinstance(value,list) else value for key,value in row.items()} for row in rows)
    lines=['# Zabbix detection coverage','',
        'Problem events are read from event.get for the target host; this is separate from prediction accuracy.',
        '', '| Scenario | Runs | Configured related triggers | Detected during intervention | By selected observation |',
        '|---|---:|---:|---:|---:|']
    for label,value in sorted(summary.items()):lines.append(f"| {label} | {value['runs']} | {value['configured_related_triggers']} | {value['related_detected_strict']} | {value['related_detected_by_selected_observation']} |")
    lines+=['','Healthy has no expected fault trigger; significant events in intended-healthy windows are reported separately and require review before calling them false positives.',
        '', 'SRV01 has no dedicated DNS or ICMP trigger in the captured inventory. Network loss may produce HTTP/Agent/link symptoms. Related trigger events do not prove a unique root cause.',
        '', 'Strict integer-second boundaries and a separate 1-second-tolerance field are retained. Event clock delta is not a sub-second causal latency measurement.',
        '', 'The experiment invokes collection on a fixed fault schedule, regardless of Zabbix alerts. It does not by itself verify production alert-to-process dispatch latency.',
        '', '[event.get 7.0](https://www.zabbix.com/documentation/7.0/en/manual/api/reference/event/get) and [trigger.get 7.0](https://www.zabbix.com/documentation/7.0/en/manual/api/reference/trigger/get).','']
    (args.output/'DETECTION.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'status':'DETECTION_AUDITED','summary':summary},ensure_ascii=True))


if __name__=='__main__':main()

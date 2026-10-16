"""Review recorded official R1 trials against independent fault logs."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

root=Path(sys.argv[1])
scenario=sys.argv[2] if len(sys.argv)>2 else 'R1'
assert scenario in ('R1','R2','R3','R4','R5','R6')
rows=[]
for folder in sorted(root.glob(scenario+'-0[123]*')):
    if not (folder/'fault.log').exists():
        continue  # Preserve aborted, pre-fault attempts outside the valid-fault denominator.
    run=json.loads((folder/'run.json').read_text())
    fault=(folder/'fault.log').read_text()
    rollback=(folder/'rollback.log').read_text()
    def stamp(text, label):
        match=re.search(r'^'+label+r' (\S+)',text,re.M)
        return datetime.fromisoformat(match.group(1)).timestamp() if match else None
    fb,fa=stamp(fault,'FAULT_BEFORE'),stamp(fault,'FAULT_AFTER')
    rb,ra=stamp(rollback,'ROLLBACK_BEFORE'),stamp(rollback,'ROLLBACK_AFTER')
    independent_local=stamp(rollback,'RESTORATION_LOCAL_VERIFIED')
    fault_marker=('"operstate":"DOWN"' in fault if scenario=='R1' else
                  '\ninactive\n' in fault if scenario in ('R2','R3') else
                  'dport 53 counter' in fault and ' drop' in fault if scenario=='R4' else
                  'ip saddr 192.168.56.10 tcp dport 80' in fault and ' drop' in fault if scenario=='R5' else
                  'stress-ng --cpu 1 --cpu-load 100 --timeout 12m' in fault)
    valid_fault=fb is not None and fa is not None and fault_marker and fa>=fb
    diagnosis=json.loads((folder/'incident.json').read_text()) if (folder/'incident.json').exists() else None
    target=next((d for d in diagnosis['diagnoses'] if d['rule_id'].startswith(scenario+'_')),None) if diagnosis else None
    cli_text=(folder/'diagnosis.log').read_text() if (folder/'diagnosis.log').exists() else ''
    collection=re.search(r'^Collection started: (\d+)',cli_text,re.M)
    pc,rc=run.get('problem_clock'),run.get('recovery_clock')
    problems=[]
    if not valid_fault: problems.append('independent fault not verified')
    if pc is not None and (fb is None or rb is None or pc<fb or pc>rb): problems.append('problem clock outside fault window')
    if target and (not collection or fa is None or rb is None or not (fa<=int(collection.group(1))<rb)): problems.append('collection outside active fault')
    if run.get('postflight',{}).get('exit_code')!=0: problems.append('remote restoration check failed')
    if pc is not None and run.get('lifecycle_status')!='closed': problems.append('recovery not stored as closed')
    if scenario in ('R2','R5') and diagnosis:
        local=[e for e in diagnosis['evidence'] if e['check_type']=='local_http']
        if not local or not all(e['result'].get('observer')=='srv01' and e['target']=='192.168.56.20'
            and pc<=e['collected_at']<=int(collection.group(1)) and int(collection.group(1))-e['collected_at']<=180 for e in local):
            problems.append('local HTTP evidence observer, timing, or freshness invalid')
    if scenario=='R4' and diagnosis:
        dns=[e for e in diagnosis['evidence'] if e['check_type'] in ('dns','dns_control_ping')]
        if len(dns)!=2 or not all(e['result'].get('observer')=='cli01' and pc<=e['collected_at']<=int(collection.group(1))
            and int(collection.group(1))-e['collected_at']<=180 for e in dns):
            problems.append('DNS evidence observer, timing, or freshness invalid')
    tcp=[r['result'] for r in diagnosis['evidence'] if r['check_type']=='tcp' and r['result'].get('port')==80] if diagnosis else []
    raw_status=target['status'] if target else 'not_run'
    success=valid_fault and not problems and raw_status=='matched'
    tcp_agent=[r['result'] for r in diagnosis['evidence'] if r['check_type']=='tcp' and r['result'].get('port')==10050] if diagnosis else []
    row={'run_id':folder.name,'scenario':scenario,'source':'ca04071','config':'978b4f9','docs':'4cabeb0',
         'fault_valid':valid_fault,'fault_before_epoch':fb,'fault_after_epoch':fa,
         'problem_event_id':run.get('problem_event_id'),'problem_epoch':pc,
         'detection_delay_min_seconds':pc-fa if pc is not None and fa is not None else None,
         'detection_delay_max_seconds':pc-fb if pc is not None and fb is not None else None,
         'timestamp_resolution_seconds':1,
         'detection_lower_with_timestamp_rounding':pc-fa-1 if pc is not None and fa is not None else None,
         'detection_upper_with_timestamp_rounding':pc-fb+1 if pc is not None and fb is not None else None,
         'incident_id':run.get('incident_id'),'target_diagnosis_status':raw_status,
         'target_success_end_to_end':success,'cli_elapsed_seconds':run.get('cli',{}).get('elapsed_seconds'),
         'collection_start_epoch':int(collection.group(1)) if collection else None,
         'rollback_before_epoch':rb,'rollback_after_epoch':ra,
         'restoration_local_verified_epoch':independent_local,
         'recovery_event_id':run.get('recovery_event_id'),'recovery_epoch':rc,
         'recovery_recognition_min_seconds':rc-ra if rc is not None and ra is not None else None,
         'recovery_recognition_max_seconds':rc-rb if rc is not None and rb is not None else None,
         'event_interval_seconds':rc-pc if rc is not None and pc is not None else None,
         'lifecycle':run.get('lifecycle_status'),'tcp80_status':tcp[0].get('status') if tcp else None,
         'tcp80_errno':tcp[0].get('errno') if tcp else None,
         'tcp10050_status':tcp_agent[0].get('status') if tcp_agent else None,
         'extra_matched_rules':';'.join(d['rule_id'] for d in diagnosis['diagnoses'] if d['status']=='matched' and not d['rule_id'].startswith(scenario+'_')) if diagnosis else '',
         'review_issues':'; '.join(problems)}
    rows.append(row)
    (folder/'review.json').write_text(json.dumps(row,indent=2)+'\n')

if rows:
    with (root/(scenario+'-summary.csv')).open('w',newline='') as out:
        w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary={'reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'recorded_runs':len(rows),
             'valid_fault_runs':sum(r['fault_valid'] for r in rows),
             'target_matched_runs':sum(r['target_success_end_to_end'] for r in rows),
             'abstentions':sum(r['target_diagnosis_status']=='insufficient_evidence' for r in rows),
             'review_issues':[r['run_id'] for r in rows if r['review_issues']], 'runs':rows,
             'limitations':['Three trials in a small lab do not establish enterprise reliability.',
                'Detection times are bounded by independent before/after fault timestamps.',
                'Fault timestamps and event clock have one-second resolution; rounding-aware bounds add a one-second margin at both ends and do not include unmeasured clock error.',
                'Event interval is not actual downtime; CLI elapsed includes API/evidence/rules/storage.',
                'Fault timers and operator rollback are separate from the diagnosis engine; actual logs define each run.',
                'Other rules with insufficient evidence are retained and are not counted as healthy negatives.']}
    (root/(scenario+'-summary.json')).write_text(json.dumps(summary,indent=2)+'\n')
    md=['# Kết quả các lượt '+scenario+' chính thức','',
        f'{summary["recorded_runs"]} lượt đã lưu; {summary["valid_fault_runs"]} fault hợp lệ; {summary["target_matched_runs"]} lượt luật mục tiêu matched với hồ sơ qua kiểm tra.','',
        '| Run | Problem → Recovery | Incident | Luật mục tiêu | Detection (s) | CLI elapsed (s) | Review |',
        '|---|---|---:|---|---|---:|---|']
    for r in rows:
        elapsed=f'{r["cli_elapsed_seconds"]:.3f}' if r['cli_elapsed_seconds'] is not None else 'NA'
        md.append(f'| {r["run_id"]} | {r["problem_event_id"]} → {r["recovery_event_id"]} | {r["incident_id"]} | {r["target_diagnosis_status"]} | {r["detection_delay_min_seconds"]}–{r["detection_delay_max_seconds"]} | {elapsed} | {r["review_issues"] or "Đã đối chiếu"} |')
    md+=['','Raw fault/rollback logs, problem/recovery API JSON, CLI logs, SQLite-derived report và review.json nằm trong từng thư mục Run ID. Không ghi đè các kết quả không đạt hoặc insufficient_evidence.','',
           'Timestamp gây lỗi và event clock có độ phân giải một giây. Các khoảng trong bảng là phép trừ theo clock đã lưu; CSV/JSON có thêm biên ±1 giây để thể hiện sai số lượng tử timestamp, chưa bao gồm sai số đồng bộ giờ chưa đo chính xác.', '',
           'Đây là kết quả ba lượt trên lab nhỏ. Không suy ra độ tin cậy dài hạn. Khoảng problem–recovery không phải downtime thật; CLI elapsed gồm cả API, thu bằng chứng, luật và lưu dữ liệu. Các luật khác thiếu bằng chứng vẫn được giữ nguyên.']
    (root/(scenario+'-summary.md')).write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))

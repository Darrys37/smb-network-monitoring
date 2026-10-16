"""Aggregate independently reviewed trials. Keep unsuccessful valid faults in denominator."""
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys

root = Path(sys.argv[1])
rows = []
aborted = []
for folder in sorted(root.glob('R[1-6]-0[123]*')):
    if (folder/'adjudication.json').exists():
        aborted.append({'run_id': folder.name, **json.loads((folder/'adjudication.json').read_text())})
    if (folder/'review.json').exists():
        row = json.loads((folder/'review.json').read_text())
        run = json.loads((folder/'run.json').read_text())
        row['detected'] = bool(run.get('detection'))
        row['engine_exit_code'] = run.get('cli', {}).get('exit_code')
        row['record_status'] = run['status']
        row['http_scope'] = run['http_scope']
        row['evidence_folder'] = folder.name
        for bound, key, margin in [('lower','min',-1),('upper','max',1)]:
            value=row.get('detection_delay_'+key+'_seconds')
            row.setdefault('detection_'+bound+'_with_timestamp_rounding', value+margin if value is not None else None)
        row.setdefault('timestamp_resolution_seconds',1)
        rows.append(row)

fields = list(dict.fromkeys(k for row in rows for k in row))
with (root/'all-trials.csv').open('w', newline='', encoding='utf-8') as out:
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

def stats(values):
    values = [v for v in values if v is not None]
    return {'n':len(values), 'min': min(values), 'median': statistics.median(values), 'max': max(values)} if values else {'n':0}

summary = {'generated_at_utc':datetime.now(timezone.utc).isoformat(), 'valid_fault_runs':sum(r['fault_valid'] for r in rows),
           'reviewed_runs':len(rows), 'aborted_attempts':aborted, 'scenarios':{},
           'formulas':{'detection_rate':'detected valid faults / all valid faults',
             'target_success_end_to_end':'valid faults with target matched and no review issues / all valid faults',
             'cli_elapsed':'wall monotonic time of API + collection + rules + SQLite; not pure inference time',
             'detection_bounds':'problem_clock minus fault_after / fault_before; add +/- 1 s for timestamp quantization',
             'recovery_bounds':'recovery_clock minus rollback_after / rollback_before; not actual downtime'},
           'limitations':['Three valid fault trials per class on one small lab.',
              'Baseline is 1806 seconds, not four hours; no engine false-positive rate can be inferred.',
              'No healthy negative dataset was defined, so specificity, TN-based accuracy, and false-positive rate are not estimated.',
              'R2/R5 not applicable under HTTP absent are excluded from negative counts.',
              'Secondary insufficient_evidence results remain abstentions, not healthy negatives.',
              'Clock quantization bounds do not measure residual NTP error; system clocks report synchronized.']}
md = ['# Tổng hợp thực nghiệm tuần 4', '',
      'Phiên bản source `ca04071`, config export `978b4f9`, phiếu thử `4cabeb0`. Cấu hình hiệu lực và hash được lưu trong baseline/freeze; công cụ ghi thử nằm ngoài engine.', '',
      '| Kịch bản | Fault hợp lệ | Phát hiện | Mục tiêu matched, hồ sơ đạt | Abstention mục tiêu | Detection median [min–max] s | CLI median [min–max] s |',
      '|---|---:|---:|---:|---:|---|---|']
for scenario in ('R1','R2','R3','R4','R5','R6'):
    group = [r for r in rows if r['scenario']==scenario and r['fault_valid']]
    if not group: continue
    result = {'valid_faults':len(group), 'detected':sum(r['detected'] for r in group),
      'target_success_end_to_end':sum(r['target_success_end_to_end'] for r in group),
      'target_abstentions':sum(r['target_diagnosis_status']=='insufficient_evidence' for r in group),
      'no_detection':sum(not r['detected'] for r in group),
      'engine_errors':sum(r['engine_exit_code'] not in (0,None) for r in group),
      'review_issues':{r['run_id']:r['review_issues'] for r in group if r['review_issues']},
      'detection_delay_lower_seconds':stats(r['detection_delay_min_seconds'] for r in group),
      'detection_delay_upper_seconds':stats(r['detection_delay_max_seconds'] for r in group),
      'cli_elapsed_seconds':stats(r['cli_elapsed_seconds'] for r in group),
      'recovery_recognition_lower_seconds':stats(r['recovery_recognition_min_seconds'] for r in group),
      'recovery_recognition_upper_seconds':stats(r['recovery_recognition_max_seconds'] for r in group),
      'run_ids':[r['run_id'] for r in group]}
    summary['scenarios'][scenario]=result
    def display(s):
        return f"{s['median']:.3f} [{s['min']:.3f}–{s['max']:.3f}]" if s['n'] else 'NA'
    md.append(f"| {scenario} | {len(group)} | {result['detected']}/{len(group)} | {result['target_success_end_to_end']}/{len(group)} | {result['target_abstentions']} | {display(result['detection_delay_lower_seconds'])} | {display(result['cli_elapsed_seconds'])} |")
    counts={}
    for row in group:
        path=root/row['run_id']/'incident.json'
        if not path.exists(): continue
        for diagnosis in json.loads(path.read_text())['diagnoses']:
            key=diagnosis['rule_id']
            counts.setdefault(key,{})
            status=diagnosis['status']
            counts[key][status]=counts[key].get(status,0)+1
    result['all_rule_status_counts']=counts

summary['complete_18_valid_faults']=len(rows)==18 and all(summary['scenarios'].get(s,{}).get('valid_faults')==3 for s in ('R1','R2','R3','R4','R5','R6'))
md += ['', 'Bảng trên dùng cận dưới clock đã lưu để mô tả detection. `all-trials.csv` giữ cả hai cận và biên làm tròn ±1 giây khi có; không gộp khoảng problem–recovery thành downtime. Mỗi thống kê có cỡ mẫu `n` trong JSON, đặc biệt khi thiếu detection/CLI.', '',
       'Lượt R5-03 bị hủy trước fault do giới hạn sử dụng ở bước duyệt lệnh. Giữ nguyên hồ sơ timeout và adjudication riêng; R5-03-retry1 là lượt fault thật tiếp theo. Không tính lần hủy vào mẫu số fault hợp lệ.', '',
       'Đối chiếu: từng thư mục Run ID chứa fault/rollback log, event API JSON, history CSV, CLI log và incident report. `review.json` là kết quả kiểm tra chéo thời gian, observer, scope, recovery và luật mục tiêu.', '',
       'Baseline mới: 30 phút 06 giây, 31 poll, 963 history rows / 28 items; không có problem mới trong cửa sổ đã kiểm tra. Đây là quan sát ngắn của Zabbix, không phải bằng chứng engine không báo sai.', '',
       'Các kết quả thiếu evidence của luật phụ được công bố trong `all_rule_status_counts` của JSON. Ví dụ R5-02 có R6 insufficient_evidence vì span mẫu CPU 239 giây, dưới ngưỡng 240 giây, dù không chủ động gây CPU cao. Giữ nguyên tiêu chí và kết quả; không coi thiếu evidence là healthy.', '',
       'Không có tập mẫu âm được định nghĩa; không báo specificity hoặc accuracy có TN. Tỷ lệ thành công ở đây chỉ xét luật mục tiêu trên các fault đã kiểm chứng. Ba lượt mỗi loại chưa đủ kết luận độ tin cậy dài hạn.', '']
(root/'experiment-summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(root/'TONG_HOP_THUC_NGHIEM_TUAN4.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k in ('valid_fault_runs','reviewed_runs','complete_18_valid_faults')},indent=2))

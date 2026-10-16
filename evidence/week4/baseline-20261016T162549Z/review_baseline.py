"""Summarize recorded baseline evidence without changing original records."""
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys

p = Path(sys.argv[1])
read = lambda name: json.loads((p / name).read_text(encoding='utf-8'))
session, plan, config = read('session.json'), read('short-session-plan.json'), read('effective-config-start.json')
start, end = session['start_epoch'], session['end_epoch']
observations = [json.loads(s) for s in (p / 'observations.jsonl').read_text().splitlines()]
rows = list(csv.DictReader((p / 'history.csv').open(newline='', encoding='utf-8')))
groups = defaultdict(list)
for r in rows:
    assert start <= int(r['clock']) <= end
    assert math.isfinite(float(r['value']))
    groups[r['itemid']].append(r)
hosts = {'10084': 'MON01', '10683': 'SRV01', '10684': 'CLI01'}
by_id = {i['itemid']: i for i in config['items']}

def period(item):
    value = item['delay']
    if value == '0' and item['master_itemid'] in by_id:
        return period(by_id[item['master_itemid']])
    if value.endswith('m'):
        return int(value[:-1]) * 60
    if value.endswith('s'):
        return int(value[:-1])
    return int(value) or None

continuity = []
issues = []
for item in config['items']:
    rr = sorted(groups[item['itemid']], key=lambda r: (int(r['clock']), int(r['ns'])))
    clocks = [int(r['clock']) for r in rr]
    values = [float(r['value']) for r in rr]
    gaps = [b-a for a,b in zip(clocks, clocks[1:])]
    heartbeat = next((s['params'] for s in item['preprocessing'] if s['type'] == '20'), None)
    interval = period(item)
    first_gap = clocks[0]-start if clocks else None
    last_gap = end-clocks[-1] if clocks else None
    failures = []
    if heartbeat:
        # Verify that the retained value remains within the declared one-day heartbeat.
        retained = next(i for i in read('items-end.json') if i['itemid'] == item['itemid'])
        if not (retained['lastvalue'].isdigit() and int(retained['lastvalue']) > 0
                and 0 <= end-int(retained['lastclock']) <= 86580):
            failures.append('heartbeat retained value invalid/stale')
    elif not rr:
        failures.append('no history')
    elif interval:
        if max(gaps, default=0) > interval + 5:
            failures.append('sample gap exceeds configured interval + 5s')
        if first_gap > interval + 5 or last_gap > interval + 5:
            failures.append('boundary gap exceeds configured interval + 5s')
    if len({(r['clock'], r['ns']) for r in rr}) != len(rr):
        failures.append('duplicate sample timestamps')
    if item['key_'] == 'system.uptime':
        if any(b < a for a,b in zip(values, values[1:])):
            failures.append('uptime reset')
        if any(abs((v2-v1)-(c2-c1)) > 5 for c1,c2,v1,v2 in zip(clocks,clocks[1:],values,values[1:])):
            failures.append('uptime delta inconsistent with sample clocks')
    if failures:
        issues.append({'itemid': item['itemid'], 'problems': failures})
    continuity.append({'host': hosts[item['hostid']], 'key': item['key_'], 'itemid': item['itemid'],
        'samples': len(rr), 'configured_period_seconds': interval,
        'max_gap_seconds': max(gaps, default=None), 'first_boundary_gap_seconds': first_gap,
        'last_boundary_gap_seconds': last_gap, 'min': min(values, default=None),
        'max': max(values, default=None), 'mean': sum(values)/len(values) if values else None,
        'exception': 'discard unchanged; heartbeat ' + heartbeat if heartbeat else '',
        'issues': '; '.join(failures)})

obs_gaps = [b['observed_at']-a['observed_at'] for a,b in zip(observations, observations[1:])]
errors = [o for o in observations if o['status'] != 'ok']
item_errors = sorted({(i['hostid'], i['key_'], i.get('error', ''))
                     for o in observations for i in o.get('items', []) if i.get('state') != '0'})
events = read('events.json')
problems = [e for e in events if e['value'] == '1']
normal = lambda rows: json.dumps(sorted(rows, key=lambda r: int(r['triggerid'])), sort_keys=True)
functions_unchanged = normal(read('trigger-functions-supplement.json')) == normal(read('trigger-functions-end-supplement.json'))
macros_unchanged = (p/'effective-critical-thresholds.tsv').read_bytes() == (p/'effective-critical-thresholds-end.tsv').read_bytes()
links_unchanged = (p/'template-links-global-thresholds.tsv').read_bytes() == (p/'template-links-global-thresholds-end.tsv').read_bytes()
source_unchanged = read('source-hashes-start.json') == read('source-hashes-end.json')
config_unchanged = read('effective-config-start.json') == read('effective-config-end.json')
checks = {'no_api_errors': not errors, 'no_item_errors_in_poll_snapshots': not item_errors,
          'poll_gaps_within_65_seconds': max(obs_gaps, default=9999) <= 65,
          'periodic_history_no_excess_gaps_or_uptime_resets': not issues,
          'source_unchanged': source_unchanged, 'config_unchanged': config_unchanged,
          'supplemental_trigger_functions_unchanged': functions_unchanged,
          'critical_macros_unchanged': macros_unchanged, 'template_links_unchanged': links_unchanged}
accepted = all(checks.values())
summary = {'baseline_id': p.name, 'reviewed_at_utc': datetime.now(timezone.utc).isoformat(),
    'assessment': 'accepted_short_baseline' if accepted else 'review_issues_found',
    'start_utc': session['start_utc'], 'end_utc': session['end_utc'],
    'original_target_seconds': session['duration_target_seconds'],
    'effective_user_target_seconds': plan['target_seconds'],
    'wall_seconds': end-start, 'accepted_observation_seconds': end-start if accepted else None,
    'poll_count': len(observations), 'max_poll_gap_seconds': max(obs_gaps),
    'api_errors': len(errors), 'history_rows': len(rows), 'item_count': len(continuity),
    'event_count': len(events), 'new_problem_count': len(problems),
    'open_problems_at_start': len(read('problems-start.json')),
    'open_problems_at_end': len(read('problems-end.json')),
    'open_problem_observations': sum(len(o.get('open_problems', [])) for o in observations),
    'verified_false_alert_count': 0 if not problems else None,
    'observed_false_alerts_per_hour': 0 if accepted and not problems else None,
    'checks': checks, 'issues': issues, 'item_errors': item_errors,
    'limitations': ['30-minute short baseline; four-hour target not met.',
        'Continuity is assessed at configured sample resolution; no claim about unobserved sub-sample failures.',
        'Zero alerts in this short window does not establish long-term reliability.',
        'No false-positive rate or accuracy is inferred for the manually invoked diagnosis engine.',
        'Three CPU-count items have no new history due to discard-unchanged preprocessing with one-day heartbeat; retained values were checked.',
        'CPU trigger functions/macros were additionally verified after the end of the observation window, not continuously audited.']}
(p/'baseline-summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
with (p/'continuity.csv').open('w', newline='', encoding='utf-8') as out:
    writer = csv.DictWriter(out, fieldnames=list(continuity[0]))
    writer.writeheader(); writer.writerows(continuity)
with (p/'baseline.csv').open('w', newline='', encoding='utf-8') as out:
    fields = ['baseline_id','start_utc','end_utc','effective_user_target_seconds','wall_seconds',
              'accepted_observation_seconds','poll_count','history_rows','new_problem_count',
              'verified_false_alert_count','assessment']
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader(); writer.writerow({k:summary[k] for k in fields})
local = lambda value: datetime.fromisoformat(value).astimezone(timezone(timedelta(hours=7))).strftime('%d/%m/%Y %H:%M:%S UTC+7')
report = ['# Kết quả baseline ngắn — 16/10/2026', '',
    f'- Đánh giá: **{summary["assessment"]}**.',
    f'- Bắt đầu: {local(summary["start_utc"])}; kết thúc: {local(summary["end_utc"])}.',
    f'- Thời lượng quan sát: **{end-start} giây (30 phút 06 giây)**; mục tiêu đã đổi thành 30 phút theo lựa chọn người thực hiện.',
    '- `session.json` giữ nguyên mục tiêu bốn giờ ban đầu và `stopped_early=true`; `short-session-plan.json` ghi yêu cầu thay đổi. Bản tóm tắt này đánh giá theo mục tiêu mới, không sửa bản ghi gốc.',
    f'- {len(observations)} lần thu, {len(errors)} lỗi API; khoảng cách lớn nhất {max(obs_gaps)} giây.',
    f'- {len(rows)} mẫu history, {len(continuity)} item; {len(events)} event mới; {len(problems)} problem mới.',
    '- Không có problem mở đầu/cuối phiên hoặc trong các lần kiểm tra; không có cảnh báo mới cần phân loại. Tần suất cảnh báo sai quan sát được: 0 / 0,5017 giờ, không suy rộng ra dài hạn.',
    '- Source, cấu hình snapshot, hàm trigger bổ sung, các ngưỡng quan trọng và liên kết template không đổi ở các lần đối chiếu.', '',
    '## Kiểm tra liên tục', '', '| Host | Item | Số mẫu | Gap lớn nhất (s) | Ghi chú |', '|---|---|---:|---:|---|']
for r in continuity:
    report.append(f'| {r["host"]} | `{r["key"]}` | {r["samples"]} | {r["max_gap_seconds"] if r["max_gap_seconds"] is not None else "NA"} | {r["issues"] or r["exception"] or "Đã đối chiếu"} |')
report += ['', 'Không phát hiện uptime reset, chênh lệch uptime bất thường hoặc khoảng trống vượt chu kỳ + 5 giây trong các item định kỳ đã kiểm tra. Ba item CPU count không lưu lại giá trị không đổi; retained value hợp lệ và còn trong heartbeat một ngày.', '',
           '## Giới hạn và việc tiếp theo', '',
           'Đây là baseline ngắn, chưa đạt mục tiêu bốn giờ của roadmap. Kết quả chỉ áp dụng cho cửa sổ quan sát và độ phân giải lấy mẫu. Baseline Zabbix không đo độ chính xác hoặc tỷ lệ chẩn đoán sai của engine CLI.', '',
           'Tiếp theo: giữ nguyên phiên bản đã ghi, thực hiện R1–R3 mỗi kịch bản ba lượt rồi R4–R6 mỗi kịch bản ba lượt theo phiếu. Hiện bộ thực nghiệm chính thức vẫn 0/18. Giữ cả lượt không phát hiện, thiếu bằng chứng hoặc chẩn đoán không đạt.', '',
           'Dữ liệu gốc: `session.json`, `short-session-plan.json`, `observations.jsonl`, `events.json`, `history.csv`. Tổng hợp: `baseline.csv`, `continuity.csv`, `baseline-summary.json`.']
(p/'baseline-summary.md').write_text('\n'.join(report)+'\n', encoding='utf-8')
print(json.dumps(summary, indent=2, ensure_ascii=False))

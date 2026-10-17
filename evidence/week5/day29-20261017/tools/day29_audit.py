"""Rebuild day 29 analytical data from immutable week 4 records. Standard library only."""
import csv, hashlib, json, re, statistics, sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT = Path(sys.argv[1])
OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
RAW = PROJECT/'evidence/week4/official-runs'
CLOSURE = PROJECT/'evidence/week4/closure-20261017'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def dump(name, value): (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
def table(name, rows):
    with (OUT/name).open('w', encoding='utf-8-sig', newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def stamp(folder, file, label):
    values=re.findall(r'^'+label+r' (\S+)', (folder/file).read_text(), re.M)
    assert len(values)==1, (folder.name,label)
    return int(datetime.fromisoformat(values[0]).timestamp())

verified={}
for base, manifest in [(RAW,'checksums-final.json'),(PROJECT/'evidence/week4/baseline-20261016T162549Z','checksums.json'),(CLOSURE,'checksums.json')]:
    hashes=read(base/manifest)
    for name, expected in hashes.items():
        assert hashlib.sha256((base/name).read_bytes()).hexdigest()==expected, name
    verified[str(base.relative_to(PROJECT)/manifest)]=len(hashes)
legacy=list(csv.DictReader((RAW/'all-trials.csv').open(encoding='utf-8-sig')))
assert len(legacy)==18 and len({r['run_id'] for r in legacy})==18
photos={p['event_id']:p for p in read(CLOSURE/'screenshots/screenshots-index.json')['event_screenshots']}
clean=[]; attempts=[]; counts=Counter()
for old in legacy:
    rid=old['run_id']; folder=RAW/rid
    run=read(folder/'run.json'); p=read(folder/'problem-after-recovery.json'); q=read(folder/'recovery.json'); report=read(folder/'incident.json'); review=read(folder/'review.json')
    assert run['run_id']==rid and run['scenario']==old['scenario']
    assert p['eventid']==old['problem_event_id']==str(run['problem_event_id'])==report['incident']['event_id']
    assert p['r_eventid']==q['eventid']==old['recovery_event_id']==report['recovery']['recovery_event_id']
    assert p['objectid']==q['objectid'] and p['value']=='1' and q['value']=='0'
    assert report['lifecycle_status']=='closed' and int(report['incident']['id'])==int(old['incident_id'])
    assert run['preflight']['exit_code']==run['cli']['exit_code']==run['postflight']['exit_code']==0
    assert review['fault_valid'] and not review['review_issues'] and not review['extra_matched_rules']
    fb=stamp(folder,'fault.log','FAULT_BEFORE'); fa=stamp(folder,'fault.log','FAULT_AFTER')
    rb=stamp(folder,'rollback.log','ROLLBACK_BEFORE'); ra=stamp(folder,'rollback.log','ROLLBACK_AFTER')
    local=stamp(folder,'rollback.log','RESTORATION_LOCAL_VERIFIED')
    pc=int(p['clock']); rc=int(q['clock'])
    collection=int(re.search(r'Collection started: (\d+)',(folder/'diagnosis.log').read_text()).group(1))
    assert fb<=fa<=pc<=collection<rb<=ra<=local<=rc, rid
    target=[d for d in report['diagnoses'] if d['rule_id'].startswith(old['scenario']+'_')]
    assert len(target)==1 and len(report['diagnoses'])==6
    counts.update(d['status'] for d in report['diagnoses'])
    image=photos[p['eventid']]; imagepath=CLOSURE/'screenshots'/image['file']
    assert imagepath.read_bytes().startswith(b'\xff\xd8\xff') and 'eventid='+p['eventid'] in image['url']
    ui_times=re.findall(r'\d{1,2}:\d{2}:\d{2} [AP]M', image['history_row'])[:2]
    expected=[datetime.fromtimestamp(t,timezone(timedelta(hours=7))).strftime('%I:%M:%S %p') for t in (pc,rc)]
    assert [s.zfill(11) for s in ui_times]==expected, (rid,ui_times,expected)
    history=list(csv.DictReader((folder/'window-history.csv').open()))
    assert history and len(history)==len({(x['itemid'],x['clock'],x['ns']) for x in history})
    assert {x['eventid'] for x in read(folder/'all-trigger-events.json')}=={p['eventid'],q['eventid']}
    row=dict(run_id=rid,scenario=old['scenario'],problem_event_id=p['eventid'],recovery_event_id=q['eventid'],incident_id=int(report['incident']['id']),fault_before_epoch=fb,fault_after_epoch=fa,problem_epoch=pc,rollback_before_epoch=rb,rollback_after_epoch=ra,recovery_epoch=rc,cli_elapsed_seconds=run['cli']['elapsed_seconds'],target_status=target[0]['status'],valid_fault=1,detected=1,engine_exit_code=run['cli']['exit_code'],review_issue_count=0,dt_lower_seconds=pc-fa,dt_upper_seconds=pc-fb,rr_lower_seconds=rc-ra,rr_upper_seconds=rc-rb,target_success=int(target[0]['status']=='matched'),collection_epoch=collection,local_restored_epoch=local,event_interval_seconds=rc-pc,timestamp_resolution_seconds=1,dt_quantized_lower_seconds=pc-fa-1,dt_quantized_upper_seconds=pc-fb+1,http_scope=run['http_scope'],screenshot=str(imagepath.relative_to(PROJECT)).replace('\\','/'),raw_folder=str(folder.relative_to(PROJECT)).replace('\\','/'))
    pairs={'fault_before_epoch':'fault_before_epoch','fault_after_epoch':'fault_after_epoch','problem_epoch':'problem_epoch','rollback_before_epoch':'rollback_before_epoch','rollback_after_epoch':'rollback_after_epoch','recovery_epoch':'recovery_epoch','cli_elapsed_seconds':'cli_elapsed_seconds','dt_lower_seconds':'detection_delay_min_seconds','dt_upper_seconds':'detection_delay_max_seconds','rr_lower_seconds':'recovery_recognition_min_seconds','rr_upper_seconds':'recovery_recognition_max_seconds'}
    for newkey,oldkey in pairs.items(): assert abs(row[newkey]-float(old[oldkey]))<1e-9,(rid,newkey)
    clean.append(row); attempts.append(dict(run_id=rid,scenario=old['scenario'],classification='valid_fault',included=1,replacement='',reason='Ground truth, event, report, recovery and screenshot joined'))
abort=read(RAW/'R5-03/adjudication.json')
assert abort['classification']=='aborted_before_fault' and not abort['include_in_valid_fault_denominator'] and not (RAW/'R5-03/fault.log').exists()
attempts.append(dict(run_id='R5-03',scenario='R5',classification=abort['classification'],included=0,replacement='R5-03-retry1',reason=abort['reason']))
assert len({r['problem_event_id'] for r in clean})==len({r['incident_id'] for r in clean})==18
metrics={'dt_lower_seconds':'detection_delay_lower_seconds','dt_upper_seconds':'detection_delay_upper_seconds','cli_elapsed_seconds':'cli_elapsed_seconds','rr_lower_seconds':'recovery_recognition_lower_seconds','rr_upper_seconds':'recovery_recognition_upper_seconds'}
summary=[]; previous=read(RAW/'experiment-summary.json')
for scenario in ['R1','R2','R3','R4','R5','R6']:
    group=[r for r in clean if r['scenario']==scenario]
    result=dict(scenario=scenario,n_valid=len(group),n_detected=sum(r['detected'] for r in group),n_target_success=sum(r['target_success'] for r in group),n_engine_errors=sum(r['engine_exit_code']!=0 for r in group),n_target_abstention=sum(r['target_status']=='insufficient_evidence' for r in group))
    result['detection_rate']=result['n_detected']/result['n_valid']; result['target_success_rate']=result['n_target_success']/result['n_valid']
    for key,oldkey in metrics.items():
        values=[r[key] for r in group]
        for stat,fn in [('min',min),('median',statistics.median),('max',max)]:
            result[key+'_'+stat]=fn(values)
            assert abs(result[key+'_'+stat]-previous['scenarios'][scenario][oldkey][stat])<1e-9
    summary.append(result)
table('clean-runs.csv',clean); table('attempts.csv',sorted(attempts,key=lambda r:r['run_id'])); table('scenario-summary.csv',summary)
issues=[
 ('R5-03','excluded_before_fault','Giữ lượt hủy trong attempts; không đưa vào mẫu số fault hợp lệ.'),
 ('R5-03-retry1','valid_replacement','Giữ nguyên Run ID retry và liên kết lượt gốc; không đổi thành R5-03.'),
 ('R2-03','unused_pre_event_probe','Probe trước event chỉ lưu vết; dữ liệu chẩn đoán dùng probe mới sau event.'),
 ('R5-02','secondary_abstention','R6 thiếu span 240 giây (thực tế 239); giữ insufficient_evidence, không loại lượt R5.'),
 ('baseline','approved_short_session','1806 giây; không coi là baseline 4 giờ hoặc gộp phiên cũ.'),
 ('all screenshots','retrospective','Ảnh trang event sau phục hồi; không phải ảnh đang gây lỗi.'),
 ('final-state-20261016T213953Z','comparison_scope_error','Giữ kiểm tra lệch scope; đối chiếu chính thức dùng final-state-20261016T214108Z.')]
table('deviations.csv',[dict(scope=a,classification=b,treatment=c,resolution='documented; preserve source') for a,b,c in issues])
audit=dict(result='PASS',generated_at=datetime.now(timezone.utc).isoformat(),valid_faults=18,attempts=19,excluded_before_fault=1,photo_event_joins=18,unique_event_ids=18,unique_incident_ids=18,checksum_manifests=verified,verified_files=sum(verified.values()),unresolved_data_errors=0,all_rule_status_counts=dict(counts),general_accuracy=None,false_positive_rate=None,negative_sample_limitation='No labeled healthy negative trials; not_matched and not_applicable are not TN.',raw_data_modified=False,formula_definitions={'DT':'[problem - fault_after, problem - fault_before]','RR':'[recovery - rollback_after, recovery - rollback_before]','CLI':'Elapsed complete CLI call, not pure rule inference','target_success_rate':'Target matched with valid fault and no review issues / all valid faults','median_min_max':'Python statistics.median, min, max, per scenario n=3','quantization':'DT bounds widened by 1 second each side; not measured NTP offset'})
dump('audit.json',audit); dump('workbook-input.json',dict(rows=clean,summary=summary,audit=audit))
dump('data-dictionary.json',{k:dict(type=type(v).__name__,unit='seconds since Unix epoch UTC' if k.endswith('_epoch') else 'seconds' if k.endswith('_seconds') else 'identifier/status/count or relative project path',source='Run folder logs/event/report; derived fields use audit.json definitions') for k,v in clean[0].items()})
lines=['# Tuần 5 — ngày 29: nghiệm thu dữ liệu thực nghiệm','', 'Ngày thực hiện: 17/10/2026 (UTC+7). **Hoàn thành phạm vi ngày 29**: đối chiếu Run ID, mốc thời gian, event, incident, ảnh và thống kê. Không chạy lại fault, không sửa engine hoặc bằng chứng tuần 4.','',f'- Kiểm tra SHA-256: {sum(verified.values())} tệp trong ba manifest; không sai lệch.','- 19 lượt trong sổ theo dõi: 18 fault hợp lệ, 1 lượt R5-03 hủy trước gây lỗi. R5-03-retry1 là lượt thay thế hợp lệ.','- 18/18 liên kết problem → incident → recovery → ảnh event đúng; không trùng ID; không phát hiện lỗi dữ liệu chưa xử lý.','- Tất cả 18 CLI kết thúc mã 0, incident closed, luật mục tiêu matched; không có luật phụ matched.','', '## Thống kê kiểm tra lại từ log gốc','', 'Đơn vị: giây. Mỗi kịch bản n=3. Bảng dùng cận dưới DT và RR; CSV có cả cận trên, không lấy thời gian bắt đầu watcher làm thời điểm lỗi.','', '| Kịch bản | DT min / median / max | CLI min / median / max | RR min / median / max | Luật mục tiêu / fault hợp lệ |','|---|---:|---:|---:|---:|']
for r in summary:
    def trip(k): return ' / '.join(f'{r[k+"_"+s]:.3f}' for s in ['min','median','max'])
    lines.append(f'| {r["scenario"]} | {trip("dt_lower_seconds")} | {trip("cli_elapsed_seconds")} | {trip("rr_lower_seconds")} | {r["n_target_success"]}/{r["n_valid"]} |')
lines+=['','## Công thức và giới hạn','', '- DT = [problem − fault_after, problem − fault_before]. RR = [recovery − rollback_after, recovery − rollback_before]. Độ phân giải timestamp 1 giây; CSV thêm cận DT mở rộng ±1 giây. Không đo được sai lệch đồng hồ chỉ từ độ phân giải này.','- Median/min/max được tính độc lập bằng Python và khớp toàn bộ thống kê tuần 4. Workbook có công thức và kiểm tra thay đổi đầu vào rồi khôi phục.','- Tỷ lệ khớp luật mục tiêu trên fault hợp lệ = 18/18 (100%). Đây là kết quả trên bộ fault nhỏ; chưa đủ mẫu âm để tính accuracy tổng quát, specificity hoặc false-positive rate.','- 108 đầu ra luật: 18 matched, 66 not_matched, 24 insufficient_evidence. not_matched không tự động là true negative; HTTP absent là ngoài phạm vi áp dụng.','- CLI gồm API, thu thập, luật và ghi dữ liệu; khoảng problem–recovery không phải downtime thực tế.','- Baseline được chấp thuận 30 phút 06 giây, không phải 4 giờ. Ảnh event chụp hồi cứu sau phục hồi.','', '## Tệp bàn giao','', '- `evidence/week5/day29-20261017/clean-runs.csv`: 18 dòng sạch, đủ ID, timestamp, khoảng DT/RR, đường dẫn ảnh và log.','- `attempts.csv`: đủ 19 lượt, cờ included và liên kết retry.','- `scenario-summary.csv`: thống kê hai cận DT/RR, CLI và tử số/mẫu số.','- `deviations.csv`: các ngoại lệ và cách xử lý, không xóa lịch sử.','- `audit.json`, `data-dictionary.json`: kết quả kiểm tra, định nghĩa và kiểu dữ liệu.','- `tools/day29_audit.py`, `tools/day29_workbook.mjs`: tái tạo đầu ra; workbook tại `outputs/week5-day29-20261017/NGAY29_KIEM_TRA_DU_LIEU.xlsx`.','', '## Chuyển sang ngày 30','', 'Dữ liệu đủ điều kiện dùng cho bảng/biểu đồ so sánh detection và diagnosis, viết ít nhất ba nhận xét dựa trên kết quả. Các giới hạn mẫu âm, n=3 và baseline ngắn vẫn phải ghi trong báo cáo. Ngày 29 không đồng nghĩa hoàn thành toàn bộ tuần 5.','']
(OUT/'NGAY_29_TUAN_5.markdown').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
print(json.dumps(audit,ensure_ascii=False,indent=2))

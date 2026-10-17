"""Validate live architecture snapshots, assemble traceability, install day 31 docs."""
import csv,hashlib,json,re,shutil
from datetime import datetime,timezone
from pathlib import Path
here=Path(__file__).resolve().parent;project=Path(r'C:\Users\Darrys\do-an');out=here/'outputs/week5-day31-20261017'
baseline=project/'evidence/week4/baseline-20261016T162549Z'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
mon=read(out/'mon01-live.json');vms=[read(out/(h+'-live.json')) for h in ['mon01','srv01','cli01']]
cfg=mon['effective_config'];assert cfg==read(baseline/'effective-config-start.json')
frozen=read(baseline/'source-hashes-start.json');assert mon['source_hashes']==frozen
for name,digest in frozen.items():assert sha(project/'diagnosis-engine'/name)==digest,name
assert len(frozen)==40
for vm,ip in zip(vms,['192.168.56.10','192.168.56.20','192.168.56.30']):
    assert all(x['exit_code']==0 and x['stdout']=='active' for x in vm['services'].values())
    assert vm['http']['exit_code']==0 and vm['http']['stdout']=='200'
    assert vm['ntp']['stdout']=='NTPSynchronized=yes'
    assert any(a.get('local')==ip for interface in json.loads(vm['interfaces']['stdout']) for a in interface['addr_info'])
assert not mon['open_problems']
assert all(h['status']=='0' and h['interfaces'][0]['available']=='1' for h in mon['hosts'])
assert mon['sqlite']['integrity_check']==[['ok']] and not mon['sqlite']['foreign_key_check']
assert set(mon['sqlite']['counts'])=={'incidents','evidence','diagnoses','recoveries'}
sql=re.sub(r'\x1b\[\d+C',' ',(out/'critical-sql-terminal.txt').read_text(encoding='utf-8'))
assert 'DAY31_BEGIN' in sql and 'DAY31_END' in sql and 'ERROR' not in sql
macros={m.group(1):m.group(2) for m in re.finditer(r'Linux by Zabbix agent\s+(\{\$[^}]+\})\s+(\S+)',sql)}
assert macros=={'{$AGENT.TIMEOUT}':'3m','{$CPU.UTIL.CRIT}':'90','{$LOAD_AVG_PER_CPU.MAX.WARN}':'1.5'}
assert re.search(r'GLOBAL_OVERRIDES\s+0',sql)
links=[('Zabbix server','Linux by Zabbix agent'),('Zabbix server','Zabbix server health'),('SRV01','Linux by Zabbix agent'),('CLI01','Linux by Zabbix agent')]
for host,template in links:assert re.search(re.escape(host)+r'\s+'+re.escape(template),sql)
functions=[]
for m in re.finditer(r'^(\d+)\s+(\d+)\s+(\d+)\s+(\w+)\s+(\S+)',sql,re.M):
    functions.append(dict(zip(['triggerid','functionid','itemid','function','parameter'],m.groups())))
assert len(functions)==8
old={f['functionid']:f for t in read(baseline/'trigger-functions-supplement.json') for f in t['functions']}
for f in functions:
    assert all(str(old[f['functionid']][k])==v for k,v in f.items()),f
dump(out/'critical-sql-reviewed.json',{'source':'critical-sql-terminal.txt; manually executed readonly-selects.sql on MON01 via SSH/sudo mysql','verified_at_utc':datetime.now(timezone.utc).isoformat(),'critical_macros':macros,'host_overrides_absent':True,'critical_global_override_count':0,'template_links':[{'host':h,'template':t} for h,t in links],'selected_trigger_functions':functions,'functions_match_baseline':True,'scope_limitation':'8 functions for experiment triggers plus CPU load dependency; not all 157 triggers SQL-checked today. API config comparison covers all 157 triggers in the baseline host scope.'})
with (out/'item-inventory.csv').open('w',encoding='utf-8-sig',newline='') as stream:
    fields=['hostid','itemid','key_','type','value_type','delay','master_itemid','history','trends','status','units','preprocessing']
    w=csv.DictWriter(stream,fieldnames=fields);w.writeheader();w.writerows({k:json.dumps(r[k],ensure_ascii=False) if k=='preprocessing' else r[k] for k in fields} for r in cfg['items'])
mapping=[]
for s in [f'R{i}' for i in range(1,7)]:
    p=read(project/f'evidence/week4/official-runs/{s}-01/problem.json')
    mapping.append({'scenario':s,'example_run_id':s+'-01','triggerid':p['objectid'],'problem_event_id':p['eventid'],'event_name':p['name']})
with (out/'trigger-scenario-map.csv').open('w',encoding='utf-8-sig',newline='') as stream:
    w=csv.DictWriter(stream,fieldnames=list(mapping[0]));w.writeheader();w.writerows(mapping)
verified={}
for folder,file in [('evidence/week4/official-runs','checksums-final.json'),('evidence/week4/baseline-20261016T162549Z','checksums.json'),('evidence/week4/closure-20261017','checksums.json'),('evidence/week5/day29-20261017','checksums.json'),('evidence/week5/day30-20261017','checksums.json')]:
    base=project/folder;manifest=read(base/file)
    for name,digest in manifest.items():assert sha((project if '/week5/' in folder else base)/name)==digest,name
    verified[folder]=len(manifest)
audit={'result':'PASS','generated_at_utc':datetime.now(timezone.utc).isoformat(),'capture_times_utc':{v['hostname']:v['captured_at_utc'] for v in vms},'vm_services_active':True,'http200_from_each_vm':True,'ntp_synchronized':True,'exact_inter_vm_clock_offset_measured':False,'zabbix_api_version':mon['api_version'],'open_problem_count':0,'agent_interfaces_available':3,'baseline_effective_config_equal':True,'item_scope_count':len(cfg['items']),'trigger_scope_count':len(cfg['triggers']),'frozen_source_files_compared_mon01_and_windows':len(frozen),'source_unchanged':True,'critical_macros_and_template_links_verified_by_sql':True,'selected_trigger_functions_sql_verified':8,'sqlite_integrity':'ok','sqlite_foreign_key_errors':0,'sqlite_row_counts':mon['sqlite']['counts'],'sqlite_lifecycle_report_states':['unverified','closed'],'prior_evidence_checksum_files_verified':verified,'engine_or_zabbix_config_modified':False,'new_fault_injected':False,'unit_tests_rerun':False,'unit_test_note':'Documentation-only change; live checks, hash/config comparison and read-only DB integrity are relevant verification. Historical 280 tests are not claimed as a new run.','notes':['R1/R2/R5 official trials use the same HTTP trigger 25334, not three independent triggers.','R2 may match TCP refusal with local HTTP missing; timeout without local HTTP remains insufficient.','Absent recovery in report is unverified, not evidence of a still-open event.','API parentTemplates result is not sufficient for inherited template verification with this token; SQL links used.']}
dump(out/'architecture-audit.json',audit)
dest=project/'evidence/week5/day31-20261017';dest.mkdir(parents=True,exist_ok=True)
for p in out.iterdir():
    if p.is_file():shutil.copy2(p,dest/p.name)
(dest/'tools').mkdir(exist_ok=True)
for name in ['day31_remote_readonly.py','day31_finalize.py']:shutil.copy2(here/name,dest/'tools'/name)
(dest/'README.md').write_text('''# Ngày 31 — kiểm chứng kiến trúc

Snapshot chỉ đọc được thu qua SSH trên ba VM; mã tools/day31_remote_readonly.py không chứa mật khẩu/token. Trên MON01 chạy bằng Python trong venv của engine, trên SRV01/CLI01 bằng python3. Script gửi qua stdin, không cần cài hay sửa source trên VM.

`ssh phat@192.168.56.10 /home/phat/do-an/diagnosis-engine/.venv/bin/python - < day31_remote_readonly.py`

Ví dụ redirect trên áp dụng shell hỗ trợ `<`; với PowerShell dùng `Get-Content -Raw ... | ssh -T ... python -`. Xác thực do người vận hành thực hiện. Lưu stdout vào tệp JSON mới.
readonly-selects.sql là các SELECT đã chạy qua sudo mysql cục bộ; không lưu credential. critical-sql-terminal.txt giữ output terminal gốc (có ANSI), critical-sql-reviewed.json là cấu trúc đối chiếu.
architecture-audit.json công bố phạm vi: 28 item, 157 trigger API, 8 hàm SQL, 40 tệp source/test. Không đánh đồng cấu hình mẫu/export YAML với cấu hình hiệu lực.
day31_finalize.py dùng đường dẫn máy hiện tại và cài tài liệu, không chạy cho mục đích đọc snapshot đơn thuần. Chương 2 sẽ còn được biên tập theo mẫu nộp; không đưa bản Chương 2 đang biên tập vào manifest evidence bất biến.
''',encoding='utf-8',newline='\n')
chapter=project/'docs/CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md'
shutil.copy2(here/'CHUONG_2_NGAY31.md',chapter)
report='''# Tuần 5 — ngày 31: hoàn thiện kiến trúc và triển khai

Ngày 17/10/2026 (UTC+7). **Hoàn thành phạm vi kỹ thuật ngày 31**: Chương 2 được đối chiếu mã nguồn, cấu hình và trạng thái lab trực tiếp; không thêm tính năng hoặc sửa trigger/rule.

## Kết quả

- Hoàn thiện topology ba VM, tài nguyên, NAT/Host-only, vai trò observer, cổng và luồng dữ liệu.
- Bổ sung bảng item/chu kỳ/preprocessing, trigger và macro; phân biệt trigger Zabbix với luật Python.
- Mô tả JSON-RPC, kiểm tra problem trước/sau collection, xử lý lỗi và giới hạn quyền API.
- Bổ sung module, cấu trúc evidence, điều kiện R1–R6, HTTP scope và freshness.
- Bổ sung sơ đồ SQLite, transaction bundle, recovery idempotent và trạng thái report `unverified`/`closed`.
- Bổ sung bảng truy vết tới source, snapshot và hồ sơ incident thật; giữ giới hạn triển khai rõ ràng.

## Kiểm tra thực tế

SSH chỉ đọc cả MON01, SRV01, CLI01; ba Agent active, Zabbix server/MySQL/Nginx MON01 active, Nginx SRV01 active. HTTP SRV01 trả 200 từ cả ba VM. Ba interface Agent available=1; không có problem mở lúc snapshot. SQLite integrity=ok, không có lỗi foreign key; số hàng 36 incidents, 268 evidence, 154 diagnoses, 26 recoveries gồm lịch sử cũ.

Cấu hình 28 item và 157 trigger trong phạm vi baseline không đổi. 40 tệp source/test/requirements/pytest.ini trên MON01 và Windows khớp mốc đóng băng. SELECT MySQL chỉ đọc xác nhận ngưỡng 3m/90/1,5, bốn liên kết template, không có override trên host/global cho ba macro này và tám hàm trigger chọn lọc. NTP synchronized không đồng nghĩa đã đo chính xác clock offset.

## Những điểm đã sửa rõ trong Chương 2

1. R1, R2, R5 cùng lấy problem HTTP trigger25334; sáu luật không tương ứng sáu trigger riêng.
2. R2 có thể khớp TCP refused dù thiếu local HTTP; timeout thiếu probe nội bộ mới bị giữ insufficient. Không mô tả mọi nhánh R2 đều bắt buộc probe nội bộ.
3. Chưa lưu recovery thì report là `unverified`, không kết luận event vẫn mở. `closed` chỉ là đã ghi recovery xác minh, không xác nhận sức khỏe hiện tại.
4. CPU trigger dùng min >90 trong 5m; R6 dùng mean ≥90 cùng độ phủ/load. CPU count có heartbeat 1d; không ép có history mới mỗi phút.
5. Có ServerActive trong file không chứng minh đang dùng active template; kiểm chứng template bằng SQL thay vì suy diễn từ kết quả API bị giới hạn quyền.

## Tệp bàn giao

- [Chương 2 hoàn thiện kỹ thuật](CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md).
- [Architecture audit](../evidence/week5/day31-20261017/architecture-audit.json).
- [Item inventory](../evidence/week5/day31-20261017/item-inventory.csv), [trigger map](../evidence/week5/day31-20261017/trigger-scenario-map.csv), [SQL đối chiếu](../evidence/week5/day31-20261017/critical-sql-reviewed.json).
- [Snapshot MON01](../evidence/week5/day31-20261017/mon01-live.json), [SRV01](../evidence/week5/day31-20261017/srv01-live.json), [CLI01](../evidence/week5/day31-20261017/cli01-live.json).

Kiểm tra phù hợp thay đổi tài liệu gồm đối chiếu source/config, DB integrity và liên kết; không chạy lại unit test rồi gán kết quả lịch sử 280 tests thành lần chạy mới. Bằng chứng tuần 4 và ngày 29–30 giữ nguyên checksum.

## Bước tiếp theo

Ngày 32 hoàn thiện Chương 3: môi trường, kịch bản, quy trình, kết quả, cảnh báo sai và hạn chế. Chưa chứng nhận ba lần demo sau reboot hoặc release nộp cuối. Chương 2 còn cần ghép theo quy chuẩn trình bày của trường khi đóng gói.
'''
doc=project/'docs/NGAY_31_TUAN_5.markdown';doc.write_text(report,encoding='utf-8',newline='\n')
checked=0
for path in [chapter,doc]:
    for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
        if '://' in link or link.startswith('#'):continue
        assert (path.parent/link.split('#')[0]).exists(),(path,link)
        checked+=1
audit['documentation_links_verified']=checked;dump(dest/'architecture-audit.json',audit)
archive=Path(r'D:\Study\network-monitoring-project\docs\bangiao')
shutil.copy2(doc,archive/doc.name);shutil.copy2(chapter,archive/chapter.name)
attrs=project/'.gitattributes';a=attrs.read_text(encoding='utf-8')
for line in ['evidence/week5/day31-20261017/** -text','docs/NGAY_31_TUAN_5.markdown -text']:
    if line not in a:a=a.rstrip()+'\n'+line+'\n'
attrs.write_text(a,encoding='utf-8',newline='\n')
files=sorted(p for p in dest.rglob('*') if p.is_file() and p.name!='checksums.json')+[doc]
manifest={str(p.relative_to(project)).replace('\\','/'):sha(p) for p in files};dump(dest/'checksums.json',manifest)
for rel,digest in manifest.items():assert sha(project/rel)==digest
print(json.dumps({'result':'PASS','document_links_checked':checked,'files_checksummed':len(manifest),'prior_evidence_files_unchanged':sum(verified.values()),'source_files_unchanged':len(frozen),'chapter':str(chapter),'report':str(doc)},indent=2))

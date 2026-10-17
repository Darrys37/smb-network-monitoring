"""Assemble verified final documents/evidence only after real demos have passed."""
import csv,hashlib,json,re,shutil,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
here=Path(__file__).resolve().parent;root=Path(r'C:\Users\Darrys\do-an');out=here/'outputs/week5-final-20261017';dest=root/'evidence/week5/final-20261017';docs=root/'docs'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
summary=load(out/'rehearsals-summary.json');assert summary['result']=='PASS' and len(summary['runs'])==3
assert all(r['status']=='PASS' and r['nginx_restored'] for r in summary['runs'])
mon=load(out/'mon01-final.json');baseline=root/'evidence/week4/baseline-20261016T162549Z'
assert mon['effective_config']==load(baseline/'effective-config-start.json')
frozen=load(baseline/'source-hashes-start.json');assert mon['source_hashes']==frozen
for name,h in frozen.items():assert sha(root/'diagnosis-engine'/name)==h,name
assert mon['sqlite']['integrity_check']==[['ok']] and not mon['sqlite']['foreign_key_check']
assert not mon['open_problems']
assert load(out/'credential-audit.json')['result']=='PASS'
assert '280 passed' in (out/'pytest.log').read_text(encoding='utf-8')
assert sha(out/'diagnosis-week5-final.db')==load(out/'sqlite-backup.json')['sha256']
with sqlite3.connect((out/'diagnosis-week5-final.db').as_uri()+'?mode=ro',uri=True) as conn:
    assert conn.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
    assert not conn.execute('PRAGMA foreign_key_check').fetchall()
    counts={t:conn.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['incidents','evidence','diagnoses','recoveries']}
    assert counts==mon['sqlite']['counts']
dest.mkdir(parents=True,exist_ok=True)
put(out/'vm-recovery-actions.json',{'description':'MON01 became unresponsive after the initial reboot; VirtualBox log reported lost heartbeat. Live snapshot failed with VERR_VM_UNEXPECTED_UNSTABLE_STATE and SUSPENDED_LS. ACPI/reset/poweroff did not finish. The identified MON01 GUI process was stopped and the VM started headless from its current VDI. No snapshot restore, disk deletion or engine edit was performed.','post_recovery_integrity':load(out/'post-recovery-integrity.json'),'snapshot_is_valid_backup':False,'srv01_cli01_processes_not_stopped':True})
for p in out.iterdir():
    if p.is_dir() and p.name.startswith('DEMO-'):shutil.copytree(p,dest/p.name,dirs_exist_ok=True)
    elif p.is_file() and p.suffix in ['.json','.log','.yaml','.db','.png','.txt'] and not p.name.startswith('SLIDE_'):shutil.copy2(p,dest/p.name)
(dest/'tools').mkdir(exist_ok=True)
for name in ['week5_rehearse.py','week5_resume_rehearsals.py','week5_run_verified.py','week5_secret_audit.py','week5_assemble.py','week5_slides.mjs','week5_prepare_docs.py','week5_package.py','day31_remote_readonly.py']:shutil.copy2(here/name,dest/'tools'/name)
(dest/'tools/requirements-tools.txt').write_text('paramiko==5.0.0\n',encoding='utf-8',newline='\n')
(dest/'README.md').write_text('''# Hồ sơ nghiệm thu kỹ thuật cuối tuần5

- rehearsals-summary.json và DEMO-*/ là ba lượt live mới, tách khỏi18 trial tuần4. DEMO-01 là attempt bị chặn trước fault; DEMO-01-retry1 là lượt mới.
- rehearsal-protocol-amendment.json ghi trước fault việc chấp nhận đúng các thông báo uptime sau reboot đã phân loại; không đổi trigger hoặc bỏ qua HTTP/Agent problem. final-background-recovery.json xác nhận cuối cùng không còn problem.
- mon01/srv01/cli01-final.json là trạng thái cuối. mon01-hypervisor-recovery.log/vm-recovery-actions.json giữ lỗi và cách khôi phục MON01; snapshot bị lỗi không tính backup hợp lệ.
- pytest.log là test thực tế MON01. pytest-windows-final.log là test từ đúng thư mục trên Windows; các log lỗi thao tác import ban đầu giữ riêng.
- diagnosis-week5-final.db là SQLite backup nhất quán, bị ignored khỏi Git nhưng có trong ZIP bàn giao. sqlite-backup.json ghi SHA; YAML là export host/template, không thay MySQL backup.
- python-mon01-freeze.txt và deployed-package-provenance.json ghi phiên bản thực tế. Nguồn40 tệp engine/test giữ nguyên, chỉ sửa .env.example và README ngoài tập source đóng băng.
- fallback/ là ảnh lịch sử tuần4 đã xem để kiểm tra credential; không gọi là ảnh active fault mới. Private lab IP được giữ để giải thích topology.

tools/ lưu mã điều phối; xác thực nhập ẩn hoặc env tạm, không có mật khẩu/token trong source. week5_rehearse.py thực sự reboot/gây lỗi Nginx, nên chỉ chạy trong lab đã cấu hình theo kịch bản. Các script finalize/assemble/package có đường dẫn máy hiện tại và không phải daemon của sản phẩm.
''',encoding='utf-8',newline='\n')
fallback=dest/'fallback';fallback.mkdir(exist_ok=True)
for name in ['05-dashboard-closure.jpg','event-939.jpg','04-hosts-postcheck.jpg']:shutil.copy2(root/'evidence/week4/closure-20261017/screenshots'/name,fallback/name)
put(fallback/'index.json',{'kind':'historical fallback; not new live screenshots','source':'evidence/week4/closure-20261017/screenshots','visually_reviewed':True,'credentials_visible':False,'ips':'Private lab addresses and loopback only; retained as topology identifiers','files':['05-dashboard-closure.jpg','event-939.jpg','04-hosts-postcheck.jpg']})
slide_dir=root/'outputs/week5-final-20261017';slide_dir.mkdir(parents=True,exist_ok=True)
shutil.copy2(out/'SLIDE_BAO_VE_TUAN5_FINAL.pptx',slide_dir/'SLIDE_BAO_VE_TUAN5_FINAL.pptx')
private_validation=load(here/'.week5-slides-build/validation-final.json')
put(dest/'slide-validation.json',{'slide_count':10,'chart_count':2,'font':'Arial','native_editable_charts_verified':True,'visual_review':'All ten slides inspected; chart slides6/7 re-rendered and re-inspected after axis/font repair','native_powerpoint_opened':False,'sha256':sha(slide_dir/'SLIDE_BAO_VE_TUAN5_FINAL.pptx')})
with (dest/'rehearsal-times.csv').open('w',encoding='utf-8-sig',newline='') as f:
    fields=['run_id','started_at_utc','ended_at_utc','elapsed_seconds','problem_event_id','incident_id','recovery_event_id','status']
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in summary['runs'])
chapter=docs/'CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md';c=chapter.read_text(encoding='utf-8')
c=c.replace('Chưa chứng nhận ba lần demo thành công sau reboot, chưa tạo release cuối, và chưa có backup độc lập ngoài laptop. Đây là công việc hoàn thiện tuần 5.','Tuần5 đã ghi ba lượt diễn tập kỹ thuật sau reboot và có bộ release/backup địa phương riêng; xem biên bản tuần5. Chưa chứng nhận năng lực thuyết trình của sinh viên hoặc backup ngoài laptop.')
chapter.write_text(c,encoding='utf-8',newline='\n')
demo=docs/'KICH_BAN_DEMO_10_PHUT.md';d=demo.read_text(encoding='utf-8');d+='\n## Kết quả thực hiện tuần5\n\nBa luồng kỹ thuật live sau reboot đã có bằng chứng problem→diagnosis→rollback→recovery/closed: [bảng thời lượng](../evidence/week5/final-20261017/rehearsal-times.csv). Lượt bị chặn trước fault do problem reboot giữ riêng; lỗi hypervisor và khôi phục MON01 ghi trong biên bản. Thời lượng này không bao gồm phần nói, thao tác trình chiếu hoặc đánh giá trình bày10 phút.\n';demo.write_text(d,encoding='utf-8',newline='\n')
rows=['# Tổng hợp hoàn thiện tuần 5','','Ngày17/10/2026 (UTC+7). Đã hoàn thành phần kỹ thuật của ngày29–35: dữ liệu sạch, bảng/hình, Chương2/3, README/hướng dẫn cài/chạy/rollback, slide, kiểm tra test và ba luồng demo live sau reboot. Gói bàn giao và Git tag được tạo sau audit này; receipt backup đặt cạnh gói nộp.','','## Công việc đã thực hiện','','| Ngày | Đầu ra |','|---|---|','|29|18 run sạch, sổ19 attempt, thống kê và workbook công thức|','|30|Bảng, ba hình PNG/SVG/PDF, bốn phát hiện có dẫn chứng|','|31|Chương2 đối chiếu source/config/SQL và runtime ba VM|','|32|Chương3 hoàn thiện phương pháp, cảnh báo sai, giới hạn và raw links|','|33|Hướng dẫn cài/khôi phục, README, demo10 phút, 10 slide và15 câu hỏi|','|34|Reboot ba VM, ba demo kỹ thuật mới, log thời lượng, ảnh dự phòng|','|35|280 tests trên MON01 và280 tests Windows, kiểm tra hash/config/DB, release địa phương và gói backup|','','## Diễn tập thật','','| Run ID | Problem → incident → recovery | Thời lượng kỹ thuật (s) | Kết quả |','|---|---|---:|---|']
for r in summary['runs']:rows.append(f'|{r["run_id"]}|{r["problem_event_id"]} → {r["incident_id"]} → {r["recovery_event_id"]}|{r["elapsed_seconds"]:.2f}|PASS, Nginx phục hồi|')
rows+=['','Các lượt này nằm ngoài18 fault tuần4, không nâng mẫu số thực nghiệm. Thời lượng gồm điều phối SSH/chờ event, không phải thời lượng CLI thuần hoặc bài nói10 phút. Một attempt ban đầu bị chặn trước fault bởi cảnh báo reboot được giữ riêng; không tính thành công hoặc fault thất bại. Trong ba lượt hợp lệ chỉ cho phép thông báo uptime sau reboot đã phân loại; không chấp nhận problem HTTP/Agent bất thường khác. Tất cả thông báo nền đã phục hồi trước snapshot cuối.','','## Sự cố vận hành được giữ lại','','Sau reboot, MON01 ngừng phản hồi SSH/heartbeat VirtualBox. Snapshot live bảo toàn trạng thái bị kẹt/lỗi; tắt mềm và reset không khôi phục được trạng thái nội bộ SUSPENDED_LS. Đã dừng chính xác phiên MON01 kẹt Stopping rồi khởi động lại từ đĩa hiện tại; không restore snapshot cũ và không sửa rule/trigger. Bản snapshot lỗi không được coi là backup hợp lệ. Kiểm tra SQLite/source/config sau khôi phục đạt, rồi mới tiếp tục demo. Xem log hypervisor và các snapshot cuối trong evidence.','','## Kiểm chứng và bàn giao','','- Engine Python/tests/requirements/pytest.ini:40 tệp khớp mốc đóng băng trên MON01 và Windows. Cấu hình28 item/157 trigger trong phạm vi baseline khớp.','- Ngoại lệ cấu hình mẫu: sửa ZABBIX_URLL thành ZABBIX_URL trong .env.example; README được cập nhật, không đổi ngưỡng hoặc thuật toán.','- Test cuối:280 passed trên MON01;280 passed trên Windows từ đúng thư mục module. Log collection lỗi ban đầu trên Windows được giữ, không coi là lỗi sản phẩm đã được sửa.','- SQLite cuối integrity=ok, foreign_key_check rỗng; bản backup nhất quán tải về có SHA256 khớp; YAML export host được giữ riêng.','- Quét token hiện tại và mẫu gán token hex trên working files/reachable blobs; ảnh fallback chọn lọc đã xem, không có mật khẩu/token. Không tuyên bố chứng nhận mọi credential cũ chưa biết.','- [Báo cáo tổng hợp](BAO_CAO_DO_AN_HOAN_THIEN.markdown), [Chương2](CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md), [Chương3](CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md).','- [Hướng dẫn cài/khôi phục](HUONG_DAN_CAI_DAT_VA_KHOI_PHUC.md), [demo](KICH_BAN_DEMO_10_PHUT.md), [câu hỏi bảo vệ](CAU_HOI_BAO_VE.md).','- [Slide](../outputs/week5-final-20261017/SLIDE_BAO_VE_TUAN5_FINAL.pptx), [bằng chứng cuối](../evidence/week5/final-20261017/rehearsals-summary.json).','','## Điều cần người thực hiện xác nhận trước nộp','','1. Tự trình bày và giải thích toàn bộ luồng mà không dựa vào nội dung gợi ý. Ba lần chạy kỹ thuật không chứng nhận năng lực bảo vệ hoặc bài nói đúng10 phút.','2. Ghép/định dạng báo cáo theo mẫu trường nếu trường yêu cầu Word/PDF, kiểm tra metadata và người hướng dẫn. Bản Markdown giữ nội dung kỹ thuật; chưa chứng nhận yêu cầu trình bày cụ thể chưa được cung cấp.','3. Hai bản trên C: vàD: nằm ở hai ổ NVMe vật lý khác nhau, nhưng cùng laptop; chưa bảo vệ trước mất thiết bị. Chưa có đường dẫn ngoài laptop được xác nhận; cần copy thêm USB/ổ ngoài hoặc nơi đồng bộ do người thực hiện chọn.','4. Không gọi18/18 là accuracy tổng quát; giữ n=3, baseline30m06s, thiếu mẫu âm và giới hạn lab trong bài bảo vệ.','','Git tag kỹ thuật dự kiến `week5-technical-20261017`; không push lên remote tự động. Checklist hoàn thành kỹ thuật không thay xác nhận nộp bài hoặc phê duyệt của giảng viên.','']
(docs/'TONG_HOP_TUAN_5.markdown').write_text('\n'.join(rows),encoding='utf-8',newline='\n')
original=Path(r'D:\Study\network-monitoring-project\docs\bangiao\bao_cao_do_an.md').read_text(encoding='utf-8')
front=original.split('Mục lục')[0].strip()
ch1=original.split('# CHƯƠNG 1',1)[1].split('# CHƯƠNG 2',1)[0].strip()
ch1=ch1.replace('lỗi đường kết nối dùng chung và dấu hiệu sử dụng CPU cao kéo dài','lỗi đường truy cập HTTP và dấu hiệu sử dụng CPU cao kéo dài')
ch1=ch1.replace('Nhóm lỗi đường kết nối dùng chung chỉ được xét khi mô hình có các đối tượng thực sự đi qua cùng một thiết bị hoặc tuyến.','Triển khai hiện tại dùng fault firewall TCP80 cho R5 vì ba host cùng subnet, không có gateway trung gian; không tuyên bố đã kiểm chứng lỗi đường kết nối dùng chung.')
references=original.split('# TÀI LIỆU THAM KHẢO',1)[1].strip()
combined=front+'\n\n# Phạm vi bản báo cáo\n\nBản kỹ thuật tổng hợp từ Chương1 đã có và Chương2/3 nghiệm thu tuần5. Các lời dự kiến trong cơ sở lý thuyết không thay cho kết quả thực nghiệm. Thông tin bìa kế thừa tài liệu người thực hiện cung cấp; kiểm tra định dạng mẫu trường trước nộp.\n\n# Chương1. Cơ sở lý thuyết và nghiên cứu liên quan\n\n'+ch1+'\n\n'+(docs/'CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md').read_text(encoding='utf-8')+'\n\n'+chapter.read_text(encoding='utf-8')+'\n\n# Kết luận và hướng phát triển\n\nHệ thống đã triển khai giám sát ba VM và module sáu luật có bằng chứng, lưu SQLite và recovery truy vết.18 fault hợp lệ đạt matched mục tiêu18/18 trong bộ thử nhỏ. Kết quả chưa chứng minh accuracy tổng quát, giảm thời gian so với quản trị thủ công hoặc độ tin cậy dài hạn. Hướng phát triển là tập âm độc lập, baseline dài, nhiều topology, đo từng pha và response-time đối chứng.\n\n# Tài liệu tham khảo\n\n'+references+'\n'
(docs/'BAO_CAO_DO_AN_HOAN_THIEN.markdown').write_text(combined,encoding='utf-8',newline='\n')
readme=root/'README.md';r=readme.read_text(encoding='utf-8')
r=r.replace('Chương 2/3 là bản thảo kỹ thuật, cần ghép với phần lý thuyết và mẫu nộp của trường. Kịch bản demo chưa thay thế biên bản ba lần diễn tập sau reboot. Các bước chụp ảnh dashboard, chuẩn bị slide, backup ngoài laptop và đóng gói release vẫn phải được xác nhận riêng.','Chương2/3 đã hoàn thiện kỹ thuật và có bản báo cáo tổng hợp; ba luồng diễn tập kỹ thuật sau reboot và test cuối có bằng chứng tuần5. Bản nộp vẫn cần kiểm tra định dạng trường, năng lực trình bày và bản backup ngoài laptop. Xem TONG_HOP_TUAN_5.markdown để biết phạm vi nghiệm thu.')
readme.write_text(r,encoding='utf-8',newline='\n')
gitignore=root/'.gitignore';g=gitignore.read_text(encoding='utf-8')
if '/evidence/week5/final-20261017/*.db' not in g:g+='\n/evidence/week5/final-20261017/*.db\n'
gitignore.write_text(g,encoding='utf-8',newline='\n')
attrs=root/'.gitattributes';a=attrs.read_text(encoding='utf-8')
for line in ['evidence/week5/final-20261017/** -text','docs/TONG_HOP_TUAN_5.markdown -text','docs/BAO_CAO_DO_AN_HOAN_THIEN.markdown -text','outputs/week5-final-20261017/*.pptx -text']:
    if line not in a:a=a.rstrip()+'\n'+line+'\n'
attrs.write_text(a,encoding='utf-8',newline='\n')
links=0
for p in [root/'README.md',root/'diagnosis-engine/README.md',*docs.glob('*.md'),*docs.glob('*.markdown')]:
    for url in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if '://' in url or url.startswith('#') or ' ' in url:continue
        if not (p.parent/url.split('#')[0]).exists():raise AssertionError((p,url))
        links+=1
audit={'result':'PASS','generated_at_utc':datetime.now(timezone.utc).isoformat(),'live_rehearsals_passed':3,'unit_tests_mon01':280,'unit_tests_windows':280,'source_files_unchanged':40,'baseline_config_unchanged':True,'sqlite_backup_integrity':'ok','sqlite_counts':counts,'documentation_links_verified':links,'sample_env_key_fixed':True,'vm_recovery_issue_disclosed':True,'release_scope':'Technical handover; student oral competence, school-specific final formatting and off-device backup are not certified.'}
put(dest/'final-audit.json',audit)
files=sorted(p for p in dest.rglob('*') if p.is_file() and p.name!='checksums.json')+[docs/'TONG_HOP_TUAN_5.markdown',docs/'BAO_CAO_DO_AN_HOAN_THIEN.markdown',slide_dir/'SLIDE_BAO_VE_TUAN5_FINAL.pptx']
put(dest/'checksums.json',{str(p.relative_to(root)).replace('\\','/'):sha(p) for p in files})
archive=Path(r'D:\Study\network-monitoring-project\docs\bangiao')
for name in ['TONG_HOP_TUAN_5.markdown','BAO_CAO_DO_AN_HOAN_THIEN.markdown','CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md','HUONG_DAN_CAI_DAT_VA_KHOI_PHUC.md','CAU_HOI_BAO_VE.md']:shutil.copy2(docs/name,archive/name)
print(json.dumps(audit,ensure_ascii=False,indent=2))

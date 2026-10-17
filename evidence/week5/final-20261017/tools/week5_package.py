"""Create and restore-check two local technical handover copies after Git commit/tag."""
import hashlib,json,shutil,sqlite3,subprocess,zipfile
from datetime import datetime,timezone
from pathlib import Path
root=Path(r'C:\Users\Darrys\do-an');here=Path(__file__).resolve().parent
tag='week5-technical-20261017';stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
primary=here/'deliverables'/('week5-'+stamp);secondary=Path(r'D:\Study\network-monitoring-project\backups')/primary.name
primary.mkdir(parents=True,exist_ok=False);secondary.mkdir(parents=True,exist_ok=False)
def git(*args,cwd=root):return subprocess.check_output(['git','-C',str(cwd),*args],stderr=subprocess.STDOUT)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not git('status','--porcelain').strip(),'Working tree must be committed before packaging'
commit=git('rev-parse','HEAD').decode().strip();assert git('rev-parse',tag+'^{}').decode().strip()==commit
bundle=primary/'network-monitoring-week5.bundle';git('bundle','create',str(bundle),'--all');verification=git('bundle','verify',str(bundle)).decode()
tracked=[root/p.decode() for p in git('ls-files','-z').split(b'\0') if p]
assert all(p.name!='.env' for p in tracked)
databases=list((root/'evidence').rglob('*.db'))
files=sorted(set(tracked+databases));assert all(p.is_file() for p in files)
payload=primary/'network-monitoring-week5-submission.zip'
metadata={'scope':'Technical handover; see docs/TONG_HOP_TUAN_5.markdown for human sign-off and off-device backup limits','git_commit':commit,'git_tag':tag,'generated_at_utc':datetime.now(timezone.utc).isoformat(),'tracked_files':len(tracked),'consistent_evidence_databases_included':len(databases),'secrets_excluded':['.env','API token','venv','runtime credentials'],'contains':'source/tests, docs/report, slides, raw evidence, accepted CSV/figures/XLSX, SQLite snapshots, Zabbix host YAML'}
with zipfile.ZipFile(payload,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:z.write(p,'project/'+str(p.relative_to(root)).replace('\\','/'))
    z.writestr('HANDOVER.json',json.dumps(metadata,ensure_ascii=False,indent=2))
with zipfile.ZipFile(payload) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(set(z.namelist()))
    for p in files:
        name='project/'+str(p.relative_to(root)).replace('\\','/')
        assert hashlib.sha256(z.read(name)).hexdigest()==sha(p),name
    restored=here/'verification'/('week5-restored-'+stamp+'.db');restored.parent.mkdir(exist_ok=True);assert not restored.exists()
    restored.write_bytes(z.read('project/evidence/week5/final-20261017/diagnosis-week5-final.db'))
with sqlite3.connect(restored.as_uri()+'?mode=ro',uri=True) as c:
    assert c.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
    assert not c.execute('PRAGMA foreign_key_check').fetchall()
    dbcounts={t:c.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['incidents','evidence','diagnoses','recoveries']}
verify_repo=here/'verification'/('week5-bundle-'+stamp+'.git');git('clone','--bare',str(bundle),str(verify_repo));git('fsck','--full',cwd=verify_repo)
assert git('rev-parse',tag+'^{}',cwd=verify_repo).decode().strip()==commit
(primary/'README.md').write_text('''# Bàn giao kỹ thuật tuần5

1. Kiểm tra SHA256SUMS.txt và BACKUP_VERIFICATION.json.
2. Giải nén network-monitoring-week5-submission.zip vào thư mục mới. Báo cáo chính: project/docs/BAO_CAO_DO_AN_HOAN_THIEN.markdown; trạng thái bàn giao: project/docs/TONG_HOP_TUAN_5.markdown. Giữ nguyên cấu trúc project để liên kết ảnh/evidence hoạt động.
3. Slide PowerPoint ở thư mục này và bên trong project/outputs/week5-final-20261017.
4. Git: git clone network-monitoring-week5.bundle <thư-mục-mới>, kiểm tra tag week5-technical-20261017. Bundle không chứa các DB ignored; bản ZIP bổ sung các SQLite snapshot nhất quán và export cấu hình.
5. Không có .env/token trong gói. Cấu hình token mới riêng theo hướng dẫn; YAML không thay backup MySQL/hệ điều hành.

Hai bản trên C/D ở hai ổ NVMe khác nhau nhưng cùng laptop; chưa có bản ngoài thiết bị. Ba demo là luồng kỹ thuật tự động, không thay đánh giá bài nói10 phút hoặc năng lực giải thích của người thực hiện.
''',encoding='utf-8',newline='\n')
shutil.copy2(root/'outputs/week5-final-20261017/SLIDE_BAO_VE_TUAN5_FINAL.pptx',primary/'SLIDE_BAO_VE_TUAN5_FINAL.pptx')
receipt={**metadata,'result':'PASS','zip_crc':'PASS','all_payload_file_hashes':'PASS','sqlite_restore_integrity':'ok','sqlite_restore_counts':dbcounts,'git_bundle_verify':'PASS','bare_clone_fsck':'PASS','primary_location':str(primary),'secondary_location':str(secondary),'off_device_backup_verified':False,'backup_limitation':'C: and D: are two local locations on the same laptop. External backup path was requested but not supplied.','checksums':{p.name:sha(p) for p in primary.iterdir() if p.is_file()}}
(primary/'BACKUP_VERIFICATION.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(primary/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(primary.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'),encoding='utf-8',newline='\n')
for p in primary.iterdir():
    if p.is_file():shutil.copy2(p,secondary/p.name);assert sha(p)==sha(secondary/p.name)
(here/'week5-delivery-latest.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'result':'PASS','git_commit':commit,'git_tag':tag,'primary':str(primary),'secondary':str(secondary),'payload_sha256':sha(payload),'payload_bytes':payload.stat().st_size,'sqlite_restore_counts':dbcounts},indent=2))

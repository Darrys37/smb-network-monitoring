"""Commit and back up the tested package-stability protocol before continuing pilot."""
from datetime import datetime,timedelta,timezone
import hashlib,json,shutil,subprocess
from pathlib import Path
from resume_ml_pilot import WORK,PROJECT,MODULE,ROOT,backup


def git(*args,cwd=PROJECT):
 return subprocess.check_output(['git','-C',str(cwd),*map(str,args)],stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace').strip()


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


preflight=sorted((ROOT/'verification').glob('recovered-platform-*'))[-1]
baseline=json.loads((preflight/'baseline.json').read_text(encoding='utf-8'))
assert baseline['platform']['schema_version']==2
assert all(not r['package_jobs_active'] and not r['dpkg_lock_held'] and r['package_audit_clean'] for r in baseline['platform']['nodes'].values())
proof=WORK/'verification/ml-suite-20261031T080321860303Z.json'
tests=json.loads(proof.read_text(encoding='utf-8'));assert tests['success'] and tests['tests_run']==57
assert all(sha(MODULE/name)==value for name,value in tests['source_sha256'].items())
assert not git('status','--porcelain','--','diagnosis-engine')
assert not git('diff','--cached','--name-only')
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
out=ROOT/'verification'/('package-recovery-acceptance-'+stamp);out.mkdir()
for pattern in ['api-error-20261031*.json','control-program-diagnostic-20261031*.json','mysql-jobs-20261031*.json',
                'zabbix-internal-20261031*.json','shadow-environment-tests-*.json','lab-wake-tests-*.json']:
 for source in (WORK/'verification').glob(pattern):shutil.copyfile(source,out/source.name)
shutil.copyfile(proof,out/'ml-tests-57-passed.json')
helpers={}
for name in ['lab_host_guard.py','ml_acceptance.py','review_ml_release.py','Run-ML-Demo.ps1','recover_mysql_ordering.py','hold_lab_awake.py',Path(__file__).name]:
 target=out/'helpers'/name;target.parent.mkdir(exist_ok=True);shutil.copyfile(WORK/name,target);helpers[name]=sha(target)
(out/'helpers-sha256.json').write_text(json.dumps(helpers,indent=2),encoding='utf-8')
local=datetime.now(timezone(timedelta(hours=7))).strftime('%d/%m/%Y %H:%M UTC+7')
note=f'''## Sau phục hồi package/DB — {local}

Coordinator PID 15692 đã dừng vì hết deadline baseline; hiện có **38/42 valid**, 8 uncertain đã chốt và một CPU run chưa chốt. Lượt CPU này sẽ audit uncertain, rồi retry bằng ID mới; không đưa dữ liệu chưa chốt vào train.

Đã xác minh auto-upgrade trên MON01 làm restart MySQL/Zabbix kẹt thứ tự: MySQL start chờ Zabbix stop, Zabbix stop chờ database (TimeoutStopUSec=infinity). Backup nguội MySQL/config 639817729 bytes đã kiểm CRC/hash, lưu riêng trên VM với quyền hạn chế; không xuất nội dung credential. Một lần rescue `systemctl start mysql --job-mode=ignore-dependencies --no-block` khôi phục MySQL/Zabbix và giải phóng chuỗi restart. Không kill apt/dpkg, không tắt cập nhật bảo mật hoặc sửa unit/power policy. Xem `evidence/ml-v2/verification/mysql-ordering-recovery-*` và `{out.relative_to(PROJECT).as_posix()}`.

Preflight mới đạt `{preflight.relative_to(PROJECT).as_posix()}`; engine source/SQLite runtime không đổi (39/301/172/29). Gate platform schema 2 bổ sung apt jobs, dpkg locks/audit và SHA trạng thái package trước/sau trial. Source/model feature/nhãn/siêu tham số phân loại giữ nguyên. **57 tests ML và 3 tests pin môi trường heldout đạt**; thêm tests guard wake/cleanup đã đạt ở mốc trước.

Trước test mới, worker sẽ lưu `lab-environment-freeze.json`; mọi trial test phải khớp package fingerprint này và kiểm tra lại khi thu xong. Có thay đổi package thì dừng trước khi mở điểm test. Đây là bổ sung protocol trước M5 vì lỗi hạ tầng thực tế, không phải điều chỉnh theo điểm mô hình. Chưa train v2/chưa thu test mới.

Tiếp theo chạy lại `full_ml_session.py` foreground, nhập SSH bằng getpass. Guard mới giữ display/system thức và renew mỗi 15 giây. Giữ các snapshot/protocol cũ là lịch sử; không chép workspace stage cũ đè lên repository.

'''
for path in [PROJECT/'docs/AI_HANDOFF/01_HIEN_TRANG_VA_CACH_TIEP_TUC.md',MODULE/'STATUS.md']:
 title,body=path.read_text(encoding='utf-8').split('\n',1)
 path.write_text(title+'\n\n'+note+body.lstrip(),encoding='utf-8')
protocol=MODULE/'docs/NGHIEM_THU_VM_V1.md'
title,body=protocol.read_text(encoding='utf-8').split('\n',1)
addition='''## Bổ sung 1.1 trước khi thu test — 31/10/2026

Một đợt auto-upgrade đã làm MySQL/Zabbix dừng trong pilot; bản thử bị gián đoạn được giữ riêng. Gate platform schema 2 yêu cầu không có apt job/dpkg lock, dpkg audit sạch, và SHA trạng thái package không đổi trong trial. Test mới còn pin package fingerprint ba VM trước khi thu và kiểm tra trước/sau mọi trial cùng lúc hoàn tất bộ test. Không tắt auto-upgrade; môi trường thay đổi thì dừng trước khi mở điểm. Feature, nhãn, lịch và tham số CART/FP giữ nguyên. Các pilot cũ có điều kiện kiểm soát yếu hơn phải được nêu là dữ liệu phát triển có hạn chế.

'''
protocol.write_text(title+'\n\n'+addition+body.lstrip(),encoding='utf-8')
path=PROJECT/'docs/AI_HANDOFF/MANIFEST.json';manifest=json.loads(path.read_text(encoding='utf-8'))
manifest['generated_at']=datetime.now(timezone(timedelta(hours=7))).isoformat()
manifest['files']={name:sha(path.parent/name) for name in manifest['files']}
path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
git('add','--','ml-research','evidence/ml-v2','docs/AI_HANDOFF')
git('diff','--cached','--check','--','ml-research','docs/AI_HANDOFF')
git('commit','-m','Guard lab trials against package upgrades and pin heldout environment')
checkpoint=backup('after-package-recovery-checkpoint-')
bundle=checkpoint/'project.bundle';git('bundle','create',bundle,'--all');git('bundle','verify',bundle)
restored=checkpoint/'restore-check.git';git('clone','--bare',bundle,restored,cwd=WORK);git('fsck','--full',cwd=restored)
head=git('rev-parse','HEAD');assert git('rev-parse','HEAD',cwd=restored)==head
second=Path(r'D:\Study\network-monitoring-project\backups')/checkpoint.name
shutil.copyfile(bundle,second/bundle.name);assert sha(bundle)==sha(second/bundle.name)
receipt={'status':'POST_PACKAGE_RECOVERY_CHECKPOINT_VERIFIED','head':head,'primary':str(checkpoint),'secondary':str(second),
 'zip_sha256':sha(checkpoint/'current-ml-evidence.zip'),'bundle_sha256':sha(bundle),'tests_passed':57,
 'heldout_environment_tests_passed':3,'preflight':str(preflight),'pending_pilot_valid':38,
 'scope':'Code/protocol/evidence checkpoint, not completed ML acceptance'}
for folder in [checkpoint,second]:(folder/'RECOVERY_CHECKPOINT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
(WORK/'recovery-checkpoint-latest.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=True),flush=True)

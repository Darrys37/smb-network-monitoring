"""Update current reading paths and seal the closure supplement without touching frozen raw data."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

project=Path(sys.argv[1])
closure=project/'evidence/week4/closure-20261017'
report=project/'docs/TONG_HOP_TUAN_4.markdown'
text=report.read_text(encoding='utf-8')
links=re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text)
bad=[]
for link in links:
    if '://' in link or link.startswith('#'): continue
    target=(report.parent/link.split('#')[0]).resolve()
    if not target.is_file(): bad.append(link)
assert not bad,bad
assert report.suffix=='.markdown' and text.count('| R6-')>=3
assert '\ufffd' not in text and '18/18' in text
readme=project/'README.md'
value=readme.read_text(encoding='utf-8')
newlink='- [Tổng hợp và nghiệm thu tuần 4](docs/TONG_HOP_TUAN_4.markdown).\n'
if newlink not in value:
    value=value.replace('## Tài liệu báo cáo và demo\n','## Tài liệu báo cáo và demo\n\n'+newlink)
    readme.write_text(value,encoding='utf-8')
chapter=project/'docs/CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md'
value=chapter.read_text(encoding='utf-8')
old='Bộ này chưa cung cấp trọn bộ screenshot dashboard/Problems đã che thông tin theo mẫu nộp.'
new='Hồ sơ đóng tuần 4 đã bổ sung ảnh dashboard, ba host, lịch sử và 18 ảnh chi tiết event tại `evidence/week4/closure-20261017/screenshots/`. Đây là ảnh lịch sử chụp sau đo, không phải ảnh active fault; xem `docs/TONG_HOP_TUAN_4.markdown` và closure audit.'
assert old in value or new in value
chapter.write_text(value.replace(old,new),encoding='utf-8')
progress=project/'docs/BAO_CAO_TIEN_DO_20261017.md'
value=progress.read_text(encoding='utf-8')
append='''

## Cập nhật nghiệm thu tuần 4

Đã bổ sung 18 ảnh event lịch sử khớp Run ID, ảnh bảng lịch sử/dashboard/ba host; đối chiếu backup phục hồi tái tạo đúng 18 report. Các việc bổ sung ảnh tuần 4 trong danh sách cũ phía trên đã được xử lý; ảnh demo mới khi diễn tập tuần 5 vẫn là công việc riêng. Baseline giữ nguyên 30 phút 06 giây theo lựa chọn phiên ngắn, không nâng thành bốn giờ.

Bản tổng hợp đầy đủ hiện hành: [TONG_HOP_TUAN_4.markdown](TONG_HOP_TUAN_4.markdown). Đọc bản này để xem bảng nghiệm thu, số liệu và giới hạn cuối; các mốc tiến độ phía trên là lịch sử tại thời điểm soạn.
'''
if '## Cập nhật nghiệm thu tuần 4' not in value:
    progress.write_text(value+append,encoding='utf-8')
audit={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'report_file':report.relative_to(project).as_posix(),
 'report_local_links_checked':len(links),'broken_links':bad,
 'historical_event_images':len(list((closure/'screenshots').glob('event-*.jpg'))),
 'jpeg_images_total':len(list((closure/'screenshots').glob('*.jpg'))),
 'original_frozen_manifests':'Unchanged; verified separately (535 official + 43 baseline files).',
 'result':'PASS'}
(closure/'report-validation.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
digest=hashlib.sha256(report.read_bytes()).hexdigest()
report.with_suffix('.markdown.sha256').write_text(digest+'  '+report.name+'\n',encoding='utf-8')
manifest={p.relative_to(closure).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(closure.rglob('*')) if p.is_file() and p.name!='checksums.json'}
(closure/'checksums.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({**audit,'report_sha256':digest,'closure_checksum_files':len(manifest)},indent=2))

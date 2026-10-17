"""Install reviewed day 30 outputs; keep week 4 and day 29 evidence immutable."""
import hashlib,json,os,re,shutil
from pathlib import Path
here=Path(__file__).resolve().parent;out=here/'outputs/week5-day30-20261017'
project=Path(r'C:\Users\Darrys\do-an'); dest=project/'evidence/week5/day30-20261017'
dest.mkdir(parents=True,exist_ok=True)
validation=json.loads((out/'analysis-validation.json').read_text())
validation['visual_review']='PASS; three PNG figures inspected: labels, units, legends, points and footnotes readable, no clipping'
(out/'analysis-validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
for p in out.iterdir():
    if p.is_file():shutil.copy2(p,dest/p.name)
(dest/'tools').mkdir(exist_ok=True)
for name in ['day30_analysis.py','day30_install.py']:shutil.copy2(here/name,dest/'tools'/name)
(dest/'tools/requirements.txt').write_text('matplotlib=='+validation['matplotlib_version']+'\n',encoding='utf-8',newline='\n')
(dest/'README.md').write_text('''# Tái tạo bảng/hình ngày 30

Python 3 và matplotlib (phiên bản trong tools/requirements.txt). Công cụ phân tích tách khỏi môi trường engine.

`python tools/day30_analysis.py C:\\Users\\Darrys\\do-an <thu_muc_dau_ra_moi>`

Script chỉ đọc project, xác minh manifest ngày 29, tính lại thống kê, tạo CSV/Markdown và 3 hình ở PNG/SVG/PDF. Không yêu cầu VM chạy.
Để dùng font tiếng Việt cần DejaVu Sans (đi kèm matplotlib). Giữ thư mục đầu ra mới để không ghi đè bản đã nghiệm thu.
`day30_install.py` là script cài bàn giao theo đường dẫn máy hiện tại; chỉ dùng khi đã kiểm tra hình, không cần cho tái tạo phân tích.
Các CSV cung cấp dữ liệu trung gian và kết quả thống kê; không phải workbook có công thức. Nguồn kiểm tra công thức nằm trong workbook ngày 29.
checksums.json dùng đường dẫn tương đối từ root project; không bao gồm chính nó hoặc Chương 3 vì Chương 3 tiếp tục được biên tập ngày 32.
''',encoding='utf-8',newline='\n')
report=dest/'PHAN_TICH_NGAY_30.markdown'; docs=project/'docs/NGAY_30_TUAN_5.markdown'
def rewrite(match):
    label,url=match.groups()
    if '://' in url or url.startswith('#'):return match.group(0)
    target=(dest/url).resolve(); relative=os.path.relpath(target,docs.parent).replace('\\','/')
    return f'[{label}]({relative})'
docs.write_text(re.sub(r'\[([^\]]*)\]\(([^)]+)\)',rewrite,report.read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
shutil.copy2(docs,Path(r'D:\Study\network-monitoring-project\docs\bangiao')/docs.name)
chapter=project/'docs/CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md';text=chapter.read_text(encoding='utf-8')
text=text.replace('![Từng thời gian phát hiện và CLI](../evidence/week4/official-runs/figures/thoi-gian-phat-hien-va-cli.png)','![Thời gian phát hiện đã kiểm tra ngày 30](../evidence/week5/day30-20261017/detection-time.png)\n\n![Thời gian CLI chẩn đoán](../evidence/week5/day30-20261017/diagnosis-cli-time.png)')
text=text.replace('![Kết quả luật mục tiêu](../evidence/week4/official-runs/figures/ket-qua-luat-muc-tieu.png)','![Kết quả luật mục tiêu](../evidence/week5/day30-20261017/diagnosis-outcomes.png)')
marker='## 3.9. Nghiệm thu bảng và biểu đồ ngày 30'
addition='''## 3.9. Nghiệm thu bảng và biểu đồ ngày 30

Bộ hình trong mục 3.5 được tái tạo từ dữ liệu đã nghiệm thu ngày 29; 90 số min/median/max khớp dữ liệu nguồn. Mỗi hình có bản PNG, SVG và PDF để đưa vào báo cáo. [Phân tích ngày 30](NGAY_30_TUAN_5.markdown) cung cấp bảng hai cận DT, kết quả mục tiêu, từng điểm trên hình và bốn phát hiện có liên kết hồ sơ gốc.

- R6 có DT median 356 s, R3 269 s, R2 10 s. Sự khác biệt phù hợp với điều kiện trigger khác nhau; chưa cô lập nguyên nhân bằng thực nghiệm đối chứng.
- R6 có CLI median thấp nhất (0,502 s), R1 cao nhất (6,660 s), dù R6 phát hiện chậm hơn. Detection và CLI là hai giai đoạn, không thể thay thế nhau.
- Sáu nhóm đều khớp mục tiêu 3/3; không có mẫu âm để tính accuracy tổng quát. Lượt hủy trước fault không vào mẫu số.
- 24/108 đầu ra luật thiếu evidence vẫn được giữ; không gán thành true negative hoặc lỗi luật mục tiêu.

[Dữ liệu điểm vẽ](../evidence/week5/day30-20261017/plotted-points.csv) · [Bảng thống kê](../evidence/week5/day30-20261017/timing-summary.csv) · [Kết quả chẩn đoán](../evidence/week5/day30-20261017/diagnosis-outcomes.csv) · [Kiểm tra tái tạo](../evidence/week5/day30-20261017/analysis-validation.json).

Hoàn thành đầu ra ngày 30; Chương 3 tiếp tục được rà soát đầy đủ vào ngày 32. Không thay đổi engine hoặc bằng chứng tuần 4.
'''
text=text.split(marker)[0].rstrip()+'\n\n'+addition;chapter.write_text(text,encoding='utf-8',newline='\n')
attr=project/'.gitattributes';a=attr.read_text(encoding='utf-8')
for line in ['evidence/week5/day30-20261017/** -text','docs/NGAY_30_TUAN_5.markdown -text']:
    if line not in a:a=a.rstrip()+'\n'+line+'\n'
attr.write_text(a,encoding='utf-8',newline='\n')
checked=0
for md in [report,docs,chapter]:
    for url in re.findall(r'\[[^\]]*\]\(([^)]+)\)',md.read_text(encoding='utf-8')):
        if '://' in url or url.startswith('#'):continue
        assert (md.parent/url.split('#')[0]).exists(),(md,url)
        checked+=1
validation=json.loads((dest/'analysis-validation.json').read_text());validation['local_document_links_verified']=checked
(dest/'analysis-validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
files=sorted(p for p in dest.rglob('*') if p.is_file() and p.name!='checksums.json')+[docs]
manifest={str(p.relative_to(project)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(dest/'checksums.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
for rel,expected in manifest.items():assert hashlib.sha256((project/rel).read_bytes()).hexdigest()==expected
print(json.dumps({'result':'PASS','links_verified':checked,'new_files_checksummed':len(manifest),'report':str(docs),'chapter3_updated':True},indent=2))

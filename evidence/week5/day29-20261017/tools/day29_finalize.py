"""Verify XLSX export and install only the new day 29 deliverables."""
import hashlib, json, shutil, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

here=Path(__file__).resolve().parent
out=here/'outputs/week5-day29-20261017'
project=Path(r'C:\Users\Darrys\do-an')
evidence=project/'evidence/week5/day29-20261017'
dest=project/'outputs/week5-day29-20261017'
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(out/'NGAY29_KIEM_TRA_DU_LIEU.xlsx') as archive:
    assert archive.testzip() is None
    formulas=0
    for name in ['xl/worksheets/sheet1.xml','xl/worksheets/sheet2.xml']:
        xml=ET.fromstring(archive.read(name))
        assert not xml.findall('.//s:c[@t="e"]',ns), name
        formulas+=len(xml.findall('.//s:f',ns))
    assert formulas>=150, formulas
    xml=ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
    for cell,expected in [('B13',18),('C13',18),('D13',18),('H13',1),('I13',1)]:
        value=xml.find(f'.//s:c[@r="{cell}"]/s:v',ns)
        assert value is not None and float(value.text)==expected,(cell,value)
validation=json.loads((out/'workbook-validation.json').read_text())
validation.update(xlsx_zip_integrity='PASS',exported_formula_count=formulas,exported_error_cells=0,exported_cached_totals='18/18 and 100%',visual_review='PASS; both worksheets and formula columns rendered and inspected')
(out/'workbook-validation.json').write_text(json.dumps(validation,indent=2)+'\n',encoding='utf-8',newline='\n')
evidence.mkdir(parents=True,exist_ok=True);dest.mkdir(parents=True,exist_ok=True)
for name in ['clean-runs.csv','attempts.csv','scenario-summary.csv','deviations.csv','audit.json','data-dictionary.json','workbook-input.json','workbook-validation.json','workbook-error-scan.ndjson','workbook-inspection.ndjson','summary-preview.png','data-preview.png','formulas-preview.png']:
    shutil.copy2(out/name,evidence/name)
(evidence/'tools').mkdir(exist_ok=True)
for name in ['day29_audit.py','day29_workbook.mjs','day29_finalize.py']:
    shutil.copy2(here/name,evidence/'tools'/name)
shutil.copy2(out/'NGAY29_KIEM_TRA_DU_LIEU.xlsx',dest/'NGAY29_KIEM_TRA_DU_LIEU.xlsx')
shutil.copy2(out/'NGAY_29_TUAN_5.markdown',project/'docs/NGAY_29_TUAN_5.markdown')
archive=Path(r'D:\Study\network-monitoring-project\docs\bangiao')
shutil.copy2(out/'NGAY_29_TUAN_5.markdown',archive/'NGAY_29_TUAN_5.markdown')
readme='''# Tái tạo kết quả ngày 29

Chạy từ một thư mục làm việc riêng với Python 3 chuẩn và Node.js có @oai/artifact-tool:

1. `python day29_audit.py C:\\Users\\Darrys\\do-an outputs/week5-day29-20261017`
2. `node day29_workbook.mjs` (đọc đường dẫn outputs ở trên, kiểm tra công thức, render, xuất XLSX).

Không chạy finalize để phân tích đơn thuần: script đó cài đầu ra vào project và archive, dùng đường dẫn máy hiện tại. Khi chuyển máy cần sửa đường dẫn tường minh.
Manifest ngày 29 chỉ phủ đầu ra mới; manifest tuần 4 giữ nguyên. Workbook dùng 18 dòng cố định theo Run ID; không sắp xếp riêng cột hoặc thêm/xóa dòng rồi coi đó là bản đã nghiệm thu.
CSV UTF-8 BOM, kiểu số khi đọc bằng csv là chuỗi: cần chuyển theo data-dictionary.json. Không điền giá trị thiếu bằng 0. Cột ID được giữ nguyên; timestamp dùng Unix UTC.
Không tái gán insufficient_evidence thành not_matched. Tỷ lệ mục tiêu dùng 18 fault hợp lệ, không dùng 19 attempt hoặc 108 đầu ra luật làm mẫu số.
'''
(evidence/'README.md').write_text(readme,encoding='utf-8',newline='\n')
files=sorted(p for p in evidence.rglob('*') if p.is_file() and p.name!='checksums.json')+[dest/'NGAY29_KIEM_TRA_DU_LIEU.xlsx',project/'docs/NGAY_29_TUAN_5.markdown']
manifest={str(p.relative_to(project)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(evidence/'checksums.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
for relative,digest in manifest.items(): assert hashlib.sha256((project/relative).read_bytes()).hexdigest()==digest
print(json.dumps({'installed_files_with_checksums':len(manifest),'xlsx_validation':validation,'report':str(project/'docs/NGAY_29_TUAN_5.markdown')},indent=2))

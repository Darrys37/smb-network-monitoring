"""Finish days 32/33 documents without changing frozen engine rules."""
from pathlib import Path
import shutil
root=Path(r'C:\Users\Darrys\do-an');here=Path(__file__).resolve().parent
docs=root/'docs'
for name in ['HUONG_DAN_CAI_DAT_VA_KHOI_PHUC.md','CAU_HOI_BAO_VE.md']:shutil.copy2(here/name,docs/name)
example=root/'diagnosis-engine/.env.example';value=example.read_text();assert 'ZABBIX_URLL=' in value or 'ZABBIX_URL=' in value
example.write_text(value.replace('ZABBIX_URLL=','ZABBIX_URL='),encoding='utf-8',newline='\n')
module='''# Diagnosis engine — bản kỹ thuật tuần 5

Python CLI, Zabbix API và SQLite. Sáu luật roadmap có matched/not_matched/insufficient_evidence; người vận hành chọn event và quyết định xử lý. Không có daemon hoặc tự khắc phục.

## Cài và kiểm tra

Trên MON01, trong thư mục module:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp -n .env.example .env
chmod 600 .env
```

Nhập ZABBIX_URL và token đọc trong .env bằng editor cục bộ; không commit token. URL API lab là http://192.168.56.10:8080/api_jsonrpc.php. Khóa mẫu đã sửa thành ZABBIX_URL (bản cũ viết nhầm ZABBIX_URLL).

```bash
.venv/bin/python -m pytest -q
.venv/bin/python app.py --host-id 10683
```

Không truyền event-id thì chỉ liệt kê problem. Để chạy/lưu, chọn problem mới còn mở đúng host, khai báo target/control/scope và probe mới. Xem [README gốc](../README.md) và [hướng dẫn đầy đủ](../docs/HUONG_DAN_CAI_DAT_VA_KHOI_PHUC.md).

## Probe và scope

- R1/R3/R6 trên SRV01: host10683, target192.168.56.20, control192.168.56.30, HTTP expected.
- R2/R5: thêm local HTTP JSON tạo trên SRV01, đúng observer srv01, địa chỉ dịch vụ, port80/path/, tuổi≤180s. TCP timeout thiếu local HTTP là insufficient; TCP refused có thể khớp R2 dù chưa có local HTTP nhưng không chứng minh Nginx dừng.
- R4: host10684, target.30, control R1.20, HTTP absent; DNS JSON tạo trên CLI01 cho example.com và IP control1.1.1.1 cùng observer cli01. Chuyển về MON01 khi còn fresh; không lấy DNS MON01 thay CLI01.
- R6: history300s, ≥3 mẫu, span≥240s, maxgap≤120s, cuối≤180s, mean≥90 và load≥CPUcount. CPU count có heartbeat1d, cho phép tuổi86580s; load≤180s. Không đồng nhất mean của luật với trigger min>90/5m.

Lệnh probe HTTP trên SRV01: `python3 ~/http_probe.py --target-ip 192.168.56.20 --observer srv01 --output <tên-mới.json>`.
DNS trên CLI01 cần dns_probe.py/evidence.py/models.py, dig và ping; không cần token API.

## Lưu và recovery

app.py --save dùng transaction bundle, event_id duy nhất và từ chối trộn evidence/diagnoses đã lưu. Kiểm tra event trước/sau collection; đây chưa phải khóa xuyên Zabbix/SQLite.
Sau rollback, chạy recovery.py --event-id với event mới đã có recovery thật. Report theo incident-id hỗ trợ json/md/csv. Chưa có recovery lưu thì unverified, có recovery xác minh thì closed; không sửa evidence gốc. Report CSV là một dòng mỗi diagnosis, khác CSV trial một dòng mỗi Run ID.

## Tài liệu và kiểm chứng

- [Kiến trúc, điều kiện luật và SQLite](../docs/CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md).
- [Thực nghiệm và giới hạn](../docs/CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md).
- [Demo và rollback](../docs/KICH_BAN_DEMO_10_PHUT.md).

280 tests trước đợt tuần4 là mốc lịch sử; kết quả test cuối tuần5 ghi trong hồ sơ final, không dùng unit test làm số fault thật. 18/18 mục tiêu khớp không phải accuracy tổng quát có mẫu âm. Legacy rules.py còn để tái lập dữ liệu cũ; bộ chính thức dùng roadmap. Giữ .env và DB runtime ngoài Git; backup bằng SQLite backup API.
'''
(root/'diagnosis-engine/README.md').write_text(module,encoding='utf-8',newline='\n')
chapter=docs/'CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md';text=chapter.read_text(encoding='utf-8')
text=text.replace('Bản thảo từ bộ dữ liệu chính thức ngày 16–17/10/2026.','Bản kỹ thuật hoàn thiện tuần 5 từ bộ dữ liệu chính thức ngày 16–17/10/2026.')
marker='## 3.10. Cảnh báo sai, tiêu chí chấm và khả năng tái lập'
addition='''## 3.10. Cảnh báo sai, tiêu chí chấm và khả năng tái lập

Đơn vị thử là một fault chủ động tạo có Run ID, log trước/sau và kiểm tra precondition; không phải từng dòng history, từng diagnosis hay từng event ngẫu nhiên. 19 attempt gồm18 fault hợp lệ và1 hủy trước fault. Sáu nhóm mỗi nhóm3, không có bộ âm độc lập. Không loại một fault hợp lệ chỉ vì engine lỗi/thiếu dữ liệu/không phát hiện; trong bộ đã thu các trường hợp mục tiêu đó đều bằng0.

Chấm mục tiêu theo điều kiện luật và ground truth của fault. R1 ngắt Host-only, R2 dừng Nginx, R3 dừng Agent, R4 chặn DNS tại CLI01, R5 lọc TCP80 từ MON01, R6 stress CPU. Các tên nguyên nhân là giả thuyết giới hạn đúng bằng chứng; không gán nhãn resolver upstream hỏng, VM mất nguồn hoặc gateway hỏng cho những fault khác.

**Cảnh báo sai:** baseline có0 problem mới trong1806s, tương đương0 sự kiện/giờ chỉ trong cửa sổ quan sát. Chưa có event nền để phân loại false alert, chưa thử tập âm engine, không có mẫu số TN/FP để tính FPR hoặc specificity. Chẩn đoán matched ngoài mục tiêu trong18 run bằng0, nhưng điều đó không thay tập âm độc lập. 24 insufficient_evidence ở108 đầu ra giữ nguyên; HTTP absent cũng không tính TN. Các problem reboot ngoài cửa sổ tuần4 được phân loại riêng trong hồ sơ diễn tập tuần5, không gộp để thay kết quả baseline.

Mỗi lượt engine chỉ chạy/lưu một lần; event hồi phục khi đang collection làm kiểm tra cuối từ chối là hành vi bảo vệ, không lý do sửa dữ liệu. Với R2/R5, probe HTTP tạo mới sau problem; với R4, DNS/IPcontrol cùng observer. Probe cũ R2-03 được giữ riêng; R5-03 hủy và retry có ID riêng. Không impute, cắt outlier hoặc đổi timestamp để rút ngắn thời gian.

Nguồn tái lập: [clean runs](../evidence/week5/day29-20261017/clean-runs.csv), [attempt register](../evidence/week5/day29-20261017/attempts.csv), [công thức và audit](../evidence/week5/day29-20261017/audit.json), [mã tạo bảng/hình](../evidence/week5/day30-20261017/tools/day30_analysis.py). Manifest giữ byte của nguồn. Bảng/hình có min/median/max, cỡ mẫu và cận thời gian; không cung cấp kiểm định hoặc confidence interval suy rộng từ n=3.

Các lượt demo sau reboot là tập diễn tập riêng trong `evidence/week5/final-20261017`, không nâng cỡ mẫu18 của thực nghiệm đóng băng. Test cuối kiểm tra phần mềm; không thay baseline hoặc fault trial. Môi trường thực tế và cấu hình đã được đối chiếu lại ở [Chương2](CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md).
'''
text=text.split(marker)[0].rstrip()+'\n\n'+addition;chapter.write_text(text,encoding='utf-8',newline='\n')
demo=docs/'KICH_BAN_DEMO_10_PHUT.md';text=demo.read_text(encoding='utf-8')
text=text.replace('Bản hướng dẫn chuẩn bị cho tuần 5, chưa phải biên bản đã diễn tập.','Kịch bản thuyết trình10 phút; kết quả diễn tập kỹ thuật thật được lưu riêng trong biên bản tuần5.')
text=text.replace('Kiểm tra cả ba VM đang chạy,','Sau reboot, chờ các problem uptime<10m phục hồi và quan sát nhiều poll liên tiếp không còn problem. Kiểm tra cả ba VM đang chạy,')
text=text.replace('## Hồ sơ dự phòng và diễn tập còn phải làm','## Hồ sơ dự phòng và nghiệm thu diễn tập')
text=text.replace('- Cần diễn tập ba lần sau một lần reboot lab, ghi thời lượng thực tế, lỗi, event/incident mới và xác nhận rollback. Chưa được đánh dấu hoàn thành chỉ vì đã có kịch bản này.','- Kết quả ba lượt kỹ thuật sau reboot phải có Run ID, thời lượng, event/incident/recovery mới và rollback. Xem biên bản cuối tuần5; không suy thời lượng luồng tự động thành thời lượng nói10 phút.')
demo.write_text(text,encoding='utf-8',newline='\n')
readme=root/'README.md';text=readme.read_text(encoding='utf-8')
text+='\n## Bàn giao tuần 5\n\n- [Cài đặt và khôi phục](docs/HUONG_DAN_CAI_DAT_VA_KHOI_PHUC.md).\n- [Câu hỏi ôn bảo vệ](docs/CAU_HOI_BAO_VE.md).\n- [Kết quả và phần cần người thực hiện xác nhận](docs/TONG_HOP_TUAN_5.markdown).\n\nTệp tổng hợp cuối công bố kết quả test/demo thực tế, bản nộp và vị trí backup; không dùng các ghi chú tiến độ cũ làm trạng thái hiện tại.\n'
readme.write_text(text,encoding='utf-8',newline='\n')
print('Days32/33 documents installed; .env.example key corrected; engine Python untouched.')

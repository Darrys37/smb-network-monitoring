# Diagnosis engine — bản kỹ thuật tuần 5

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

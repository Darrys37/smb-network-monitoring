# Diagnosis engine — bản tối ưu sau tuần 5

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

## Bản cleanup ngày 17/10/2026

CLI và `diagnose_roadmap()` cùng mặc định HTTP scope `unknown`. Caller Python cũ
muốn đánh giá web server cần khai báo `http_service="expected"`. Lệnh demo trong
README gốc đã khai báo scope; điều kiện R1–R6 khi scope tường minh được giữ nguyên.

`app.main()` điều phối; `collect_evidence()` chỉ thu/nhập; `evaluate_evidence()`
chọn luật; `print_assessment()` trình bày; repository ghi transaction. `policy.py`
giữ ngưỡng roadmap. Hai importer dùng `probe_evidence.py` kiểm tra envelope,
UTF-8, giới hạn 64 KiB và tuổi dữ liệu; `dns_evidence.py` kiểm tra query/control.
`--dns-evidence` yêu cầu cả `--dns-name` và `--dns-control-ip`.

Probe DNS mới xuất version 1; file DNS cũ thiếu version vẫn đọc được nếu hợp lệ.
Probe trên CLI01 vẫn chỉ cần dns_probe.py/evidence.py/models.py và ping/dig;
HTTP probe trên SRV01 vẫn là một file Python độc lập. MON01 cần **toàn bộ module**,
bao gồm policy.py, probe_evidence.py và dns_evidence.py, không chép riêng app.py.

355 tests đạt trên Windows và MON01; 108 kết quả của 18 hồ sơ cũ được replay
không đổi; 576 tổ hợp tổng hợp khớp bản trước khi scope tường minh. Dữ liệu/tag
tuần 4–5 giữ nguyên; số liệu này không phải một chiến dịch fault live mới.

Kiểm tra cho developer:

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
```

- [Logic và hướng phát triển](../docs/DIAGNOSIS_ENGINE_LOGIC_VA_PHAT_TRIEN.md).
- [Giới thiệu, giải thích và gợi ý bảo vệ](../docs/GIOI_THIEU_VA_GIAI_THICH_DO_AN.md).

Các báo cáo nghiệm thu tuần 5 mô tả phiên bản đã đóng tại tag
`week5-technical-20261017`; hai tài liệu trên mô tả source sau cleanup.


## Tối ưu đọc item ngày 17/10/2026

CLI roadmap dùng `collect_roadmap_metrics()` đọc sáu key một lần, rồi tạo bốn
metric ngữ cảnh, agent_metric và cpu_history. History CPU vẫn có request riêng.
Với lượt thành công có history, tổng API giảm từ 8 xuống 6; vẫn kiểm tra event
trước/sau collection. Không có cache qua các lượt; không đổi tuổi mẫu hoặc rule.

369 tests đạt trên Windows và bản thử riêng trên MON01. 15 tình huống collector
khớp source `7d32be7`; 108 kết luận lịch sử giữ nguyên. Thu thật ở trạng thái
bình thường xác nhận một item.get và một history.get. Chưa có benchmark để công
bố tỷ lệ tăng tốc. Xem mục 17 tài liệu logic để hiểu mốc thời gian chung và thứ
tự evidence mới; các kết quả 355 tests ở trên thuộc đợt cleanup trước đó.

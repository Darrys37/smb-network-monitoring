# Diagnosis engine — bản đối chiếu Tuần 3

Python CLI + Zabbix API + SQLite, không FastAPI, không AI/ML và không tự sửa lỗi.
Đây là bản tiếp nối gói 26 file gửi ngày 01/10/2026; không viết lại bằng chứng cũ.

## Chạy

Giữ `.env` cũ trên MON01 (không commit). `.env.example` chỉ là mẫu;
URL cần đúng frontend đang dùng, không mặc định thay URL hiện tại.

```bash
cd ~/do-an/diagnosis-engine
source .venv/bin/activate
python -m pytest -q
python app.py
```

Chẩn đoán problem đang mở trên SRV01 (thay EVENT_ID bằng số thật):

```bash
python app.py --event-id EVENT_ID --save
```

Mặc định chạy bộ roadmap, luôn trả sáu đánh giá; thiếu cấu hình/evidence thì
`insufficient_evidence`. Không coi sáu dòng kết quả là sáu lỗi hoặc sáu ca PASS.
`--host-id` mặc định 10683, `--target-ip` mặc định 192.168.56.20. Nếu đổi host,
phải đổi đúng cả hai; người cấu hình chịu trách nhiệm ánh xạ IP-host.
Chạy thủ công là phương án được roadmap cho phép; chưa có polling nền.

Tái lập cách đánh giá cũ (HTTP/reachability/CPU/RAM/disk) bằng `--ruleset legacy`.
Hồ sơ cũ giữ nguyên rule ID, không đổi nhãn thành R1–R6 và không chẩn đoán lại
với bằng chứng cũ để giả tạo một kết quả mới.

## R1–R6 và bằng chứng

| Luật | Điều kiện triển khai | Giới hạn |
|---|---|---|
| R1_HOST_OR_LOCAL_CONNECTIVITY | Ping đích không trả lời, TCP80 timeout, gateway còn ping được | Nghi host/đường cục bộ; không khẳng định host tắt |
| R2_HTTP_SERVICE_SUSPECTED | Ping đích thành công, TCP80 refused/timeout | Nginx hoặc chính sách truy cập; chưa kiểm tra lỗi ứng dụng khi TCP vẫn mở |
| R3_AGENT_UNAVAILABLE | Ping còn, agent.ping từng có nhưng quá 180s không có mẫu, TCP10050 refused/timeout | Dành cho passive agent trong lab; không suy từ item chưa từng có dữ liệu hoặc bị disabled |
| R4_DNS_RESOLVER_SUSPECTED | CLI01 ping IP đối chứng được, DNS lỗi/timeout/NXDOMAIN/no A answer | Cần tên ứng dụng thật, resolver đúng; NXDOMAIN không có nghĩa DNS server hỏng |
| R5_GATEWAY_OR_SHARED_PATH | Ping đích, host thứ hai và gateway đều không phản hồi | Phải xác minh topology phụ thuộc gateway; còn có thể lỗi điểm đo/shared link |
| R6_SUSTAINED_CPU_HIGH | CPU trung bình >=90%, đủ lịch sử, load 1m >= số CPU | Suy đoán quá tải; cần response baseline và process để giải thích |

Tất cả chọn evidence mới nhất, tuổi 0–180s; không lùi về mẫu tốt cũ khi mẫu mới lỗi.
R6 lấy lịch sử 300s, yêu cầu >=3 mẫu, phủ >=240s, khoảng trống <=120s,
mẫu cuối <=180s; dùng `history.get` theo `value_type`. Cần các item
`system.cpu.util`, `system.cpu.num`, `system.cpu.load[all,avg1]`.
Ngưỡng này là cấu hình rule, không tự động đồng bộ với macro trigger Zabbix.

`rules.py` cũ và các test của nó giữ nguyên; RAM/disk là chức năng bổ sung.
`roadmap_rules.py` mới có fixture khớp/không khớp/thiếu dữ liệu cho từng R1–R6.
Fixture test không thay cho thực nghiệm 18 run của Tuần 4.

## Gateway và DNS: cấu hình chưa được biết, không tự điền

R1/R5 nhận `--gateway-ip` và R5 thêm `--peer-ip`. Không lấy 192.168.56.1
làm gateway chỉ vì nó là adapter Windows. SRV01 và CLI01 cùng subnet host-only
không cần router để trao đổi, nên ngắt default gateway NAT không đại diện R5.
Cần topology gateway thật hoặc quyết định phương án firewall thay thế và đồng bộ
code/tài liệu trước Tuần 4. Bản này triển khai nhánh gateway gốc, chưa tự chọn nhánh firewall.

R4 dùng file đo từ CLI01, không dùng DNS của MON01 giả làm CLI01.
Đặt các file Python/requirements cần thiết trên CLI01 và cài dependencies, `dig`/`ping`.
Không cần đưa token Zabbix sang CLI01: dns_probe chỉ gọi lệnh cục bộ.

```bash
# Trên CLI01; thay service.test bằng tên thực của ca DNS đã thiết kế:
python dns_probe.py --name service.test --control-ip 192.168.56.20 --output dns-cli01.json
```

Chép file về MON01, chạy trong 180s với `--dns-name service.test --dns-evidence PATH`.
Tên observer mặc định `cli01` (hostname chữ thường); dùng `--dns-observer` nếu khác.
File được coi là evidence do người vận hành cung cấp, chưa có chữ ký xác thực nguồn.
Web scenario hiện dùng IP trực tiếp, nên không gán DNS của tên bất kỳ làm nguyên nhân
HTTP event 458. DNS là ca riêng cần thiết kế tên và cấu hình trên CLI01.

## Recovery và xuất báo cáo

```bash
python recovery.py --event-id 458
python report.py --incident-id 11 --format json --output reports/incident-11-v2.json
python report.py --incident-id 11 --format md --output reports/incident-11-v2.md
python report.py --incident-id 11 --format csv --output reports/incident-11-v2.csv
```

Recovery đọc problem và event liên kết từ API, kiểm tra ID, trigger, host, value,
thời điểm rồi thêm bảng `recoveries` vào SQLite trong transaction. Chạy lặp không
thêm bản ghi; recovery xung đột bị từ chối. Không đổi `incidents.value=1` thành 0.
`lifecycle_status=closed` được suy từ bản ghi recovery đã lưu; chưa có recovery
thì `unverified`, không mặc định sự cố còn mở. File JSON recovery cũ vẫn giữ nguyên.
Nếu API không còn cho đọc event (housekeeping/quyền), dừng với thông báo; không
lấy dữ liệu tự chế để đóng incident. Cần một ca thật mới nếu không lấy lại được.

CSV có một dòng cho mỗi diagnosis, event/recovery ID, thời điểm, khoảng cách event
và evidence JSON có timestamp. Đây là CSV hồ sơ, chưa phải CSV thực nghiệm có
Run ID/fault injection time/ground truth. Không thể suy detection time từ dữ liệu
chưa ghi thời điểm gây lỗi. File xuất dùng exclusive create, không ghi đè báo cáo cũ.
Các lỗi API không xóa dữ liệu; các bundle trùng tiếp tục bị từ chối như phiên bản cũ.

## Bảo mật và lịch sử Git

Gói này không chứa `.env` hoặc token thật được chủ động cấu hình.
Điều đó không chứng minh lịch sử Git trên laptop sạch.
Trên Windows, từ repository do-an, chạy Python script `scan_git_token.py`, nhập
API token bằng prompt ẩn, không dán token vào chat/lệnh có history.
Script chỉ in số lượng trùng, kiểm tra tracked working files và blob trong các
ref Git hiện có (`--all`). Không kiểm tra credential cũ chưa biết, remote chưa fetch,
reflog/unreachable objects hoặc file ngoài repo. Nếu từng có token cũ, quét riêng
và thu hồi token đã lộ; không tự rewrite history.

## Tài liệu API đã đối chiếu

- https://www.zabbix.com/documentation/7.0/en/manual/api/reference/history/get
- https://www.zabbix.com/documentation/7.0/en/manual/api/reference/event/object

`r_eventid` là liên kết recovery; `history` phải khớp kiểu giá trị của item.

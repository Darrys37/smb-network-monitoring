# Hệ thống giám sát và hỗ trợ chẩn đoán sự cố mạng

Đồ án sử dụng Zabbix để giám sát và phát sinh cảnh báo, kết hợp module Python CLI thu bằng chứng, áp dụng luật và lưu hồ sơ sự cố có giải thích. Người vận hành kiểm tra và xử lý sự cố; module không tự khắc phục.


## Tài liệu tiếp nhận và source hiện tại

- [Giới thiệu và giải thích đồ án](docs/GIOI_THIEU_VA_GIAI_THICH_DO_AN.md).
- [Logic diagnosis engine, đọc code và phát triển](docs/DIAGNOSIS_ENGINE_LOGIC_VA_PHAT_TRIEN.md).

Cleanup ngày 17/10/2026 thống nhất HTTP mặc định `unknown` giữa CLI/Python,
tách rõ orchestration/collection/rules và chuẩn hóa nhập HTTP/DNS. Bản này đạt
355 tests trên Windows và MON01; replay 108 kết quả trong 18 hồ sơ giữ nguyên.
Kết quả thực nghiệm ở tag tuần 4–5 vẫn thuộc phiên bản lịch sử. Xem mục 16 của
tài liệu logic để biết thay đổi tương thích, cách kiểm thử và cách giải thích code.

## Mô hình lab

| Máy | IP Host-only | Vai trò |
|---|---|---|
| MON01 | 192.168.56.10/24 | Zabbix 7.0 LTS, MySQL, frontend, Agent2, Python và SQLite |
| SRV01 | 192.168.56.20/24 | Nginx cổng 80, SSH và Agent2; host ID 10683 |
| CLI01 | 192.168.56.30/24 | Máy khách, điểm đo DNS và Agent2; host ID 10684 |

Ba VM Ubuntu Server chạy trong VirtualBox. `enp0s3` dùng NAT riêng để ra Internet; `enp0s8` dùng IP tĩnh trên cùng mạng Host-only. Lưu lượng giữa các IP 192.168.56.x đi trực tiếp trên subnet này. Gateway NAT 10.0.2.2 của từng VM và adapter Windows 192.168.56.1 không phải router trung gian của luồng nội bộ.

Giao diện Zabbix trong lab: `http://192.168.56.10:8080/`. Host MON01 có tên kỹ thuật `Zabbix server` trong Zabbix. Giám sát Agent dùng template passive; HTTP scenario do MON01 thực hiện tới SRV01; phép đo DNS nằm trên CLI01.

## Luồng xử lý

```text
Zabbix problem → API / chuẩn hóa → evidence hiện tại → R1–R6 → SQLite
                                           recovery.py → xác minh recovery
                                               report.py → JSON / Markdown / CSV
```

Engine là CLI. Khi không truyền event ID, chương trình liệt kê problem đang mở của host được chọn. Khi chẩn đoán, chương trình xác minh event còn mở trước và sau collection; chỉ ghi dữ liệu khi có `--save`. Event ID dùng để chống tạo incident trùng. Hồ sơ lịch sử được giữ nguyên khi đồng bộ recovery.

Evidence phản ánh thời điểm thu, không tự tái dựng trạng thái tại event time. `matched` nghĩa là điều kiện của luật khớp bằng chứng; `not_matched` chỉ nói về luật đó; `insufficient_evidence` giữ rõ dữ liệu chưa đủ để đánh giá.

| Nhóm luật hiện hành | Đối chiếu chính |
|---|---|
| R1 — mất liên lạc với host / đường cục bộ | Ping/TCP đích và host đối chứng cùng subnet |
| R2 — dịch vụ/listener HTTP nghi gặp lỗi | Ping, TCP80 và HTTP probe từ máy dịch vụ |
| R3 — Agent không khả dụng | Ping, tuổi agent.ping và TCP10050 |
| R4 — phân giải / đường truy cập DNS nghi gặp lỗi | DNS và ping IP đối chứng cùng observer CLI01 |
| R5 — filtering / đường truy cập HTTP nghi gặp lỗi | Remote TCP thất bại nhưng local HTTP200 trên IP dịch vụ |
| R6 — CPU cao kéo dài | Lịch sử CPU, độ phủ mẫu, load và CPU count |

R5 hiện hành dùng phương án firewall HTTP thay gateway. R1 thực nghiệm bằng ngắt Host-only, R4 bằng chặn truy vấn DNS trên CLI01. Không mô tả các phép thử này như đã kiểm chứng tắt VM, gateway chung hoặc resolver upstream hỏng.

## Vận hành CLI trên MON01

Các lệnh sau dành cho lab đã cài đặt. Hướng dẫn module và cấu hình mẫu nằm trong [diagnosis-engine/README.md](diagnosis-engine/README.md).

```bash
cd ~/do-an/diagnosis-engine
source .venv/bin/activate
python app.py
```

Với R1/R3/R6, chẩn đoán event mới của SRV01 khi fault còn tồn tại:

```bash
read -r -p 'Problem event ID mới của SRV01: ' EVENT_ID
python app.py --event-id "$EVENT_ID" --host-id 10683 \
  --target-ip 192.168.56.20 --ruleset roadmap \
  --control-ip 192.168.56.30 --http-service expected --save
```

**R2/R5 cần HTTP evidence mới từ SRV01**, dùng IP dịch vụ 192.168.56.20, observer `srv01`, tuổi không quá 180 giây. Sau khi chuyển JSON về MON01, chạy:

```bash
read -r -p 'Problem event ID mới của SRV01: ' EVENT_ID
read -r -p 'Đường dẫn HTTP JSON mới trên MON01: ' HTTP_FILE
python app.py --event-id "$EVENT_ID" --host-id 10683 \
  --target-ip 192.168.56.20 --ruleset roadmap \
  --control-ip 192.168.56.30 --http-service expected \
  --http-observer srv01 --http-evidence "$HTTP_FILE" --save
```

Probe chạy trên **SRV01**, bằng Python tiêu chuẩn:

```bash
python3 ~/http_probe.py --target-ip 192.168.56.20 --observer srv01 \
  --output "$HOME/http-$(date -u +%Y%m%dT%H%M%SZ).json"
```

**R4 dùng host CLI01**: host ID 10684, target 192.168.56.30, control R1 192.168.56.20, HTTP scope `absent`. DNS probe chạy trên CLI01 cho `example.com`, IP đối chứng `1.1.1.1`; JSON được chuyển sang MON01 khi còn fresh. Trên MON01:

```bash
read -r -p 'Problem event ID DNS mới của CLI01: ' EVENT_ID
read -r -p 'Đường dẫn DNS JSON mới trên MON01: ' DNS_FILE
python app.py --event-id "$EVENT_ID" --host-id 10684 \
  --target-ip 192.168.56.30 --ruleset roadmap \
  --control-ip 192.168.56.20 --http-service absent \
  --dns-name example.com --dns-observer cli01 \
  --dns-control-ip 1.1.1.1 --dns-evidence "$DNS_FILE" --save
```

Sau khôi phục, đồng bộ recovery rồi xuất hồ sơ bằng incident ID đã được engine in ra:

```bash
python recovery.py --event-id "$EVENT_ID"
read -r -p 'Incident ID đã được engine lưu: ' INCIDENT_ID
python report.py --incident-id "$INCIDENT_ID" --format json
```

Report hỗ trợ JSON, Markdown và CSV. File output được tạo theo chế độ không ghi đè; chọn tên mới khi xuất. CSV incident có một dòng cho mỗi diagnosis, khác với bảng thực nghiệm có một dòng cho mỗi Run ID.

## Kiểm chứng và thực nghiệm

- Mốc trước đợt đo: 280 tests passed trên MON01; tests không thay thế các lượt fault thật.
- Source tham chiếu `ca04071`, export host/template `978b4f9`, phiếu thử `4cabeb0`. Snapshot hiệu lực và hash source được lưu trong hồ sơ freeze/baseline.
- Baseline ngày 16/10/2026 kéo dài 30 phút 06 giây theo lựa chọn người thực hiện, đã kiểm tra liên tục và lưu 963 mẫu history của 28 item. Đây là phiên ngắn, chưa đạt mục tiêu bốn giờ của roadmap.
- Hồ sơ chính thức nằm trong [evidence/week4/official-runs](evidence/week4/official-runs). Xem [phụ lục vận hành](evidence/week4/official-runs/PHU_LUC_VAN_HANH_THUC_NGHIEM.md) để phân biệt engine với công cụ ghi thử, timer fault và cách đo/chấm.
- Mỗi lượt giữ fault/rollback log độc lập, problem/recovery ID, CLI log, evidence và report nếu engine hoàn tất. Lượt không phát hiện, engine error hoặc thiếu bằng chứng cũng phải được giữ.

Chỉ ba lượt mỗi kịch bản trên lab nhỏ; kết quả không chứng minh độ tin cậy vận hành doanh nghiệp. Tần suất cảnh báo nền của Zabbix và tỷ lệ chẩn đoán sai của engine CLI là hai đại lượng khác nhau. Khoảng problem–recovery không phải downtime thật; CLI elapsed gồm cả API, collection, luật và lưu trữ.

## Dữ liệu và cấu hình

Database SQLite của module độc lập với MySQL của Zabbix. Sao lưu SQLite bằng backup API nhất quán. Export YAML lưu cấu hình host/template, không thay thế backup database hoặc cấu hình daemon/global settings.

Source sử dụng `.env` trên MON01 cho URL/API token có quyền đọc phù hợp. Probe trên CLI01/SRV01 không cần token Zabbix. Repository loại cấu hình bí mật, venv và database runtime theo `.gitignore`.

Các thư mục evidence có checksum cần giữ nguyên byte khi lưu/chuyển/checkout. Dữ liệu gốc, bảng tổng hợp và nhận xét phải truy ngược được theo Run ID và đúng phiên bản thực nghiệm.

## Tài liệu báo cáo và demo

- [Tổng hợp và nghiệm thu tuần 4](docs/TONG_HOP_TUAN_4.markdown).

- [Tiến độ và việc tiếp theo ngày 17/10/2026](docs/BAO_CAO_TIEN_DO_20261017.md).
- [Chương 2: kiến trúc và triển khai](docs/CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md).
- [Chương 3: thực nghiệm và đánh giá](docs/CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md).
- [Kịch bản demo 10 phút](docs/KICH_BAN_DEMO_10_PHUT.md).
- [Bảng tổng hợp chính thức](evidence/week4/official-runs/TONG_HOP_THUC_NGHIEM_TUAN4.md), [dữ liệu từng lượt](evidence/week4/official-runs/all-trials.csv) và [công thức/thống kê JSON](evidence/week4/official-runs/experiment-summary.json).

Chương2/3 đã hoàn thiện kỹ thuật và có bản báo cáo tổng hợp; ba luồng diễn tập kỹ thuật sau reboot và test cuối có bằng chứng tuần5. Bản nộp vẫn cần kiểm tra định dạng trường, năng lực trình bày và bản backup ngoài laptop. Xem TONG_HOP_TUAN_5.markdown để biết phạm vi nghiệm thu.

## Bàn giao tuần 5

- [Cài đặt và khôi phục](docs/HUONG_DAN_CAI_DAT_VA_KHOI_PHUC.md).
- [Câu hỏi ôn bảo vệ](docs/CAU_HOI_BAO_VE.md).
- [Kết quả và phần cần người thực hiện xác nhận](docs/TONG_HOP_TUAN_5.markdown).

Tệp tổng hợp cuối công bố kết quả test/demo thực tế, bản nộp và vị trí backup; không dùng các ghi chú tiến độ cũ làm trạng thái hiện tại.

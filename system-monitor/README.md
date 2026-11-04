# Worker V3 — Chẩn đoán chuyên gia và tương quan cảnh báo

Worker V3 tự động đọc sự kiện Zabbix, thu bằng chứng, đánh giá **8 luật / 7 nhóm sự cố** từ SQLite và gom cảnh báo theo topology. Hướng dẫn này dành cho lab **MON01, CLI01 và SRV01**.

**[Giới thiệu dự án](../README.md)** · **[Triển khai lại](deployment/README.md)** · **[Kết quả kiểm chứng](../docs/KIEM_CHUNG_WORKER_V3.md)**

## Trước khi vận hành

Lab hiện tại dùng mạng quản trị `192.168.56.0/24` và mạng dịch vụ `172.30.20.0/24` qua CLI01. Các IP, host ID và tên NIC trong cấu hình là giá trị của lab này, cần đối chiếu nếu triển khai nơi khác.

1. Bật lần lượt **CLI01 → SRV01 → MON01**, chờ từng máy vào được SSH. Giữ laptop cắm sạc và màn hình thức trong lúc diễn tập.
2. Trên MON01, xác nhận worker active và xem trạng thái:

   ```bash
   systemctl is-active do-an-monitor-v3.service
   /home/phat/do-an/diagnosis-engine/.venv/bin/python /home/phat/do-an/system-monitor/report.py
   ```

3. Chỉ bắt đầu tạo lỗi khi SRV01 HTTP 200, parent up, các nguồn dữ liệu hoạt động, không còn sự cố của lượt trước và hàng đợi đã xử lý hết. Notice khởi động đã được cấu hình có thể được hiển thị riêng.

## Xem và đọc kết quả

Trên **MON01**:

```bash
cd /home/phat/do-an/diagnosis-engine
.venv/bin/python ../system-monitor/report.py
```

Xuất trạng thái đầy đủ hoặc xem log gần nhất:

```bash
.venv/bin/python ../system-monitor/report.py --json
journalctl -u do-an-monitor-v3.service -n 10 --no-pager
```

`report.py` đọc trạng thái worker đã lưu, không khởi động thêm worker. Các số cần đọc:

| Trường | Cách hiểu |
|---|---|
| Active events | Các sự kiện lỗi còn hoạt động sau khi tách notice đã cấu hình |
| Incident groups | Các nhóm sau tương quan |
| Suppressed dependent alerts | Cảnh báo con được gắn về nhóm gốc theo phụ thuộc |
| Pending diagnosis jobs | Các job chưa hoàn thành; cần kiểm tra khi không giảm |
| ROOT | Node và loại nhóm sự cố, không phải kết luận chắc chắn duy nhất |

Mỗi node có vector 7 nhóm: `[icmp_status, tcp80_status, http_status_code, dns_response_time_ms, resource_status, agent_availability, parent_status]`. CPU/RAM thô và chất lượng lịch sử vẫn được giữ riêng.

Sau khi phục hồi, dịch vụ hoạt động lại trước khi mọi item/trigger Zabbix kịp cập nhật. Chờ dữ liệu mới rồi kiểm tra lại. `Raw events retained` tăng theo lịch sử, không cần về 0.

## Demo Nginx từng bước để quay video

Mở sẵn SSH vào MON01 và SRV01. Trên MON01 chạy report một lần để thấy trạng thái bình thường.

**1. Tạo lỗi trên SRV01:**

```bash
sudo python3 /home/phat/do-an/system-monitor/fault_control.py arm nginx --seconds 180
systemctl is-active nginx
```

Helper kiểm tra Nginx ban đầu active, tạo và xác nhận timer phục hồi độc lập trước khi dừng dịch vụ. Cần thấy `timer_active: true`, `fault_applied: true` và Nginx inactive.

**2. Sau khoảng 15–30 giây, xem trên MON01:**

```bash
/home/phat/do-an/diagnosis-engine/.venv/bin/python /home/phat/do-an/system-monitor/report.py
```

Nếu observation chưa cập nhật, đợi thêm rồi xem lại. Tìm nhóm `ROOT srv01 | http_service` và luật `R2_HTTP_SERVICE_SUSPECTED`. Bằng chứng chính: máy vẫn ping được, TCP/80 refused và trạng thái Nginx cục bộ inactive. HTTP null riêng lẻ chưa đủ chứng minh Nginx dừng.

**3. Phục hồi trên SRV01:**

```bash
sudo python3 /home/phat/do-an/system-monitor/fault_control.py recover nginx
systemctl is-active nginx
```

**4. Xem lại trên MON01:** đợi các phép đo cập nhật, chạy report và xác nhận HTTP 200, lỗi của lượt thử hết, queue về 0. Đây mới là kết thúc một cảnh demo đầy đủ.

Trên giao diện Zabbix chọn **Monitoring → Problems → History**, đặt khoảng thời gian gần đây và lọc các host của lab. History giữ dòng **RESOLVED** sau phục hồi; chế độ chỉ xem problem đang mở sẽ không giữ lỗi đã hết. Worker quan sát và ghi nhận phục hồi; người vận hành/helper thực hiện việc khắc phục.

## Demo tự động trên Windows

Mở PowerShell tại thư mục gốc repository. Cài thư viện cho CLI điều khiển một lần:

```powershell
python -m pip install -r .\system-monitor\requirements-operator.txt
```

Wrapper yêu cầu ba VM running, SSH/sudo hoạt động, host keys đã xác minh và Paramiko có trong môi trường Python.

Thiết lập đường dẫn cục bộ trong `tools/lab.local.json` theo [mẫu cấu hình](../tools/lab-settings.example.json). `coordination_root` là thư mục ghi được dùng để khóa phiên demo; `dependency_paths` là danh sách đường dẫn thư viện phụ nếu có. File này không chứa mật khẩu/token và không được đưa vào Git.

```powershell
python .\system-monitor\system_lab.py status

# Chạy một tình huống mỗi lần
python .\system-monitor\system_lab.py demo --fault nginx
python .\system-monitor\system_lab.py demo --fault gateway
python .\system-monitor\system_lab.py demo --fault multi
python .\system-monitor\system_lab.py demo --fault storm
```

| Tình huống | Nội dung kiểm tra |
|---|---|
| nginx | Dừng Nginx, phát hiện nhóm dịch vụ, khởi động lại và xác nhận phục hồi |
| gateway | Tắt forwarding CLI01, gom cảnh báo kết nối phụ thuộc về gateway |
| multi | Gateway lỗi đồng thời Nginx dừng; giữ lỗi dịch vụ độc lập |
| storm | Gateway lỗi kèm 20 kênh synthetic để thử tương quan/ức chế khi nhiều cảnh báo |

Wrapper lưu hồ sơ `before/detected/recovered` dưới `evidence/system-v3/demos/<thời điểm>`. Nó tự phục hồi sau khi đạt điều kiện nên thời gian giữ cảnh ngắn hơn cách quay thủ công.

Demo storm cần token cấu hình tại `.env.admin` trên MON01 để ghi 20 kênh thử. Worker thông thường dùng token chỉ đọc riêng. Các kênh synthetic là cảnh báo được bơm vào Zabbix, không phải 20 VM hay 20 sự cố vật lý.

Timer Nginx/gateway của wrapper có thời hạn 120 giây, storm 100 giây. Có cleanup trong `finally`. Nếu mất kết nối laptop, timer đã được tạo bên trong VM vẫn là cơ chế phục hồi dự phòng; sau đó vẫn phải kiểm tra trạng thái thực tế.

## Phục hồi khi demo bị ngắt

Trên **Windows**, tại repository:

```powershell
python .\system-monitor\system_lab.py recover
python .\system-monitor\system_lab.py status
```

Nếu cần thao tác riêng qua SSH:

```bash
# SRV01
sudo python3 /home/phat/do-an/system-monitor/fault_control.py recover nginx
```

```bash
# CLI01
sudo python3 /home/phat/do-an/system-monitor/fault_control.py recover gateway
```

```bash
# MON01: chỉ dùng khi đã thử synthetic storm
/home/phat/do-an/diagnosis-engine/.venv/bin/python /home/phat/do-an/system-monitor/storm_control.py 0
```

Kiểm tra HTTP 200, parent up, các lỗi của lượt thử được phục hồi và pending jobs = 0. Không xóa runtime DB, cursor hoặc lịch sử Zabbix để làm sạch màn hình. Không flush toàn bộ firewall.

## Các luật và điều kiện cần hiểu

| Luật | Nội dung |
|---|---|
| R1 | Mất phản hồi đích khi máy đối chứng vẫn phản hồi |
| R2 | Dịch vụ/listener HTTP nghi gặp lỗi |
| R3 | Agent không khả dụng |
| R4 | DNS lỗi khi kết nối IP đối chứng vẫn tốt |
| R5 | RemoteHTTP lỗi nhưng HTTP cục bộ 200; nghi ngờ đường truy cập/lọc |
| R6 | CPU trung bình ≥ 90% với lịch sử đủ dài và load/số CPU đối chứng |
| R7 | Nút cha có bằng chứng down còn mới |
| R8 | Ít nhất10 sự kiện lỗi mới trong 30 giây |

R6 kiểm ít nhất 3 mẫu, độ phủ ≥ 240 giây, khoảng cách mẫu ≤ 120 giây và độ mới hợp lệ. Một mẫu CPU cao hoặc RAM cao chưa đủ để R6 khớp.

R8 xét cửa sổ trượt của sự kiện mới. Sau 30 giây có thể không còn khớp dù những cảnh báo đó vẫn đang mở; chẩn đoán đã lưu tại thời điểm xảy ra là hồ sơ cần truy lại. Wrapper storm kiểm hành vi tương quan/suppression; không lấy riêng việc 20 cảnh báo xuất hiện làm bằng chứng mọi luật đều đã khớp.

Mỗi luật trả `matched`, `not_matched` hoặc `insufficient_evidence`. Luật khớp có3 giả thuyết và điểm ưu tiên85/65/45% do chuyên gia gán. Đây không phải xác suất đúng đã được đo. Các luật độc lập nên có thể cùng khớp trong một observation.

## Mạng dịch vụ và tương quan

```text
MON01 192.168.56.10
  → route 172.30.20.0/24 via 192.168.56.30
CLI01 192.168.56.30 / 172.30.20.1
  → Internal Network do-an-v3-backend
SRV01 172.30.20.20
```

SRV01 giữ IP quản trị `192.168.56.20`; đường trả lời từ IP dịch vụ dùng bảng route 203 qua CLI01. Gateway được kiểm tra forwarding, interface và route, không chỉ ping.

Correlation dùng cửa sổ 30 giây, topology đã khai báo và bằng chứng parent down còn mới. Cảnh báo con cũ không tự bị quy ngược cho gateway mới hỏng. Lỗi dịch vụ có bằng chứng cục bộ độc lập, CPU và DNS không bị ức chế chỉ vì parent down. Sự kiện gốc luôn được giữ.

## Dữ liệu, cấu hình và sửa luật

| File | Vai trò |
|---|---|
| `config/expert_seed.json` | Nguồn điều kiện: 8 luật, 40 hàng quyết định và các giả thuyết |
| `catalog/expert_rules.sqlite` | Catalog SQLite được runtime mở chỉ đọc |
| `config/lab.json` | Profile, topology, ánh xạ host/trigger và đường dẫn khóa probe |
| `config/provisioned.json` | ID các đối tượng Zabbix thuộc lab |
| `runtime/monitoring.sqlite` | Sự kiện, cursor, queue, diagnostics, batches và trạng thái node |

Muốn sửa luật: backup catalog, sửa seed, tạo **catalog ở đường dẫn mới**, kiểm thử rồi đổi cấu hình chạy và restart worker. Catalog được cache theo phiên; sửa file giữa chừng không đồng nghĩa worker đã tải lại luật.

`build_catalog.py` từ chối ghi đè catalog đã có. Không xóa catalog/runtime đang dùng chỉ để chạy lại bước tạo mới.

Worker dùng file lock. Không chạy `monitor.py once` đồng thời với service đang giữ cùng runtime DB; nếu cần chế độ một lần phải dừng service rồi khởi động lại sau.

Chạy kiểm thử hệ thống từ thư mục gốc repository:

```powershell
Push-Location .\system-monitor
python -m unittest discover -s tests -v
Pop-Location
```

Regression sử dụng các observation lịch sử đã đóng gói trong `tests/fixtures`, kèm checksum và nguồn gốc; không cần tải nhánh khác hoặc giữ đường dẫn trên laptop gốc. Kiểm thử tự động không thay thế diễn tập tạo lỗi và xác minh phục hồi.

## Triển khai và backup

Đọc [hướng dẫn triển khai](deployment/README.md) khi phục hồi VM cũ hoặc đưa sang môi trường khác. Nó giả định các thành phần Zabbix/Agent/Nginx đã được cài nền, không phải trình cài mới hoàn chỉnh.

SSH của probe dùng khóa riêng, giới hạn nguồn MON01 và forced command chỉ cho phép đọc bằng chứng. Không đưa private key hoặc `.env*` lên Git. Backup SQLite bằng backup API nhất quán; backup VM, MySQL, cấu hình và secrets là các phần riêng.

Muốn tắt riêng worker trên MON01:

```bash
sudo systemctl disable --now do-an-monitor-v3.service
```

Muốn gỡ mạng thử, dừng worker rồi làm theo trình tự trong tài liệu triển khai. Giữ state `/var/lib/do-an-system-v3/network-before.json` để gỡ đúng tài nguyên do module sở hữu.

## Giới hạn

Phạm vi hiện tại là 3 VM, chưa có kiểm chứng máy Ubuntu vật lý hoặc tải production. Worker hỗ trợ điều tra và tương quan, không tự khắc phục hoặc gửi email/chat. Các notice chỉ được tách khi khớp đúng cấu hình node/trigger/tên/severity; không bỏ qua toàn bộ cảnh báo Warning.

Đọc [báo cáo kiểm chứng](../docs/KIEM_CHUNG_WORKER_V3.md) để xem hồ sơ thử và giới hạn tại từng mốc. Các nhật ký phát triển được giữ riêng trong [mục lục tài liệu](../docs/README.md).

## Quay video demo gọn

Mỗi lượt quay một tình huống, bốn màn hình tiếng Việt và nhấn Enter để chuyển bước. Công cụ tự tạo lỗi có rollback, đọc kết quả worker rồi xác nhận phục hồi.

```powershell
python .\system-monitor\video_demo.py
```

[Hướng dẫn quay từng video](../docs/QUAY_VIDEO_DEMO.md). Cài requirements-operator và cấu hình lab theo hướng dẫn vận hành trước khi chạy.

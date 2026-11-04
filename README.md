# Hệ thống giám sát tập trung và hỗ trợ chẩn đoán sự cố mạng

Đồ án xây dựng hệ thống giám sát hạ tầng mạng doanh nghiệp nhỏ bằng **Zabbix 7.0 LTS**, kết hợp **worker Python tự động thu thập bằng chứng, đối chiếu luật chuyên gia trong SQLite và tương quan cảnh báo theo topology**.

Thay vì chỉ báo “không truy cập được web”, hệ thống kiểm tra thêm kết nối, trạng thái dịch vụ và thiết bị phụ thuộc để hỗ trợ người quản trị phân biệt lỗi dịch vụ, lỗi đường truy cập hoặc lỗi gateway.

**[Mã nguồn Worker V3](https://github.com/Darrys37/smb-network-monitoring/tree/feature/ml-research-v2/system-monitor)** · **[Hướng dẫn vận hành và demo](https://github.com/Darrys37/smb-network-monitoring/blob/feature/ml-research-v2/system-monitor/README.md)** · **[Tài liệu dự án](https://github.com/Darrys37/smb-network-monitoring/blob/feature/ml-research-v2/docs/README.md)**

> **Chọn đúng phiên bản:** Worker V3 hiện nằm trên nhánh [`feature/ml-research-v2`](https://github.com/Darrys37/smb-network-monitoring/tree/feature/ml-research-v2). Tên nhánh được giữ từ quá trình phát triển; nội dung giới thiệu dưới đây tập trung vào hệ thống chuyên gia V3. Nhánh `main` giữ mã nguồn baseline và trang giới thiệu này.

## Chức năng chính

- Tự động đọc sự kiện lỗi và phục hồi từ Zabbix API; lưu sự kiện, con trỏ đọc và hàng đợi xử lý trong SQLite.
- Thu thập bảy nhóm đặc trưng: ICMP, TCP/80, HTTP, DNS, tài nguyên CPU/RAM, Zabbix Agent và trạng thái nút cha.
- Đánh giá **8 luật thuộc 7 nhóm sự cố**, với **40 hàng quyết định** lưu trong SQLite; kết quả kèm bằng chứng, giả thuyết và hướng kiểm tra tiếp theo.
- Gom cảnh báo theo cửa sổ thời gian **30 giây** và quan hệ phụ thuộc; giảm cảnh báo dây chuyền khi gateway gặp lỗi.
- Giữ lại lỗi độc lập khi nhiều sự cố xảy ra đồng thời, chẳng hạn gateway không chuyển tiếp và Nginx thực sự dừng.
- Lưu lịch sử chẩn đoán và trạng thái phục hồi để đối chiếu sau thử nghiệm.

Worker hỗ trợ chẩn đoán. Việc khắc phục do người quản trị hoặc công cụ tạo/hoàn tác lỗi trong lab thực hiện.

## Kiến trúc và luồng hoạt động

```text
                  Zabbix Server
               sự kiện / số liệu
                        |
                        v
              Worker Python tự động
                        |
          lưu sự kiện + hàng đợi SQLite
                        |
        thu và kiểm tra độ mới của bằng chứng
                        |
            bảng quyết định SQLite
                 8 luật chuyên gia
                        |
       tương quan cảnh báo theo topology
                        |
        nhóm sự cố + giải thích + lịch sử
```

Worker chạy bằng systemd trên MON01, đọc sự kiện theo chu kỳ và làm mới bằng chứng định kỳ. Người vận hành dùng `report.py` để xem kết quả đã xử lý; không cần chọn từng event ID rồi gọi chẩn đoán thủ công.

Các luật được xét độc lập nên có thể đồng thời khớp. Dữ liệu thiếu hoặc quá cũ được giữ thành `unknown` / `insufficient_evidence`, tránh biến một phép đo thất bại thành kết luận chắc chắn.

## Mô hình thực nghiệm

Hệ thống hiện được triển khai trên **3 máy ảo Ubuntu Server trong VirtualBox**.

| Máy | IP quản trị | IP mạng dịch vụ | Vai trò |
|---|---|---|---|
| MON01 | `192.168.56.10` | Truy cập qua CLI01 | Zabbix Server, MySQL, giao diện web, worker Python và SQLite |
| CLI01 | `192.168.56.30` | `172.30.20.1` | Gateway chuyển tiếp và máy quan sát DNS |
| SRV01 | `192.168.56.20` | `172.30.20.20` | Nginx Web Server và Zabbix Agent2 |

```text
MON01 192.168.56.10
          |
          | route tới 172.30.20.0/24
          v
CLI01 192.168.56.30 / 172.30.20.1
          |
          | Internal Network: do-an-v3-backend
          v
SRV01 172.30.20.20 — Nginx TCP/80
```

Các IP `192.168.56.x` dùng cho quản trị. IP dịch vụ `172.30.20.20` đi qua CLI01, giúp kiểm chứng sự phụ thuộc gateway thật. Đường quản trị riêng cho phép worker đọc trạng thái Nginx ngay cả khi đường dịch vụ gặp lỗi.

`CLI01-Gateway` và `SRV01-Routed` là hai đối tượng giám sát trong Zabbix, không phải hai VM bổ sung. Giao diện web trong lab: `http://192.168.56.10:8080/`.

## Bộ luật chẩn đoán

| Luật | Nhóm | Dấu hiệu chính |
|---|---|---|
| R1 | Ping / kết nối | Đích không phản hồi ICMP và TCP, máy đối chứng vẫn phản hồi |
| R2 | Dịch vụ HTTP | Nginx inactive/failed hoặc dấu hiệu dịch vụ/listener không phục vụ |
| R3 | Agent | Agent cục bộ dừng hoặc thiếu mẫu mới kèm bằng chứng kết nối phù hợp |
| R4 | DNS | Phân giải tên thất bại trong khi kết nối IP đối chứng vẫn hoạt động |
| R5 | Đường truy cập HTTP | Ping được, TCP/80 từ xa lỗi nhưng HTTP tại đúng IP dịch vụ vẫn trả 200 |
| R6 | Tài nguyên | CPU trung bình cao kéo dài, đủ lịch sử và có load/số CPU đối chứng |
| R7 | Gateway / nút cha | Nút cha được cấu hình có bằng chứng down còn mới |
| R8 | Bão cảnh báo | Có ít nhất 10 sự kiện lỗi khác nhau trong cửa sổ 30 giây |

R2 và R5 cùng thuộc nhóm HTTP nên có 8 luật nhưng 7 nhóm. Điều kiện chi tiết nằm trong [bảng luật nguồn](https://github.com/Darrys37/smb-network-monitoring/blob/feature/ml-research-v2/system-monitor/config/expert_seed.json), được nạp vào catalog SQLite.

`matched` nghĩa là phù hợp dấu hiệu của luật, chưa khẳng định duy nhất nguyên nhân. Các điểm 85/65/45% là điểm ưu tiên điều tra do chuyên gia gán, không phải xác suất đúng đã được hiệu chỉnh.

## Lấy mã nguồn

```bash
git clone --branch feature/ml-research-v2 --single-branch https://github.com/Darrys37/smb-network-monitoring.git
cd smb-network-monitoring
```

Để triển khai sang môi trường khác, làm theo [hướng dẫn triển khai V3](https://github.com/Darrys37/smb-network-monitoring/blob/feature/ml-research-v2/system-monitor/deployment/README.md). Tài liệu giả định đã có ba VM và các dịch vụ nền; đây chưa phải bộ cài đặt tự động từ một máy trống. IP, host ID, NIC và SSH phải được đối chiếu với môi trường thực tế.

## Xem trạng thái trên lab đã cấu hình

Trên **MON01**:

```bash
systemctl is-active do-an-monitor-v3.service

/home/phat/do-an/diagnosis-engine/.venv/bin/python \
  /home/phat/do-an/system-monitor/report.py
```

Những trường cần đọc:

| Trường | Ý nghĩa |
|---|---|
| `Active events` | Sự kiện lỗi đang hoạt động sau khi tách các thông báo đã được cấu hình |
| `Incident groups` | Số nhóm sự cố sau tương quan |
| `Suppressed dependent alerts` | Số cảnh báo con được gắn về nhóm gốc do phụ thuộc |
| `Pending diagnosis jobs` | Số công việc chẩn đoán chưa hoàn thành |
| `ROOT srv01 \| http_service` | Nhóm sự cố dịch vụ HTTP trên SRV01 |

Suppression giữ nguyên sự kiện nguồn trong Zabbix và SQLite. Vì vậy Zabbix vẫn có thể hiện nhiều cảnh báo trong khi module chỉ đưa ra một nhóm gốc cần điều tra.

## Demo có kiểm soát

Trên **Windows**, mở terminal tại thư mục repository của lab đã cấu hình:

```powershell
python .\system-monitor\system_lab.py status

# Chọn một tình huống mỗi lần
python .\system-monitor\system_lab.py demo --fault nginx
python .\system-monitor\system_lab.py demo --fault gateway
python .\system-monitor\system_lab.py demo --fault multi
python .\system-monitor\system_lab.py demo --fault storm
```

Các lệnh `demo` chủ động tạo lỗi, kiểm tra kết quả rồi phục hồi. Có timer rollback độc lập cho các can thiệp; demo storm dùng 20 kênh cảnh báo synthetic, không đại diện cho 20 VM hoặc 20 lỗi vật lý. Cần ba VM hoạt động, SSH/sudo đã cấu hình và thiết lập cục bộ theo [hướng dẫn vận hành](https://github.com/Darrys37/smb-network-monitoring/blob/feature/ml-research-v2/system-monitor/README.md).

Nếu demo bị ngắt, chạy lệnh phục hồi rồi kiểm tra lại trạng thái:

```powershell
python .\system-monitor\system_lab.py recover
python .\system-monitor\system_lab.py status
```

Các kịch bản V3 đã có hồ sơ kiểm chứng Nginx, gateway, nhiều lỗi và bão cảnh báo trong [báo cáo thực nghiệm](https://github.com/Darrys37/smb-network-monitoring/blob/feature/ml-research-v2/docs/HOAN_THIEN_HE_THONG_20261103.md). Hồ sơ ghi kết quả tại thời điểm thử; một README không thay thế việc kiểm tra baseline trước lần demo mới.

## Cấu trúc mã nguồn V3

| Đường dẫn | Nội dung |
|---|---|
| [`system-monitor/monitor.py`](https://github.com/Darrys37/smb-network-monitoring/blob/feature/ml-research-v2/system-monitor/monitor.py) | Điểm vào worker, xem danh mục luật và replay |
| [`system-monitor/monitoring/`](https://github.com/Darrys37/smb-network-monitoring/tree/feature/ml-research-v2/system-monitor/monitoring) | Thu bằng chứng, chuẩn hóa dữ liệu, thực thi luật, hàng đợi và tương quan |
| [`system-monitor/config/`](https://github.com/Darrys37/smb-network-monitoring/tree/feature/ml-research-v2/system-monitor/config) | Profile lab, topology và nguồn bảng quyết định |
| `system-monitor/catalog/` | Catalog SQLite được tạo khi triển khai bằng [`build_catalog.py`](https://github.com/Darrys37/smb-network-monitoring/blob/feature/ml-research-v2/system-monitor/build_catalog.py) |
| [`system-monitor/deployment/`](https://github.com/Darrys37/smb-network-monitoring/tree/feature/ml-research-v2/system-monitor/deployment) | Hướng dẫn và script triển khai |
| [`system-monitor/tests/`](https://github.com/Darrys37/smb-network-monitoring/tree/feature/ml-research-v2/system-monitor/tests) | Kiểm thử logic hệ thống |
| [`evidence/system-v3/`](https://github.com/Darrys37/smb-network-monitoring/tree/feature/ml-research-v2/evidence/system-v3) | Hồ sơ thử nghiệm và kết quả demo đã lưu |
| [`diagnosis-engine/`](https://github.com/Darrys37/smb-network-monitoring/tree/feature/ml-research-v2/diagnosis-engine) | Engine CLI gốc và thành phần API/thu số liệu được tái sử dụng |

## Phạm vi và giới hạn

Hệ thống được kiểm chứng trong lab 3 VM, chưa thử trên máy Ubuntu vật lý và chưa đánh giá tải vận hành doanh nghiệp. CPU cao, lỗi DNS hay mất kết nối là dấu hiệu hỗ trợ điều tra; kết luận phải đi cùng chất lượng và thời điểm của bằng chứng.

Worker V3 không tự sửa hạ tầng và chưa tích hợp gửi thông báo ra email/chat. Token, private key, môi trường Python và database runtime được cấu hình riêng; GitHub không thay thế backup VM, MySQL hoặc dữ liệu vận hành.

Nhật ký theo tuần và các phiên bản cũ được giữ trong tài liệu lịch sử để truy vết; chúng không phải hướng dẫn vận hành V3 hiện tại. Xem [mục lục tài liệu](https://github.com/Darrys37/smb-network-monitoring/blob/feature/ml-research-v2/docs/README.md) để chọn đúng phần cần đọc.

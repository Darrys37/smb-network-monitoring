# Hệ thống giám sát tập trung và hỗ trợ chẩn đoán sự cố mạng

Đồ án xây dựng hệ thống giám sát hạ tầng mạng doanh nghiệp nhỏ bằng **Zabbix 7.0 LTS và Worker Python V3**. Worker tự động tiếp nhận sự kiện, kiểm tra thêm bằng chứng và đối chiếu bảng quyết định SQLite để hỗ trợ người quản trị xác định vấn đề cần điều tra.

## Báo cáo và thuyết trình

- **[Báo cáo đồ án — Word](docs/bao-cao/Bao_cao_do_an.docx)**
- **[Slide thuyết trình đầy đủ — PowerPoint](docs/bao-cao/Bao_ve_do_an.pptx)**

## Hệ thống làm gì?

Zabbix phát hiện bất thường. Worker bổ sung bằng chứng để phân biệt các tình huống như máy mất kết nối, dịch vụ web dừng, đường truy cập bị cản trở hoặc gateway gặp sự cố. Kết quả gồm **nguyên nhân nghi ngờ, luật khớp và bằng chứng giải thích**.

```text
Zabbix thu thập dữ liệu và tạo sự kiện
                  ↓ Zabbix API
Worker tiếp nhận sự kiện và đưa vào hàng đợi
                  ↓
Kiểm tra thực tế, tổng hợp đặc trưng và độ mới của bằng chứng
                  ↓
Đối chiếu 8 luật trong bảng quyết định SQLite
                  ↓
Gom nhóm, xử lý phụ thuộc và lưu lịch sử
                  ↓
Báo cáo chẩn đoán và trạng thái phục hồi
```

Worker chạy nền bằng systemd trên MON01. Các luật được xét độc lập nên có thể nhận diện nhiều vấn đề cùng lúc. Worker hỗ trợ chẩn đoán; người quản trị xử lý sự cố, còn công cụ demo chỉ tạo và hoàn tác lỗi thử nghiệm.

## Mô hình triển khai

| Máy ảo | IP quản trị | Vai trò |
|---|---|---|
| MON01 | `192.168.56.10` | Zabbix Server, MySQL, Worker Python và SQLite |
| CLI01 | `192.168.56.30` | Gateway, IP mạng dịch vụ `172.30.20.1` |
| SRV01 | `192.168.56.20` | Nginx, Zabbix Agent2, IP dịch vụ `172.30.20.20` |

Đường dịch vụ đi theo **MON01 → CLI01 → SRV01**. Đường quản trị riêng giúp kiểm tra trực tiếp dịch vụ ngay cả khi đường dịch vụ bị gián đoạn. `CLI01-Gateway` và `SRV01-Routed` trong Zabbix là đối tượng giám sát, không phải máy ảo bổ sung.

Zabbix lưu dữ liệu giám sát trong MySQL. Worker lấy thông tin qua Zabbix API và dùng SQLite để lưu bảng quyết định, sự kiện, hàng đợi, bằng chứng và kết quả chẩn đoán.

## Đầu vào và đầu ra

**Đầu vào:** sự kiện Zabbix, kết quả kiểm tra thực tế và cấu hình quan hệ phụ thuộc. Bảy nhóm đặc trưng chính gồm ICMP/Ping, TCP/80, mã HTTP, thời gian phản hồi DNS, tài nguyên CPU/RAM, Zabbix Agent và trạng thái nút cha. Một số luật còn cần trạng thái dịch vụ trực tiếp, lịch sử CPU hoặc số sự kiện trong cửa sổ thời gian.

**Đầu ra:** nhóm sự cố, nguyên nhân nghi ngờ, luật khớp, bằng chứng giải thích và lịch sử phục hồi. Dữ liệu thiếu hoặc quá cũ được ghi nhận tương ứng; không mặc định phép kiểm tra thất bại là bằng chứng chắc chắn của một nguyên nhân.

## Cơ sở tri thức: 8 luật chẩn đoán

| Luật | Tình huống hỗ trợ nhận diện |
|---|---|
| R1 | Máy đích hoặc đường kết nối tới máy đích gặp sự cố |
| R2 | Dịch vụ web có dấu hiệu ngừng hoạt động |
| R3 | Zabbix Agent hoặc kết nối tới Agent gặp vấn đề |
| R4 | Phân giải DNS gặp sự cố trong khi kết nối IP đối chứng vẫn hoạt động |
| R5 | Truy cập HTTP từ xa lỗi nhưng web tại IP dịch vụ vẫn trả HTTP 200 |
| R6 | CPU quá tải kéo dài, có đủ lịch sử và bằng chứng đối chứng |
| R7 | Gateway/nút cha có bằng chứng không hoạt động còn mới |
| R8 | Ít nhất 10 sự kiện lỗi khác nhau trong cửa sổ 30 giây |

Xem [điều kiện chi tiết của bảng quyết định](system-monitor/config/expert_seed.json). R2 và R5 cùng thuộc nhóm HTTP nên có **8 luật thuộc 7 nhóm**. R8 nhận diện bão cảnh báo, không tự xác định nguyên nhân gốc của toàn bộ cảnh báo.

Worker gom cảnh báo trong cửa sổ **30 giây** và theo topology. Khi nút cha gặp lỗi, cảnh báo phụ thuộc được gắn về nhóm gốc; sự kiện nguồn vẫn được giữ. Lỗi độc lập có thể tiếp tục xuất hiện trong kết quả. Các điểm ưu tiên do chuyên gia thiết kế không phải xác suất chẩn đoán đã hiệu chỉnh.

## Minh họa hoạt động

Khi Nginx trên SRV01 ngừng hoạt động, máy vẫn phản hồi Ping nhưng kết nối TCP/80 bị từ chối, không có phản hồi HTTP và trạng thái dịch vụ tại máy là `inactive`. Worker đối chiếu các bằng chứng này, áp dụng R2 và gom các cảnh báo liên quan thành nhóm sự cố dịch vụ web trên SRV01.

Sau khi dịch vụ được khôi phục, các phép đo trở lại bình thường và hệ thống cập nhật trạng thái phục hồi. Kết quả được lưu trong SQLite để đối chiếu quá trình phát hiện và phục hồi.

| Thông tin đầu ra | Ý nghĩa |
|---|---|
| Sự kiện lỗi đang hoạt động | Những bất thường chưa ghi nhận phục hồi |
| Nhóm sự cố | Các cảnh báo liên quan được gom theo thời gian và topology |
| Luật khớp và bằng chứng | Cơ sở đề xuất nguyên nhân cần điều tra |
| Cảnh báo phụ thuộc | Các cảnh báo được gắn về sự cố nút cha để giảm nhiễu |
| Trạng thái phục hồi | Ghi nhận kết quả kiểm tra sau khi khắc phục |

## Mã nguồn và triển khai

```bash
git clone https://github.com/Darrys37/smb-network-monitoring.git
cd smb-network-monitoring
```

| Đường dẫn | Nội dung |
|---|---|
| [system-monitor/](system-monitor/) | Worker V3 và công cụ vận hành |
| [system-monitor/monitoring/](system-monitor/monitoring/) | Thu bằng chứng, hàng đợi, thực thi luật và tương quan |
| [system-monitor/config/](system-monitor/config/) | Cấu hình lab, topology và bảng luật nguồn |
| [system-monitor/deployment/](system-monitor/deployment/) | Hướng dẫn triển khai |
| [system-monitor/tests/](system-monitor/tests/) | Kiểm thử logic |
| [docs/bao-cao/](docs/bao-cao/) | Báo cáo và slide thuyết trình |
| [evidence/system-v3/](evidence/system-v3/) | Hồ sơ kiểm chứng đã công bố |
| [diagnosis-engine/](diagnosis-engine/) | Thành phần nền được worker tái sử dụng |

Môi trường mới cần cấu hình Zabbix, mạng, SSH và thông tin xác thực theo [hướng dẫn triển khai](system-monitor/deployment/README.md). Repository chưa phải bộ cài đặt tự động từ máy trống. Không đưa token, mật khẩu, khóa riêng hoặc dữ liệu vận hành nhạy cảm lên GitHub.

## Phạm vi thực nghiệm

Đồ án được kiểm chứng trên **3 VM Ubuntu Server trong VirtualBox**. Chưa kiểm chứng trên máy vật lý hoặc đánh giá tải doanh nghiệp. Khả năng chẩn đoán giới hạn bởi bằng chứng thu thập được và các luật đã xây dựng; kết quả là hỗ trợ điều tra, không bảo đảm xác định duy nhất nguyên nhân.

GitHub lưu mã nguồn và tài liệu. Để phục hồi toàn bộ lab cần sao lưu riêng VM, dữ liệu MySQL, SQLite và cấu hình cục bộ.

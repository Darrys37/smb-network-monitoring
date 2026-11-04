> Bản dùng để chuyển chat/tài khoản. Nguồn: `docs/GIOI_THIEU_VA_GIAI_THICH_DO_AN.md` tại `8df20a7bd5143ba0210b5116a1cc26fcc0a53366`.
> Nội dung lấy từ tài liệu nguồn; các liên kết được đổi để dùng ngoài project. Đọc file 01 về trạng thái cuối phiên trước khi tiếp tục.

# Giới thiệu đồ án — Worker V3

Đề tài: **Xây dựng hệ thống giám sát tập trung, cảnh báo và hỗ trợ chẩn đoán sự cố cho hạ tầng mạng doanh nghiệp nhỏ.** Phiên bản chính nằm trên nhánh `main` của repository.

## Hệ thống giải quyết việc gì?

Zabbix phát hiện dấu hiệu bất thường, chẳng hạn không kết nối được cổng web. Worker Python tự lấy sự kiện, thu thêm bằng chứng và so với bảng quyết định trong SQLite để hỗ trợ người quản trị khoanh vùng nguyên nhân. Khi nhiều cảnh báo xuất hiện cùng đợt, worker dùng quan hệ phụ thuộc để gom nhóm và giữ riêng các lỗi độc lập.

Ví dụ: Nginx dừng nhưng máy còn sống thì ping vẫn thành công, TCP/80 bị từ chối và probe cục bộ đọc được Nginx inactive. R2 khớp và các cảnh báo web được gom về nhóm dịch vụ SRV01. Sau khi người vận hành bật lại Nginx, worker tiếp tục quan sát để ghi nhận phục hồi.

## Mô hình ba VM

| Máy | Địa chỉ | Vai trò |
|---|---|---|
| MON01 | `192.168.56.10` | Zabbix 7.0 LTS, MySQL và worker Python |
| CLI01 | `192.168.56.30` / `172.30.20.1` | Gateway chuyển tiếp và máy quan sát DNS |
| SRV01 | `192.168.56.20` / `172.30.20.20` | Nginx và Zabbix Agent2 |

Đường dịch vụ từ MON01 tới `172.30.20.20` đi qua CLI01. Các địa chỉ `192.168.56.x` giữ chức năng quản trị, nhờ đó vẫn đọc được trạng thái Nginx khi gateway không chuyển tiếp. Hai host logic `CLI01-Gateway` và `SRV01-Routed` trong Zabbix không phải hai VM bổ sung.

## Đầu vào và kết quả

Bảy nhóm đặc trưng gồm ICMP, TCP/80, HTTP, DNS, tài nguyên CPU/RAM, Agent và nút cha. Các phép đo có timestamp và được kiểm độ mới, không giả định mọi chỉ số được lấy cùng một thời điểm tuyệt đối.

Tám luật thuộc bảy nhóm: R1 kết nối; R2 dịch vụ HTTP; R3 Agent; R4 DNS; R5 đường truy cập HTTP; R6 CPU cao kéo dài; R7 gateway/nút cha; R8 bão cảnh báo. R2 và R5 cùng thuộc nhóm HTTP.

Kết quả gồm trạng thái từng luật, bằng chứng, giả thuyết, hướng kiểm tra tiếp và nhóm sự cố sau tương quan. Một observation có thể khớp nhiều luật; hệ thống không ép mọi lỗi vào một nguyên nhân.

## Ranh giới cần hiểu

- Worker tự chẩn đoán và theo dõi phục hồi; người quản trị/helper thực hiện khắc phục.
- Suppression gom cảnh báo phụ thuộc vào nhóm gốc, giữ nguyên sự kiện nguồn trong Zabbix và SQLite.
- `matched` là phù hợp dấu hiệu. Điểm 85/65/45% là ưu tiên điều tra do chuyên gia gán, chưa phải xác suất đúng đã hiệu chỉnh.
- Hệ thống hiện được kiểm chứng trên ba VM, chưa có thử nghiệm máy Ubuntu vật lý hoặc tải production.

Đọc [logic V3](03_LOGIC_DIAGNOSIS_ENGINE.md), [hướng dẫn vận hành](https://github.com/Darrys37/smb-network-monitoring/blob/8df20a7bd5143ba0210b5116a1cc26fcc0a53366/system-monitor/README.md) và [hồ sơ kiểm chứng](https://github.com/Darrys37/smb-network-monitoring/blob/8df20a7bd5143ba0210b5116a1cc26fcc0a53366/docs/KIEM_CHUNG_WORKER_V3.md) để đi sâu hơn.

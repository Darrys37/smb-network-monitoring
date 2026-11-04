# Logic Worker V3 và bản đồ mã nguồn

Luồng chính là **Zabbix → lưu sự kiện/hàng đợi → thu bằng chứng → bảng quyết định SQLite → tương quan topology → báo cáo và lịch sử**.

## Một vòng xử lý

1. `monitor.py watch` khởi tạo worker; service systemd chạy nó trên MON01. Chỉ một worker được giữ lock cho cùng runtime DB.
2. `monitoring/worker.py` đọc event/recovery mới từ Zabbix. Lưu sự kiện, job và cursor trong transaction; sự kiện trùng ID không được tạo thành lần mới. Khi khởi tạo runtime, worker bổ sung các problem đang mở để không bỏ sót lỗi cũ.
3. Cập nhật trạng thái các node. Gateway được kiểm tra forwarding, interface và route, không chỉ ping.
4. Các job cùng node dùng chung một lần thu bằng chứng trong vòng. Worker còn làm mới probe định kỳ 30 giây khi không có event mới.
5. `collector.py` thu ping/TCP từ MON01, số liệu từ Zabbix và probe đọc qua SSH giới hạn quyền. HTTP/dịch vụ được đo trên SRV01; DNS của cấu hình lab được quan sát tại CLI01.
6. `facts.py` kiểm tra định dạng, nguồn, độ mới và lịch sử CPU. Lỗi nguồn được giữ rõ; job chưa hoàn tất được thử lại, không tạo số liệu giả để đánh dấu thành công.
7. `catalog.py` đọc điều kiện từ SQLite và dùng bộ so khớp chung. Chọn hàng đầu tiên khớp trong từng luật; các luật độc lập với nhau.
8. `correlation.py` dùng topology và bằng chứng parent down còn mới để gom cảnh báo. Lỗi dịch vụ đo độc lập, DNS hoặc CPU không tự bị mất chỉ vì gateway hỏng.
9. Kết quả được lưu vào `diagnostics` và `batches`. `report.py` đọc trạng thái đã xử lý, không khởi chạy thêm worker.

Khoảng chờ polling mục tiêu là 5 giây, thời gian thực còn phụ thuộc API/probe; không suy ra độ trễ phát hiện luôn bằng 5 giây.

## Các file chính

| File dưới `system-monitor/` | Vai trò |
|---|---|
| `monitor.py`, `monitoring/worker.py` | Điểm vào và điều phối |
| `monitoring/collector.py`, `probes.py` | Thu dữ liệu API và phép đo chủ động |
| `monitoring/facts.py`, `vector.py` | Chuẩn hóa, kiểm chất lượng và tạo vector |
| `monitoring/catalog.py`, `expressions.py` | Đọc và đánh giá điều kiện SQLite |
| `monitoring/topology.py`, `correlation.py` | Quan hệ phụ thuộc và gom nhóm |
| `monitoring/store.py` | Sự kiện, cursor, job và kết quả bền vững |
| `report.py` | Xem kết quả |
| `fault_control.py`, `storm_control.py` | Công cụ tạo/hoàn tác lỗi lab, tách khỏi worker |

Engine CLI nền trong `diagnosis-engine` được giữ để tái sử dụng API/thu số liệu và đối chiếu. Người vận hành V3 dùng service worker cùng `system-monitor/report.py`; không cần nhập từng event ID vào `app.py` để worker hoạt động.

## Điều kiện cần chú ý

| Luật | Ý nghĩa và điều kiện chính |
|---|---|
| R1 | Ping đích no_reply, TCP80 timeout, máy đối chứng success; chưa khẳng định đích đã tắt |
| R2 | Có Nginx inactive/failed hoặc chữ ký dịch vụ/listener phù hợp; TCP refused riêng lẻ chưa chứng minh duy nhất Nginx dừng |
| R3 | Agent cục bộ inactive/failed hoặc thiếu mẫu mới kèm điều kiện kết nối phù hợp |
| R4 | DNS có kết quả lỗi/timeout có nghĩa, trong khi IP đối chứng cùng observer còn tốt |
| R5 | Ping thành công, TCP80 từ xa timeout/refused, HTTP tại đúng IP dịch vụ trả 200; cần kiểm thêm firewall/route để chốt nguyên nhân |
| R6 | CPU trung bình ≥ 90%, ít nhất 3 mẫu, độ phủ ≥ 240 giây, khoảng cách mẫu ≤ 120 giây, mẫu mới còn hợp lệ; load ≥ số CPU |
| R7 | Nút cha được cấu hình có bằng chứng down còn mới; lỗi con không tự chứng minh parent down |
| R8 | Ít nhất 10 sự kiện lỗi khác nhau trong cửa sổ 30 giây; sau khi cửa sổ trượt, luật có thể không còn khớp dù cảnh báo còn mở |

Điều kiện chi tiết ở [expert_seed.json](../system-monitor/config/expert_seed.json), gồm 8 luật / 40 hàng quyết định. [build_catalog.py](../system-monitor/build_catalog.py) tạo catalog mới; runtime mở catalog chỉ đọc và cache theo phiên. Muốn đổi luật cần tạo phiên bản mới, kiểm thử rồi restart với catalog phù hợp; không sửa ngầm catalog để làm demo khớp.

## Nhóm sự cố và suppression

`ROOT cli01 | dependency` nghĩa là một nhóm gốc liên quan phụ thuộc CLI01 theo bằng chứng và topology. `ROOT srv01 | http_service` là nhóm dịch vụ HTTP trên SRV01. ROOT là kết quả tương quan, không phải phán quyết chắc chắn duy nhất về nguyên nhân vật lý.

Các cảnh báo phụ thuộc thuộc cùng đợt được gắn về parent down. Cảnh báo con có trước lỗi parent quá cửa sổ 30 giây không tự bị quy ngược. Nginx inactive đọc qua đường quản trị riêng vẫn là lỗi độc lập khi gateway không chuyển tiếp, vì vậy có thể giữ cả hai nhóm.

## Dữ liệu và kiểm thử

`runtime/monitoring.sqlite` chứa sự kiện, cursor, jobs, diagnostics, batches và trạng thái node. Nó độc lập với MySQL của Zabbix và không đưa vào Git. Dọn tài liệu/evidence cũ không phải thao tác xóa runtime hoặc xóa lịch sử cảnh báo.

Regression V3 dùng observation đã đóng gói tại [tests/fixtures](../system-monitor/tests/fixtures); test engine nền có fixture riêng trong [diagnosis-engine/tests](../diagnosis-engine/tests). Các thư mục evidence theo tuần không phải đầu vào runtime của V3.

Xem [hướng dẫn chạy và phục hồi](../system-monitor/README.md), [kiểm chứng](KIEM_CHUNG_WORKER_V3.md) và [mục lục bằng chứng](../evidence/README.md).

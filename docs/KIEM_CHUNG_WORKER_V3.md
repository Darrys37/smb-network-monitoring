# Kiểm chứng Worker V3 trên nhánh chính

Worker V3 là phiên bản chính của đồ án: Zabbix → worker Python → bằng chứng → bảng quyết định SQLite → tương quan cảnh báo → hồ sơ chẩn đoán và phục hồi.

## Những gì có trong bản main

- Worker chạy bằng systemd, xử lý cả sự kiện lỗi và phục hồi; cursor và queue được lưu trong SQLite.
- 8 luật thuộc 7 nhóm sự cố, 40 hàng quyết định và vector 7 nhóm đặc trưng.
- Mạng dịch vụ đi qua CLI01 tới IP `172.30.20.20` của SRV01; đường quản trị riêng phục vụ probe cục bộ.
- Công cụ demo Nginx, gateway, multi-fault và 20 kênh cảnh báo thử; có rollback độc lập.
- Helper SSH và cấu hình operator nằm trong `tools/`, không cần thư mục nghiên cứu để chạy V3.
- Observation phục vụ regression được đóng gói dưới `system-monitor/tests/fixtures`, có nguồn gốc và SHA256; test không phụ thuộc vị trí project trên laptop ban đầu.

## Kết quả thử lab đã lưu

Các kết quả sau thuộc lượt thử ngày 03/11/2026, không phải các phép tạo lỗi mới trong lần đưa source lên main.

| Tình huống | Kết quả ghi nhận |
|---|---|
| Gateway tắt forwarding | 6 sự kiện hoạt động → 1 nhóm CLI01, 4 cảnh báo con bị ức chế |
| Gateway + 20 kênh synthetic | 26 sự kiện → 1 nhóm, 24 cảnh báo bị ức chế, queue đã xử lý hết |
| Gateway và Nginx cùng lỗi | 6 sự kiện → 2 nhóm; giữ lỗi dịch vụ độc lập |
| Wrapper Nginx | Phát hiện nhóm dịch vụ rồi phục hồi hoàn toàn |
| Wrapper multi | Giữ 2 nhóm, phục hồi hoàn toàn |
| Wrapper storm | Tương quan/ức chế cảnh báo thử rồi phục hồi hoàn toàn |

Các lượt có thể có số cảnh báo khác nhau do thời điểm poll và cửa sổ trigger. 20 kênh synthetic không đại diện cho 20 VM hoặc 20 sự cố vật lý. Suppression ở module giữ nguyên sự kiện nguồn trong Zabbix và SQLite.

[Biên bản trích xuất kết quả hệ thống](../evidence/system-v3/main-release/historical-system-verification.json) giữ checksum và liên kết đến hồ sơ gốc. Trích xuất chỉ chọn các trường của hệ thống chuyên gia; không sửa dữ liệu thí nghiệm cũ để biến thành kết quả mới.

## Kiểm tra bản source đưa lên main

[Biên bản kiểm tra phát hành](../evidence/system-v3/main-release/source-validation.json) ghi kết quả kiểm thử, tạo catalog từ seed và kiểm tra các điểm vào CLI trên bản source đã tách phụ thuộc. Đây là kiểm tra offline; không thay thế một lần tạo lỗi live trên VM.

Từ thư mục repository:

```powershell
python -m pip install -r .\system-monitor\requirements-operator.txt
Push-Location .\system-monitor
python -m unittest discover -s tests -v
Pop-Location
python .\system-monitor\build_catalog.py
python .\system-monitor\monitor.py rules
python .\system-monitor\system_lab.py --help
```

Chỉ chạy `build_catalog.py` khi catalog chưa tồn tại; script từ chối ghi đè. Các snapshot regression là dữ liệu lịch sử cho kiểm tra tương thích, không được tính thành lượt fault mới hoặc dùng để công bố accuracy trên mạng doanh nghiệp.

## Giới hạn cần trình bày đúng

Mô hình hiện có 3 VM, chưa có máy Ubuntu vật lý và chưa kiểm tải production. `matched` nghĩa là dấu hiệu phù hợp luật; điểm ưu tiên giả thuyết không phải xác suất đúng đã hiệu chỉnh. Worker không tự sửa hạ tầng hoặc gửi email/chat.

R6 yêu cầu lịch sử CPU và các kiểm tra chất lượng, không chỉ một mẫu cao. R8 yêu cầu đủ sự kiện mới trong 30 giây; việc nhìn thấy 20 cảnh báo đang mở không tự chứng minh R8 đã khớp đúng cửa sổ. Xem [hướng dẫn vận hành](../system-monitor/README.md) để hiểu cách đọc kết quả và phục hồi.

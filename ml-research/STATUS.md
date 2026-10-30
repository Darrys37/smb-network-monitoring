# Tiến độ triển khai ML v2 — 30/10/2026

- M0: backup local đã phục hồi kiểm tra; sau đó backup runtime/source trên ba VM trước thử nghiệm. MON01 có SQLite backup nhất quán và bản .env lưu tại VM với quyền hạn chế; không đưa secret vào Git.
- M1: đã có data dictionary, label map, protocol và split policy trong docs/ và config/.
- M2: đã có registry append-only, observation validator và collector độc lập nhãn. 8 tests mới đạt; baseline engine 369 tests đạt.
- M2 live: SRV01 thu 13 evidence; CLI01 thu 12 evidence, HTTP not_applicable theo profile. Không có source error.
- M3: bắt đầu một lượt pilot dừng Nginx trên SRV01, thu hai cửa sổ cùng Run ID, xác minh dịch vụ inactive, Zabbix event 1144, rồi bật lại Nginx và kiểm tra HTTP200. Có timer failsafe và log độc lập.
- Hai snapshot trong fault là một lượt, không phải hai sự cố độc lập. Các smoke observations có planned healthy nhưng vẫn pending review; không được tính vào tập healthy valid.
- Background CLI01 có event 1143 về OS description thay đổi; ghi nhận riêng, không tự đóng hoặc đổi cấu hình Zabbix.
- Chưa hoàn tất pilot 42 lượt/nhiều phiên. Chưa có tập test độc lập, chưa huấn luyện mô hình v2 hoặc kích hoạt luật ML.

Việc tiếp theo: hoàn thiện run scheduler/fault scripts cho R1/R3/R4/R5/R6 với rollback, thu pilot theo protocol, dựng quality report và kiểm tra shortcut trước khi train. Healthy cần review độc lập; điều chỉnh các profile để không để một lớp chỉ thuộc một host.

Evidence thật nằm trong `evidence/ml-v2` ở root repository. Phiên bản engine baseline được giữ nguyên; M1/M2 được thêm như module riêng trên nhánh feature/ml-research-v2.

Postflight đã xác minh event 1144 có recovery 1145; SRV01 không còn problem mở, Nginx active và HTTP200. Source engine trên MON01 và số hàng SQLite runtime không đổi.

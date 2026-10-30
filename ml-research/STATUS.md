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

## M3 — kết quả đợt pilot đầu

Đã chạy 10 attempt trong pilot-v2-s01; 7 attempt hợp lệ, 3 attempt uncertain được giữ nguyên. Có đủ bảy trạng thái (healthy + sáu fault) ở SRV01. Retry có ID và parent riêng, không ghi đè lượt cũ. Có 24 cửa sổ đo toàn bộ, không được coi là từng ấy sự cố độc lập.

Đã thêm scheduler 42 lượt có resume, fault/rollback scripts, source execution snapshots, quality report và CSV pilot. CSV dùng cửa sổ cuối mỗi valid run, feature whitelist tách metadata. Chưa train v2; chưa có phiên test độc lập.

Bộ kiểm thử ML hiện có 22 tests đạt, gồm lỗi timer đã hết, cửa sổ sau deadline failsafe, lệch clock giữa máy, provenance và ghi JSON không để lại file dở. Baseline 369 tests đã chạy đạt ở mốc trước; source engine không đổi.

Lỗi điều phối đã phát hiện: cleanup timer đã bị systemd thu hồi; timestamp giây nguyên khác máy làm ranh giới rollback chưa chắc chắn. Đã giữ log lỗi, bổ sung timer LoadState và coordinator monotonic timeline; chạy retry riêng. Phiên đầu chưa có source manifest lúc khởi chạy được ghi là pilot debug, không dùng làm test cuối.

Postflight: Nginx/Agent active, HTTP200, DNS/control tốt, interface enp0s8 UP; không còn firewall table/timer mlv2. Engine source và 39 incidents runtime không đổi; SQLite integrity ok.

Tiếp theo: hoàn tất các lượt/phiên còn lại theo lịch và audit; chưa đủ cơ sở tính accuracy/FPR tổng quát. Tổng hợp chi tiết tại evidence/ml-v2/quality/QUALITY.md.

## Cập nhật ML ngày 30/10/2026, khoảng 17:15 UTC+7

Đây là trạng thái đang chạy, không phải xác nhận đã hoàn tất ML. Nhánh local `feature/ml-research-v2`; checkpoint trước tiếp tục `89c9848`. Engine baseline không sửa. Ba VM đang dùng cho pilot, không coi ghi chú shutdown ngày 17/10 bên dưới là hiện trạng live.

- Đã backup trước tiếp tục ở C:/D:, bundle/ZIP phục hồi được; có backup runtime nhất quán trên MON01. Backup bổ sung dữ liệu dở dang: `before-pilot-resume-20261030T095935920203Z`, hash archive `fa448bbb93751f9c694d8e8ef579e545d79364fae9abac0bca560c107e91764e`.
- Pilot mới: 14 valid, 4 uncertain tại mốc kiểm tra; lượt CPU tiếp theo đang chạy. Lượt bị ngắt được audit và retry riêng, không sửa thành valid. Chỉ dùng dữ liệu trong `evidence/ml-v2`, không chép đè từ workspace stage cũ.
- M4 đã có CART numeric/discrete, FP-classifier, ablations, grouped validation, export candidate SQLite và wrapper demo shadow. **32 tests đạt**, replay expert trên 7 quan sát thật tạo 42 assessment; chưa fit ML vì lịch thu chưa đủ.
- Hai tiến trình tại mốc này: coordinator PID 5468, supervisor PID 18004. Supervisor chờ coordinator kết thúc trước khi tiếp quản; không chạy hai bộ gây lỗi đồng thời. PID có thể đổi/kết thúc; phải kiểm tra trạng thái thật.
- Trạng thái cập nhật: `C:\Users\Darrys\Documents\ChatGPT\Đồ án network\verification\ml-supervisor-status.json`; log cùng thư mục `ml-supervisor.log`. Mật khẩu chỉ nằm trong RAM, không nằm trong file/config.
- Supervisor dự kiến hoàn tất các attempt hợp lệ cho 42 lượt, postflight, tests, export, benchmark pilot, replay và demo healthy shadow rồi backup. Chỉ coi xong khi phase=`COMPLETE_PILOT_M4`, có báo cáo thật, postflight đạt và `ml-research/AUTORUN_RESULT.md`. Nếu phase=`STOPPED_REQUIRES_REVIEW`, đọc lỗi/log; không mở thêm coordinator khi tiến trình cũ còn chạy.
- Kết quả M4 là pilot nội bộ; M5 test mới khóa riêng chưa thu, không công bố accuracy tổng quát hoặc khả năng chuyển sang PC thật. SQLite chỉ candidate, không tự active. M6/M7 mới có prototype/export và wrapper riêng, chưa thay engine vận hành.

Hướng dẫn: `ml-research/docs/HUONG_DAN_M4.md`. Chi tiết phương pháp/kế hoạch nằm cùng thư mục docs. Các thông tin nền dưới đây được giữ như bản bàn giao lịch sử.

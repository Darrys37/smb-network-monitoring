# ML research v2 — thu dữ liệu có kiểm soát

Đây là bộ công cụ M1/M2 theo kế hoạch đã duyệt. Collector không gây fault, không cần problem event, không ghi DB incident và không biết nhãn. Nó chạy được ở healthy cũng như trong fault. CLI điều phối từ laptop qua SSH, dùng source probe chuẩn của engine trong RAM trên observer; không cài đè source VM.

Đọc docs/DATA_DICTIONARY.md và docs/EXPERIMENT_PROTOCOL.md. Profile cho SRV01 và CLI01 nằm trong config/. Nhãn/thao tác và diagnostic family được tách ở config/labels.json.

Ví dụ từ thư mục module (Python có paramiko):

```powershell
python -m mlv2 --data-root outputs register --session pilot-session-01 --run run-001 --labels healthy
python -m mlv2 --data-root outputs collect --session pilot-session-01 --run run-001 --profile config/srv01.json --engine-source C:\Users\Darrys\do-an\diagnosis-engine
python -m mlv2 --data-root outputs review --session pilot-session-01 --run run-001 --validity valid --labels healthy --evidence path-to-independent-preflight.log
python -m unittest discover -s tests -v
```

Mật khẩu SSH được nhập ẩn mỗi lần, không lưu vào config/output. Host key phải có trong known_hosts. Collector ghi observation ngay cả khi một nguồn lỗi rồi trả exit=2; kết quả lỗi không tự trở thành bằng chứng fault. Profile/target sai thì dừng. Collector hiện chạy tuần tự; mẫu metric có thời gian riêng và history CPU không đồng thời với probe.

Đầu ra registry và observations tách thư mục; tệp không ghi đè. Review evidence được lưu theo hash để không mất khi file gốc đổi. Chỉ review có bằng chứng tham chiếu mới được valid; con người vẫn chịu trách nhiệm nội dung log, validator không chứng minh ground truth chỉ từ việc file tồn tại.

Phần feature/training v2 chưa được hoàn thành chỉ bởi collector này. POC v1 và các kết quả cũ được lưu trong backup riêng. Không gọi smoke test là pilot hay coi một observation là mẫu healthy hợp lệ trước khi review.

## Tiếp tục pilot

```powershell
python run_pilot.py --data-root outputs --engine-source C:\Users\Darrys\do-an\diagnosis-engine --max-runs 7
python export_dataset.py --data-root outputs --output outputs/quality
```

Lịch cố định có 42 lượt (hai session, ba lượt mỗi trạng thái/session), seed=37. Mặc định mỗi lần chạy tối đa bảy lượt mới. Chỉ bỏ qua lượt đã có RESULT; lượt đăng ký nhưng chưa có RESULT phải được xem xét trước khi tiếp tục, không tự ghi đè. Một session_id là block chạy do người vận hành định nghĩa; hai ID chạy liên tiếp không tự chứng minh độc lập thống kê.

Các fault đều tác động SRV01 trong pass đầu, kể cả DNS, để không gắn riêng nhãn DNS với CLI01. DNS được quan sát từ SRV01 theo profile và không có trigger DNS riêng trên SRV01 trong baseline; việc không có alert DNS không được bỏ qua khi đánh giá end-to-end.

CPU giữ khoảng 330 giây để có history; Agent giữ 210 giây để quan sát mất mẫu. Trước lượt tiếp theo, bộ chạy chờ history CPU bình thường, dịch vụ/HTTP/DNS/control tốt và không còn problem nghiêm trọng của SRV01. Thời gian toàn bộ pilot vì vậy có thể dài; không rút ngắn ngưỡng chỉ để chạy nhanh.

Fault interface-down có thể làm mất cả SSH tới observer. Source errors được lưu thật, còn timer độc lập bật lại interface. Firewall rollback chỉ xóa table mang token riêng của lượt; CPU rollback chỉ dừng unit stress của lượt. Timer được hủy sau rollback thành công để tránh chạy trễ trong lượt sau.

Execution-snapshots lưu source và hash khi mở mỗi batch mới. Batch đầu tiên trước khi thêm cơ chế này là dữ liệu pilot kiểm tra protocol, chưa có source manifest lúc khởi chạy; không dùng nó làm test cuối. Các script shell thực thi và log phải được lưu cùng evidence khi tổng kết.

Dataset export hiện chỉ là dữ liệu pilot, mỗi valid run một dòng. Feature whitelist gồm 7 cột trạng thái và 5 cột số, thuộc các nhóm quan sát đã công bố; chưa phải đúng bảy scalar. CPU mean chỉ có khi history đủ độ phủ; chưa thay thế toàn bộ semantics R6 vì chưa có load/core trong feature v2. Không gọi CSV này là bằng chứng mô hình đã đạt chất lượng.

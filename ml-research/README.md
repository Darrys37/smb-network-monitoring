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

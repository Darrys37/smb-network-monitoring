# Backup và xuất bản GitHub — 01/11/2026

Theo yêu cầu người dùng, cả MON01, SRV01 và CLI01 đã shutdown qua ACPI và được xác nhận **poweroff**. Không poweroff cưỡng bức, không tạo thêm fault hoặc chạy lại huấn luyện.

Backup lạnh mới: `D:\Study\network-monitoring-project\backups\cold-vms-after-ml-20261101T090139460860Z`. Tổng 45,829,268,563 byte (khoảng 45.83 GB), 56 tệp và 28 hard disk trong chuỗi cấu hình. SHA256 nguồn/bản sao khớp từng tệp; nguồn giữ nguyên trong lúc copy và mọi disk trong chuỗi đều có mặt. Chưa boot thử bản phục hồi. [Biên nhận](../evidence/maintenance/20261101-backup-publication/cold-backup-summary.json).

Backup source/tài liệu/evidence riêng được lưu trên C và D; receipt cuối ở `workflow-after-backup-latest.json` trong workspace điều phối. Backup này không chứa toàn bộ đĩa VM. GitHub cũng không chứa đĩa VM, .env, private key hoặc machine-local lab.local.json. Dữ liệu candidate SQLite thuộc nghiên cứu được giữ trong repo; database runtime/secret riêng vẫn ngoài Git.

Nhánh xuất bản là `feature/ml-research-v2`, không tự merge vào main hoặc force push. Receipt `github-push-latest.json` trong workspace ghi commit và remote ref sau khi push được xác minh; không dùng biên nhận cũ ngày 17/10 để suy trạng thái mới.

Khi chuẩn bị Git, phát hiện clean filter có thể đổi CRLF/LF của dữ liệu ML. Đã thêm quy tắc giữ raw byte evidence và pin newline từng source đã đóng băng theo byte gốc. Đây là sửa cách đóng gói Git, không sửa thuật toán, kết quả hoặc manifest nghiên cứu để hợp thức hóa checksum. Các thay đổi newline trong Git diff của evidence là lưu đúng byte thực đã được nghiệm thu.

Nguồn thực nghiệm vẫn ở mốc `8ba97a7bab5debb24f6eeb852fd59f49c66462d7`; runtime mới có 74 tests đạt và 88 observation replay khớp bản cũ. Chưa chạy lại fault live sau đổi wrapper/runtime. [Hướng dẫn quy trình](TOI_UU_QUY_TRINH_20261101.md) và [báo cáo/hướng dẫn tổng hợp](TONG_HOP_VA_HUONG_DAN_20261031/README.md).

# Bằng chứng Worker V3

Thư mục này giữ các hồ sơ ngắn phục vụ kiểm chứng phiên bản chính:

| File | Nội dung |
|---|---|
| [historical-system-verification.json](system-v3/main-release/historical-system-verification.json) | Kết quả các lượt thử lab đã lưu; có nguồn và checksum hồ sơ gốc |
| [source-validation.json](system-v3/main-release/source-validation.json) | Kiểm tra source khi đưa Worker V3 lên main |
| [system-tests.txt](system-v3/main-release/system-tests.txt) | Log kiểm thử source tương ứng |
| [docs-cleanup-validation.json](system-v3/main-release/docs-cleanup-validation.json) | Kiểm tra sau khi dọn docs/evidence, đối chiếu code và fixture |

Dữ liệu regression cần để chạy test được giữ ở [system-monitor/tests/fixtures](../system-monitor/tests/fixtures) và [diagnosis-engine/tests/fixtures](../diagnosis-engine/tests/fixtures). Đây là dữ liệu test lịch sử, không phải các lượt tạo lỗi mới.

Nhật ký, log và các export theo tuần đã đưa khỏi cây file main; bản trước khi dọn ở [nhánh lưu trữ](https://github.com/Darrys37/smb-network-monitoring/tree/archive/docs-evidence-before-cleanup-20261105/evidence). Có thể khôi phục file cũ từ đó hoặc từ lịch sử Git.

`runtime/monitoring.sqlite`, MySQL của Zabbix, cấu hình bí mật và đĩa VM là dữ liệu vận hành riêng. Chúng không nằm trong phần dọn tài liệu này. Sau một lần demo mới, lưu bộ hồ sơ có timestamp mới; không ghi đè bằng chứng cũ để trình bày như một phép thử mới.

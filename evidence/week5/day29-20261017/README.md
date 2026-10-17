# Tái tạo kết quả ngày 29

Chạy từ một thư mục làm việc riêng với Python 3 chuẩn và Node.js có @oai/artifact-tool:

1. `python day29_audit.py C:\Users\Darrys\do-an outputs/week5-day29-20261017`
2. `node day29_workbook.mjs` (đọc đường dẫn outputs ở trên, kiểm tra công thức, render, xuất XLSX).

Không chạy finalize để phân tích đơn thuần: script đó cài đầu ra vào project và archive, dùng đường dẫn máy hiện tại. Khi chuyển máy cần sửa đường dẫn tường minh.
Manifest ngày 29 chỉ phủ đầu ra mới; manifest tuần 4 giữ nguyên. Workbook dùng 18 dòng cố định theo Run ID; không sắp xếp riêng cột hoặc thêm/xóa dòng rồi coi đó là bản đã nghiệm thu.
CSV UTF-8 BOM, kiểu số khi đọc bằng csv là chuỗi: cần chuyển theo data-dictionary.json. Không điền giá trị thiếu bằng 0. Cột ID được giữ nguyên; timestamp dùng Unix UTC.
Không tái gán insufficient_evidence thành not_matched. Tỷ lệ mục tiêu dùng 18 fault hợp lệ, không dùng 19 attempt hoặc 108 đầu ra luật làm mẫu số.

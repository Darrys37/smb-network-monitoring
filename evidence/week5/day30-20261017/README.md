# Tái tạo bảng/hình ngày 30

Python 3 và matplotlib (phiên bản trong tools/requirements.txt). Công cụ phân tích tách khỏi môi trường engine.

`python tools/day30_analysis.py C:\Users\Darrys\do-an <thu_muc_dau_ra_moi>`

Script chỉ đọc project, xác minh manifest ngày 29, tính lại thống kê, tạo CSV/Markdown và 3 hình ở PNG/SVG/PDF. Không yêu cầu VM chạy.
Để dùng font tiếng Việt cần DejaVu Sans (đi kèm matplotlib). Giữ thư mục đầu ra mới để không ghi đè bản đã nghiệm thu.
`day30_install.py` là script cài bàn giao theo đường dẫn máy hiện tại; chỉ dùng khi đã kiểm tra hình, không cần cho tái tạo phân tích.
Các CSV cung cấp dữ liệu trung gian và kết quả thống kê; không phải workbook có công thức. Nguồn kiểm tra công thức nằm trong workbook ngày 29.
checksums.json dùng đường dẫn tương đối từ root project; không bao gồm chính nó hoặc Chương 3 vì Chương 3 tiếp tục được biên tập ngày 32.

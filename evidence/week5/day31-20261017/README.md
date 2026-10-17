# Ngày 31 — kiểm chứng kiến trúc

Snapshot chỉ đọc được thu qua SSH trên ba VM; mã tools/day31_remote_readonly.py không chứa mật khẩu/token. Trên MON01 chạy bằng Python trong venv của engine, trên SRV01/CLI01 bằng python3. Script gửi qua stdin, không cần cài hay sửa source trên VM.

`ssh phat@192.168.56.10 /home/phat/do-an/diagnosis-engine/.venv/bin/python - < day31_remote_readonly.py`

Ví dụ redirect trên áp dụng shell hỗ trợ `<`; với PowerShell dùng `Get-Content -Raw ... | ssh -T ... python -`. Xác thực do người vận hành thực hiện. Lưu stdout vào tệp JSON mới.
readonly-selects.sql là các SELECT đã chạy qua sudo mysql cục bộ; không lưu credential. critical-sql-terminal.txt giữ output terminal gốc (có ANSI), critical-sql-reviewed.json là cấu trúc đối chiếu.
architecture-audit.json công bố phạm vi: 28 item, 157 trigger API, 8 hàm SQL, 40 tệp source/test. Không đánh đồng cấu hình mẫu/export YAML với cấu hình hiệu lực.
day31_finalize.py dùng đường dẫn máy hiện tại và cài tài liệu, không chạy cho mục đích đọc snapshot đơn thuần. Chương 2 sẽ còn được biên tập theo mẫu nộp; không đưa bản Chương 2 đang biên tập vào manifest evidence bất biến.

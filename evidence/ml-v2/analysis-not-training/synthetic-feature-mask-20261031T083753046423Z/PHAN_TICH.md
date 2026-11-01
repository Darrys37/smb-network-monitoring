# Phân tích che feature giả định trên mô hình pilot

**Đây là vector giả định, không phải lượt thí nghiệm đã đo và không được đưa vào train/test.**

Chọn theo quy tắc cố định một observation healthy trong tập phát triển có Ping, TCP80, TCP10050 và control ping đều thành công. Chỉ thay local HTTP và DNS thành unknown; giữ nguyên reachability và giá trị CPU/RAM.

| Mô hình | Vector gốc | Sau che HTTP/DNS |
|---|---|---|
| CART | healthy | interface_down |
| FP-Growth | healthy | ABSTAIN |

Phép thử này giải thích hành vi logic của chính model/rule đã học; không ước lượng tần suất lỗi ngoài thực tế. Nếu nhãn interface_down xuất hiện khi core probes vẫn thành công, đó là ví dụ model có thể nhầm mất kênh quan sát với sự cố mạng trong trường hợp ngoài các lớp lab đã biết.

Giữ nguyên mô hình/config đã khóa; không đổi tham số hoặc chạy lại test vì phân tích này. Cần thêm dữ liệu lỗi nguồn đo và kiểm tra nhất quán triệu chứng trong nghiên cứu tiếp theo trước khi kích hoạt luật tự động. Confidence train không chứng minh tính đúng ở vector ngoài phân phối.

Tập test chính vẫn được giữ riêng theo protocol; phân tích này chỉ dùng pilot. Đường dẫn JSON đi kèm lưu đầy đủ vector, rule khớp và SHA để kiểm tra.

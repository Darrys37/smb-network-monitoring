# Protocol pilot v2.0

1. Đăng ký session/run và planned intervention trước khi thao tác. Lịch fault không truyền vào collector.
2. Xác minh giờ đồng bộ, dịch vụ nền, profile và mapping API. Ghi open problems đang có; không gán healthy nếu còn bất thường chưa giải thích.
3. Chạy bộ thu chung trước fault. Đặt failsafe/rollback trước mỗi can thiệp phần mềm.
4. Ghi fault markers và xác minh can thiệp bằng nguồn độc lập (service/interface/firewall/process). Không lấy output model làm nhãn.
5. Thu theo cùng lịch ở các trạng thái. Giữ source errors và mọi attempt; không chỉ giữ cửa sổ phân loại đúng.
6. Thu giai đoạn ổn định và transition riêng. CPU cần history đủ phủ; mẫu trước fault vẫn giữ nhưng phải được nhận diện trong feature builder.
7. Rollback; xác minh baseline phục hồi và chờ load/history ổn định trước lượt khác.
8. Review valid/invalid/uncertain dựa trên log độc lập. Healthy cũng cần kiểm tra, không suy từ không có matched.

Pilot đề xuất 2 phiên x 3 lượt x (6 fault + healthy); đảo thứ tự trong từng phiên, ghi seed/lịch. Đây là ngân sách kiểm tra protocol, không phải số mẫu đảm bảo chất lượng nghiên cứu. Có thể thêm lượt nhưng không được loại lượt hợp lệ vì không phát hiện/chẩn đoán thành công.

Định danh fault phải không đi vào feature. Khi collector không thu được target do down interface, lưu lỗi nguồn để phân biệt lỗi đo với không có tín hiệu; phiên bản ML đầu tiên cần phép thử missingness/shortcut trước tuning.

Chia tập theo session_id trước preprocessing. Các window cùng run phải cùng tập. Tập 18 lượt cũ là development đã nhìn thấy; pilot dùng kiểm tra protocol; thu phiên test mới sau khi khóa feature/params/abstention. Mọi encoder/bin/mining/pruning chỉ fit train. Không tối ưu và đánh giá cuối trên cùng test.

So sánh chuyên gia và ML trên cùng evidence tại cùng decision_time, theo diagnostic family. Giữ insufficient/abstain; không đổi not_matched thành healthy. Multi-fault và gateway/alert storm là các bộ thử riêng.

Điều kiện dừng pilot: bất thường nền chưa xác minh, lỗi timestamp/observer/mapping, thiếu failsafe, không xác minh được can thiệp hoặc baseline chưa phục hồi. Giữ log và đánh dấu validity; không sửa kết quả cho đẹp.

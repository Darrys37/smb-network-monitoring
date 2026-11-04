# Quay từng video bằng màn hình demo gọn

Từ thư mục repository, chạy `python system-monitor/video_demo.py` hoặc mở `tools/record_video.cmd`. Chọn một mã R1–R8; Enter mặc định chọn R5. Nhập mật khẩu lab trước khi bắt đầu quay. Cả ba VM phải đang chạy và baseline phải bình thường; chương trình sẽ tự kiểm tra.

Mỗi lượt chỉ tạo **một video**, không tự chuyển qua các lỗi khác.

1. **HỆ THỐNG ĐANG BÌNH THƯỜNG:** bấm ghi hình; đọc tên tình huống rồi nhấn Enter.
2. **ĐÃ TẠO LỖI:** nói “Worker đang tự kiểm tra bằng chứng và đối chiếu luật.” Không cần gõ thêm lệnh.
3. **ĐÃ PHÁT HIỆN:** chỉ vào các dòng bằng chứng, đọc câu KẾT LUẬN. Thuyết minh xong nhấn Enter để phục hồi.
4. **ĐÃ PHỤC HỒI — HỆ THỐNG BÌNH THƯỜNG:** đọc “Sau khi khôi phục, hệ thống xác nhận hoạt động bình thường”, dừng quay và lưu video riêng.

Không cần mở thêm màn hình JSON, Zabbix hay terminal khác trong video ngắn. Màn hình này lấy kết quả worker thật, không dựng kết luận có sẵn. Có thể quay thêm Zabbix trong đoạn phụ nếu muốn đối chiếu.

## Nên quay tiếp tình huống nào?

R2 đã có thì giữ lại. Quay R5 tiếp theo để thấy khác biệt: **R2 dịch vụ dừng; R5 dịch vụ còn chạy nhưng truy cập từ xa bị chặn**. Sau đó có thể quay R3, R4, R1, R7, R8; để R6 cuối vì cần khoảng 5–6 phút thu lịch sử CPU và thêm thời gian xác nhận phục hồi.

## Khi kết quả chưa đạt

Nếu hiện “LƯỢT DEMO CHƯA HOÀN TẤT”, không dùng lượt đó làm video thành công. Chương trình thử thu hồi lỗi trong cleanup và còn timer phục hồi độc lập trong VM. Nếu Windows/VM mất kết nối, phải kiểm tra trạng thái lại; không mặc nhiên coi timer đã làm xong.

Các lỗi có thời gian phục hồi dự phòng. Nếu nói quá lâu ở bước 3, lỗi có thể đã tự hết; bảng ghi rõ thời điểm worker thu bằng chứng. Nhấn Enter vẫn thực hiện kiểm tra phục hồi. Không kéo dài lỗi vô hạn để giữ màn hình.

R8 dùng 20 kênh cảnh báo thử, không phải 20 VM. R7 yêu cầu có cả luật khớp và cảnh báo con được gom. Chương trình không hiện thành công chỉ vì đã gửi lệnh tạo lỗi.

Hồ sơ thật của mỗi lượt được lưu dưới `evidence/system-v3/video-demos/<thời điểm>/<mã lượt>/`. Mật khẩu không được lưu. Worker không bị đổi luật hay thay bằng mô hình dự đoán khác.

Chế độ mới đã được kiểm tra bằng các bài offline; chưa coi 8 lượt tạo lỗi live là đã nghiệm thu chỉ từ kết quả kiểm tra source.

## Điều khiển dành riêng cho người trình bày

Màn hình chiếu không hiện lời nhắc quay phim hoặc nhấn phím. Người trình bày nhớ ba điểm dừng im lặng: bước 1 nhấn Enter để tạo lỗi; bước 3 nhấn Enter để phục hồi; bước 4 giữ kết quả để thầy xem, dừng ghi hình rồi mới nhấn Enter để thoát.

## Nội dung giải thích trên màn hình

Màn hình phát hiện hiện số đo thực tế, trạng thái gốc, điều kiện luật, các luật đang khớp và số cảnh báo được gom. Kết quả thiếu được ghi rõ chưa đủ dữ liệu. Màn hình phục hồi hiện lại các số đo để đối chiếu. Các điểm chờ Enter vẫn im lặng, không hiện lời hướng dẫn dành cho người quay.

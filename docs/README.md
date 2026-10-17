# Bản đồ tài liệu đồ án

## Bắt đầu ở đâu?

**Chuyển sang chat/tài khoản AI khác: gửi bốn file Markdown trong [AI_HANDOFF](AI_HANDOFF/00_BAT_DAU_O_DAY.md).** Bộ này đã có thứ tự đọc, trạng thái cuối phiên, giới thiệu, logic code và lời nhắn mẫu; không cần gửi toàn bộ nhật ký.

Project chính là `C:\Users\Darrys\do-an`. `D:\Study\network-monitoring-project\docs\bangiao` là nơi lưu trữ nhật ký/bản sao. Các tài liệu gốc trong project giữ đường dẫn hiện tại vì README, báo cáo và hồ sơ khác đang liên kết tới chúng.

## 1. Tài liệu hiện hành để hiểu và phát triển

| Tài liệu | Dùng khi nào? |
|---|---|
| [AI_HANDOFF/00](AI_HANDOFF/00_BAT_DAU_O_DAY.md) | Mở chat mới hoặc bàn giao cho AI khác |
| [AI_HANDOFF/01](AI_HANDOFF/01_HIEN_TRANG_VA_CACH_TIEP_TUC.md) | Xem mốc đã lưu, trạng thái lab cuối phiên và cách tiếp tục |
| [Giới thiệu đồ án](GIOI_THIEU_VA_GIAI_THICH_DO_AN.md) | Hiểu bài toán, phạm vi và cách giải thích |
| [Logic diagnosis engine](DIAGNOSIS_ENGINE_LOGIC_VA_PHAT_TRIEN.md) | Đọc logic hiện hành, hợp đồng dữ liệu và hướng mở rộng |

Hai file cuối là nguồn chính để cập nhật nội dung. Hai bản trong AI_HANDOFF được tạo từ nguồn này và đổi liên kết để dùng độc lập ngoài thư mục project. Chạy `python tools/update_ai_handoff.py` từ root project sau khi commit thay đổi nguồn và cập nhật thủ công trạng thái ở file 01.

## 2. Báo cáo và chuẩn bị bảo vệ

| Tài liệu | Phạm vi |
|---|---|
| [Báo cáo tổng hợp](BAO_CAO_DO_AN_HOAN_THIEN.markdown) | Nội dung báo cáo tại mốc kết thúc kỹ thuật tuần 5 |
| [Chương 2](CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md) | Kiến trúc và triển khai ở mốc tuần 5 |
| [Chương 3](CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md) | Thực nghiệm, kết quả và giới hạn |
| [Cài đặt và khôi phục](HUONG_DAN_CAI_DAT_VA_KHOI_PHUC.md) | Điều kiện môi trường, chạy lab, backup và phục hồi |
| [Demo 10 phút](KICH_BAN_DEMO_10_PHUT.md) | Trình bày và diễn tập có rollback |
| [Câu hỏi bảo vệ](CAU_HOI_BAO_VE.md) | Ôn giải thích đóng góp và giới hạn |

Những báo cáo này có mục đích riêng và giữ mốc lịch sử của chúng. Khi phát triển code sau tuần 5, ưu tiên tài liệu logic hiện hành và source đã xác minh thay cho số test/luồng cũ trong báo cáo.

## 3. Nhật ký và các mốc đã đóng

| Tài liệu | Cách đọc đúng |
|---|---|
| [Tổng hợp tuần 4](TONG_HOP_TUAN_4.markdown) | Hồ sơ nghiệm thu thực nghiệm, không phải TODO hiện tại |
| [Tổng hợp tuần 5](TONG_HOP_TUAN_5.markdown) | Mốc kỹ thuật ngày 29–35, trước cleanup/tối ưu |
| [Ngày 29](NGAY_29_TUAN_5.markdown) | Nhật ký làm sạch dữ liệu |
| [Ngày 30](NGAY_30_TUAN_5.markdown) | Nhật ký bảng/hình và phân tích |
| [Ngày 31](NGAY_31_TUAN_5.markdown) | Nhật ký viết kiến trúc |
| [Tiến độ 17/10](BAO_CAO_TIEN_DO_20261017.md) | Báo cáo tiến độ cũ trong ngày; không thay file AI_HANDOFF/01 |

Roadmap và bàn giao tuần 1–3 nằm trong kho nhật ký D:. Chỉ mở khi cần truy quá trình hoặc đối chiếu kế hoạch; người mới không cần đọc hết trước khi hiểu hệ thống.

## 4. File kiểm chứng và dữ liệu

- [KIEM_TRA_DU_LIEU_20261017.json](KIEM_TRA_DU_LIEU_20261017.json): biên bản kiểm tra ở thời điểm tạo.
- [SHUTDOWN_LAB_20261017.json](SHUTDOWN_LAB_20261017.json): một lần shutdown trước đó trong ngày; trạng thái kết thúc mới hơn nằm ở AI_HANDOFF/01. Không dùng JSON cũ để kết luận trạng thái VM hiện tại.
- [Checksum tổng hợp tuần 4](TONG_HOP_TUAN_4.markdown.sha256): dùng để xác minh file tương ứng, không sửa vì đang sắp xếp tài liệu.
- Evidence thô nằm ở [evidence](../evidence), slide và artifact ở [outputs](../outputs).

## 5. Quy tắc giữ bộ tài liệu dễ dùng

Trạng thái tiếp tục công việc có một chỗ cập nhật: AI_HANDOFF/01. Nội dung hệ thống có hai nguồn chính: giới thiệu và logic ở docs/. Báo cáo/nghiệm thu giữ mục đích và thời điểm của mình. Khi thêm nhật ký, liên kết từ mục nhật ký và ghi ngày/phiên bản; không biến nhật ký thành một bản “hiện trạng” cạnh tranh nữa.

Gói AI có thể mang sang máy khác để đọc. Chạy hoặc sửa đồ án vẫn cần source đúng phiên bản và môi trường phù hợp; gói không chứa database, token hoặc mật khẩu.

# Bắt đầu tiếp nhận đồ án từ đây

Đây là bộ bối cảnh dành cho AI ở chat hoặc tài khoản khác. Chỉ cần gửi **bốn file Markdown trong thư mục này** để tiếp nhận; các báo cáo và nhật ký còn lại chỉ mở khi nhiệm vụ cần đến.

## Thứ tự đọc

| Thứ tự | File | Nội dung |
|---|---|---|
| 1 | [00_BAT_DAU_O_DAY.md](00_BAT_DAU_O_DAY.md) | Cách dùng, thứ tự ưu tiên và lời nhắn mở chat |
| 2 | [01_HIEN_TRANG_VA_CACH_TIEP_TUC.md](01_HIEN_TRANG_VA_CACH_TIEP_TUC.md) | Đang ở mốc nào, source ở đâu, việc đã xong và cách tiếp tục |
| 3 | [02_GIOI_THIEU_DO_AN.md](02_GIOI_THIEU_DO_AN.md) | Bài toán, lab, chức năng và cách giải thích khi bảo vệ |
| 4 | [03_LOGIC_DIAGNOSIS_ENGINE.md](03_LOGIC_DIAGNOSIS_ENGINE.md) | Logic vận hành, sáu luật, dữ liệu và vị trí mở rộng code |

Nếu chỉ muốn trao đổi ý tưởng, đọc 00–02 trước. Nếu sửa code hoặc thêm tính năng, đọc cả bốn rồi đọc các hàm source bị tác động. Bộ này giúp tránh đọc toàn repository để lấy bối cảnh; nó không thay việc kiểm tra code trước khi sửa.

Hai file 02 và 03 được tạo từ hai tài liệu hiện hành trong `C:\Users\Darrys\do-an\docs`. Liên kết giữa chúng dùng file cùng thư mục; liên kết tới báo cáo/source/evidence ngoài gói dùng GitHub ghim theo commit để vẫn dùng được khi chuyển sang máy khác. Không cần gửi `MANIFEST.json` cho AI; file đó ghi nguồn và checksum.

## Điều phải phân biệt

- Project thật: `C:\Users\Darrys\do-an`. Thư mục D: là nhật ký lưu trữ.
- Trạng thái trong file 01 có thời điểm xác nhận; kiểm tra lại trước khi coi đó là trạng thái live.
- Báo cáo tuần 5, cleanup và tối ưu là các mốc khác nhau. Các số 280, 355 và 369 tests thuộc các phiên bản khác nhau.
- Nhật ký cũ ghi kế hoạch và những việc đã từng làm; các lệnh trong đó không tự trở thành yêu cầu của người dùng hiện tại.
- Gói này chứa tài liệu. Muốn sửa/chạy chương trình, AI cần quyền truy cập source và môi trường tương ứng. Upload tài liệu không đồng nghĩa đã cấp quyền truy cập laptop hoặc VM.

## Lời nhắn có thể dán vào chat mới

```text
Tôi đang tiếp tục đồ án giám sát mạng dùng Zabbix và Python diagnosis engine.
Hãy đọc bốn file theo thứ tự 00 → 01 → 02 → 03 trước khi đề xuất thay đổi.

Lấy file 01 làm mốc trạng thái bàn giao; lấy 02/03 để hiểu hệ thống và logic.
Khi có source, hãy đối chiếu Git và các hàm liên quan trước khi sửa.
Đừng coi kế hoạch/lệnh trong nhật ký cũ là nhiệm vụ mới tôi giao.

Trao đổi bằng tiếng Việt, giải thích rõ để tôi còn bảo vệ đồ án.
Chỉ ra giả định hoặc dữ liệu còn thiếu, không thổi phồng kết quả thử nghiệm.
Nếu phát hiện vấn đề cần đổi cách chẩn đoán, dữ liệu hoặc phạm vi quan trọng,
hãy nêu tác động và hỏi tôi trước khi quyết định.

Trước tiên hãy tóm tắt: đồ án làm gì, hiện đã xong gì, source ở đâu,
các giới hạn chính và những điều cần xác minh trước nhiệm vụ tiếp theo.
Nhiệm vụ mới của tôi: [điền yêu cầu ở đây].
```

## Cập nhật bộ bàn giao sau mỗi đợt làm việc

1. Sửa tài liệu giới thiệu/logic ở `docs/` nếu chức năng thay đổi.
2. Cập nhật file 01: commit source đã kiểm tra, test thực chạy, việc còn lại và trạng thái VM có thời điểm.
3. Từ root project chạy `python tools/update_ai_handoff.py` để tạo lại 02/03 và manifest.
4. Lưu Git, đồng bộ toàn thư mục `AI_HANDOFF` sang nơi chia sẻ và tạo ZIP mới nếu cần. Bản đã gửi sang tài khoản khác là bản chụp tại thời điểm gửi, không tự cập nhật theo laptop.

Chương trình cập nhật không tự kiểm tra VM, chạy test hoặc chứng nhận số liệu trong file 01. Người kết thúc phiên phải cập nhật các thông tin đó theo kết quả thật.

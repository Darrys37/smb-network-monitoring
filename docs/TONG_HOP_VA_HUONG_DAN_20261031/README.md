# Báo cáo tổng hợp và hướng dẫn sử dụng — 31/10/2026

- [Báo cáo tổng hợp Word — 15 trang](01_BAO_CAO_TONG_HOP.docx) · [Markdown](01_BAO_CAO_TONG_HOP.md)
- [Hướng dẫn sử dụng Word — 11 trang](02_HUONG_DAN_SU_DUNG.docx) · [Markdown](02_HUONG_DAN_SU_DUNG.md)

Báo cáo trình bày baseline, kiến trúc, quy trình thu/nhãn dữ liệu, CART, FP-Growth, SQLite, đối chứng và bằng chứng thực nghiệm. Hướng dẫn gồm xem kết quả offline, chạy demo, engine chuyên gia, môi trường nghiên cứu mới, xử lý lỗi, shutdown và khôi phục.

Mốc code thực nghiệm: `8ba97a7bab5debb24f6eeb852fd59f49c66462d7`. Kết quả mới trên VM: CART numeric 42/42; CART discrete và FP có gate 36/42, sáu ca từ chối được giữ trong mẫu số. Chỉ có lỗi đơn trên SRV01, chưa kiểm chứng máy thật/multi-fault/production. Registry có hai model validated cho nghiên cứu, không có rule active.

Đã xuất Word và xem đủ 26 trang. `AUTHORING_MANIFEST.json` là dấu vết lúc sinh tài liệu; `DOCUMENTS_QA.json` là nghiệm thu cuối với checksum, số trang và xác nhận nguồn bất biến. Các tệp PDF/PNG kiểm tra bố cục được giữ trong workspace tác giả, không phải bản nộp bổ sung.

MON01, SRV01 và CLI01 đã shutdown qua ACPI, trạng thái poweroff. Backup lạnh đầy đủ: `D:\Study\network-monitoring-project\backups\cold-vms-after-ml-20261031T142959433223Z` (56 tệp, 28 đĩa cấu hình, 45.70 GB). Đã đối chiếu SHA256 mọi tệp; chưa boot thử bản phục hồi. Không khởi động VM chỉ để đọc tài liệu này.

Khi khôi phục tài liệu, giải nén gói backup vào thư mục riêng và đối chiếu `FILES_SHA256.json` trước khi thay bản đang dùng. Gói tài liệu không thay thế backup source/evidence và backup lạnh VM; vị trí từng loại đã ghi trong hướng dẫn.

# Tổng hợp hoàn thiện tuần 5

Ngày17/10/2026 (UTC+7). Đã hoàn thành phần kỹ thuật của ngày29–35: dữ liệu sạch, bảng/hình, Chương2/3, README/hướng dẫn cài/chạy/rollback, slide, kiểm tra test và ba luồng demo live sau reboot. Gói bàn giao và Git tag được tạo sau audit này; receipt backup đặt cạnh gói nộp.

## Công việc đã thực hiện

| Ngày | Đầu ra |
|---|---|
|29|18 run sạch, sổ19 attempt, thống kê và workbook công thức|
|30|Bảng, ba hình PNG/SVG/PDF, bốn phát hiện có dẫn chứng|
|31|Chương2 đối chiếu source/config/SQL và runtime ba VM|
|32|Chương3 hoàn thiện phương pháp, cảnh báo sai, giới hạn và raw links|
|33|Hướng dẫn cài/khôi phục, README, demo10 phút, 10 slide và15 câu hỏi|
|34|Reboot ba VM, ba demo kỹ thuật mới, log thời lượng, ảnh dự phòng|
|35|280 tests trên MON01 và280 tests Windows, kiểm tra hash/config/DB, release địa phương và gói backup|

## Diễn tập thật

| Run ID | Problem → incident → recovery | Thời lượng kỹ thuật (s) | Kết quả |
|---|---|---:|---|
|DEMO-01-retry1|1038 → 37 → 1041|67.88|PASS, Nginx phục hồi|
|DEMO-02|1044 → 38 → 1047|59.03|PASS, Nginx phục hồi|
|DEMO-03|1052 → 39 → 1059|60.75|PASS, Nginx phục hồi|

Các lượt này nằm ngoài18 fault tuần4, không nâng mẫu số thực nghiệm. Thời lượng gồm điều phối SSH/chờ event, không phải thời lượng CLI thuần hoặc bài nói10 phút. Một attempt ban đầu bị chặn trước fault bởi cảnh báo reboot được giữ riêng; không tính thành công hoặc fault thất bại. Trong ba lượt hợp lệ chỉ cho phép thông báo uptime sau reboot đã phân loại; không chấp nhận problem HTTP/Agent bất thường khác. Tất cả thông báo nền đã phục hồi trước snapshot cuối.

## Sự cố vận hành được giữ lại

Sau reboot, MON01 ngừng phản hồi SSH/heartbeat VirtualBox. Snapshot live bảo toàn trạng thái bị kẹt/lỗi; tắt mềm và reset không khôi phục được trạng thái nội bộ SUSPENDED_LS. Đã dừng chính xác phiên MON01 kẹt Stopping rồi khởi động lại từ đĩa hiện tại; không restore snapshot cũ và không sửa rule/trigger. Bản snapshot lỗi không được coi là backup hợp lệ. Kiểm tra SQLite/source/config sau khôi phục đạt, rồi mới tiếp tục demo. Xem log hypervisor và các snapshot cuối trong evidence.

## Kiểm chứng và bàn giao

- Engine Python/tests/requirements/pytest.ini:40 tệp khớp mốc đóng băng trên MON01 và Windows. Cấu hình28 item/157 trigger trong phạm vi baseline khớp.
- Ngoại lệ cấu hình mẫu: sửa ZABBIX_URLL thành ZABBIX_URL trong .env.example; README được cập nhật, không đổi ngưỡng hoặc thuật toán.
- Test cuối:280 passed trên MON01;280 passed trên Windows từ đúng thư mục module. Log collection lỗi ban đầu trên Windows được giữ, không coi là lỗi sản phẩm đã được sửa.
- SQLite cuối integrity=ok, foreign_key_check rỗng; bản backup nhất quán tải về có SHA256 khớp; YAML export host được giữ riêng.
- Quét token hiện tại và mẫu gán token hex trên working files/reachable blobs; ảnh fallback chọn lọc đã xem, không có mật khẩu/token. Không tuyên bố chứng nhận mọi credential cũ chưa biết.
- [Báo cáo tổng hợp](BAO_CAO_DO_AN_HOAN_THIEN.markdown), [Chương2](CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md), [Chương3](CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md).
- [Hướng dẫn cài/khôi phục](HUONG_DAN_CAI_DAT_VA_KHOI_PHUC.md), [demo](KICH_BAN_DEMO_10_PHUT.md), [câu hỏi bảo vệ](CAU_HOI_BAO_VE.md).
- [Slide](../outputs/week5-final-20261017/SLIDE_BAO_VE_TUAN5_FINAL.pptx), [bằng chứng cuối](../evidence/week5/final-20261017/rehearsals-summary.json).

## Điều cần người thực hiện xác nhận trước nộp

1. Tự trình bày và giải thích toàn bộ luồng mà không dựa vào nội dung gợi ý. Ba lần chạy kỹ thuật không chứng nhận năng lực bảo vệ hoặc bài nói đúng10 phút.
2. Ghép/định dạng báo cáo theo mẫu trường nếu trường yêu cầu Word/PDF, kiểm tra metadata và người hướng dẫn. Bản Markdown giữ nội dung kỹ thuật; chưa chứng nhận yêu cầu trình bày cụ thể chưa được cung cấp.
3. Hai bản trên C: vàD: nằm ở hai ổ NVMe vật lý khác nhau, nhưng cùng laptop; chưa bảo vệ trước mất thiết bị. Chưa có đường dẫn ngoài laptop được xác nhận; cần copy thêm USB/ổ ngoài hoặc nơi đồng bộ do người thực hiện chọn.
4. Không gọi18/18 là accuracy tổng quát; giữ n=3, baseline30m06s, thiếu mẫu âm và giới hạn lab trong bài bảo vệ.

Git tag kỹ thuật `week5-technical-20261017`; không push lên remote tự động. Checklist hoàn thành kỹ thuật không thay xác nhận nộp bài hoặc phê duyệt của giảng viên.

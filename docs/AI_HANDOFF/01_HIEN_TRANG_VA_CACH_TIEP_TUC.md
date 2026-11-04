# Trạng thái và cách tiếp tục — 05/11/2026

## Phạm vi đã chốt

- Worker V3 là bản chính trên GitHub `main`: worker tự động, 8 luật / 7 nhóm, bảng quyết định SQLite và tương quan cảnh báo theo topology.
- Chỉ có ba VM MON01, CLI01 và SRV01. Thử máy Ubuntu vật lý đã hoãn; không ghi thành đã hoàn thành.
- Nội dung demo/bảo vệ tập trung vào worker chuyên gia. Không lấy kết quả của hướng nghiên cứu riêng để làm bằng chứng cho V3.
- Worker hỗ trợ chẩn đoán và quan sát phục hồi; người vận hành/helper thực hiện sửa lỗi.

## Những thay đổi gần nhất

Đã đưa source V3 cùng helper SSH độc lập và dữ liệu regression có checksum lên `main`. README, hướng dẫn và tài liệu hiện hành trỏ vào bản này. Tài liệu và evidence theo tuần được giữ ở nhánh lưu trữ; dữ liệu test trong `system-monitor/tests/fixtures` vẫn được giữ nguyên.

Hồ sơ kiểm tra source và dọn tài liệu nằm trong [evidence hiện hành](https://github.com/Darrys37/smb-network-monitoring/tree/main/evidence/system-v3/main-release). Những bài kiểm tra source là offline, không thay cho một lượt fault mới trên VM. Trạng thái live của VM phải được kiểm tra lại trước khi demo.

## Tiếp tục an toàn

Repository cục bộ đã dùng là `C:\Users\Darrys\do-an`; các bản báo cáo nộp được lưu riêng dưới `D:\Study\network-monitoring-project\docs`. Kiểm tra branch và working tree trước khi sửa: checkout cục bộ có thể còn ở nhánh phát triển với thay đổi chưa commit. Không tự reset hoặc ghi đè chúng để chuyển sang main.

Trên MON01, dùng `systemctl is-active do-an-monitor-v3.service` và `/home/phat/do-an/diagnosis-engine/.venv/bin/python /home/phat/do-an/system-monitor/report.py` để đọc trạng thái. Không chạy worker thứ hai vào cùng DB.

Trước tạo lỗi: HTTP 200, parent up, nguồn đo hoạt động, queue đã xử lý xong và lỗi của lượt trước đã phục hồi. Mỗi cảnh cần quay đủ baseline → tạo lỗi → bằng chứng/luật → phục hồi → xác nhận sau phục hồi.

Nếu sửa quy tắc hoặc source, đọc code đúng phiên bản và chạy kiểm tra phù hợp. Ghi rõ thứ đã kiểm chứng, chưa thử và giới hạn; không suy ra hệ thống luôn ổn định từ một lần demo thành công.

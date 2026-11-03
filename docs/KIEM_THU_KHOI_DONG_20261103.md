# Kiểm tra khởi động lại ba VM — 03/11/2026

**Kết quả: chức năng tự khởi động và demo đạt, kèm cảnh báo về độ ổn định của MON01.** Cả hai lượt bật tuần tự đều lên được các dịch vụ; lượt bật gần đồng thời đầu tiên không đạt. Chưa thể tuyên bố lỗi boot của nền tảng đã được khắc phục hoàn toàn.

[Bằng chứng máy đọc được](../evidence/system-v3/powercycle-20261103/VERIFICATION.json) · [Cách dùng và khôi phục](../system-monitor/README.md).

## Đã thử những gì?

Giờ dưới đây là UTC+7 trên laptop lab ngày03/11; timeline JSON giữ UTC để đối chiếu.

| Lượt | Thao tác và kết quả |
|---|---|
| 18:30 | Tắt sạch bằng ACPI cả ba VM, xác nhận đều poweroff, bật gần đồng thời. CLI01/SRV01 tự lên; MON01 kẹt boot, SSH không trở lại trong240s. Lưu ảnh/log và đánh dấu thất bại. |
| 18:46 | Sau khi người dùng xác nhận, reset cưỡng bức riêng MON01. Máy lên lại, MySQL/Zabbix/worker tự chạy. Lượt phục hồi này không được tính là một lần cold boot sạch đạt. |
| 18:50–18:54 | Tắt sạch cả ba, bật tuần tự CLI01→SRV01→MON01, chờ SSH từng máy. Dịch vụ tự chạy; tại lần kiểm tra chưa thấy kernel stall. |
| 18:59–19:04 | Lặp lại quy trình tuần tự với bản sửa thông báo khởi động. Cả ba tự chạy. MON01 có một soft lockup lúc boot rồi tiếp tục hoạt động; không giấu cảnh báo này. |
| 19:16 | Demo gateway hỏng + Nginx dừng:6 sự kiện cần xử lý,2 nhóm,3 cảnh báo phụ thuộc bị ức chế. Rollback xong về0 sự cố/0 job chờ. |

Ở các lượt sạch, không gọi `systemctl start/restart` để làm dịch vụ lên sau boot. Boot ID của cả ba máy đã đổi. Các unit mạng thử, Agent2, Nginx, MySQL, Zabbix và worker đều active; đồng hồ NTP đã đồng bộ. MON01 truy cập HTTP200 qua đường routed và TTL1 xác nhận hop CLI01. SSH trên hai máy con có thể được kích hoạt qua socket; không coi `ssh.service disabled` là lỗi khi socket/SSH thực tế hoạt động.

## Dữ liệu có an toàn không?

- Đã chụp checkpoint SQLite nhất quán trước khi thử.158 sự kiện gốc trước thử còn nguyên toàn bộ payload và thời điểm nhận, không mất/đổi bản ghi.
- Sau boot/demo có174 sự kiện; cursor Zabbix đi từ2378 tới2424, không quay ngược. SQLite integrity ok, không có lỗi foreign key.
- `diagnosis.db` baseline vẫn39 incidents /301 evidence /172 diagnoses /29 recoveries.
- Kiểm nhanh sáu bảng MySQL Zabbix (`hosts/items/triggers/events/history/history_uint`) đều OK. Đây là kiểm tra những bảng nêu trên, không phải cam kết mọi dữ liệu trên toàn bộ đĩa đều đã được kiểm chứng.
- Đã tạo checkpoint sau thử. Không restore đĩa VM, không xóa snapshot, không sao chép thêm một bộ virtual disks45GB.

## Sửa lỗi được phát hiện khi chạy quy trình

Zabbix template giữ hai cảnh báo `has been restarted (uptime <10m)` trong10 phút. Ban đầu wrapper coi chúng là sự cố và chặn demo, dù các dịch vụ đã khỏe. Bản sửa chỉ nhận diện đúng node + trigger ID + tên nguyên bản + severity của hai tín hiệu đó; chúng vẫn xuất hiện trong `notices`, `active_notice_events` và sự kiện raw. Không bỏ qua toàn bộ cảnh báo mức Warning.

Replay snapshot thật đang có hai thông báo cho kết quả2 thông báo /0 sự cố cần xử lý; raw vẫn160 event.36 tests hệ thống qua, gồm đổi tên/mức độ/ID phải giữ sự kiện actionable, cảnh báo CPU cùng severity vẫn giữ, recovery xóa trạng thái thông báo.74 tests ML cũng qua; model, train/test/freeze không thay đổi.

Sau khi cài chính sách đã chạy lại một lượt tắt/bật sạch để worker tự nạp source/config mới; không dùng việc restart service thủ công để chứng minh tự khởi động. Demo cuối thực hiện khi các thông báo10 phút đã hết; khả năng xử lý trường hợp còn hai thông báo được chứng minh bằng replay snapshot thật và unit tests, không gọi đó là lượt fault live mới.

## Giới hạn còn lại và cách dùng

MON01 từng kẹt hoàn toàn ở lượt đầu; sau reset có một soft lockup, và ở lượt sạch cuối còn ghi `CPU#1 stuck for34s [boot:1349]` lúc khởi động. PID đó về sau thuộc MySQL/InnoDB. Khi chạy demo không phát sinh thêm stall, nhưng chưa xác định nguyên nhân gốc hay chứng minh lỗi nền tảng đã hết. Bật tuần tự là quy trình đã thử thành công, không phải bằng chứng nhân quả rằng bật đồng thời gây treo.

Trước demo: bật CLI01, chờ SSH; bật SRV01, chờ SSH; bật MON01, chờ SSH và `system_lab.py status` báo worker active, baseline khỏe. Nếu guest kẹt, giữ log và kiểm tra; script thử sạch không tự reset cưỡng bức. Reset lần này đã có xác nhận riêng của người dùng.

Phép thử này là **tắt/bật VM đang dùng**, chưa phải phục hồi toàn bộ VM từ cold backup rồi boot. Chưa thử máy Ubuntu thật, chưa đánh giá khả năng chịu tải production. Các lỗi nền tảng còn thấy được giữ trong báo cáo thay vì chuyển thành kết quả đạt tuyệt đối.

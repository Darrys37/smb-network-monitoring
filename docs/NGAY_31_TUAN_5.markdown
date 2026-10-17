# Tuần 5 — ngày 31: hoàn thiện kiến trúc và triển khai

Ngày 17/10/2026 (UTC+7). **Hoàn thành phạm vi kỹ thuật ngày 31**: Chương 2 được đối chiếu mã nguồn, cấu hình và trạng thái lab trực tiếp; không thêm tính năng hoặc sửa trigger/rule.

## Kết quả

- Hoàn thiện topology ba VM, tài nguyên, NAT/Host-only, vai trò observer, cổng và luồng dữ liệu.
- Bổ sung bảng item/chu kỳ/preprocessing, trigger và macro; phân biệt trigger Zabbix với luật Python.
- Mô tả JSON-RPC, kiểm tra problem trước/sau collection, xử lý lỗi và giới hạn quyền API.
- Bổ sung module, cấu trúc evidence, điều kiện R1–R6, HTTP scope và freshness.
- Bổ sung sơ đồ SQLite, transaction bundle, recovery idempotent và trạng thái report `unverified`/`closed`.
- Bổ sung bảng truy vết tới source, snapshot và hồ sơ incident thật; giữ giới hạn triển khai rõ ràng.

## Kiểm tra thực tế

SSH chỉ đọc cả MON01, SRV01, CLI01; ba Agent active, Zabbix server/MySQL/Nginx MON01 active, Nginx SRV01 active. HTTP SRV01 trả 200 từ cả ba VM. Ba interface Agent available=1; không có problem mở lúc snapshot. SQLite integrity=ok, không có lỗi foreign key; số hàng 36 incidents, 268 evidence, 154 diagnoses, 26 recoveries gồm lịch sử cũ.

Cấu hình 28 item và 157 trigger trong phạm vi baseline không đổi. 40 tệp source/test/requirements/pytest.ini trên MON01 và Windows khớp mốc đóng băng. SELECT MySQL chỉ đọc xác nhận ngưỡng 3m/90/1,5, bốn liên kết template, không có override trên host/global cho ba macro này và tám hàm trigger chọn lọc. NTP synchronized không đồng nghĩa đã đo chính xác clock offset.

## Những điểm đã sửa rõ trong Chương 2

1. R1, R2, R5 cùng lấy problem HTTP trigger25334; sáu luật không tương ứng sáu trigger riêng.
2. R2 có thể khớp TCP refused dù thiếu local HTTP; timeout thiếu probe nội bộ mới bị giữ insufficient. Không mô tả mọi nhánh R2 đều bắt buộc probe nội bộ.
3. Chưa lưu recovery thì report là `unverified`, không kết luận event vẫn mở. `closed` chỉ là đã ghi recovery xác minh, không xác nhận sức khỏe hiện tại.
4. CPU trigger dùng min >90 trong 5m; R6 dùng mean ≥90 cùng độ phủ/load. CPU count có heartbeat 1d; không ép có history mới mỗi phút.
5. Có ServerActive trong file không chứng minh đang dùng active template; kiểm chứng template bằng SQL thay vì suy diễn từ kết quả API bị giới hạn quyền.

## Tệp bàn giao

- [Chương 2 hoàn thiện kỹ thuật](CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md).
- [Architecture audit](../evidence/week5/day31-20261017/architecture-audit.json).
- [Item inventory](../evidence/week5/day31-20261017/item-inventory.csv), [trigger map](../evidence/week5/day31-20261017/trigger-scenario-map.csv), [SQL đối chiếu](../evidence/week5/day31-20261017/critical-sql-reviewed.json).
- [Snapshot MON01](../evidence/week5/day31-20261017/mon01-live.json), [SRV01](../evidence/week5/day31-20261017/srv01-live.json), [CLI01](../evidence/week5/day31-20261017/cli01-live.json).

Kiểm tra phù hợp thay đổi tài liệu gồm đối chiếu source/config, DB integrity và liên kết; không chạy lại unit test rồi gán kết quả lịch sử 280 tests thành lần chạy mới. Bằng chứng tuần 4 và ngày 29–30 giữ nguyên checksum.

## Bước tiếp theo

Ngày 32 hoàn thiện Chương 3: môi trường, kịch bản, quy trình, kết quả, cảnh báo sai và hạn chế. Chưa chứng nhận ba lần demo sau reboot hoặc release nộp cuối. Chương 2 còn cần ghép theo quy chuẩn trình bày của trường khi đóng gói.

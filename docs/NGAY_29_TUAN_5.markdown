# Tuần 5 — ngày 29: nghiệm thu dữ liệu thực nghiệm

Ngày thực hiện: 17/10/2026 (UTC+7). **Hoàn thành phạm vi ngày 29**: đối chiếu Run ID, mốc thời gian, event, incident, ảnh và thống kê. Không chạy lại fault, không sửa engine hoặc bằng chứng tuần 4.

- Kiểm tra SHA-256: 631 tệp trong ba manifest; không sai lệch.
- 19 lượt trong sổ theo dõi: 18 fault hợp lệ, 1 lượt R5-03 hủy trước gây lỗi. R5-03-retry1 là lượt thay thế hợp lệ.
- 18/18 liên kết problem → incident → recovery → ảnh event đúng; không trùng ID; không phát hiện lỗi dữ liệu chưa xử lý.
- Tất cả 18 CLI kết thúc mã 0, incident closed, luật mục tiêu matched; không có luật phụ matched.

## Thống kê kiểm tra lại từ log gốc

Đơn vị: giây. Mỗi kịch bản n=3. Bảng dùng cận dưới DT và RR; CSV có cả cận trên, không lấy thời gian bắt đầu watcher làm thời điểm lỗi.

| Kịch bản | DT min / median / max | CLI min / median / max | RR min / median / max | Luật mục tiêu / fault hợp lệ |
|---|---:|---:|---:|---:|
| R1 | 15.000 / 19.000 / 32.000 | 6.656 / 6.660 / 6.665 | 9.000 / 14.000 / 26.000 | 3/3 |
| R2 | 5.000 / 10.000 / 23.000 | 0.582 / 0.610 / 0.638 | 8.000 / 16.000 / 21.000 | 3/3 |
| R3 | 183.000 / 269.000 / 295.000 | 0.469 / 0.583 / 0.610 | 78.000 / 99.000 / 102.000 | 3/3 |
| R4 | 69.000 / 77.000 / 83.000 | 0.564 / 0.766 / 1.688 | 1.000 / 8.000 / 19.000 | 3/3 |
| R5 | 16.000 / 24.000 / 34.000 | 2.446 / 2.590 / 2.646 | 3.000 / 14.000 / 25.000 | 3/3 |
| R6 | 316.000 / 356.000 / 391.000 | 0.487 / 0.502 / 0.522 | 32.000 / 46.000 / 51.000 | 3/3 |

## Công thức và giới hạn

- DT = [problem − fault_after, problem − fault_before]. RR = [recovery − rollback_after, recovery − rollback_before]. Độ phân giải timestamp 1 giây; CSV thêm cận DT mở rộng ±1 giây. Không đo được sai lệch đồng hồ chỉ từ độ phân giải này.
- Median/min/max được tính độc lập bằng Python và khớp toàn bộ thống kê tuần 4. Workbook có công thức và kiểm tra thay đổi đầu vào rồi khôi phục.
- Tỷ lệ khớp luật mục tiêu trên fault hợp lệ = 18/18 (100%). Đây là kết quả trên bộ fault nhỏ; chưa đủ mẫu âm để tính accuracy tổng quát, specificity hoặc false-positive rate.
- 108 đầu ra luật: 18 matched, 66 not_matched, 24 insufficient_evidence. not_matched không tự động là true negative; HTTP absent là ngoài phạm vi áp dụng.
- CLI gồm API, thu thập, luật và ghi dữ liệu; khoảng problem–recovery không phải downtime thực tế.
- Baseline được chấp thuận 30 phút 06 giây, không phải 4 giờ. Ảnh event chụp hồi cứu sau phục hồi.

## Tệp bàn giao

- `evidence/week5/day29-20261017/clean-runs.csv`: 18 dòng sạch, đủ ID, timestamp, khoảng DT/RR, đường dẫn ảnh và log.
- `attempts.csv`: đủ 19 lượt, cờ included và liên kết retry.
- `scenario-summary.csv`: thống kê hai cận DT/RR, CLI và tử số/mẫu số.
- `deviations.csv`: các ngoại lệ và cách xử lý, không xóa lịch sử.
- `audit.json`, `data-dictionary.json`: kết quả kiểm tra, định nghĩa và kiểu dữ liệu.
- `tools/day29_audit.py`, `tools/day29_workbook.mjs`: tái tạo đầu ra; workbook tại `outputs/week5-day29-20261017/NGAY29_KIEM_TRA_DU_LIEU.xlsx`.

## Chuyển sang ngày 30

Dữ liệu đủ điều kiện dùng cho bảng/biểu đồ so sánh detection và diagnosis, viết ít nhất ba nhận xét dựa trên kết quả. Các giới hạn mẫu âm, n=3 và baseline ngắn vẫn phải ghi trong báo cáo. Ngày 29 không đồng nghĩa hoàn thành toàn bộ tuần 5.

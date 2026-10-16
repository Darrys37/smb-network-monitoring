# Tổng hợp thực nghiệm tuần 4

Phiên bản source `ca04071`, config export `978b4f9`, phiếu thử `4cabeb0`. Cấu hình hiệu lực và hash được lưu trong baseline/freeze; công cụ ghi thử nằm ngoài engine.

| Kịch bản | Fault hợp lệ | Phát hiện | Mục tiêu matched, hồ sơ đạt | Abstention mục tiêu | Detection median [min–max] s | CLI median [min–max] s |
|---|---:|---:|---:|---:|---|---|
| R1 | 3 | 3/3 | 3/3 | 0 | 19.000 [15.000–32.000] | 6.660 [6.656–6.665] |
| R2 | 3 | 3/3 | 3/3 | 0 | 10.000 [5.000–23.000] | 0.610 [0.582–0.638] |
| R3 | 3 | 3/3 | 3/3 | 0 | 269.000 [183.000–295.000] | 0.583 [0.469–0.610] |
| R4 | 3 | 3/3 | 3/3 | 0 | 77.000 [69.000–83.000] | 0.766 [0.564–1.688] |
| R5 | 3 | 3/3 | 3/3 | 0 | 24.000 [16.000–34.000] | 2.590 [2.446–2.646] |
| R6 | 3 | 3/3 | 3/3 | 0 | 356.000 [316.000–391.000] | 0.502 [0.487–0.522] |

Bảng trên dùng cận dưới clock đã lưu để mô tả detection. `all-trials.csv` giữ cả hai cận và biên làm tròn ±1 giây khi có; không gộp khoảng problem–recovery thành downtime. Mỗi thống kê có cỡ mẫu `n` trong JSON, đặc biệt khi thiếu detection/CLI.

Lượt R5-03 bị hủy trước fault do giới hạn sử dụng ở bước duyệt lệnh. Giữ nguyên hồ sơ timeout và adjudication riêng; R5-03-retry1 là lượt fault thật tiếp theo. Không tính lần hủy vào mẫu số fault hợp lệ.

Đối chiếu: từng thư mục Run ID chứa fault/rollback log, event API JSON, history CSV, CLI log và incident report. `review.json` là kết quả kiểm tra chéo thời gian, observer, scope, recovery và luật mục tiêu.

Baseline mới: 30 phút 06 giây, 31 poll, 963 history rows / 28 items; không có problem mới trong cửa sổ đã kiểm tra. Đây là quan sát ngắn của Zabbix, không phải bằng chứng engine không báo sai.

Các kết quả thiếu evidence của luật phụ được công bố trong `all_rule_status_counts` của JSON. Ví dụ R5-02 có R6 insufficient_evidence vì span mẫu CPU 239 giây, dưới ngưỡng 240 giây, dù không chủ động gây CPU cao. Giữ nguyên tiêu chí và kết quả; không coi thiếu evidence là healthy.

Không có tập mẫu âm được định nghĩa; không báo specificity hoặc accuracy có TN. Tỷ lệ thành công ở đây chỉ xét luật mục tiêu trên các fault đã kiểm chứng. Ba lượt mỗi loại chưa đủ kết luận độ tin cậy dài hạn.

# Kết quả các lượt R3 chính thức

3 lượt đã lưu; 3 fault hợp lệ; 3 lượt luật mục tiêu matched với hồ sơ qua kiểm tra.

| Run | Problem → Recovery | Incident | Luật mục tiêu | Detection (s) | CLI elapsed (s) | Review |
|---|---|---:|---|---|---:|---|
| R3-01 | 945 → 950 | 25 | matched | 183.0–183.0 | 0.610 | Đã đối chiếu |
| R3-02 | 951 → 956 | 26 | matched | 295.0–295.0 | 0.469 | Đã đối chiếu |
| R3-03 | 957 → 962 | 27 | matched | 269.0–269.0 | 0.583 | Đã đối chiếu |

Raw fault/rollback logs, problem/recovery API JSON, CLI logs, SQLite-derived report và review.json nằm trong từng thư mục Run ID. Không ghi đè các kết quả không đạt hoặc insufficient_evidence.

Đây là kết quả ba lượt trên lab nhỏ. Không suy ra độ tin cậy dài hạn. Khoảng problem–recovery không phải downtime thật; CLI elapsed gồm cả API, thu bằng chứng, luật và lưu dữ liệu. Các luật khác thiếu bằng chứng vẫn được giữ nguyên.

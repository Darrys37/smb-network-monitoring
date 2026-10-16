# Kết quả các lượt R2 chính thức

3 lượt đã lưu; 3 fault hợp lệ; 3 lượt luật mục tiêu matched với hồ sơ qua kiểm tra.

| Run | Problem → Recovery | Incident | Luật mục tiêu | Detection (s) | CLI elapsed (s) | Review |
|---|---|---:|---|---|---:|---|
| R2-01 | 939 → 940 | 22 | matched | 10.0–10.0 | 0.610 | Đã đối chiếu |
| R2-02 | 941 → 942 | 23 | matched | 5.0–5.0 | 0.638 | Đã đối chiếu |
| R2-03 | 943 → 944 | 24 | matched | 23.0–23.0 | 0.582 | Đã đối chiếu |

Raw fault/rollback logs, problem/recovery API JSON, CLI logs, SQLite-derived report và review.json nằm trong từng thư mục Run ID. Không ghi đè các kết quả không đạt hoặc insufficient_evidence.

Đây là kết quả ba lượt trên lab nhỏ. Không suy ra độ tin cậy dài hạn. Khoảng problem–recovery không phải downtime thật; CLI elapsed gồm cả API, thu bằng chứng, luật và lưu dữ liệu. Các luật khác thiếu bằng chứng vẫn được giữ nguyên.

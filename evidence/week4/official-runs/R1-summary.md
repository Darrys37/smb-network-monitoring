# Kết quả các lượt R1 chính thức

3 lượt đã lưu; 3 fault hợp lệ; 3 lượt luật mục tiêu matched với hồ sơ qua kiểm tra.

| Run | Problem → Recovery | Incident | R1 | Detection (s) | CLI elapsed (s) | Review |
|---|---|---:|---|---|---:|---|
| R1-01 | 933 → 934 | 19 | matched | 19.0–20.0 | 6.656 | Đã đối chiếu |
| R1-02 | 935 → 936 | 20 | matched | 15.0–15.0 | 6.665 | Đã đối chiếu |
| R1-03 | 937 → 938 | 21 | matched | 32.0–32.0 | 6.660 | Đã đối chiếu |

Raw fault/rollback logs, problem/recovery API JSON, CLI logs, SQLite-derived report và review.json nằm trong từng thư mục Run ID. Không ghi đè các kết quả không đạt hoặc insufficient_evidence.

Đây là kết quả ba lượt trên lab nhỏ. Không suy ra độ tin cậy dài hạn. Khoảng problem–recovery không phải downtime thật; CLI elapsed gồm cả API, thu bằng chứng, luật và lưu dữ liệu. Các luật khác thiếu bằng chứng vẫn được giữ nguyên.

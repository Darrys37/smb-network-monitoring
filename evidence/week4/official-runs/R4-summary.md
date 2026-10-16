# Kết quả các lượt R4 chính thức

3 lượt đã lưu; 3 fault hợp lệ; 3 lượt luật mục tiêu matched với hồ sơ qua kiểm tra.

| Run | Problem → Recovery | Incident | Luật mục tiêu | Detection (s) | CLI elapsed (s) | Review |
|---|---|---:|---|---|---:|---|
| R4-01 | 963 → 964 | 28 | matched | 69.0–69.0 | 0.766 | Đã đối chiếu |
| R4-02 | 965 → 966 | 29 | matched | 77.0–77.0 | 0.564 | Đã đối chiếu |
| R4-03 | 967 → 968 | 30 | matched | 83.0–83.0 | 1.688 | Đã đối chiếu |

Raw fault/rollback logs, problem/recovery API JSON, CLI logs, SQLite-derived report và review.json nằm trong từng thư mục Run ID. Không ghi đè các kết quả không đạt hoặc insufficient_evidence.

Timestamp gây lỗi và event clock có độ phân giải một giây. Các khoảng trong bảng là phép trừ theo clock đã lưu; CSV/JSON có thêm biên ±1 giây để thể hiện sai số lượng tử timestamp, chưa bao gồm sai số đồng bộ giờ chưa đo chính xác.

Đây là kết quả ba lượt trên lab nhỏ. Không suy ra độ tin cậy dài hạn. Khoảng problem–recovery không phải downtime thật; CLI elapsed gồm cả API, thu bằng chứng, luật và lưu dữ liệu. Các luật khác thiếu bằng chứng vẫn được giữ nguyên.

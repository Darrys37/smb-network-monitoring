# Tuần 5 — ngày 30: bảng, biểu đồ và phát hiện thực nghiệm

Ngày 17/10/2026 (UTC+7). Hoàn thành phạm vi ngày 30 theo roadmap: bảng kết quả, biểu đồ detection theo kịch bản, kết quả chẩn đoán và các phát hiện có bằng chứng. Đầu vào là dữ liệu đã nghiệm thu ngày 29; không gây thêm lỗi hoặc thay đổi luật/trigger.

## Dữ liệu và phương pháp

Đối chiếu toàn bộ 19 tệp trong manifest ngày 29 trước phân tích. Tính lại 90 số thống kê (6 kịch bản × 5 chỉ số × 3 phép min/median/max), khớp bảng ngày 29 với sai số kiểm tra < 1e-9. 18 fault hợp lệ, mỗi nhóm n=3; R5-03 hủy trước fault không vào mẫu số. 18 CLI mã 0, 18 incident closed.

DT là khoảng [problem − fault_after, problem − fault_before]; bảng báo median hai cận và miền từ cận dưới nhỏ nhất đến cận trên lớn nhất. Miền này không phải confidence interval. Hình DT hiển thị từng lượt, median cận dưới và khoảng đo mở rộng ±1 giây do độ phân giải timestamp. Sai lệch clock chưa đo được. CLI đo toàn bộ lần gọi chương trình, không phải suy luận thuần.

## Bảng 30.1 — thời gian và kết quả

| Kịch bản | n | DT median hai cận (s) | Miền DT (s) | CLI median [min–max] (s) | Mục tiêu khớp |
|---|---:|---:|---:|---:|---:|
| R1 | 3 | 19–20 | 15–32 | 6.660 [6.656–6.665] | 3/3 |
| R2 | 3 | 10–10 | 5–23 | 0.610 [0.582–0.638] | 3/3 |
| R3 | 3 | 269–269 | 183–295 | 0.583 [0.469–0.610] | 3/3 |
| R4 | 3 | 77–77 | 69–83 | 0.766 [0.564–1.688] | 3/3 |
| R5 | 3 | 24–24 | 16–34 | 2.590 [2.446–2.646] | 3/3 |
| R6 | 3 | 356–356 | 316–391 | 0.502 [0.487–0.522] | 3/3 |

[Bảng thời gian đầy đủ](../evidence/week5/day30-20261017/timing-summary.csv) · [Kết quả chẩn đoán](../evidence/week5/day30-20261017/diagnosis-outcomes.csv) · [Từng điểm trên hình](../evidence/week5/day30-20261017/plotted-points.csv) · [108 đầu ra luật](../evidence/week5/day30-20261017/rule-status-counts.csv)

## Hình 30.1 — thời gian phát hiện

![Thời gian phát hiện](../evidence/week5/day30-20261017/detection-time.png)

## Hình 30.2 — thời gian CLI chẩn đoán

![Thời gian CLI](../evidence/week5/day30-20261017/diagnosis-cli-time.png)

## Hình 30.3 — kết quả chẩn đoán

![Kết quả luật mục tiêu](../evidence/week5/day30-20261017/diagnosis-outcomes.png)

Các nhóm không khớp, thiếu bằng chứng mục tiêu, không phát hiện và lỗi engine đều bằng 0. Đây là kết quả luật mục tiêu, không phải chấm toàn bộ luật phụ thành đúng/sai. 108 đầu ra luật gồm 18 matched, 66 not_matched, 24 insufficient_evidence.

## Các phát hiện có bằng chứng

1. **Detection thay đổi rõ giữa các kịch bản.** R6 có median 356 s và miền 316–391 s; R3 có median 269 s và miền 183–295 s; R2 có median 10 s và miền 5–23 s. Các lần thử đều cho R6/R3 chậm hơn R2. Điều này phù hợp với việc các trigger dùng cửa sổ/điều kiện khác nhau, nhưng bộ thử không cô lập từng nguyên nhân hoặc đo chi phí từng bước Zabbix. Không dùng khác biệt này để kết luận engine Python chậm. Bằng chứng: [bảng](../evidence/week5/day30-20261017/timing-summary.csv), [R6-01](../evidence/week4/official-runs/R6-01/run.json), [R3-01](../evidence/week4/official-runs/R3-01/run.json), [R2-01](../evidence/week4/official-runs/R2-01/run.json), [snapshot trigger](../evidence/week4/baseline-20261016T162549Z/effective-config-start.json).

2. **Detection và thời gian CLI đo hai giai đoạn khác nhau.** R6 có DT median cao nhất (356 s) nhưng CLI median thấp nhất (0,502 s); R1 có DT median 19–20 s nhưng CLI median cao nhất (6,660 s), khoảng 13,27 lần R6. R5 có CLI median 2,590 s. Thứ hạng khác nhau cho thấy không nên lấy detection làm thời gian chạy thuật toán. Chưa có profiling để phân chia chi phí API/probe/SQLite hoặc chứng minh chính xác nguyên nhân chênh lệch. Bằng chứng: [từng điểm](../evidence/week5/day30-20261017/plotted-points.csv), [log R1-01](../evidence/week4/official-runs/R1-01/diagnosis.log), [log R6-01](../evidence/week4/official-runs/R6-01/diagnosis.log).

3. **Luật mục tiêu khớp cả sáu nhóm, nhưng 18/18 chưa đo accuracy tổng quát.** Mỗi nhóm đạt 3/3 trong đúng fault đã chủ động tạo; R5-03-retry1 thay lượt hủy trước fault, không phải chọn lại sau một chẩn đoán sai. Chưa có tập âm độc lập để tính specificity, false-positive rate hay accuracy có TN. Không biến các kết quả not_matched ngoài mục tiêu thành TN. Bằng chứng: [kết quả theo nhóm](../evidence/week5/day30-20261017/diagnosis-outcomes.csv), [sổ 19 lượt](../evidence/week5/day29-20261017/attempts.csv), [adjudication lượt hủy](../evidence/week4/official-runs/R5-03/adjudication.json).

4. **Thiếu evidence ở luật phụ vẫn cần giữ trong phân tích.** Có 24/108 đầu ra insufficient_evidence, dù cả 18 luật mục tiêu matched. Ví dụ R5-02 có R6 thiếu cửa sổ CPU (239 s so với yêu cầu 240 s). Đây không phải kết quả mục tiêu R5 sai, cũng không chứng minh CPU khỏe. Dữ liệu không đầy đủ phải được giữ đúng trạng thái. Bằng chứng: [bảng 108 đầu ra](../evidence/week5/day30-20261017/rule-status-counts.csv), [hồ sơ R5-02](../evidence/week4/official-runs/R5-02/incident.json).

## Giới hạn và nghiệm thu

Các thống kê chỉ mô tả ba lượt mỗi loại trên cùng lab; không có kiểm định suy rộng hoặc khoảng tin cậy. Baseline 30 phút 06 giây không đủ đánh giá cảnh báo dài hạn và không thay mẫu âm cho engine. Ảnh event được chụp hồi cứu sau phục hồi. Không cộng DT và CLI để gọi tổng thời gian xử lý vì còn khoảng chờ/chuyển probe trước CLI.

Đã tạo ba hình ở PNG, SVG, PDF; CSV cung cấp tất cả điểm và hai cận DT/RR. Nguồn, SHA-256 và phương pháp trong [analysis-validation.json](../evidence/week5/day30-20261017/analysis-validation.json). Mã tái tạo tại [tools/day30_analysis.py](../evidence/week5/day30-20261017/tools/day30_analysis.py). Ngày 31 tiếp theo là hoàn thiện Chương 2; việc nghiệm thu ngày 30 không đóng toàn bộ Chương 3 hoặc toàn bộ tuần 5.

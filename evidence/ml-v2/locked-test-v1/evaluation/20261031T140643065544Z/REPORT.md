# Kết quả test mới đã khóa trước khi thu

Train: 42 lượt pilot; test mới: 42 lượt, hai block trên cùng SRV01. Không fit lại trên test.

| Phương pháp | Đúng / tổng | Macro-F1 | Coverage |
|---|---:|---:|---:|
| cart_numeric | 42/42 | 1.000 | 100.0% |
| cart_discrete | 36/42 | 0.857 | 85.7% |
| cart_no_quality | 42/42 | 1.000 | 100.0% |
| cart_missingness | 22/42 | 0.432 | 100.0% |
| cart_common | 35/42 | 0.832 | 100.0% |
| fp_classifier | 36/42 | 0.857 | 85.7% |
| majority | 6/42 | 0.036 | 100.0% |

Đây là test giữ riêng theo thời gian, trong phạm vi cùng host/lab. Hai block không đủ để ước lượng CI theo phiên đáng tin cậy hoặc chứng minh chuyển host. Các phiên pilot đã được nhìn trong thiết kế phương pháp.

Tập cân bằng bảy lớp có tỷ lệ lỗi khác production. Confidence/lift và tỷ lệ lớp tại lá cây không phải xác suất nguyên nhân đúng đã hiệu chỉnh.

Đã đối chiếu cùng raw observations với sáu nhận định chuyên gia; insufficient_evidence giữ riêng. Đọc family_comparison.csv thay vì ép expert thành nhãn healthy.

Các cột accuracy bao gồm ABSTAIN trong mẫu số. Per-class metrics, missingness-only/common/no-quality ablations và toàn bộ dự đoán đều được lưu; không bỏ ca khó theo điểm mô hình.

Serving policy đã khóa: CART discrete/FP abstain khi thiếu bất kỳ core ping/TCP80/TCP10050/control probe; các CART khác là đối chứng nghiên cứu. Đã kiểm tra cả raw model serialization và policy này với kết quả live.

SQLite chỉ chứa luật fit trên train; registry ghi validated theo nghĩa kiểm chứng serialization và lưu đánh giá cho nghiên cứu shadow, không phê duyệt production. Không có luật active.

Latency là warm offline cùng đầu vào, gồm dựng feature và inference; không bao gồm API/SSH hoặc thời gian Zabbix phát hiện. Không suy scalability production từ phép đo này.

M8 (máy thật, multi-fault, topology/suppression) chưa được chứng minh bởi tập lỗi đơn này.

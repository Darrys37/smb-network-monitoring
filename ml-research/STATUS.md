# Tiến độ triển khai ML v2 — 30/10/2026

## Hoàn tất nghiệm thu ban đầu phần ML trên ba VM — 31/10/2026 21:13 UTC+7

**COMPLETE_INITIAL_VM_ML_RELEASE_VERIFIED.** Chuỗi thu dữ liệu, huấn luyện, test mới, SQLite/shadow, báo cáo/hình và một demo lỗi thật đã hoàn tất. Đây là phạm vi ba VM hiện có; chưa có máy Ubuntu thật, multi-fault hoặc topology/suppression.

- Train/development: 42 valid; 9 uncertain được giữ riêng. Test mới khóa trước khi thu: 42 valid; 1 uncertain giữ riêng. Mỗi run chỉ dùng cửa sổ cuối; không tính hai cửa sổ của một fault thành hai phép thử độc lập.
- Đã kiểm tra hash nguồn/nhãn/raw, embargo, cùng đầu vào expert/ML, model Python/SQLite và 42 ca shadow lúc fault. Registry có hai model được validated cho nghiên cứu, **không có rule active** trong engine vận hành.
- Báo cáo thật: `evidence/ml-v2/locked-test-v1/evaluation/20261031T140643065544Z/presentation-20261031T141036524152Z/BAO_CAO_NGHIEM_THU.md`. Bảng luật: cùng thư mục `LUAT_HOC_DUOC.md`. CSV/JSON đầy đủ: `evidence/ml-v2/locked-test-v1/evaluation/20261031T140643065544Z`.

| Mô hình | Đúng / tổng test | Macro-F1 | Coverage |
|---|---:|---:|---:|
| cart_numeric | 42/42 | 1.000 | 100.0% |
| cart_discrete | 36/42 | 0.857 | 85.7% |
| fp_classifier | 36/42 | 0.857 | 85.7% |
| majority | 6/42 | 0.036 | 100.0% |
| cart_missingness | 22/42 | 0.432 | 100.0% |

- Expert trả sáu nhận định độc lập; đọc bảng theo diagnostic family, không gán một accuracy bảy lớp cho expert. Confidence/lift và tỷ lệ lớp tại lá là thống kê train, không phải xác suất chẩn đoán đúng đã hiệu chỉnh.
- Demo thật: `evidence/ml-v2/demos/checks/demo-20261031T141114556079Z/result.json`; raw/comparisons ở `evidence/ml-v2/demos`. Chạy lại trên laptop bằng `pwsh -NoProfile -File "C:\Users\Darrys\Documents\ChatGPT\Đồ án network\Run-ML-Demo.ps1"`; nhập SSH ẩn. Wrapper giữ khóa lab và yêu cầu màn hình/system thức tạm thời. Không chạy cùng coordinator thu dữ liệu.
- Postflight sau demo: dịch vụ/HTTP/DNS/control tốt, không còn timer/firewall/stress của lượt; engine source và SQLite runtime vẫn 39 incidents /301 evidence /172 diagnoses /29 recoveries. Bằng chứng `evidence/ml-v2/verification/final-acceptance-20261031T141341675699Z`.
- Từng có Modern Standby làm gián đoạn lab; giữ power-event evidence và các lượt uncertain. Guard hiện tái áp dụng yêu cầu display/system mỗi 15 giây và clear khi kết thúc. Không đổi power plan, lock policy, affinity/priority, CPU/RAM VM. Không quy mọi RCU stall lịch sử về cùng nguyên nhân.
- Kết quả chỉ cho các can thiệp lỗi đơn đã biết trên SRV01, test cân bằng cùng host. Không suy chất lượng production, tỷ lệ lỗi thực tế, chuyển máy thật hoặc suy luận nhân quả từ các điểm số này.
- Hạn chế đã biết từ pilot: che HTTP/DNS thành unknown trên một vector healthy giả định có core probes tốt khiến CART gợi ý interface_down, FP từ chối. Đây là phân tích feature giả định, không phải lượt fault thực; mô hình giữ nguyên, chưa được phê duyệt production. Báo cáo chính giữ vector và SHA gốc.
- Accuracy phân loại và việc Zabbix phát hiện là hai phép đo riêng. Collector được gọi theo lịch; chưa chứng minh tự động event-to-process dispatch. Audit detection đi kèm báo cáo, nêu rõ SRV01 chưa có trigger DNS/ICMP riêng.
- Không cần chạy lại `full_ml_session.py` để xem báo cáo. Source đúng ở repository; workspace stage `ml-v2` cũ không được ghi đè lên đây. Backup chốt xem `ml-final-checkpoint-latest.json` trong workspace và receipt trong thư mục backup C/D.

Các ghi chú tiến độ cũ được giữ trong [lịch sử trước nghiệm thu](../evidence/ml-v2/verification/final-acceptance-20261031T141341675699Z/ml-status-before-final.md).

## Tài liệu thực hiện

Đọc [README](README.md), [protocol nghiệm thu](docs/NGHIEM_THU_VM_V1.md) và [phương pháp nghiên cứu](docs/PHUONG_PHAP_NGHIEN_CUU.md).

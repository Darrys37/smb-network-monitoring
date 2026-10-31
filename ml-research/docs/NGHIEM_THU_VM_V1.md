# Protocol nghiệm thu ML trên VM, phiên bản 1

## Bổ sung 1.1 trước khi thu test — 31/10/2026

Một đợt auto-upgrade đã làm MySQL/Zabbix dừng trong pilot; bản thử bị gián đoạn được giữ riêng. Gate platform schema 2 yêu cầu không có apt job/dpkg lock, dpkg audit sạch, và SHA trạng thái package không đổi trong trial. Test mới còn pin package fingerprint ba VM trước khi thu và kiểm tra trước/sau mọi trial cùng lúc hoàn tất bộ test. Không tắt auto-upgrade; môi trường thay đổi thì dừng trước khi mở điểm. Feature, nhãn, lịch và tham số CART/FP giữ nguyên. Các pilot cũ có điều kiện kiểm soát yếu hơn phải được nêu là dữ liệu phát triển có hạn chế.

Chốt trước khi thu test mới, ngày 30/10/2026. Đây là nghiệm thu ban đầu cho phần ML; máy thật, nhiều lỗi đồng thời và topology/suppression cần các bộ thử riêng.

## Dữ liệu và ngân sách

Train/development: pilot đã có, dự kiến 42 valid run thuộc hai block, bảy trạng thái (healthy và sáu can thiệp). Dữ liệu pilot đã được xem khi thiết kế phương pháp, vì vậy không gọi điểm CV pilot là test cuối.

Test giữ riêng: **42 valid run mới = hai block × ba lượt × bảy trạng thái**, seed lịch 101. Không đưa sample tổng hợp vào tập thực nghiệm. Đề xuất 210 lượt trong plan ban đầu là ngân sách tham khảo; đợt nghiệm thu này thu nhỏ để hoàn thiện luồng và đo sai số ban đầu. Không tuyên bố đã đáp ứng nghiên cứu quy mô 210 lượt.

Các block trên cùng SRV01 vẫn có phụ thuộc theo host/thời gian. Test được giữ riêng theo quy trình và thời gian; điều đó không tự biến 42 lượt thành 42 phép thử độc lập IID hoặc chứng minh khả năng chuyển host. Mỗi lớp chỉ có sáu lượt test; báo counts, confusion matrix và giới hạn thay vì gán CI tổng quát thiếu cơ sở.

## Khóa trước test

`development-freeze.json` lưu nhãn train đã đối chiếu review độc lập, SHA raw/review, profile, config, lịch test, phiên bản package và hash source. Dùng nguyên cấu hình pilot, không tìm lại tham số theo test. Có embargo tối thiểu 600 giây kể từ quan sát train cuối để tránh chồng dữ liệu lịch sử CPU.

Collector, thứ tự probe, thời lượng fault và điều kiện validity không phụ thuộc điểm mô hình. Mỗi scheduled run cần đúng một attempt hợp lệ; attempt uncertain giữ lại và retry bằng ID mới. Không chạy lại vì classifier đoán sai. Chọn cửa sổ cuối mỗi valid run theo quy tắc cố định.

Chỉ mở điểm test khi thu xong cả hai block. Nếu sửa feature/thuật toán sau khi đọc điểm, test đó trở thành development và phải thu test mới để tuyên bố đánh giá giữ riêng.

## Thu, shadow và rollback

Một worker giữ khóa lab; worker kế tiếp phải chờ worker pilot kết thúc thành công. Backup local và VM mới trước test. Mỗi fault có timer độc lập, rollback sở hữu tài nguyên theo token và kiểm tra baseline trước lượt sau. Không giảm gate hoặc đóng cưỡng bức alert để chạy nhanh.

Trong lúc fault, shadow nhận raw observation không chứa nhãn; lưu cả expert và hai đề xuất CART/FP. Kết quả được lưu riêng, không dùng vào quyết định retry/validity. Lỗi inference được ghi riêng, không biến ground truth thành nhãn do model chọn.

Serving policy cố định: profile phải trùng; CART discrete và FP từ chối (ABSTAIN) nếu thiếu core ping/TCP80/TCP10050/control probe. CART numeric và các ablation còn lại là đối chứng nghiên cứu. Không diễn giải thiếu bằng chứng thành healthy.

## Đánh giá và SQLite

- Accuracy tính trên mọi valid run, có ABSTAIN trong mẫu số; macro-F1, coverage và per-class metrics cùng confusion matrix được lưu.
- So expert ở sáu câu hỏi độc lập, giữ matched/not_matched/insufficient_evidence. Không ép expert thành nhãn healthy.
- Các ablation common/no-quality/missingness-only được chạy với cùng train/test và không chọn kết quả thuận lợi để báo riêng.
- Đo warm latency từ cùng raw observation đã nạp: gồm dựng feature/inference, không gồm SSH/API/đọc đĩa hoặc thời gian Zabbix phát hiện. Chưa phải benchmark scalability production.
- Luật CART/FP trong candidate SQLite chỉ fit trên train. Kiểm tra model Python và evaluator SQLite trên cả test và ca biên. So lại với bản shadow đã lưu lúc fault.
- Registry riêng lưu datasets/experiments/models/rules/evaluations/lifecycle với foreign key và audit bất biến. `validated` nghĩa đã kiểm chứng serialization và lưu đánh giá nghiên cứu, chưa phê duyệt production; không có rule active.

Tập thử cân bằng có tỷ lệ lỗi khác production. Association confidence/lift và tỷ lệ lớp ở lá là thống kê train, không phải xác suất nguyên nhân đúng đã hiệu chỉnh. CPU cao cũng có thể là công việc hợp lệ ngoài lab; nhãn cpu_stress chỉ mô tả can thiệp đã tạo.

### Cách diễn giải đối chứng

CART discrete và FP-Growth dùng cùng tập feature đã chia bins, để so thuật toán trong cùng cách biểu diễn. CART numeric còn giữ giá trị liên tục; chênh lệch với FP có thể đến từ cả thuật toán lẫn biểu diễn, không quy toàn bộ cho thuật toán.

`cart_no_quality` chỉ bỏ hai cột coverage/max-gap khỏi input. Cách tạo `cpu_mean` vẫn giữ cùng điều kiện chất lượng như các mô hình khác; đây không phải thí nghiệm tắt toàn bộ quality gate. `cart_missingness` chỉ nhìn có/thiếu dữ liệu, giúp kiểm tra tín hiệu đến từ availability thay vì giá trị đo.

Bins 90% là lựa chọn domain cố định trước test, không phải ngưỡng tối ưu do FP tự tìm. Ngưỡng của CART numeric phản ánh các mức tải đã xuất hiện trong train, không tự trở thành ranh giới sự cố vật lý hoặc bằng chứng nhân quả.

## Đầu ra và cách chạy offline

Trong `ml-research`:

```powershell
python locked_test_v2.py freeze --project-root .. --pilot-output <thu-muc-benchmark-pilot> --freeze ..\evidence\ml-v2\locked-test-v1\development-freeze.json
python locked_test_v2.py evaluate --project-root .. --freeze ..\evidence\ml-v2\locked-test-v1\development-freeze.json --test-root ..\evidence\ml-v2\locked-test-v1 --output-root ..\evidence\ml-v2\locked-test-v1\evaluation
```

Worker đang chạy đã tự điều phối các bước này; không mở thêm coordinator song song. Trạng thái worker nghiệm thu nằm ở workspace `verification/ml-acceptance-status.json`; log là `ml-acceptance.log`. Các lệnh trên không tự gây fault hoặc thu dữ liệu.

Sau thành công: `evaluation/latest.json` trỏ tới REPORT.md, CSV dự đoán, per-class metrics, family comparison, latency, hai DB SQLite và manifest. `ACCEPTANCE_RESULT.md` chỉ được sinh sau postflight và đối chiếu shadow. Tiếp tục dùng engine baseline bằng cách không gọi wrapper ML; không có migration hoặc thay cấu hình runtime engine để rollback.

# Huấn luyện và demo ML v2

Đây là pipeline pilot nội bộ. Lịch 42 lượt phải hoàn tất và mỗi lớp trong mỗi block phải có ít nhất ba lượt hợp lệ trước khi train. Lượt thiếu bằng chứng được giữ nguyên; chạy lại bằng ID khác. Mỗi lượt chỉ lấy cửa sổ cuối theo quy tắc cố định.

## Cách chạy

Từ `C:\Users\Darrys\do-an\ml-research`, dùng môi trường Python riêng với `requirements.txt` và `requirements-ml.txt`. Không nâng dependency trên VM engine chỉ để chạy benchmark này.

```powershell
python -m unittest discover -s tests -v
python export_dataset.py --data-root ..\evidence\ml-v2 --output ..\evidence\ml-v2\quality
python train_v2.py --project-root .. --data-root ..\evidence\ml-v2 --output-root ..\evidence\ml-v2\benchmark
```

Kết quả nằm trong thư mục có timestamp; `benchmark/latest.json` trỏ đến lần chạy mới. Đọc `REPORT.md`, `forward_block_metrics.json`, `held_out_predictions.csv` và `family_comparison.csv`. `dataset_used.csv` có metadata để audit; chỉ feature whitelist được truyền vào model.

```powershell
$result = (Get-Content ..\evidence\ml-v2\benchmark\latest.json -Raw | ConvertFrom-Json).output_dir
python demo_v2.py --observation <duong-dan-observation.json> --candidate-db "$result\candidate_rules.sqlite" --engine-source ..\diagnosis-engine
python demo_live_v2.py --candidate-db "$result\candidate_rules.sqlite" --engine-source ..\diagnosis-engine --output-root ..\evidence\ml-v2\shadow-demo
```

Lệnh demo live nhập mật khẩu SSH ẩn, thu cùng lịch probe trên MON01/SRV01, rồi đưa cùng observation vào luật chuyên gia và model. Không truyền tên lỗi cho collector hoặc model. Raw observation và hai kết quả được lưu chung thư mục. Lệnh này không tự gây lỗi; thử fault phải dùng quy trình có preflight, timer rollback và log độc lập.

## Phương pháp đã khóa cho pilot

- CART numeric và CART discrete: depth tối đa 6, min_samples_leaf=2, seed=37. Không tìm tham số theo điểm test.
- Numeric imputation bằng median, one-hot encoding và các chỉ báo missing được fit riêng trên train trong mỗi fold.
- FP-Growth: ít nhất hai lượt train hỗ trợ tập mục, confidence >=0.80, lift >=1.10, tối đa bốn điều kiện. Chỉ luật feature -> label được giữ. Pruning chỉ nhìn train; xung đột đồng hạng hoặc không có luật thì ABSTAIN.
- Bins định trước: CPU/RAM/CPU mean >=90%; history coverage >=240 giây; max-gap <=120 giây. Không gọi đây là ngưỡng tối ưu.
- Leave-one-session-out giữ cả block cùng tập. Báo riêng train block trước/test block sau. Không tách ngẫu nhiên các cửa sổ cùng lượt sang hai tập.
- Đối chứng: majority; CART bỏ local HTTP/DNS; CART bỏ coverage/max-gap; CART chỉ nhìn availability. Kiểm tra missingness, vector trùng khác nhãn trong `quality_and_identifiability.json`.
- So engine chuyên gia ở sáu câu hỏi độc lập, giữ `insufficient_evidence`; không ép toàn bộ `not_matched` thành healthy. So mô hình đa lớp riêng, gồm ABSTAIN trong mẫu số accuracy.

## Luật trong SQLite và giải thích

`candidate_rules.sqlite` có schema version, metadata và luật CART/FP-Growth trạng thái `candidate`. Điều kiện là JSON với toán tử cho phép; không dùng eval/exec để chạy điều kiện. Rule ID, số lượt train hỗ trợ và loại thống kê đều có trong output.

Trước khi ghi nhận xuất thành công, pipeline đối chiếu tất cả dự đoán trên pilot giữa sklearn và evaluator SQLite. Unit tests có ca category chưa thấy, missing, điều kiện sai và xung đột luật. Đây chưa phải kiểm chứng đầy đủ trên môi trường mới.

Confidence của luật kết hợp và tỷ lệ lớp tại lá cây mô tả dữ liệu train; **không phải xác suất nguyên nhân đúng đã được hiệu chỉnh**. Candidate được fit lại trên toàn pilot dành cho demo và nghiên cứu; điểm validation trong báo cáo đến từ mô hình fit riêng từng fold.

## Giới hạn phải trình bày khi bảo vệ

Hai block trên cùng SRV01/cùng lab vẫn là pilot (một block có thể tiếp tục qua nhiều ngày), chưa phải test mù hay chứng minh chuyển sang PC thật. Thiết kế đã xem dữ liệu pilot ban đầu. Không có CI tổng quát hoặc tuyên bố độ chính xác production từ 42 lượt này.

Mục tiêu hiện tại là nhận diện thao tác lỗi đơn đã biết. Tải CPU cao có thể là công việc hợp lệ ngoài lab; model không được coi mọi CPU cao là hạ tầng hỏng. Các ca giống triệu chứng, tải hợp lệ, host mới, thiếu probe và nhiều lỗi đồng thời cần tập đánh giá riêng.

M4 có code benchmark; M5 cần bộ mới khóa riêng. SQLite hiện là prototype M6; wrapper live là công cụ shadow riêng, chưa thay engine vận hành hoặc hoàn tất M7. Gateway, alert storm và máy thật thuộc M8.

## Tài liệu thuật toán

- [FP-Growth trong mlxtend](https://rasbt.github.io/mlxtend/user_guide/frequent_patterns/fpgrowth/).
- [Định nghĩa support, confidence, lift](https://rasbt.github.io/mlxtend/user_guide/frequent_patterns/association_rules/).
- [Cấu trúc cây sklearn](https://scikit-learn.org/stable/auto_examples/tree/plot_unveil_tree_structure.html).
- [Chia tập theo nhóm và thời gian](https://scikit-learn.org/stable/modules/cross_validation.html).

## Độ ổn định điều phối

Sau timeout SSH thật, đã thêm retry có giới hạn cho bước kiểm tra baseline, không retry che lỗi observation. Authentication/host key lỗi vẫn dừng. Deadline baseline tối đa 20 phút; không hạ tiêu chí CPU/history/dịch vụ/cảnh báo. Cảnh báo load average phải tự phục hồi trước lượt mới. Các attempt gián đoạn vẫn uncertain và retry có ID mới. Bộ kiểm thử sau sửa có 36 tests đạt.

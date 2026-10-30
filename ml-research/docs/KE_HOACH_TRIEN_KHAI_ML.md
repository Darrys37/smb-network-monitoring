# Kế hoạch nâng cấp học luật cho đồ án mạng

Ngày: 30/10/2026 (UTC+7). Trạng thái: kế hoạch triển khai; mới hoàn tất checkpoint và nghiên cứu/POC offline. Các mục bên dưới chưa tự được coi là đã triển khai.

## 1. Checkpoint đã có và phạm vi bảo toàn

- Project: `C:\Users\Darrys\do-an`.
- Nhánh `main`, working tree sạch tại commit `4483cb6299ee3dd1871dfcd6bccdd0c137c65f9e`.
- Cây `diagnosis-engine` không thay đổi so với commit tối ưu `34bf592`.
- Backup chính: `C:\Users\Darrys\Documents\ChatGPT\Đồ án network\deliverables\pre-ml-20261030T055556584993Z`.
- Backup thứ hai: `D:\Study\network-monitoring-project\backups\pre-ml-20261030T055556584993Z`.
- Đã clone lại bundle, đối chiếu HEAD/toàn bộ refs, chạy fsck, giải nén và đối chiếu hash từng file; bản C:/D: khớp.
- 904 file project và 34 file prototype; 7 SQLite lịch sử và 2 SQLite của prototype qua integrity/foreign-key checks.
- Đây là backup local. Chưa có snapshot mới của database live MON01, MySQL, secret VM hoặc đĩa VM. Hai bản trên cùng laptop chưa bảo vệ khỏi mất toàn bộ thiết bị.

Gói `project-working-tree.zip` chứa trạng thái project trước tích hợp ML; `ml-research-prototype.zip` bảo toàn nghiên cứu đã làm riêng. Lịch sử Git nằm trong `project-history.bundle`. `.venv`, cache và node_modules không được lưu; metadata, manifest, checksum và cách phục hồi ở cùng thư mục.

Không dùng thông tin “369 tests từng đạt” thay kết quả chạy mới. Khi bắt đầu sửa code, phải tái kiểm tra trạng thái Git và chạy baseline tests hiện hành.

## 2. Mục tiêu nghiên cứu và giới hạn từng giai đoạn

Mục tiêu: từ cùng bộ bằng chứng, so sánh khả năng hỗ trợ chẩn đoán của luật chuyên gia, CART và bộ phân loại từ luật kết hợp khai phá bằng FP-Growth. Đo chất lượng, khả năng từ chối khi thiếu dữ liệu, độ trễ và độ phức tạp luật.

Giai đoạn ML đầu tiên dùng VM và sáu nhóm lỗi đơn; bổ sung các phiên bình thường đã xác minh. Giữ metadata để sau này thử chuyển sang máy thật. Multi-fault dùng bài toán đa nhãn riêng. Gateway/alert storm cần topology và chuỗi sự kiện riêng, không giả lập Parent Node Status bằng ping host đối chứng.

Những giả định thiết kế đề xuất để bắt đầu:

| Vấn đề | Lựa chọn khởi đầu | Khi cần xét lại |
|---|---|---|
| Thuật toán chính | CART; FP-classifier là đối chứng học luật | Có dữ liệu và kết quả validation cho thấy cần đổi |
| Số feature | Bảy nhóm đo, số cột công bố rõ | Nếu thầy yêu cầu đúng 5–7 scalar thì thu hẹp nhóm lỗi/đại lượng |
| Nhãn | Tách can thiệp thật và giả thuyết chẩn đoán | Không phân biệt được các cơ chế bằng bằng chứng hiện có |
| Confidence | Thống kê train/validation ghi rõ mẫu số | Chỉ gọi xác suất hiệu chỉnh sau khi có dữ liệu calibration đủ |
| Luật tự sinh | Candidate trước, chưa tự active | Chỉ kích hoạt sau equivalence tests và đánh giá độc lập |
| Dữ liệu cũ | Bộ phát triển đã nhìn thấy | Không dùng lại như test cuối độc lập |

## 3. Các mốc, phụ thuộc và đầu ra

| Mốc | Công việc | Đầu ra kiểm tra được | Điều kiện qua mốc |
|---|---|---|---|
| M0 — đã xong | Backup và kiểm tra phục hồi | Bundle, ZIP, MANIFEST, CHECKSUMS, VERIFICATION, RESTORE | Bản sao đọc được, hash đúng, Git/SQLite đạt |
| M1 | Chốt bài toán, schema và protocol | Data dictionary, label map, experiment protocol, split policy | Không có nhãn lấy từ output engine; xác định rõ predictor và metadata |
| M2 | Xây collector và registry thực nghiệm | Module thu đồng nhất, export/import, run registry, smoke tests | Healthy và fault chạy cùng lịch probe; thời gian/observer hợp lệ |
| M3 | Thu pilot VM | Dataset pilot + raw logs + quality report | Có bình thường, đủ nhóm dự kiến, không loại ca thất bại theo điểm mô hình |
| M4 | Xây pipeline nghiên cứu v2 | CART numeric/discrete, FP-classifier, grouped CV, report | Preprocessing chỉ fit train; kết quả tái lập, abstention được tính |
| M5 | Thu và đánh giá bộ độc lập | Manifest train/validation/test, bảng đối chứng, CI phù hợp | Test chưa dùng tuning; so cùng nhiệm vụ/evidence; công bố giới hạn |
| M6 | Chuẩn hóa luật và SQLite | Schema version, evaluator, candidate registry, export | Không eval chuỗi tùy ý; output tương đương mô hình trong phạm vi đã định |
| M7 | Tích hợp chế độ quan sát | Engine adapter, audit/report, live shadow run | Baseline không hồi quy; ML không tự sửa hệ thống; rollback đã thử |
| M8 | Máy thật, multi-fault, correlation | Các bộ thực nghiệm riêng + đánh giá mở rộng | Có đủ hạ tầng và ground truth cho từng tuyên bố |

M1–M3 có thể hoàn thành mà chưa cần máy thật. M4 không được dùng để bù cho protocol thu dữ liệu còn sai. M6 có thể phác thảo schema sớm nhưng chỉ chốt semantics sau M1 và kết quả M4.

## 4. M1 — thiết kế dữ liệu và nhãn

### 4.1. Ba loại nhãn/trạng thái

- `intervention_label`: thao tác thực tế từ log gây lỗi, ví dụ nginx_stop hoặc tcp80_drop.
- `diagnostic_family`: mức kết luận mà bằng chứng hỗ trợ, ví dụ http_service hoặc http_access_path.
- `ground_truth_status`: valid/invalid/uncertain, lý do và bằng chứng xác minh.

Với multi-fault sau này, trường nhãn là một tập, không tạo một class mới cho từng tổ hợp. Trạng thái insufficient của mô hình không phải một loại fault. Healthy phải có xác minh độc lập; không lấy “không matched” làm nhãn healthy.

### 4.2. Schema tối thiểu

| Nhóm trường | Trường chính | Dùng vào ML? |
|---|---|---|
| Định danh | dataset_version, session_id, run_id, window_id | Không; dùng chia tập/audit |
| Ngữ cảnh | host_id, profile_id, topology_version, observer | Host ID không; scope/profile dùng có kiểm soát và phải kiểm tra confounding |
| Thời gian | fault interval, decision_time, sample_time, collected_at | Không dùng timestamp tuyệt đối như predictor |
| Quan sát | ping/TCP/HTTP/DNS/resource/agent/control | Có, qua policy xử lý chất lượng |
| Chất lượng | stale/tool_error/not_collected/not_applicable | Cổng đánh giá và ablation; không gộp thành 0 |
| Ground truth | intervention/family/validity, nguồn log | Chỉ y hoặc lọc chất lượng đã định trước |
| Provenance | collector/code/config version, raw file hashes | Không |

Tách ba tệp/bảng logic: observations, experiment_registry, labels. Khi suy luận, mô hình chỉ nhận observations và context được phép; collector không được nhận tên fault để chọn phép đo.

### 4.3. Định nghĩa thời gian

Chốt một thời điểm ra quyết định, chỉ dùng bằng chứng sẵn có trước hoặc tại thời điểm đó. CPU history dùng cửa sổ lùi, có coverage/max-gap/tuổi mẫu; không dùng dữ liệu recovery. Phép đo mới lấy có thể chứa sample trước fault, phải ghi nhận rõ. Lượt ổn định và giai đoạn chuyển tiếp được đánh giá riêng.

Nghiệm thu M1: có bảng ví dụ đầu vào/nhãn cho healthy, R1–R6, thiếu probe và lỗi collector; chứng minh không cần nhãn để dựng feature; công bố mapping giả thuyết cho baseline chuyên gia.

## 5. M2 — collector và tổ chức code

Trước khi viết: đọc các module liên quan trong project thật và kiểm tra AGENTS.md nếu có. Tạo nhánh phát triển `feature/ml-research-v2` trên checkout phù hợp, giữ tag nghiệm thu cũ. Không tự tạo worktree hoặc đổi nhánh khi có sửa đổi của người dùng chưa được xem xét.

Cấu trúc đề xuất trong repository khi triển khai:

```text
ml-research/
  schemas/                 # Quan sát, nhãn, feature, luật
  config/                  # Profile/threshold/version không có secret
  src/                     # Validate, features, splits, CART, FP, metrics, export
  tests/                   # Rủi ro leakage/time/semantics/serialization
  docs/                    # Protocol, data dictionary, hướng dẫn chạy
  outputs/                 # Artifact theo experiment ID, tránh commit file lớn tùy tiện
evidence/ml-v2/
  runs/<run_id>/           # Raw log bất biến, registry và hashes
```

Phân công công việc:

- Codex: viết/kiểm tra module, script thu và rollback, validation, export, test và báo cáo từ dữ liệu.
- Chủ đồ án: xác nhận thiết bị/điều kiện lab, thực hiện thao tác vật lý, quay minh chứng, trao đổi yêu cầu thầy và hiểu kết quả bảo vệ.
- Các fault do phần mềm chỉ chạy sau preflight và với timer rollback, theo phạm vi thực nghiệm đã thống nhất.

Collector phải thu cùng bộ phép đo theo profile ở mọi trạng thái, có timeout và ghi lỗi riêng từng nguồn. HTTP local và DNS phải từ đúng observer. Khi target mất liên lạc, ghi không thu được; không tự dựng giá trị giả. Retry phải lưu attempt và thời điểm, không biến các attempt thành lượt độc lập.

Nghiệm thu: kiểm tra target/host mapping, observer, timestamp tương lai/cũ, units, disabled item, malformed payload, timeout và không ghi hồ sơ dở. Có một lần healthy thu end-to-end; chứng minh schedule không phụ thuộc fault label.

Trước khi thay bất kỳ cấu hình hoặc source trên VM: tạo backup runtime mới bằng SQLite backup API hoặc phương thức nhất quán, kiểm tra DB; sao lưu config/source cần đổi. Backup local M0 không thay bước này. MySQL/đĩa VM chỉ cần phạm vi backup tương ứng nếu triển khai thay đổi chạm tới chúng.

## 6. M3 — pilot trên VM

Trình tự một lượt:

1. Đăng ký Run ID và kịch bản dự kiến trước khi gây lỗi.
2. Kiểm tra giờ, topology/profile, dịch vụ và baseline; chuẩn bị rollback.
3. Thu quan sát trước fault theo lịch chung.
4. Ghi marker trước/sau thao tác; xác minh can thiệp thành công bằng nguồn độc lập.
5. Tiếp tục thu trong fault, kể cả khi Zabbix chưa có alert hoặc engine không kết luận.
6. Rollback, xác minh khôi phục, chờ history/load ổn định trước lượt khác.
7. Chốt validity và nhãn từ log; xuất manifest và quality report.

Pilot đề xuất: hai phiên riêng, mỗi phiên ba lượt cho sáu nhóm fault và ba cửa sổ healthy độc lập theo protocol: 42 lượt/cửa sổ thử. Đây là ngân sách kiểm tra protocol, chưa phải cỡ mẫu chứng minh accuracy. Các quan sát healthy phải có thời lượng/trạng thái xác minh rõ, không coi từng giây là một lượt.

Kiểm tra sau pilot: phân bố lớp, missingness theo lớp/host, vector trùng khác nhãn, mẫu trước fault, leakage qua profile, lỗi thu, độ dài cửa sổ. Phải đánh giá cả việc collector thất bại. Dừng để sửa schema/protocol nếu probe chỉ có ở một lớp hoặc nhãn bị lộ qua tên file/ID/feature.

## 7. M4 — pipeline học luật v2

Các bước theo thứ tự:

1. Nạp registry, kiểm tra hash/version, tạo group theo phiên và run.
2. Chốt split trước preprocessing; mọi window của cùng run nằm cùng tập.
3. Dựng feature hợp lệ: rời rạc hóa domain định trước hoặc fit bin chỉ trong train.
4. Fit CART numeric và CART discrete; tham số depth/leaf/pruning chọn trong development CV.
5. FP-Growth lấy frequent itemsets; chỉ tạo luật feature -> diagnostic label.
6. Lọc theo support, confidence, lift và số Run ID hỗ trợ; xử lý luật trùng/thừa.
7. Khóa chính sách xung đột và abstention trên validation; không âm thầm chọn nhãn theo test.
8. Lưu từng dự đoán ngoài fold, tất cả tham số, seed, versions, hashes và thời gian.

Ngưỡng support=0.10/confidence=0.80/lift=1.10 và depth=4 của POC là tham số minh họa, không phải ngưỡng tối ưu đã nghiên cứu. Lưới tuning phải nhỏ và có lý do; không tăng số cấu hình để tìm điểm đẹp trên 18 lượt.

Ablation bắt buộc: common vs thêm local HTTP/DNS; numeric vs discrete cho CART; có/không thông tin chất lượng; presence-only như phép phát hiện shortcut. Khi hoán vị nhãn để kiểm tra ngẫu nhiên, hoán vị ở đơn vị nhóm phù hợp, không phá cấu trúc phụ thuộc giữa cửa sổ.

Nghiệm thu M4: không có group giao nhau, không fit preprocessing toàn tập, không dùng label/event name/recovery làm predictor, abstain tính rõ mẫu số, xuất/import mô hình tái lập dự đoán. Cây cần xem xét các nhánh suy luận phi lý; không ép cây học theo luật chuyên gia bằng cách sửa ground truth.

## 8. M5 — thiết kế đối chứng và test cuối

Sau pilot mới chốt ngân sách thu chính thức. Phương án khởi đầu để ước lượng công sức: sáu phiên mới, năm lượt mỗi trạng thái (sáu fault + healthy) = 210 lượt; bốn phiên phát triển, hai phiên test khóa riêng. Đây là đề xuất công việc, **không phải chứng minh cỡ mẫu đủ**. Khi đó test chỉ có mười lượt mỗi lớp, khoảng bất định vẫn rộng. Điều chỉnh ngân sách theo learning curve, độ bất định và thời gian thực tế.

Không dùng pilot/test đã xem để chọn tham số rồi gọi là đánh giá độc lập. Nếu sửa phương pháp sau khi mở test, đánh dấu test đã thành development và thu test mới.

Hai phép đánh giá:

- So CART/FP trên cùng nhãn và evidence; healthy là lớp có xác minh, unknown là tình huống stress test hoặc abstention policy.
- So với luật chuyên gia ở mức từng diagnostic family: giữ matched/not_matched/insufficient; so recall, báo nhầm, coverage và lỗi khi có kết luận. Không lấy một matched thuận lợi làm dự đoán cho từng ca.

| Tiêu chí | Cách đo |
|---|---|
| Nhận diện | Macro-F1, precision/recall từng nhóm, confusion matrix |
| Báo nhầm | False-positive rate trên healthy, số lượt và khoảng bất định |
| Thiếu bằng chứng | Coverage, abstention rate, lỗi trên ca được trả lời và trên toàn bộ ca |
| End-to-end | Tính cả fault hợp lệ monitoring bỏ sót; tách detection và classification |
| Độ trễ | Collection/API, feature extraction, inference; median/p95, cùng máy và input |
| Dễ giải thích | Số luật, số điều kiện, depth, số lượt hỗ trợ, độ ổn định giữa split |
| Mở rộng | Tăng host/event/rule có kiểm soát, đo throughput/CPU/RAM; không suy từ cỡ mẫu 18 |

CI/bootstrapping phải theo nhóm độc lập thích hợp; báo số phiên/host và giới hạn của số nhóm ít. Không có yêu cầu “ML bắt buộc hơn chuyên gia” hoặc “accuracy phải 100%”. Kết quả âm có giá trị nếu phương pháp và bằng chứng chặt.

## 9. M6 — luật và SQLite

Giữ database học luật riêng với database incident ban đầu cho đến khi schema tích hợp được duyệt. Thiết kế tối thiểu:

- datasets/experiments: nguồn, split, hashes và phiên bản.
- models: thuật toán, feature schema, preprocessing, hyperparameters, metrics.
- rules: rule version, điều kiện có kiểu dữ liệu, nhãn/giả thuyết, scope/observer/freshness requirements.
- rule_evaluations: train counts, support/confidence/lift, validation/test results có nguồn.
- rule_lifecycle: candidate -> validated -> active -> retired, thời điểm và lý do.

Không gộp association_confidence, leaf purity và calibrated probability vào cùng trường “confidence” thiếu định nghĩa. Không tự kích hoạt chỉ vì confidence train cao. Bất kỳ thay đổi ý nghĩa chẩn đoán hoặc schema runtime phải được trình bày tác động trước khi triển khai.

Nghiệm thu: evaluator dùng tập toán tử cho phép; xử lý unknown/absent đúng; serialization không đổi ngưỡng; Python model và rule-table evaluator cho cùng đầu ra trên test và ca biên; mô hình/luật cũ vẫn truy vết được. Không dùng eval/exec để chạy điều kiện từ DB.

## 10. M7 — tích hợp và rollback

1. Tái kiểm tra Git, tests, VM và backup runtime mới.
2. Chạy offline replay trên dữ liệu đã đóng băng; giữ kết quả baseline riêng.
3. Tích hợp ML như chế độ tùy chọn/shadow, log cả bằng chứng và model/rule version.
4. Chạy các ca healthy/fault có rollback, đối chiếu report; không tự hành động khắc phục từ kết luận ML.
5. Kiểm tra service, dữ liệu và backup; cập nhật handoff theo kết quả thật.

Điều kiện rollback: regression ở validation event, freshness, observer, transaction hoặc report; trộn evidence giữa lượt; dự đoán dùng feature sai version; lỗi DB; chênh lệch không giải thích được giữa model và rule evaluator.

Rollback ứng dụng: tắt chế độ ML và dùng phiên bản baseline đã lưu. Nếu có migration DB thì phải có migration ngược hoặc phục hồi bản DB nhất quán vào vị trí mới để kiểm tra; không chép đè DB live đang mở. Không chạy `git reset --hard` trên checkout người dùng đang làm việc. Giữ log của lượt lỗi để truy nguyên.

## 11. M8 — mở rộng theo yêu cầu thầy

| Hạng mục | Phụ thuộc | Thí nghiệm cần có |
|---|---|---|
| Máy thật | LAN/Agent/observer và profile được xác minh | Test chuyển VM -> PC, tách dữ liệu theo host; video + log/ID |
| Multi-fault | Nhãn tập hợp, đủ bằng chứng phân biệt | Các cặp lỗi đã xác minh; báo micro/macro-F1 và exact match |
| Gateway | Router/parent thật trên đường giám sát | Mất parent và lỗi con độc lập, topology version |
| Alert storm | Event timeline + topology + latency policy | Parent trước/sau child, nhiều lỗi độc lập cùng 30s, parent phục hồi |
| Suppression | Audit không mất raw event | Tỷ lệ giảm thông báo và tỷ lệ che nhầm lỗi con độc lập |

Không ép “chỉ một root alert” khi có nhiều fault thật. Giữ raw event và dấu vết suppression. So với trigger dependencies Zabbix và giải thích phần đóng góp bổ sung của engine.

## 12. Nhịp triển khai và tiêu chí kết thúc

Ước lượng sơ bộ theo phiên làm việc tập trung, chưa phải lịch cam kết: M1 khoảng 1–2 phiên; M2 2–3; M3 2–4; M4 2–3; M5 phụ thuộc số lượt và thời gian ổn định CPU/Agent; M6–M7 khoảng 3–5 phiên. Sau pilot mới ước lượng giờ thu chính thức từ thời gian fault/rollback thật. M8 có lịch riêng theo thiết bị sẵn có.

Sau mỗi mốc: có trạng thái done/blocked/remaining, lệnh thực chạy, artifact, tests/kiểm chứng, limitations, Git commit theo phạm vi được giao và checkpoint mới khi cần. Kết thúc giai đoạn ML khi có protocol, dữ liệu truy vết được, đánh giá độc lập, luật giải thích được, kiểm tra tích hợp/rollback và tài liệu bảo vệ; không chỉ khi script in accuracy.

Việc bắt đầu tiếp theo: **M1 — tạo data dictionary, label map và protocol thu đồng nhất**. M0 đã hoàn tất; chưa bắt đầu tích hợp học máy vào engine.

Tham khảo phương pháp và nguồn khoa học: [PHUONG_PHAP_NGHIEN_CUU.md](PHUONG_PHAP_NGHIEN_CUU.md).

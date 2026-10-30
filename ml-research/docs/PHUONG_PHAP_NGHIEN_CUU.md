# Phương pháp học luật cho đồ án giám sát mạng

Ngày nghiên cứu: 30/10/2026. Trạng thái: đề xuất phương pháp sau khi đọc tài liệu khoa học và kiểm tra pipeline `offline-poc-v1`; chưa triển khai protocol thu mới hoặc thay engine live.

## 1. Kết luận lựa chọn phương pháp

Hướng phù hợp là **học luật phân loại có giám sát từ bằng chứng đa nguồn**, với CART là mô hình dễ giải thích đầu tiên, và bộ phân loại dựa trên luật kết hợp khai phá bằng FP-Growth là phương pháp đối chứng. Luật chuyên gia là baseline vận hành. Không mặc định phương pháp học máy phải thắng.

Câu hỏi nghiên cứu đề xuất:

> Với cùng thông tin đo và ngân sách thời gian, luật học từ dữ liệu nhận diện các nhóm sự cố trong lab tốt đến đâu so với luật chuyên gia, và kết quả thay đổi thế nào khi chuyển phiên thu, host hoặc thiếu bằng chứng?

Ba giả thuyết cần kiểm tra, không coi là kết quả sẵn có:

- H1: thêm góc nhìn HTTP nội bộ/DNS đúng observer giúp phân biệt lỗi có cùng triệu chứng từ xa.
- H2: điểm đánh giá theo phiên/host chưa thấy thấp hơn điểm chia ngẫu nhiên các quan sát gần nhau.
- H3: cơ chế từ chối kết luận làm giảm sai trên các trường hợp thiếu bằng chứng, đổi lại coverage thấp hơn.

Phạm vi đầu tiên là sáu kịch bản lỗi đơn đã có và các phiên bình thường đã xác minh. Multi-fault cần đầu ra đa nhãn và thí nghiệm riêng; alert storm cần dữ liệu chuỗi sự kiện và topology. Không gộp tất cả thành một bài toán phân loại bảy lớp.

RCA là phạm vi rộng hơn phân loại kịch bản. Bài tổng quan của Solé và cộng sự phân tích nhiều mô hình/kỹ thuật RCA theo yêu cầu hiệu năng và khả năng mở rộng; nó không chứng nhận riêng FP-Growth/CART là lựa chọn tối ưu cho lab này. [Solé et al., 2017](https://arxiv.org/abs/1701.08546).

## 2. Phát hiện cụ thể từ dữ liệu hiện tại

Đã đối chiếu `pipeline.py`, CSV đầu ra, cây toàn tập và kết quả CV tại `outputs/20261030T050537323942Z`.

| Quan sát | Ý nghĩa phương pháp |
|---|---|
| 18 Run ID, ba lượt mỗi kịch bản | Là 18 lượt riêng; chưa chứng minh độc lập thống kê giữa các lượt cùng lab/phiên |
| Bộ common chỉ có 5 vector khác nhau | Nhiều dòng là lặp của cùng một kiểu quan sát sau rời rạc hóa |
| Cả ba R2 và ba R4 có vector common giống hệt | Mô hình tất định chỉ nhìn các cột common không thể phân biệt đủ sáu dòng này |
| Trần khớp nhãn trên chính tập common là 15/18 | CART đạt 15/18 đã chạm trần biểu diễn trong tập này; không thể chữa bằng tuning thuật toán |
| Bộ extended có 6 vector khác nhau | Mỗi lớp có một kiểu vector; 18/18 còn là bài toán rất dễ trong phạm vi mẫu đã thu |
| Chỉ nhìn việc có thu HTTP/DNS cũng đúng 9/18 ngoài fold | Quy trình thu dữ liệu tiết lộ một phần nhãn |
| Cây toàn tập không dùng cpu_band | Nhánh nhận diện CPU đang dựa vào các đặc điểm khác; cần kiểm tra cơ chế trước khi vận hành |
| Chỉ R4 dùng host CLI01, phần lớn lỗi khác dùng SRV01 | Có confounding giữa host/service profile và nhãn; bỏ host_id chưa xóa hết dấu vết host |

Chi tiết tính toán nằm trong `methodology-audit.json`. Trần 15/18 được tính bằng cách nhóm các vector giống nhau rồi cộng số mẫu của nhãn đông nhất trong từng nhóm. Đây là giới hạn khớp nhãn của **biểu diễn hiện tại trên tập hiện tại**, không phải giới hạn của mọi dữ liệu mạng hoặc mọi feature mới.

Hai lớp R2/R4 còn khác thiết kế dịch vụ: CLI01 vốn không cung cấp HTTP. Vì vậy `TCP80=refused` ở CLI01 không cùng ý nghĩa sự cố với `refused` ở SRV01. Context về dịch vụ là cần thiết, nhưng phải thu đủ nhiều lỗi và trạng thái bình thường trên mỗi profile để tránh biến profile thành đáp án.

Các điểm của pipeline trước cần gọi đúng tên:

- Ba fold theo Run ID mới chống cùng lượt xuất hiện ở cả train/test; chưa chống phụ thuộc giữa các lượt cùng phiên.
- FP-Growth + bộ chọn luật hiện có là thiết kế POC riêng, không phải cài đặt CBA chuẩn.
- Chín cột thuộc bảy nhóm đo không phải đúng bảy scalar features.
- Cửa sổ tuổi mẫu 180 giây không biến tất cả bằng chứng thành phép đo đồng thời hoặc cùng trạng thái fault.
- Kho luật ứng viên có 188 luật FP; số lượng luật nhiều chưa chứng minh chất lượng, còn cần lọc trùng và đánh giá độ ổn định.

## 3. Phân biệt triệu chứng, can thiệp và giả thuyết

Ví dụ: `remote TCP80 timeout + local HTTP200` hỗ trợ giả thuyết đường truy cập HTTP có vấn đề. Trong một lượt thử cụ thể, log injection có thể xác nhận thao tác firewall drop. Điều này không chứng minh mọi tình huống tương tự ngoài lab đều do firewall.

Lưu cả ba lớp thông tin:

1. `intervention_label`: thao tác thật, như dừng Nginx, drop TCP80, down interface.
2. `diagnostic_family`: nhóm giả thuyết engine có thể hỗ trợ bằng quan sát, như dịch vụ HTTP hoặc đường truy cập HTTP.
3. `ground_truth_status`: valid, invalid, uncertain, cùng tham chiếu log xác minh.

Không dùng `matched`, tên trigger hoặc câu kết luận của engine làm nhãn ground truth. Không gán nhãn healthy chỉ vì không có alert. Một lượt bình thường cần kiểm tra dịch vụ, trạng thái máy và các phép đo liên quan. Lượt fault hợp lệ nhưng Zabbix không phát hiện vẫn phải được ghi nhận khi đánh giá end-to-end; không chỉ giữ lượt có incident đẹp.

Nếu hai can thiệp khác nhau tạo đúng cùng bằng chứng đo, lựa chọn đúng là thêm phép đo, dùng nhãn giả thuyết rộng hơn, hoặc abstain. Không ép thuật toán phân biệt điều không nhận diện được từ đầu vào.

## 4. Đơn vị dữ liệu và thời gian

Đơn vị thực nghiệm độc lập cần quản lý là một lượt can thiệp trong một phiên xác định, có baseline trước và khôi phục sau. Một dòng học máy có thể là một cửa sổ quan sát thuộc lượt đó. Nhiều cửa sổ cùng lượt vẫn là dữ liệu phụ thuộc.

Metadata tối thiểu: `experiment_id`, `session_id`, `run_id`, `window_id`, `host_id`, `service_profile`, `topology_version`, `collector_version`, `fault_start`, `fault_end`, `decision_time`, nguồn nhãn và chất lượng nhãn. Metadata giữ để audit/chia tập; không tự động đưa hết vào mô hình.

Quy tắc thời gian đề xuất:

- Mọi feature phải có sẵn tại `decision_time`; không dùng recovery hoặc mẫu thu sau đó.
- Lưu cả sample time và collected time, observer, tuổi mẫu, khoảng lệch giữa các probe.
- Tách cửa sổ ổn định khỏi thời kỳ chuyển trạng thái khi huấn luyện bản đầu. Giữ transition windows để đánh giá độ trễ riêng.
- Một snapshot sau fault vẫn có thể chứa CPU/Agent lấy trước fault. Cần kiểm tra thời gian từng mẫu, không chỉ `max(collected_at)`.
- Nếu CPU dùng lịch sử 5 phút, cửa sổ đó phải kết thúc tại thời điểm ra quyết định; ghi coverage, số mẫu và max gap.
- Chu kỳ lấy item, thời gian trigger chờ, thời gian probe và cửa sổ correlation là các đại lượng khác nhau. CPU trigger chờ nhiều phút không tự tương quan đúng với HTTP alert chỉ vì đặt cửa sổ 30 giây.

## 5. Bộ feature đề xuất

Ưu tiên bảy **nhóm** có ý nghĩa. Số cột thực tế có thể lớn hơn bảy; nếu yêu cầu môn học bắt buộc đúng 5–7 scalar, cần thu hẹp mục tiêu thay vì giấu nhiều đại lượng trong một ô.

| Nhóm | Dữ liệu nên giữ | Lưu ý |
|---|---|---|
| ICMP | trạng thái, tỷ lệ mất gói trong cửa sổ | Không biến tool error thành host down |
| TCP dịch vụ | success/refused/timeout cho đúng port | Refused và timeout khác nhau |
| HTTP | remote/local status, mã HTTP, observer | Cần cả góc nhìn; non-200 khác lỗi không kết nối |
| DNS | trạng thái/rcode, latency khi trả lời, control cùng observer | Timeout có status riêng, không điền latency=0; nếu kiểm tra nội dung DNS cần IP kỳ vọng |
| Resource | CPU mean/max/coverage, load trên core, RAM | CPU và RAM là đại lượng riêng; CPU cao không tự chứng minh ứng dụng chậm |
| Agent | tuổi mẫu, trạng thái item, TCP10050 | Phân biệt mẫu cũ, item disabled và service không phản hồi |
| Topology/control | control reachability và parent reachability riêng | Peer control không được đổi tên thành parent |

Chất lượng dữ liệu cần phân biệt `not_collected`, `not_applicable`, `stale`, `tool_error`, `measured_failure`. Không gộp tất cả thành số 0. Chất lượng và HTTP scope được dùng trong cổng kiểm tra khả năng đánh giá; nếu dùng làm predictor thì cần thí nghiệm ablation để đo shortcut.

Các tham số tuổi mẫu phải dựa trên chu kỳ thu và mục tiêu chẩn đoán. Ngưỡng CPU 90% có thể giữ như lựa chọn domain định trước, nhưng phải ghi rõ. Ngưỡng RAM90 của POC chưa có luận chứng riêng. So sánh CART trên số liên tục với CART/FP trên các bin định trước để thấy ảnh hưởng rời rạc hóa.

## 6. Vai trò thực sự của FP-Growth

FP-Growth nén giao dịch bằng FP-tree và khai phá các tập mục thường xuất hiện bằng tăng trưởng mẫu. Nó là thuật toán khai phá frequent itemsets; chất lượng phân loại còn phụ thuộc lớp xây dựng bộ phân loại phía sau. [Han et al., 2004, bản mở rộng công trình FP-Growth](https://www.cs.sfu.ca/~jpei/publications/dami03_fpgrowth.pdf).

Giao dịch ví dụ: `{ping=up, tcp80=timeout, local_http=200, fault=http_access_path}`. Chỉ cho nhãn xuất hiện ở vế phải khi xây luật phân loại. Input dự đoán không chứa nhãn.

Với A là tổ hợp feature và C là nhãn:

`support(A→C)=n(A∩C)/N`; `confidence(A→C)=n(A∩C)/n(A)`; `lift=confidence/support(C)`.

Confidence 1 với ba ca chưa có cùng ý nghĩa thực tiễn như confidence 0.95 với hàng trăm lượt độc lập. Lift cũng thay đổi theo tỷ lệ lớp của bộ thử; tập fault cân bằng nhân tạo không phản ánh tần suất sự cố trong vận hành. Các định nghĩa: [mlxtend](https://rasbt.github.io/mlxtend/user_guide/frequent_patterns/association_rules/).

Pipeline nghiên cứu nên có các bước tách biệt:

1. Chốt hoặc học bin chỉ trong train.
2. Khai phá frequent itemsets từ train, giới hạn chiều dài điều kiện để dễ giải thích.
3. Lọc class association rules, yêu cầu cả support tương đối và số **Run ID** hỗ trợ; số cửa sổ dài không được lấn át số lượt.
4. Lọc luật trùng/thừa. Nếu luật dài không có lợi ích validation so với luật ngắn cùng kết luận, ưu tiên luật ngắn.
5. Xử lý xung đột, chọn bộ luật và chính sách abstain trên validation.
6. Đánh giá bộ luật đã khóa trên test mới.

Nền tảng phù hợp là associative classification/CARs. CBA của Liu–Hsu–Ma có bước sinh luật và xây classifier riêng, với thứ tự và default class cụ thể. Nếu thay khai phá bằng FP-Growth, đổi cách xếp hạng hoặc dùng abstain, phải mô tả là biến thể, không nhận là tái lập nguyên CBA. [Liu et al., KDD 1998](https://cdn.aaai.org/KDD/1998/KDD98-012.pdf).

Khai phá nhiều luật còn làm tăng khả năng gặp mẫu ngẫu nhiên vượt ngưỡng. Holdout/permutation hoặc kiểm soát nhiều phép thử có cơ sở nghiên cứu; riêng đồ án này ưu tiên bộ validation độc lập và báo số luật thử/giữ. Không xem lift>1 là kiểm định ý nghĩa thống kê. [Liu, Zhang & Wong](https://arxiv.org/abs/1110.6652).

## 7. CART và so sánh công bằng

CART chia nhị phân theo feature/ngưỡng để giảm độ hỗn tạp của nhãn. Đường gốc–lá có thể diễn đạt thành IF...THEN. `DecisionTreeClassifier` của scikit-learn là CART, chọn entropy không biến nó thành C4.5. Giới hạn depth, số mẫu ở lá và pruning để kiểm soát cây. [Tài liệu scikit-learn](https://scikit-learn.org/stable/modules/tree.html).

Đề xuất ba cấu hình nghiên cứu:

- CART-numeric: giữ số liên tục hợp lệ, mã hóa các biến trạng thái.
- CART-discrete: dùng cùng bin/feature với FP để đối chứng biểu diễn.
- FP-classifier: CARs + chính sách giải quyết xung đột được công bố.

Các phép so sánh này trả lời hai câu khác nhau: thuật toán nào phù hợp với cùng biểu diễn, và pipeline nào tốt hơn khi được dùng dạng dữ liệu phù hợp. Không quy mọi chênh lệch cho thuật toán nếu đầu vào khác nhau.

POC dùng `max_depth=4`, `min_samples_leaf=1`. Đây là thông số thử, không phải kết quả tối ưu. Khi đủ nhóm độc lập, thử một lưới nhỏ trong validation; không chạy hàng trăm cấu hình trên 18 lượt rồi chọn điểm cao nhất.

## 8. Thiết kế thu dữ liệu trước khi chạy thuật toán mới

Thu cùng bộ phép đo định trước trong mọi lượt, bất kể fault nào được tạo. Script collector chỉ biết profile/target và lịch lấy mẫu; không nhận tên fault để chọn có chạy DNS/HTTP hay không. Log injection giữ riêng cho nhãn.

Trong một phiên, đảo thứ tự kịch bản theo lịch ghi nhận được. Sau mỗi lượt phải rollback và kiểm tra baseline ổn định; CPU cần đủ thời gian để history/load không còn mang ảnh hưởng lượt trước. Thay đổi tải nền có kiểm soát và ghi metadata. Tránh để một fault luôn thuộc một host, một giờ hoặc một cấu hình duy nhất.

| Nhóm thí nghiệm | Mục đích |
|---|---|
| Bình thường nhàn rỗi và có tải hợp lệ | Đo báo nhầm, tránh đồng nhất tải cao với hỏng |
| Sáu fault đơn | Đánh giá nhận diện nhóm lỗi |
| Tình huống giống triệu chứng | Firewall reject so với service dừng; ICMP bị chặn nhưng TCP tốt; DNS tên sai so với đường DNS lỗi |
| Thiếu/lỗi collector | Đánh giá abstention, tránh gán tool error thành fault |
| Lỗi đồng thời đã xác minh | Thử bài toán đa nhãn sau khi bản đơn ổn |
| Host/phiên mới | Đánh giá khả năng chuyển môi trường |

Nếu một tình huống không tạo được an toàn hoặc xác minh không thành công, ghi invalid/uncertain kèm lý do; không đổi nhãn theo output mô hình. Không bổ sung sample tổng hợp vào tập test thực để nâng điểm. Dữ liệu tổng hợp chỉ nên dùng kiểm tra logic hoặc một nghiên cứu riêng ghi rõ nguồn.

Không có số mẫu tối thiểu phổ quát như “100 dòng là đủ”. Có thể bắt đầu một pilot nhiều phiên để kiểm tra protocol, sau đó lập learning curve theo số lượt/phiên độc lập và chọn độ bất định chấp nhận được.

Ví dụ toán học: nếu có ba phép thử Bernoulli độc lập đều thành công, khoảng Wilson hai phía 95% có cận dưới khoảng 43.9%. Nếu có 60 lượt bình thường độc lập và không báo nhầm, cận trên exact một phía 95% của xác suất báo nhầm vẫn khoảng 4.87%. Đây là minh họa dưới giả định độc lập, không phải CI hợp lệ tự động cho các fold phụ thuộc của 18 lượt cũ. [NIST về khoảng tin cậy tỷ lệ](https://itl.nist.gov/div898/handbook/prc/section2/prc241.htm).

## 9. Chia tập và đánh giá

Chia nhóm trước mọi thao tác học từ dữ liệu. Các cửa sổ cùng run ở cùng tập; các run cùng phiên nên ở cùng tập cho thí nghiệm tổng quát theo phiên. Với chuỗi thời gian, train trên các phiên trước, test các phiên sau; nếu cửa sổ lịch sử chồng qua ranh giới thì cần khoảng cách để loại chồng lấn. [Grouped/time-series CV](https://scikit-learn.org/stable/modules/cross_validation.html).

Thiết kế khả thi khi có dữ liệu mới:

1. Dùng các phiên phát triển để fit và chọn tham số với grouped CV nội bộ.
2. Khóa feature, preprocessing, luật và ngưỡng abstain.
3. Đánh giá một tập phiên test thu mới, chưa dùng chọn model.
4. Đánh giá chuyển host/topology bằng tập riêng; chỉ gọi là chuyển sang máy thật khi thật sự có tập đó.

Nếu vừa tuning vừa ước lượng hiệu năng bằng CV trên toàn tập phát triển, dùng nested CV, với chia nhóm thích hợp ở cả hai vòng. Không bắt buộc nested CV nếu đã có test độc lập khóa riêng. [Nested CV](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html).

Các chỉ số chính: macro-F1 và precision/recall từng nhóm lỗi; false-positive rate trên bình thường; coverage, lỗi trên các ca được trả lời, và lỗi/tỷ lệ abstain trên toàn bộ tập. Chỉ số end-to-end phải tính cả lượt fault hợp lệ không được monitoring phát hiện.

Với multi-fault, dùng tập nhãn ground truth, báo micro/macro-F1 theo nhãn và exact-match của tập nhãn. Không coi mỗi cặp fault là một lớp mới rồi tuyên bố đã giải quyết mọi phối hợp.

Khi so với engine chuyên gia: engine trả sáu giả thuyết độc lập, `not_matched` không phải healthy. Ưu tiên đối chiếu từng giả thuyết với nhãn chuẩn hóa, giữ riêng abstain/insufficient. Nếu cần bảng phân loại đơn, phải công bố phép ánh xạ trước test; không tùy chọn một matched có lợi nhất cho mỗi ca.

Lặp đo latency trên cùng máy, cùng evidence và quy mô; tách collection/API, feature extraction và inference. Báo median/p95 và cấu hình, không so microsecond predict với giây CLI đầy đủ. Scalability cần thay đổi số host/event/rule và đo throughput/CPU/RAM, không suy từ 18 lượt.

Độ bất định nên tính theo đơn vị độc lập. Khi có nhiều cửa sổ/run/phiên, bootstrap theo nhóm thay vì từng dòng. So sánh mô hình trên cùng các ca test và báo chênh lệch cùng độ bất định; với mẫu ít, kết luận mô tả có ích hơn tuyên bố thắng dựa trên vài phần trăm.

## 10. Confidence, giải thích và xuất SQLite

Ba con số khác nhau: confidence của luật kết hợp; tỷ lệ lớp tại lá cây; và xác suất dự đoán đã được kiểm tra/hiệu chỉnh. Hiện chỉ có hai loại đầu. Calibration cần dữ liệu tách khỏi fit, giữ quy tắc chia nhóm; không tự hiệu chỉnh đáng tin bằng 18 lượt. [Probability calibration](https://scikit-learn.org/stable/modules/calibration.html).

Giao diện thử nên hiển thị: điều kiện khớp, giá trị/observer/thời điểm evidence, số lượt hỗ trợ luật, support/confidence/lift train và kết quả validation. Chưa nên hiển thị “xác suất nguyên nhân đúng 100%”. Giải thích cây là diễn giải quyết định mô hình, không chứng minh nhân quả vật lý.

SQLite nên lưu tối thiểu rule_id/version, algorithm/version, feature_schema/binning_version, điều kiện có kiểu dữ liệu, nhãn/giả thuyết, scope và requirements về freshness/observer, provenance dataset, train counts, validation metrics và lifecycle candidate/validated/active/retired. Đây là thiết kế đề xuất; database POC hiện chỉ có candidate.

Không thực thi `eval()` trên chuỗi điều kiện. Bộ đánh giá dùng toán tử được phép và semantics rõ cho missing/unknown. Kiểm tra tương đương output Python và luật đã xuất trên nhiều ca, gồm biên ngưỡng/missing/unknown category, trước khi kích hoạt.

## 11. Tài liệu nào dùng đúng chỗ?

- Han et al.: cơ sở frequent itemsets/FP-tree, không thay phương pháp xây classifier.
- Liu–Hsu–Ma: cơ sở class association rules và xây classifier; hữu ích trực tiếp cho nhánh FP.
- Solé et al.: đặt vấn đề RCA và lựa chọn mô hình theo yêu cầu hệ thống.
- Tài liệu scikit-learn: triển khai CART, chia tập và calibration.
- Tìm thấy bài năm 2025 phù hợp mô tả người dùng: **SHAP-assisted EE-LightGBM model for explainable fault diagnosis in practical optical networks**, DOI `10.1364/JOCN.527872`. Đã kiểm tra metadata/abstract, chưa đọc toàn văn. Bài này nghiên cứu mạng quang và LightGBM/SHAP; chưa xác nhận đây chính là bài thầy chỉ định, và không được chuyển số liệu hiệu năng sang lab LAN/Nginx. [Trang nhà xuất bản](https://opg.optica.org/jocn/abstract.cfm?uri=jocn-17-2-81).
- RFC ICMP/DNS giúp định nghĩa giao thức/phép đo; không chứng minh độ chính xác ML. aerOS/ITOC360 cần định danh tài liệu chính xác trước khi đưa vào thư mục tham khảo khoa học; hiện chưa dùng làm căn cứ lựa chọn ML.

## 12. Thứ tự công việc đề xuất

1. Chốt nhãn/giả thuyết và bảng điều kiện đủ bằng chứng; giữ bộ 18 lượt làm dữ liệu phát triển đã nhìn thấy.
2. Viết schema quan sát và registry thí nghiệm; kiểm tra collector thu đồng nhất ở healthy và mọi fault.
3. Thu pilot nhiều phiên trên VM trước; phân tích thiếu dữ liệu, trùng vector và khả năng phân biệt nhãn.
4. Xây CART-numeric, CART-discrete và FP-classifier có pruning/abstention theo protocol đã khóa.
5. Chọn tham số trên development, đánh giá test mới, so baseline chuyên gia trên cùng nhiệm vụ.
6. Xuất luật có version; kiểm tra tương đương và chạy chế độ quan sát trước khi dùng kết quả để ra cảnh báo.

Nghiên cứu phương pháp này không yêu cầu phải có máy thật ngay. Điều cần làm trước khi sửa thuật toán tiếp là **thiết kế lại cách thu dữ liệu và đánh giá**, vì kiểm tra hiện tại đã cho thấy giới hạn biểu diễn và shortcut do quy trình thu.

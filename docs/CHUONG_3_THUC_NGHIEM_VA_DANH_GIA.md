# Chương 3. Thực nghiệm và đánh giá

Bản kỹ thuật hoàn thiện tuần 5 từ bộ dữ liệu chính thức ngày 16–17/10/2026. Các số được tạo từ `all-trials.csv` và `experiment-summary.json`, không lấy từ dry run hoặc số unit test. Cần ghép vào mẫu báo cáo của trường trước khi nộp.

## 3.1. Mục tiêu và môi trường

Thực nghiệm đánh giá khả năng Zabbix phát hiện sáu điều kiện lỗi trong lab, khả năng luật mục tiêu của module Python khớp evidence khi fault còn tồn tại, và khả năng lưu recovery đúng liên kết event. Lab gồm MON01, SRV01 và CLI01 trên cùng laptop VirtualBox như Chương 2. Không có tập host độc lập hoặc đánh giá vận hành doanh nghiệp.

Source tham chiếu `ca04071`, export cấu hình `978b4f9`, phiếu thử `4cabeb0`. Trước đợt đo đã lưu snapshot hiệu lực, macro/template bổ sung, thông số runtime và hash source/tests. Trước mỗi trial, bộ ghi đối chiếu hash engine. Engine, trigger và sampling không được sửa giữa các lượt để khớp kết quả.

Mốc kiểm tra trước baseline có 280 tests passed. Đây là kiểm tra module, tách biệt khỏi kết quả 18 lượt fault thật. Các công cụ điều khiển fault/ghi thử không phải chức năng tự khắc phục của engine.

## 3.2. Baseline và điều kiện trước thử

Baseline mới bắt đầu 16/10/2026 16:26:08 UTC, kết thúc 16:56:14 UTC, tương ứng 23:26:08–23:56:14 UTC+7: tổng cộng 1.806 giây (30 phút 06 giây). Theo lựa chọn phiên ngắn, không gọi đây là baseline bốn giờ. Có 31 poll, 963 history rows của 28 item; đã đối chiếu lịch sử event, khoảng lấy mẫu, item errors và uptime. Không thấy problem mới trong cửa sổ quan sát đã kiểm tra.

Tần suất problem mới quan sát trong baseline là 0 / (1806/3600) = 0 sự kiện/giờ trong đúng cửa sổ ngắn này. Không có event để phân loại false alert; số 0 không ước lượng chắc chắn rủi ro dài hạn. Engine là CLI, không chạy liên tục trên tập âm nên baseline Zabbix không cung cấp tỷ lệ chẩn đoán sai của engine.

Trước mỗi fault, kiểm tra host reachable, HTTP 200, service đang chạy và không có problem nền trên host mục tiêu. Các VM báo NTP synchronized; chưa đo chính xác sai số clock giữa các VM. Trước lượt CPU tiếp theo, chờ history năm phút không còn mẫu CPU cao và không còn problem; lưu riêng bằng chứng precondition.

## 3.3. Sáu kịch bản và quy trình

| Kịch bản | Fault thực thi | Observer/đích và đối chứng | Rollback |
|---|---|---|---|
| R1 | Ngắt enp0s8 của SRV01 | MON01 → SRV01; CLI01 đối chứng cùng subnet | Timer bật lại card, có failsafe riêng |
| R2 | Dừng Nginx SRV01 | MON01 đo ping/TCP; SRV01 đo local HTTP | Start Nginx |
| R3 | Dừng Agent 2 SRV01 | MON01 đo ping, TCP10050 và agent history | Start Agent 2; chờ telemetry mới và recovery |
| R4 | Chặn UDP/TCP đích 53 tại output CLI01 | CLI01 đo example.com và ping 1.1.1.1; HTTP scope absent | Xóa đúng bảng nft riêng |
| R5 | Chặn TCP80 từ MON01 tại input SRV01 | MON01 đo remote; SRV01 đo HTTP trên IP dịch vụ | Xóa đúng bảng nft riêng |
| R6 | stress-ng, một worker CPU 100%, timeout 12 phút | History CPU/load của SRV01, một vCPU | Dừng đúng PID, xác nhận không còn worker |

R1 không mô phỏng đầy đủ mất nguồn VM; R4 không chứng minh resolver upstream hỏng; R5 dùng phương án firewall thay gateway theo phạm vi đã chốt. Vì vậy kết quả chỉ kiểm chứng những fault đã thực thi.

Mỗi lượt ghi timestamp trước/sau gây lỗi trên VM độc lập với MON01. Bộ ghi poll API khoảng năm giây, nhận đúng trigger đã chọn, chạy engine một lần, chờ recovery, đồng bộ SQLite và xuất report. Với R2/R5, HTTP JSON được thu tại SRV01 sau event; với R4, DNS và IP control được thu cùng observer CLI01 sau event. Các file phải còn fresh khi collection bắt đầu.

Có một lần R5-03 được tạo watcher nhưng lệnh gây fault bị chặn trước thực thi vì giới hạn sử dụng ở bước duyệt tự động. Hồ sơ timeout giữ nguyên, kèm adjudication `aborted_before_fault`; R5-03-retry1 là fault trial mới có mã riêng. Không tính lần bị hủy vào mẫu số detection. R2-03 có probe trước event được giữ riêng, còn diagnosis dùng probe mới sau event; engine không được chạy lại để chọn kết quả đẹp.

## 3.4. Chỉ số và cách chấm

- Detection rate = số fault hợp lệ có đúng problem / tổng fault hợp lệ.
- Target diagnosis success end-to-end = số fault hợp lệ có luật mục tiêu matched bằng evidence và hồ sơ qua kiểm tra / tổng fault hợp lệ. No detection, engine error và insufficient_evidence không bị loại khỏi mẫu số.
- Detection time nằm giữa `problem_clock − fault_after` và `problem_clock − fault_before`. Các timestamp có độ phân giải một giây; CSV bổ sung biên ±1 giây cho lượng tử hóa, chưa gồm sai số NTP chưa đo.
- CLI elapsed đo bằng monotonic clock từ khi gọi app tới khi kết thúc, gồm API, collection, luật và SQLite; không phải thời gian suy luận thuần túy.
- Recovery recognition nằm giữa `recovery_clock − rollback_after` và `recovery_clock − rollback_before`. Khoảng problem–recovery không phải downtime thật.
- Chỉ ba lượt mỗi loại: báo từng giá trị, median, min, max và cỡ mẫu; không suy ra độ tin cậy doanh nghiệp. Không có tập âm nên không tính specificity/accuracy có TN. HTTP scope absent và evidence thiếu không được tính thành healthy negative.

## 3.5. Kết quả

| Scenario | Fault hợp lệ | Detection | Target success | Abstention mục tiêu | Detection median [min–max] s | CLI median [min–max] s |
|---|---:|---:|---:|---:|---|---|
| R1 | 3 | 3/3 | 3/3 | 0 | 19.000 [15.000–32.000] | 6.660 [6.656–6.665] |
| R2 | 3 | 3/3 | 3/3 | 0 | 10.000 [5.000–23.000] | 0.610 [0.582–0.638] |
| R3 | 3 | 3/3 | 3/3 | 0 | 269.000 [183.000–295.000] | 0.583 [0.469–0.610] |
| R4 | 3 | 3/3 | 3/3 | 0 | 77.000 [69.000–83.000] | 0.766 [0.564–1.688] |
| R5 | 3 | 3/3 | 3/3 | 0 | 24.000 [16.000–34.000] | 2.590 [2.446–2.646] |
| R6 | 3 | 3/3 | 3/3 | 0 | 356.000 [316.000–391.000] | 0.502 [0.487–0.522] |

Tổng cộng detection 18/18 và target success end-to-end 18/18 trong bộ fault hợp lệ này. Số đếm này chỉ đo luật mục tiêu trên các lỗi được tạo; không phải accuracy phân loại trên lưu lượng vận hành bình thường.

![Thời gian phát hiện đã kiểm tra ngày 30](../evidence/week5/day30-20261017/detection-time.png)

![Thời gian CLI chẩn đoán](../evidence/week5/day30-20261017/diagnosis-cli-time.png)

![Kết quả luật mục tiêu](../evidence/week5/day30-20261017/diagnosis-outcomes.png)

Bảng dùng cận dưới detection theo clock; CSV giữ cả cận trên và sai số lượng tử. Vạch median chỉ mô tả ba điểm, không phải ước lượng có khoảng tin cậy. Các file SVG/PDF tương ứng dùng để đưa hình vào bản nộp.

## 3.6. Ba nhận xét dựa trên dữ liệu

1. Cơ chế trigger ảnh hưởng lớn tới detection. R3 có median 269 giây, so với R2 10 giây và R4 77 giây. R3 phải chờ availability và cửa sổ ba phút; không thể so độ trễ các nhóm như thể chúng dùng cùng chu kỳ và biểu thức.
2. Remote HTTP thất bại chưa đủ phân biệt lỗi service với lọc truy cập. R2-01 có local HTTP refused; R5-01 có local HTTP 200 trong khi bảng nft độc lập ghi rule chặn MON01. Luật phân biệt được hai tổ hợp evidence trong các lượt này, nhưng riêng output R5 vẫn chỉ là nghi ngờ filtering/đường truy cập, chưa tự đọc firewall hoặc xác định chính xác nguyên nhân.
3. Chất lượng và cửa sổ dữ liệu là một phần kết quả. R5-02 có R6 phụ insufficient_evidence vì CPU history span 239 giây thay vì tối thiểu 240 giây; không sửa luật hoặc chạy lại engine để loại kết quả này. Trong R6-01, history đạt span 241 giây, mean CPU 100%, load 1 và một vCPU nên luật mục tiêu matched. Cần phân biệt abstention do độ phủ dữ liệu với bằng chứng host khỏe.

## 3.7. Giới hạn và việc chưa được chứng minh

Lab dùng một laptop, một topology nhỏ và ba lượt lặp cho mỗi fault, không có tập kiểm tra độc lập. Lượt CPU có nghỉ giữa các fault nhưng vẫn cùng host và cấu hình; chưa đánh giá phân bố tải nền khác, jitter lớn, packet loss hỗn hợp hoặc nhiều fault đồng thời. Baseline ngắn chưa đủ phản ánh hoạt động qua đêm hoặc nhiều ngày.

R6 cho thấy CPU/load cao theo luật, chưa chứng minh tác động ứng dụng vì chưa có đối chứng response-time đầy đủ. Dữ liệu CPU count có heartbeat một ngày; tuổi mẫu lớn không tự là mất giám sát nếu phù hợp preprocessing. Các luật ngoài mục tiêu có insufficient_evidence được giữ trong JSON; không đếm thành true negative.

Mean CPU của luật là trung bình số học các mẫu, chưa dùng trọng số theo khoảng thời gian. Trigger CPU còn có dependency với load-high; bộ thử một worker chưa bao phủ trường hợp load-high trở thành problem và ảnh hưởng event CPU. Không suy rộng ba lượt này thành phát hiện mọi tình huống quá tải hoặc mọi tổ hợp trigger.

Dữ liệu thô và event API thay cho việc chép tay số từ dashboard. Hồ sơ đóng tuần 4 đã bổ sung ảnh dashboard, ba host, lịch sử và 18 ảnh chi tiết event tại `evidence/week4/closure-20261017/screenshots/`. Đây là ảnh lịch sử chụp sau đo, không phải ảnh active fault; xem `docs/TONG_HOP_TUAN_4.markdown` và closure audit. Tuần5 đã ghi ba lượt diễn tập kỹ thuật sau reboot và có bộ release/backup địa phương riêng; xem biên bản tuần5. Chưa chứng nhận năng lực thuyết trình của sinh viên hoặc backup ngoài laptop.

## 3.8. Truy vết từng lượt

| Run ID | Problem → Recovery | Incident | Luật mục tiêu | Hồ sơ |
|---|---|---:|---|---|
| R1-01 | 933 → 934 | 19 | matched | [raw](../evidence/week4/official-runs/R1-01/run.json) |
| R1-02 | 935 → 936 | 20 | matched | [raw](../evidence/week4/official-runs/R1-02/run.json) |
| R1-03 | 937 → 938 | 21 | matched | [raw](../evidence/week4/official-runs/R1-03/run.json) |
| R2-01 | 939 → 940 | 22 | matched | [raw](../evidence/week4/official-runs/R2-01/run.json) |
| R2-02 | 941 → 942 | 23 | matched | [raw](../evidence/week4/official-runs/R2-02/run.json) |
| R2-03 | 943 → 944 | 24 | matched | [raw](../evidence/week4/official-runs/R2-03/run.json) |
| R3-01 | 945 → 950 | 25 | matched | [raw](../evidence/week4/official-runs/R3-01/run.json) |
| R3-02 | 951 → 956 | 26 | matched | [raw](../evidence/week4/official-runs/R3-02/run.json) |
| R3-03 | 957 → 962 | 27 | matched | [raw](../evidence/week4/official-runs/R3-03/run.json) |
| R4-01 | 963 → 964 | 28 | matched | [raw](../evidence/week4/official-runs/R4-01/run.json) |
| R4-02 | 965 → 966 | 29 | matched | [raw](../evidence/week4/official-runs/R4-02/run.json) |
| R4-03 | 967 → 968 | 30 | matched | [raw](../evidence/week4/official-runs/R4-03/run.json) |
| R5-01 | 969 → 970 | 31 | matched | [raw](../evidence/week4/official-runs/R5-01/run.json) |
| R5-02 | 971 → 972 | 32 | matched | [raw](../evidence/week4/official-runs/R5-02/run.json) |
| R5-03-retry1 | 973 → 974 | 33 | matched | [raw](../evidence/week4/official-runs/R5-03-retry1/run.json) |
| R6-01 | 975 → 976 | 34 | matched | [raw](../evidence/week4/official-runs/R6-01/run.json) |
| R6-02 | 977 → 978 | 35 | matched | [raw](../evidence/week4/official-runs/R6-02/run.json) |
| R6-03 | 979 → 980 | 36 | matched | [raw](../evidence/week4/official-runs/R6-03/run.json) |

[CSV toàn bộ lượt](../evidence/week4/official-runs/all-trials.csv) · [JSON công thức, cỡ mẫu và thống kê](../evidence/week4/official-runs/experiment-summary.json) · [Phụ lục vận hành](../evidence/week4/official-runs/PHU_LUC_VAN_HANH_THUC_NGHIEM.md)

## 3.9. Nghiệm thu bảng và biểu đồ ngày 30

Bộ hình trong mục 3.5 được tái tạo từ dữ liệu đã nghiệm thu ngày 29; 90 số min/median/max khớp dữ liệu nguồn. Mỗi hình có bản PNG, SVG và PDF để đưa vào báo cáo. [Phân tích ngày 30](NGAY_30_TUAN_5.markdown) cung cấp bảng hai cận DT, kết quả mục tiêu, từng điểm trên hình và bốn phát hiện có liên kết hồ sơ gốc.

- R6 có DT median 356 s, R3 269 s, R2 10 s. Sự khác biệt phù hợp với điều kiện trigger khác nhau; chưa cô lập nguyên nhân bằng thực nghiệm đối chứng.
- R6 có CLI median thấp nhất (0,502 s), R1 cao nhất (6,660 s), dù R6 phát hiện chậm hơn. Detection và CLI là hai giai đoạn, không thể thay thế nhau.
- Sáu nhóm đều khớp mục tiêu 3/3; không có mẫu âm để tính accuracy tổng quát. Lượt hủy trước fault không vào mẫu số.
- 24/108 đầu ra luật thiếu evidence vẫn được giữ; không gán thành true negative hoặc lỗi luật mục tiêu.

[Dữ liệu điểm vẽ](../evidence/week5/day30-20261017/plotted-points.csv) · [Bảng thống kê](../evidence/week5/day30-20261017/timing-summary.csv) · [Kết quả chẩn đoán](../evidence/week5/day30-20261017/diagnosis-outcomes.csv) · [Kiểm tra tái tạo](../evidence/week5/day30-20261017/analysis-validation.json).

Hoàn thành đầu ra ngày 30; Chương 3 tiếp tục được rà soát đầy đủ vào ngày 32. Không thay đổi engine hoặc bằng chứng tuần 4.

## 3.10. Cảnh báo sai, tiêu chí chấm và khả năng tái lập

Đơn vị thử là một fault chủ động tạo có Run ID, log trước/sau và kiểm tra precondition; không phải từng dòng history, từng diagnosis hay từng event ngẫu nhiên. 19 attempt gồm18 fault hợp lệ và1 hủy trước fault. Sáu nhóm mỗi nhóm3, không có bộ âm độc lập. Không loại một fault hợp lệ chỉ vì engine lỗi/thiếu dữ liệu/không phát hiện; trong bộ đã thu các trường hợp mục tiêu đó đều bằng0.

Chấm mục tiêu theo điều kiện luật và ground truth của fault. R1 ngắt Host-only, R2 dừng Nginx, R3 dừng Agent, R4 chặn DNS tại CLI01, R5 lọc TCP80 từ MON01, R6 stress CPU. Các tên nguyên nhân là giả thuyết giới hạn đúng bằng chứng; không gán nhãn resolver upstream hỏng, VM mất nguồn hoặc gateway hỏng cho những fault khác.

**Cảnh báo sai:** baseline có0 problem mới trong1806s, tương đương0 sự kiện/giờ chỉ trong cửa sổ quan sát. Chưa có event nền để phân loại false alert, chưa thử tập âm engine, không có mẫu số TN/FP để tính FPR hoặc specificity. Chẩn đoán matched ngoài mục tiêu trong18 run bằng0, nhưng điều đó không thay tập âm độc lập. 24 insufficient_evidence ở108 đầu ra giữ nguyên; HTTP absent cũng không tính TN. Các problem reboot ngoài cửa sổ tuần4 được phân loại riêng trong hồ sơ diễn tập tuần5, không gộp để thay kết quả baseline.

Mỗi lượt engine chỉ chạy/lưu một lần; event hồi phục khi đang collection làm kiểm tra cuối từ chối là hành vi bảo vệ, không lý do sửa dữ liệu. Với R2/R5, probe HTTP tạo mới sau problem; với R4, DNS/IPcontrol cùng observer. Probe cũ R2-03 được giữ riêng; R5-03 hủy và retry có ID riêng. Không impute, cắt outlier hoặc đổi timestamp để rút ngắn thời gian.

Nguồn tái lập: [clean runs](../evidence/week5/day29-20261017/clean-runs.csv), [attempt register](../evidence/week5/day29-20261017/attempts.csv), [công thức và audit](../evidence/week5/day29-20261017/audit.json), [mã tạo bảng/hình](../evidence/week5/day30-20261017/tools/day30_analysis.py). Manifest giữ byte của nguồn. Bảng/hình có min/median/max, cỡ mẫu và cận thời gian; không cung cấp kiểm định hoặc confidence interval suy rộng từ n=3.

Các lượt demo sau reboot là tập diễn tập riêng trong `evidence/week5/final-20261017`, không nâng cỡ mẫu18 của thực nghiệm đóng băng. Test cuối kiểm tra phần mềm; không thay baseline hoặc fault trial. Môi trường thực tế và cấu hình đã được đối chiếu lại ở [Chương2](CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md).

# Tiến độ triển khai ML v2 — 30/10/2026

## Đang thu block test thứ hai — 31/10/2026 19:59 UTC+7

- Người dùng đã yêu cầu tiếp tục sau checkpoint tạm dừng, xác nhận màn hình sáng và cắm sạc. **Đang chạy, chưa nghiệm thu xong**.
- M4:42 pilot valid/9 uncertain. M5 hiện có **21/42 test valid**, 1 uncertain; block thứ nhất đã đủ21. Giữ nguyên lượt gián đoạn và dùng retry ID mới; chưa mở dự đoán hoặc điểm test.
- Session foreground74874, coordinator7124, child13872. Khóa lab và source/model/config trước test vẫn giữ nguyên. Không chạy thêm coordinator hoặc sửa5 helper quan trọng trong lúc thu.
- Windows đã vào Modern Standby trong lần tiếp tục đầu; power event lưu ở workspace `verification/resume-power-events-20261031.json`. Preflight phục hồi `evidence/ml-v2/verification/recovered-platform-20261031T121304081495Z` đã đạt; package khớp bản khóa. Không đổi power plan, affinity/CPU/RAM VM hoặc source baseline.
- Có wake guard riêng session61318, giới hạn3giờ, để giữ liên tục tới QA/demo/backup. Phải kết thúc guard khi hoàn tất hoặc người dùng yêu cầu dừng; worker cũng có guard riêng.
- Phần còn lại: thu đủ42 test valid → mở điểm/đối chiếu SQLite+shadow → kiểm tra24 hàng đối chứng theo run ID → xem3 hình → demoNginx thật → finalizer+backup khôi phục C/D. Chưa có release cuối; không có luật active.
- Chỉ dùng kết quả cho lab baVM/lỗi đơn đã biết. Chưa có PC thật, multi-fault hoặc topology/suppression. Phân tích che feature pilot đã ghi nhận CART có thể nhầm lỗi nguồn đo; không sửa mô hình theo test để che hạn chế này.
- Các mục tạm dừng/cột mốc phía dưới là lịch sử; xem trạng thái worker hiện tại ở workspace trước khi thao tác.

## Tạm dừng theo yêu cầu người dùng — 2026-10-31T09:17:48.984776+00:00

- **PAUSED_BY_USER. Không tự chạy tiếp** cho tới khi người dùng yêu cầu tiếp tục.
- M4 đã hoàn tất: 42 pilot valid, 9 uncertain; benchmark `20261031T082356416394Z`.
- M5: **11/42 test valid**, 1 uncertain. Lượt CPU đang chờ baseline khi dừng được giữ nguyên và audit uncertain; không tái tạo timeline thiếu, không chấm điểm test.
- Hai coordinator12676/1784 đã dừng và khóa lab được lấy thành công để cleanup. Postflight: baseline/service/network tốt, không còn timer/firewall/stress của thí nghiệm; source engine và SQLite39/301/172/29 được giữ nguyên. Bằng chứng `C:\Users\Darrys\do-an\evidence\ml-v2\verification\paused-by-user-20261031T091748980745Z`.
- Mô hình/config và 5 helper quan trọng vẫn khóa; KHÔNG sửa để chạy tiếp. Khi được phép resume, xác minh package fingerprint ba VM khớp `locked-test-v1/lab-environment-freeze.json`; nếu đã đổi package thì dừng xem lại protocol, không bỏ gate hoặc âm thầm gộp test.
- Chưa mở dự đoán/điểm test. Chưa làm final QA, xem hình, public demo hoặc final release. `checkpoint_active_test.py` giữ raw/source/context C/D; bản chốt pause xem `paused-ml-latest.json` trong workspace.

## Điều phối đang chạy — 31/10/2026 15:23 UTC+7

PID coordinator hiện hành: 12676; phase: `running_pilot_foreground`. Đếm trực tiếp RESULT: **41/42 valid**, 9 uncertain; đây không phải accuracy. Không mở coordinator/fault thứ hai.

Windows có Event 506 vào Modern Standby lúc 13:48:37 ngày 31/10, trùng giai đoạn mất SSH trên cả ba VM; người dùng xác nhận màn hình đã tắt/khóa và đánh thức máy. Event 507 ghi thoát lúc 14:01:48 (SC_MONITORPOWER) và 14:01:51 (Input Keyboard). Sau đó SSH phản hồi lại. Giữ kết luận giới hạn cho đợt này, không quy mọi RCU stall lịch sử về cùng nguyên nhân.

Lượt Agent retry1 đã chốt uncertain do UnexpectedPlatformFault; retry2 đã valid. Model/feature/nhãn/gate giữ nguyên. Đã bổ sung yêu cầu giữ display+system thức tạm thời, tái áp dụng mỗi 10/15 giây; tự clear khi worker kết thúc. Không đổi power plan, lock policy, affinity/priority hay CPU/RAM VM. Ba tests helper wake/renew/cleanup đạt; source và power-event evidence ở `evidence/ml-v2/verification/modern-standby-20261031T070608479433Z`.

Coordinator hiện hành được khởi động lại sau checkpoint `79dc603`, đã nạp guard display/system renew 15 giây và platform schema 2 (kernel + package jobs/locks/audit/hash). Các helper display tạm cũ đã kết thúc; guard của coordinator mới duy trì wake request. Không sửa snapshot startup lịch sử. Không dùng workspace stage `ml-v2` cũ ghi đè repository.

Đã xử lý riêng deadlock auto-upgrade MySQL/Zabbix bằng backup nguội và one-off service rescue; không kill apt/dpkg hoặc tắt cập nhật. Gate mới đã preflight đạt; 57 tests ML, 3 tests pin package environment và 3 tests wake guard đã đạt. M5 sẽ pin package fingerprint toàn bộ ba VM trước test; đổi package thì dừng trước khi mở điểm. Code feature, nhãn và siêu tham số giữ nguyên.

Tiếp theo: đủ 42 valid → postflight/tests → train/SQLite pilot → khóa trước 42 test mới/shadow → evaluate/report/QA/release/demo. `review_ml_release.py` chỉ mở kết quả sau phase COMPLETE_INITIAL_VM_ML; `Run-ML-Demo.ps1` giữ khóa lab và chỉ dùng release đã QA. Các phần này chưa được coi là hoàn tất chỉ vì đã có code.

## Sau phục hồi package/DB — 31/10/2026 15:07 UTC+7

Coordinator PID 15692 đã dừng vì hết deadline baseline; hiện có **38/42 valid**, 8 uncertain đã chốt và một CPU run chưa chốt. Lượt CPU này sẽ audit uncertain, rồi retry bằng ID mới; không đưa dữ liệu chưa chốt vào train.

Đã xác minh auto-upgrade trên MON01 làm restart MySQL/Zabbix kẹt thứ tự: MySQL start chờ Zabbix stop, Zabbix stop chờ database (TimeoutStopUSec=infinity). Backup nguội MySQL/config 639817729 bytes đã kiểm CRC/hash, lưu riêng trên VM với quyền hạn chế; không xuất nội dung credential. Một lần rescue `systemctl start mysql --job-mode=ignore-dependencies --no-block` khôi phục MySQL/Zabbix và giải phóng chuỗi restart. Không kill apt/dpkg, không tắt cập nhật bảo mật hoặc sửa unit/power policy. Xem `evidence/ml-v2/verification/mysql-ordering-recovery-*` và `evidence/ml-v2/verification/package-recovery-acceptance-20261031T080700853123Z`.

Preflight mới đạt `evidence/ml-v2/verification/recovered-platform-20261031T080427843278Z`; engine source/SQLite runtime không đổi (39/301/172/29). Gate platform schema 2 bổ sung apt jobs, dpkg locks/audit và SHA trạng thái package trước/sau trial. Source/model feature/nhãn/siêu tham số phân loại giữ nguyên. **57 tests ML và 3 tests pin môi trường heldout đạt**; thêm tests guard wake/cleanup đã đạt ở mốc trước.

Trước test mới, worker sẽ lưu `lab-environment-freeze.json`; mọi trial test phải khớp package fingerprint này và kiểm tra lại khi thu xong. Có thay đổi package thì dừng trước khi mở điểm test. Đây là bổ sung protocol trước M5 vì lỗi hạ tầng thực tế, không phải điều chỉnh theo điểm mô hình. Chưa train v2/chưa thu test mới.

Tiếp theo chạy lại `full_ml_session.py` foreground, nhập SSH bằng getpass. Guard mới giữ display/system thức và renew mỗi 15 giây. Giữ các snapshot/protocol cũ là lịch sử; không chép workspace stage cũ đè lên repository.

## Điều phối đang chạy — 31/10/2026 14:15 UTC+7

PID coordinator hiện hành: 15692; phase: `running_pilot_foreground`. Đếm trực tiếp RESULT: **33/42 valid**, 8 uncertain; đây không phải accuracy. Không mở coordinator/fault thứ hai.

Windows có Event 506 vào Modern Standby lúc 13:48:37 ngày 31/10, trùng giai đoạn mất SSH trên cả ba VM; người dùng xác nhận màn hình đã tắt/khóa và đánh thức máy. Event 507 ghi thoát lúc 14:01:48 (SC_MONITORPOWER) và 14:01:51 (Input Keyboard). Sau đó SSH phản hồi lại. Giữ kết luận giới hạn cho đợt này, không quy mọi RCU stall lịch sử về cùng nguyên nhân.

Lượt Agent retry1 đã chốt uncertain do UnexpectedPlatformFault; retry2 đã valid. Model/feature/nhãn/gate giữ nguyên. Đã bổ sung yêu cầu giữ display+system thức tạm thời, tái áp dụng mỗi 10/15 giây; tự clear khi worker kết thúc. Không đổi power plan, lock policy, affinity/priority hay CPU/RAM VM. Ba tests helper wake/renew/cleanup đạt; source và power-event evidence ở `evidence/ml-v2/verification/modern-standby-20261031T070608479433Z`.

WORK `lab_host_guard.py` mới sẽ được dùng trong interpreter test mới; coordinator M4 đang chạy đã nạp bản cũ nên được bổ sung bằng tiến trình `display_guard_diagnostic.py` định kỳ. Các snapshot startup cũ được giữ đúng bản đã chạy; không sửa retrospective. Không dừng helper wake khi lab còn đang thu. Các thư mục workspace stage `ml-v2` đã cũ, không dùng ghi đè repository.

Tiếp theo: đủ 42 valid → postflight/tests → train/SQLite pilot → khóa trước 42 test mới/shadow → evaluate/report/QA/release/demo. `review_ml_release.py` chỉ mở kết quả sau phase COMPLETE_INITIAL_VM_ML; `Run-ML-Demo.ps1` giữ khóa lab và chỉ dùng release đã QA. Các phần này chưa được coi là hoàn tất chỉ vì đã có code.

## Tiếp tục theo yêu cầu người dùng — 31/10/2026 13:42 UTC+7

Người dùng đã yêu cầu tiếp tục; trạng thái PAUSED_BY_USER trong ghi chú bên dưới là lịch sử. Ba VM đang chạy; không có coordinator cũ chạy song song. Backup C/D tại mốc tạm dừng đã đối chiếu SHA-256 trùng nhau.

- Preflight mới đạt: `evidence/ml-v2/verification/recovered-platform-20261031T063429354666Z`. Có backup source/runtime mới trên ba VM, SQLite integrity/foreign keys tốt và số hàng engine vẫn 39/301/172/29. Cảnh báo uptime <10m sau boot đã tự phục hồi; không đóng cưỡng bức event.
- Pilot đang có 29/42 valid trong 35 attempt đã chốt. Lượt `pilot-v2-s02/r02-02-agent_stopped` cần audit uncertain rồi retry; chưa fit v2, chưa thu held-out.
- Source Python ML khớp SHA với lần 54 tests đạt; không đổi feature/nhãn/tham số để chạy nhanh. Các lượt pilot cũ chưa có đầy đủ gate kernel, vẫn phải giữ caveat phương pháp. Test mới sẽ khóa trước khi thu và giữ nguyên chính sách validity.
- Tiếp theo chạy `full_ml_session.py` foreground trong workspace: backup, audit lượt dở, thu hết pilot, train, 42 test mới, shadow/SQLite/evaluation/report. Trạng thái live ở `verification/full-ml-status.json`, `ml-supervisor-status.json`, `ml-acceptance-status.json`; các PID trong ghi chú cũ đã hết hiệu lực.
- Phạm vi chỉ ba VM theo xác nhận người dùng; chưa có PC Ubuntu thật. Không tuyên bố nghiệm thu máy thật, multi-fault hoặc topology/suppression từ kết quả này.

- M0: backup local đã phục hồi kiểm tra; sau đó backup runtime/source trên ba VM trước thử nghiệm. MON01 có SQLite backup nhất quán và bản .env lưu tại VM với quyền hạn chế; không đưa secret vào Git.
- M1: đã có data dictionary, label map, protocol và split policy trong docs/ và config/.
- M2: đã có registry append-only, observation validator và collector độc lập nhãn. 8 tests mới đạt; baseline engine 369 tests đạt.
- M2 live: SRV01 thu 13 evidence; CLI01 thu 12 evidence, HTTP not_applicable theo profile. Không có source error.
- M3: bắt đầu một lượt pilot dừng Nginx trên SRV01, thu hai cửa sổ cùng Run ID, xác minh dịch vụ inactive, Zabbix event 1144, rồi bật lại Nginx và kiểm tra HTTP200. Có timer failsafe và log độc lập.
- Hai snapshot trong fault là một lượt, không phải hai sự cố độc lập. Các smoke observations có planned healthy nhưng vẫn pending review; không được tính vào tập healthy valid.
- Background CLI01 có event 1143 về OS description thay đổi; ghi nhận riêng, không tự đóng hoặc đổi cấu hình Zabbix.
- Chưa hoàn tất pilot 42 lượt/nhiều phiên. Chưa có tập test độc lập, chưa huấn luyện mô hình v2 hoặc kích hoạt luật ML.

Việc tiếp theo: hoàn thiện run scheduler/fault scripts cho R1/R3/R4/R5/R6 với rollback, thu pilot theo protocol, dựng quality report và kiểm tra shortcut trước khi train. Healthy cần review độc lập; điều chỉnh các profile để không để một lớp chỉ thuộc một host.

Evidence thật nằm trong `evidence/ml-v2` ở root repository. Phiên bản engine baseline được giữ nguyên; M1/M2 được thêm như module riêng trên nhánh feature/ml-research-v2.

Postflight đã xác minh event 1144 có recovery 1145; SRV01 không còn problem mở, Nginx active và HTTP200. Source engine trên MON01 và số hàng SQLite runtime không đổi.

## M3 — kết quả đợt pilot đầu

Đã chạy 10 attempt trong pilot-v2-s01; 7 attempt hợp lệ, 3 attempt uncertain được giữ nguyên. Có đủ bảy trạng thái (healthy + sáu fault) ở SRV01. Retry có ID và parent riêng, không ghi đè lượt cũ. Có 24 cửa sổ đo toàn bộ, không được coi là từng ấy sự cố độc lập.

Đã thêm scheduler 42 lượt có resume, fault/rollback scripts, source execution snapshots, quality report và CSV pilot. CSV dùng cửa sổ cuối mỗi valid run, feature whitelist tách metadata. Chưa train v2; chưa có phiên test độc lập.

Bộ kiểm thử ML hiện có 22 tests đạt, gồm lỗi timer đã hết, cửa sổ sau deadline failsafe, lệch clock giữa máy, provenance và ghi JSON không để lại file dở. Baseline 369 tests đã chạy đạt ở mốc trước; source engine không đổi.

Lỗi điều phối đã phát hiện: cleanup timer đã bị systemd thu hồi; timestamp giây nguyên khác máy làm ranh giới rollback chưa chắc chắn. Đã giữ log lỗi, bổ sung timer LoadState và coordinator monotonic timeline; chạy retry riêng. Phiên đầu chưa có source manifest lúc khởi chạy được ghi là pilot debug, không dùng làm test cuối.

Postflight: Nginx/Agent active, HTTP200, DNS/control tốt, interface enp0s8 UP; không còn firewall table/timer mlv2. Engine source và 39 incidents runtime không đổi; SQLite integrity ok.

Tiếp theo: hoàn tất các lượt/phiên còn lại theo lịch và audit; chưa đủ cơ sở tính accuracy/FPR tổng quát. Tổng hợp chi tiết tại evidence/ml-v2/quality/QUALITY.md.

## Cập nhật ML ngày 30/10/2026, khoảng 17:15 UTC+7

Đây là trạng thái đang chạy, không phải xác nhận đã hoàn tất ML. Nhánh local `feature/ml-research-v2`; checkpoint trước tiếp tục `89c9848`. Engine baseline không sửa. Ba VM đang dùng cho pilot, không coi ghi chú shutdown ngày 17/10 bên dưới là hiện trạng live.

- Đã backup trước tiếp tục ở C:/D:, bundle/ZIP phục hồi được; có backup runtime nhất quán trên MON01. Backup bổ sung dữ liệu dở dang: `before-pilot-resume-20261030T095935920203Z`, hash archive `fa448bbb93751f9c694d8e8ef579e545d79364fae9abac0bca560c107e91764e`.
- Pilot mới: 14 valid, 4 uncertain tại mốc kiểm tra; lượt CPU tiếp theo đang chạy. Lượt bị ngắt được audit và retry riêng, không sửa thành valid. Chỉ dùng dữ liệu trong `evidence/ml-v2`, không chép đè từ workspace stage cũ.
- M4 đã có CART numeric/discrete, FP-classifier, ablations, grouped validation, export candidate SQLite và wrapper demo shadow. **32 tests đạt**, replay expert trên 7 quan sát thật tạo 42 assessment; chưa fit ML vì lịch thu chưa đủ.
- Hai tiến trình tại mốc này: coordinator PID 5468, supervisor PID 18004. Supervisor chờ coordinator kết thúc trước khi tiếp quản; không chạy hai bộ gây lỗi đồng thời. PID có thể đổi/kết thúc; phải kiểm tra trạng thái thật.
- Trạng thái cập nhật: `C:\Users\Darrys\Documents\ChatGPT\Đồ án network\verification\ml-supervisor-status.json`; log cùng thư mục `ml-supervisor.log`. Mật khẩu chỉ nằm trong RAM, không nằm trong file/config.
- Supervisor dự kiến hoàn tất các attempt hợp lệ cho 42 lượt, postflight, tests, export, benchmark pilot, replay và demo healthy shadow rồi backup. Chỉ coi xong khi phase=`COMPLETE_PILOT_M4`, có báo cáo thật, postflight đạt và `ml-research/AUTORUN_RESULT.md`. Nếu phase=`STOPPED_REQUIRES_REVIEW`, đọc lỗi/log; không mở thêm coordinator khi tiến trình cũ còn chạy.
- Kết quả M4 là pilot nội bộ; M5 test mới khóa riêng chưa thu, không công bố accuracy tổng quát hoặc khả năng chuyển sang PC thật. SQLite chỉ candidate, không tự active. M6/M7 mới có prototype/export và wrapper riêng, chưa thay engine vận hành.

Hướng dẫn: `ml-research/docs/HUONG_DAN_M4.md`. Chi tiết phương pháp/kế hoạch nằm cùng thư mục docs. Các thông tin nền dưới đây được giữ như bản bàn giao lịch sử.

## Cập nhật điều phối 30/10/2026 17:28 UTC+7

Worker cũ đã dừng do SSHException; sau kiểm tra thật, dịch vụ/HTTP/DNS đã tốt, không còn stress/timer nhưng Zabbix còn cảnh báo load average. Không đóng cưỡng bức event. Đã sửa retry chỉ cho lỗi kết nối tạm thời trong kiểm tra baseline, giữ deadline; lỗi xác thực/host key vẫn dừng ngay. Client kết nối lỗi được đóng. Gate baseline giữ nguyên tiêu chí, thời gian chờ tối đa tăng từ 8 lên 20 phút để cảnh báo/load tự phục hồi; collector, feature và thời lượng fault không đổi.

36 tests đạt, có evidence tại `evidence/ml-v2/verification/m4-code-20261030T102759686247Z`. CPU attempt bị gián đoạn được giữ uncertain. Tại mốc ghi: 19 attempt đã chốt, 14 valid; không phải accuracy. Baseline đã đạt trước khi worker mới PID 17188 mở CPU retry lúc khoảng 17:26. Tiến trình cũ PID 5468/18004 đã kết thúc, không còn là PID hiện hành.

Worker tiếp tục chạy nền theo lịch đã duyệt. Xem `verification/ml-supervisor.log` trong workspace để biết lượt/gate hiện hành; `ml-supervisor-status.json` ghi phase và số đếm tại lúc đổi phase, không phải bộ đếm realtime. Chưa fit mô hình v2. Đọc `AUTORUN_RESULT.md` và báo cáo benchmark chỉ sau khi worker báo hoàn tất.

## Bổ sung nghiệm thu ML 30/10/2026 18:02 UTC+7

Người dùng yêu cầu tiếp tục tới khi hoàn chỉnh phần ML. Đã thêm `locked_test_v2.py`, `registry_v2.py`, protocol `docs/NGHIEM_THU_VM_V1.md`: train từ pilot, thêm 42 test run mới (hai block x ba lượt x bảy trạng thái), khóa source/config/nhãn trước test, embargo history 600 giây, chỉ mở điểm sau khi thu xong. Đây là ngân sách nghiệm thu ban đầu thay cho đề xuất 210 lượt chưa chốt; không suy ra chất lượng production hoặc chuyển PC.

43 tests ML và 369 tests baseline vừa chạy đạt; evidence `evidence/ml-v2/verification/acceptance-code-20261030T105732091265Z`. Engine source không đổi. Test code có fixture tổng hợp để kiểm tra toàn luồng; không đưa fixture vào dữ liệu thực nghiệm.

Worker pilot PID 17188 vẫn chạy. Worker nghiệm thu PID 24132 đang chờ PID 17188 kết thúc thành công; không chạy fault song song. Worker mới sẽ backup VM/local, khóa train, thu test với shadow trực tiếp trong fault, kiểm tra model/SQLite/live tương đương, đánh giá và lưu registry/reports/backup. Chưa coi các bước tương lai này là đã hoàn tất.

Đọc `verification/ml-acceptance-status.json` và `ml-acceptance.log` trong workspace để theo dõi. Trong lúc worker 24132 chờ, không sửa các helper `ml_acceptance.py`, `resume_ml_pilot.py`, `ml_supervisor.py`, `ml_vm_preflight.py`: worker kiểm tra hash và sẽ dừng nếu helper đổi. Không sửa source pipeline/collector sau khi `locked-test-v1/development-freeze.json` được tạo, nếu còn muốn giữ test đó là test khóa riêng.

Kết quả nghiệm thu chỉ có khi phase=`COMPLETE_INITIAL_VM_ML_ACCEPTANCE`, có `ACCEPTANCE_RESULT.md`, báo cáo evaluation thật và postflight. Luật vẫn candidate/validated cho nghiên cứu shadow, không active. Máy thật/multi-fault/topology/suppression thuộc M8, chưa được chứng minh bằng đợt này.

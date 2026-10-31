# Hiện trạng và cách tiếp tục đồ án

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

## Tạm dừng theo yêu cầu người dùng — 30/10/2026 20:52 UTC+7

**PAUSED_BY_USER. Không tự tiếp tục và không tự chạy fault.** Người dùng yêu cầu tạm dừng vì hết token và backup trước khi kết thúc. Các PID/worker trong ghi chú cũ bên dưới đã hết hiệu lực.

- Dữ liệu hiện có: 29/42 lượt pilot hợp lệ; 6 uncertain đã chốt; một lượt Agent đăng ký nhưng chưa chốt, phải audit uncertain rồi retry bằng ID mới. Chưa huấn luyện chính thức v2; chưa thu 42 lượt held-out. Không có accuracy thật để công bố.
- 54/54 tests ML đạt, thêm 3/3 tests helper phục hồi đạt. Bộ baseline 369 tests đã đạt ở mốc trước, source engine không sửa. Bằng chứng mới: `evidence/ml-v2/verification/paused-by-user-20261030T135222185697Z`.
- Người dùng xác nhận chỉ có ba VM, chưa có máy Ubuntu thật; đã cắm sạc và giữ host mở. Phạm vi nghiệm thu tiếp theo là cùng host VM, không gọi là nghiệm thu máy thật.
- Đã tạo snapshot cả ba VM: `ml-pre-graceful-recovery-20261030T133856583807Z`. Cả ba đã tắt qua ACPI; lúc dừng coordinator phục hồi MON01 đã nhận lệnh khởi động lại. Trạng thái xác minh: {"MON01": {"state": "running", "snapshot": "ml-pre-graceful-recovery-20261030T133856583807Z"}, "SRV01": {"state": "poweroff", "snapshot": "ml-pre-graceful-recovery-20261030T133856583807Z"}, "CLI01": {"state": "poweroff", "snapshot": "ml-pre-graceful-recovery-20261030T133856583807Z"}}. Không reset/poweroff cưỡng bức; không đổi CPU/RAM, affinity, priority hay bảo mật host.
- Lab có RCU stall/soft lockup và SSH timeout; chưa kết luận nguyên nhân. Các lượt bị tác động không được sửa thành valid. Đã tách timeout điều khiển và probe, thêm gate kernel/boot ID, retry điều khiển có giới hạn, chặn valid nếu thiếu một trong hai observation. Các mẫu pilot cũ chưa có đầy đủ gate kernel, phải giữ caveat trong báo cáo.
- Khi được yêu cầu tiếp tục: kiểm tra tiến trình/locks thật; khởi động SRV01 và CLI01 nếu còn poweroff; chờ MON01 boot xong; chạy `preflight_recovered_lab.py` trong workspace để backup/source/SQLite/services/kernel. Đọc `resume_ml_pilot.py` mới (audit append-only, retry bảo toàn credential), rồi chạy `full_ml_session.py` foreground. Không chạy launcher detached cũ, không chạy fault song song. Mật khẩu qua getpass, không ghi file/chat.
- Nguồn đúng: `C:/Users/Darrys/do-an/ml-research` và `evidence/ml-v2`. Stage `WORK/ml-v2` đã cũ, không đồng bộ chép đè. M5 chỉ được thu sau M4 đủ 42 valid; đóng băng trước test, không đổi model theo điểm test. Demo công khai cần ML_RELEASE.json đã QA, hiện chưa có.

## Bổ sung nghiệm thu ML 30/10/2026 18:02 UTC+7

Người dùng yêu cầu tiếp tục tới khi hoàn chỉnh phần ML. Đã thêm `locked_test_v2.py`, `registry_v2.py`, protocol `docs/NGHIEM_THU_VM_V1.md`: train từ pilot, thêm 42 test run mới (hai block x ba lượt x bảy trạng thái), khóa source/config/nhãn trước test, embargo history 600 giây, chỉ mở điểm sau khi thu xong. Đây là ngân sách nghiệm thu ban đầu thay cho đề xuất 210 lượt chưa chốt; không suy ra chất lượng production hoặc chuyển PC.

43 tests ML và 369 tests baseline vừa chạy đạt; evidence `evidence/ml-v2/verification/acceptance-code-20261030T105732091265Z`. Engine source không đổi. Test code có fixture tổng hợp để kiểm tra toàn luồng; không đưa fixture vào dữ liệu thực nghiệm.

Worker pilot PID 17188 vẫn chạy. Worker nghiệm thu PID 24132 đang chờ PID 17188 kết thúc thành công; không chạy fault song song. Worker mới sẽ backup VM/local, khóa train, thu test với shadow trực tiếp trong fault, kiểm tra model/SQLite/live tương đương, đánh giá và lưu registry/reports/backup. Chưa coi các bước tương lai này là đã hoàn tất.

Đọc `verification/ml-acceptance-status.json` và `ml-acceptance.log` trong workspace để theo dõi. Trong lúc worker 24132 chờ, không sửa các helper `ml_acceptance.py`, `resume_ml_pilot.py`, `ml_supervisor.py`, `ml_vm_preflight.py`: worker kiểm tra hash và sẽ dừng nếu helper đổi. Không sửa source pipeline/collector sau khi `locked-test-v1/development-freeze.json` được tạo, nếu còn muốn giữ test đó là test khóa riêng.

Kết quả nghiệm thu chỉ có khi phase=`COMPLETE_INITIAL_VM_ML_ACCEPTANCE`, có `ACCEPTANCE_RESULT.md`, báo cáo evaluation thật và postflight. Luật vẫn candidate/validated cho nghiên cứu shadow, không active. Máy thật/multi-fault/topology/suppression thuộc M8, chưa được chứng minh bằng đợt này.


## Cập nhật điều phối 30/10/2026 17:28 UTC+7

Worker cũ đã dừng do SSHException; sau kiểm tra thật, dịch vụ/HTTP/DNS đã tốt, không còn stress/timer nhưng Zabbix còn cảnh báo load average. Không đóng cưỡng bức event. Đã sửa retry chỉ cho lỗi kết nối tạm thời trong kiểm tra baseline, giữ deadline; lỗi xác thực/host key vẫn dừng ngay. Client kết nối lỗi được đóng. Gate baseline giữ nguyên tiêu chí, thời gian chờ tối đa tăng từ 8 lên 20 phút để cảnh báo/load tự phục hồi; collector, feature và thời lượng fault không đổi.

36 tests đạt, có evidence tại `evidence/ml-v2/verification/m4-code-20261030T102759686247Z`. CPU attempt bị gián đoạn được giữ uncertain. Tại mốc ghi: 19 attempt đã chốt, 14 valid; không phải accuracy. Baseline đã đạt trước khi worker mới PID 17188 mở CPU retry lúc khoảng 17:26. Tiến trình cũ PID 5468/18004 đã kết thúc, không còn là PID hiện hành.

Worker tiếp tục chạy nền theo lịch đã duyệt. Xem `verification/ml-supervisor.log` trong workspace để biết lượt/gate hiện hành; `ml-supervisor-status.json` ghi phase và số đếm tại lúc đổi phase, không phải bộ đếm realtime. Chưa fit mô hình v2. Đọc `AUTORUN_RESULT.md` và báo cáo benchmark chỉ sau khi worker báo hoàn tất.


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

## Bản bàn giao nền ngày 17/10/2026

Bản bàn giao ngày **17/10/2026, UTC+7**. Công việc gần nhất về chương trình là tối ưu đọc Zabbix; sau đó đã lưu Git/GitHub, sao lưu và shutdown lab. Phiên sắp xếp tài liệu chỉ thay tài liệu/công cụ đóng gói, không khởi động VM.

## 1. Source nào là đúng?

| Nội dung | Vị trí / phiên bản |
|---|---|
| Repository chính trên laptop | `C:\Users\Darrys\do-an` |
| Engine Python | `C:\Users\Darrys\do-an\diagnosis-engine` |
| GitHub | [Darrys37/smb-network-monitoring](https://github.com/Darrys37/smb-network-monitoring) |
| Commit chương trình gần nhất đã kiểm thử và triển khai | [`34bf592cf83e0fa39d36a1fecf8a836d3dc25eab`](https://github.com/Darrys37/smb-network-monitoring/commit/34bf592cf83e0fa39d36a1fecf8a836d3dc25eab) |
| Mốc cleanup trước đó | `7d32be7` |
| Mốc kỹ thuật kết thúc tuần 5 | `26b581e`, tag `week5-technical-20261017` |
| Mốc nghiệm thu tuần 4 | tag `week4-complete-20261017` |
| Nhật ký trên D: | `D:\Study\network-monitoring-project\docs\bangiao` |
| Engine chạy trên MON01 | `/home/phat/do-an/diagnosis-engine` |

Các commit tiếp theo có thể chỉ cập nhật tài liệu. Đối chiếu `MANIFEST.json` và cây `diagnosis-engine` trước khi kết luận chương trình đã đổi. Nhánh GitHub `main` có thể tiếp tục phát triển sau ngày bàn giao; các liên kết ghim trong gói mô tả đúng phiên bản đã gửi.

**Không dùng bản tiến độ cũ trên D: để ghi đè trạng thái hiện tại.** Trước khi sắp xếp, file `BAO_CAO_TIEN_DO_20261017.md` ở D: khác và cũ hơn file cùng tên trong project. Các báo cáo tiến độ vẫn là nhật ký lịch sử; file này mới là bản chốt tiếp nhận tại ngày nêu trên.

## 2. Đã đi đến đâu theo roadmap?

- Tuần 1–3: dựng lab, Zabbix/Agent, API và engine Python; tài liệu bàn giao cũ chỉ cần khi truy lịch sử.
- Tuần 4: có 18 lượt fault hợp lệ thuộc sáu nhóm, mỗi nhóm ba; một attempt bị hủy trước fault được giữ riêng. Baseline theo lựa chọn phiên ngắn dài **30 phút 06 giây**, không đạt mục tiêu bốn giờ nếu có thể trong roadmap.
- Tuần 5: phần kỹ thuật ngày 29–35 đã hoàn tất: đối chiếu dữ liệu, bảng/hình, Chương 2/3, báo cáo, hướng dẫn, slide, demo và backup. Đây là mốc hoàn thành kỹ thuật; chưa đồng nghĩa giảng viên đã duyệt hoặc bài đã nộp.
- Sau tuần 5: cleanup thống nhất logic và làm code dễ giải thích, rồi tối ưu các lần đọc Zabbix. Người dùng đã chủ động yêu cầu các công việc sau mốc đóng băng; kết quả không được nhập ngược vào bộ thực nghiệm tuần 4.
- Công việc tối ưu trước đó đã hoàn tất và được lưu. Không có fault/baseline đang chạy hay một tính năng mới đang triển khai dở được giao tiếp trong bản bàn giao này.

Việc còn cần chủ đồ án xác nhận trước nộp: định dạng theo mẫu trường, tự trình bày/bảo vệ, bản sao lưu ngoài laptop. Các mở rộng như profile host hoặc giao diện cần một yêu cầu mới và phạm vi cụ thể.

## 3. Các thay đổi mới nhất cần biết

Cleanup `7d32be7`:

- CLI và hàm Python cùng mặc định HTTP scope `unknown`; máy có web cần `expected`, máy không có HTTP dùng `absent`.
- Tách rõ orchestration, collection/import, rule và repository; gom ngưỡng roadmap trong `policy.py`.
- HTTP/DNS kiểm tra file ngoài qua validation chung; DNS có đối chiếu query/control/observer và tương thích probe cũ hợp lệ.

Tối ưu `34bf592`:

- `collect_roadmap_metrics(host_id)` gộp ba lần `item.get` thành một lần lấy sáu key của cùng host.
- Bốn metric ngữ cảnh, agent_metric và cpu_history dùng mốc nhận cùng phản hồi item; `lastclock` mẫu giữ nguyên. History CPU vẫn đọc riêng.
- Một lượt roadmap thành công có CPU history giảm **8 xuống 6 request API**; vẫn xác minh event trước và sau collection.
- Không có cache qua các lượt. Thứ tự evidence thay đổi, rule chọn theo loại/target/port/thời gian, không theo chỉ số list.
- Giữ điều kiện R1–R6 và cấu trúc SQLite/report/probe. Chưa có benchmark trước/sau để công bố phần trăm tăng tốc.

Đọc mục 17 file 03 trước khi sửa collection; đọc mục 16 để hiểu đợt cleanup. Các chương báo cáo cũ mô tả mốc tuần 5, vì vậy không dùng chúng thay source hiện hành khi phát triển tiếp.

## 4. Đã kiểm chứng được gì?

| Mốc | Kiểm chứng đã thực hiện |
|---|---|
| Tuần 5 (`26b581e`) | 280 tests Windows và 280 tests MON01; ba demo HTTP sau reboot có problem → incident → recovery |
| Cleanup (`7d32be7`) | 355 tests ở hai môi trường; đối chiếu 576 tổ hợp tổng hợp; 108 kết luận của 18 hồ sơ cũ giữ nguyên |
| Tối ưu (`34bf592`) | 369 tests ở hai môi trường; 15 tình huống collector khớp bản trước; 108 kết luận lịch sử giữ nguyên; Ruff lint/format đạt |
| Thu thử thật sau tối ưu | Một item.get và một history.get, 10 evidence với host đối chứng; các phép đo bình thường, R4 thiếu DNS probe nên insufficient |
| Khi triển khai tối ưu | Source MON01 đối chiếu hash; DB/.env không đổi; SQLite integrity=ok, không lỗi foreign key |

Các số test là kết quả của những lần chạy đã ghi nhận, không phải cam kết lần chạy mới chắc chắn đạt. 18/18 là tỷ lệ mục tiêu khớp trong bộ thử nhỏ, **không phải accuracy tổng quát 100%**; chưa có tập âm độc lập. Engine có thể trả nhiều matched/insufficient cùng lúc; chưa có xếp hạng nguyên nhân gốc.

## 5. Lab và trạng thái kết thúc phiên

| VM | SSH / IP | Vai trò | Host ID Zabbix |
|---|---|---|---|
| MON01 | `ssh phat@192.168.56.10` | Zabbix, MySQL, frontend 8080, Agent2, engine và SQLite | `10084` |
| SRV01 | `ssh phat@192.168.56.20` | Nginx 80, Agent2, local HTTP observer | `10683` |
| CLI01 | `ssh phat@192.168.56.30` | Agent2, DNS observer và host đối chứng | `10684` |

**Trạng thái được xác nhận lúc 19:52:44 ngày 17/10/2026 (UTC+7): cả ba VM đã `PowerOff` bằng shutdown an toàn.** Đây là kết quả cuối phiên trước, không phải kiểm tra live ở mỗi lần mở tài liệu. Khi người dùng yêu cầu làm tiếp trên VM, kiểm tra VirtualBox và kết nối thực tế; VM đang tắt sẽ không phản hồi SSH.

Trước khi shutdown, cả ba phản hồi SSH, các dịch vụ liên quan active và không có problem mở trên ba host. SQLite runtime có 39 incidents, 301 evidence, 172 diagnoses, 29 recoveries. Số hàng này gồm các giai đoạn trước và demo, không phải chỉ 18 lượt chính thức tuần 4.

MON01 từng mất phản hồi trong quá trình làm việc, đã được người dùng reset rồi kiểm tra lại trước khi triển khai. Nguyên nhân sự cố VM chưa được kết luận; không coi tối ưu Python là đã sửa lỗi VirtualBox.

Ba IP dùng Host-only cùng subnet; không có router trung gian chung. R5 dùng phương án firewall TCP80. Live collector dùng `ping`, `dig`, `ip` trên Linux; tests đạt trên Windows không chứng minh live collector chạy native Windows. Host ID và target IP còn truyền riêng, chưa tự đối chiếu mapping.

Gói tài liệu không chứa mật khẩu, API token, `.env` hoặc database. Nếu cần truy cập, lấy quyền và thông tin xác thực từ chủ đồ án hoặc môi trường đã được chủ đồ án cấu hình.

## 6. Sao lưu và phục hồi ở đâu?

- Source/docs/evidence của mốc tối ưu: `C:\Users\Darrys\Documents\ChatGPT\Đồ án network\deliverables\engine-optimization-20261017T125023Z` và `D:\Study\network-monitoring-project\backups\engine-optimization-20261017T125023Z`.
- Có Git bundle, ZIP và biên bản đã thử khôi phục bundle/fsck. Gói này **không chứa `.env` hay SQLite runtime**.
- Source MON01 trước tối ưu: `/home/phat/diagnosis-before-optimization-20261017T124751Z`.
- Bộ backup cuối tuần 5 có SQLite nhất quán nằm riêng tại các thư mục `week5-20261017T025017Z` trong hai gốc backup trên. Đối chiếu manifest/commit/thời điểm trước khi phục hồi; đó là mốc tuần 5, không tự chứa code tối ưu mới.
- GitHub lưu tracked source/docs/evidence; không thay backup VM/MySQL/SQLite hay các secret. Hai ổ C:/D: vẫn thuộc cùng laptop.

## 7. Cách tiếp tục một phiên mới

1. Xác nhận yêu cầu mới của người dùng. Những đề xuất dưới đây chưa phải nhiệm vụ tự động thực hiện.
2. Nếu có source: kiểm tra `git status`, nhánh, HEAD và remote; giữ các sửa đổi chưa commit của người dùng. Đọc file 03 và những module liên quan.
3. Nếu nhiệm vụ cần VM: kiểm tra VM thực tế, dịch vụ và problem nền trước khi chạy. Việc đọc tài liệu không cần bật lab.
4. Khi sửa: collector thu bằng chứng, rule chỉ đánh giá, repository ghi SQLite. Giữ ba trạng thái, scope/observer/freshness và kiểm tra event trước/sau.
5. Chạy kiểm tra phù hợp, dùng dữ liệu lịch sử để kiểm tra hồi quy khi đổi logic. Không ghi đè hồ sơ/tag thực nghiệm cũ. Nếu thay schema/ý nghĩa chẩn đoán hoặc gặp vấn đề quan trọng, nêu tác động và hỏi người dùng.
6. Cập nhật tài liệu và trạng thái cuối phiên theo kết quả thật, rồi lưu Git/backup theo phạm vi được giao.

Các hướng có căn cứ để cân nhắc: cấu hình theo host và xác minh host→IP; version hóa rule/assessment trước khi hỗ trợ chẩn đoán lại; bổ sung dữ liệu âm/nhiều lỗi để đánh giá. Chưa có lý do đã được kiểm chứng để tự thay engine bằng AI/ML, thêm confidence score hoặc tự khắc phục.

## 8. Chỉ mở thêm khi cần

Các liên kết dưới ghim tại mốc chương trình `34bf592` để gói vẫn dùng được ngoài laptop:

- [Source engine](https://github.com/Darrys37/smb-network-monitoring/tree/34bf592cf83e0fa39d36a1fecf8a836d3dc25eab/diagnosis-engine).
- [Hướng dẫn cài/chạy/khôi phục](https://github.com/Darrys37/smb-network-monitoring/blob/34bf592cf83e0fa39d36a1fecf8a836d3dc25eab/docs/HUONG_DAN_CAI_DAT_VA_KHOI_PHUC.md).
- [Tổng hợp tuần 5](https://github.com/Darrys37/smb-network-monitoring/blob/34bf592cf83e0fa39d36a1fecf8a836d3dc25eab/docs/TONG_HOP_TUAN_5.markdown).
- [Bộ 18 lượt thực nghiệm](https://github.com/Darrys37/smb-network-monitoring/tree/34bf592cf83e0fa39d36a1fecf8a836d3dc25eab/evidence/week4/official-runs).
- [Báo cáo tổng hợp](https://github.com/Darrys37/smb-network-monitoring/blob/34bf592cf83e0fa39d36a1fecf8a836d3dc25eab/docs/BAO_CAO_DO_AN_HOAN_THIEN.markdown).

Nếu tài khoản khác không truy cập được repository, cung cấp source hoặc artifact đúng phạm vi cần sửa qua kênh người dùng cho phép. Không suy đoán các file chưa đọc từ nội dung nhật ký.

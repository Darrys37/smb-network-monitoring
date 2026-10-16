# Phụ lục ghi nhận cách vận hành các lượt chính thức

Tài liệu này ghi cách điều khiển và thu dữ liệu trong phiên tiếp tục roadmap ngày 17/10/2026 (UTC+7). Phiếu thử tham chiếu vẫn là commit `4cabeb0`; mã engine `ca04071` và bản export tham chiếu `978b4f9`. Source của engine được đối chiếu hash với snapshot freeze trước từng lượt, không sửa luật/trigger/sampling để làm đẹp kết quả.

## Công cụ đo nằm ngoài engine

`watch_trial.py` là bộ ghi thử trong thư mục evidence, không thuộc sản phẩm engine. Bộ ghi kiểm tra problem qua API khoảng năm giây một lần, chọn đúng host/trigger, gọi `app.py --save` một lần cho event, sau đó gọi CLI đồng bộ recovery và xuất report. Nó không tự tạo lỗi hoặc tự sửa hệ thống. Thao tác gây lỗi/rollback do người vận hành điều khiển qua các script độc lập.

Với R2/R5, bộ ghi chờ HTTP JSON từ SRV01. Với R4, nó chờ DNS JSON từ CLI01. Các probe dùng đúng IP dịch vụ/observer/control và được chuyển qua SSH bằng IP. Thời gian chờ, chuyển file và poll ảnh hưởng collection delay; CLI elapsed chỉ tính từ lúc tiến trình app bắt đầu đến lúc kết thúc và bao gồm API, thu evidence, luật, lưu SQLite.

## Thao tác điều khiển

- R1: ngắt `enp0s8` trên SRV01 bằng `ip link set ... down`. Ngoài failsafe mười phút trong phiếu, có rollback định giờ khoảng 120 giây vì ngắt Host-only cũng ngắt SSH. Cả ba lượt dùng cùng cách này. Mốc rollback thực tế lấy từ log; không mặc định fault kéo dài đúng 120 giây. Timer dự phòng được dọn sau khi khôi phục và trước lượt kế tiếp.
- R2: dừng Nginx, failsafe mười phút; bật lại sau khi engine thu/lưu xong.
- R3: dừng Agent2, failsafe mười lăm phút; bật lại sau khi engine thu/lưu xong. Phải chờ dữ liệu Agent mới, availability=1 và recovery trước lượt tiếp theo. Trạng thái service active hoặc TCP10050 mở riêng lẻ chưa đủ xác nhận Zabbix đã nhận biết phục hồi.
- R4: chặn UDP/TCP đích 53 ở output CLI01 trong bảng nftables riêng; failsafe xóa đúng bảng sau mười phút. Bao gồm IPv4, IPv6 và loopback DNS stub.
- R5: chặn TCP80 có nguồn MON01 tại SRV01, trong bảng nftables riêng; failsafe mười phút. HTTP nội bộ trên IP dịch vụ vẫn được kiểm tra độc lập.
- R6: một worker CPU, timeout tự kết thúc tối đa mười hai phút. Rollback chủ động gửi SIGINT tới đúng PID stress đã ghi, xác nhận tiến trình dừng và telemetry giảm. Các lượt không dùng chung cửa sổ CPU history còn tải của lượt trước.

Timer và script rollback là hạ tầng điều khiển fault của thực nghiệm, không phải chức năng tự khắc phục của module.

## Cách ghi thời gian và giữ kết quả

Fault/rollback có timestamp trước và sau trên máy gây lỗi. Dùng UTC, giữ độ phân giải thực tế của dữ liệu. Với timestamp giây và event clock giây, phép trừ có sai số lượng tử; không diễn giải kết quả như độ chính xác mili giây. Đồng bộ NTP đã kiểm tra, nhưng không suy ra sai số giữa các VM bằng không.

Khoảng problem–recovery không phải downtime thật. Thời gian lưu recovery có thêm độ trễ của bộ ghi. Không dùng số unit test làm kết quả của 18 lượt lab; không tính các cặp HTTP không áp dụng trên CLI01 thành true negative.

Mỗi event chỉ gọi/lưu engine một lần. Không chạy lại đến khi matched rồi bỏ kết quả xấu. Retry, nếu có, phải có Run ID riêng. `insufficient_evidence`, engine error và no detection được giữ trong hồ sơ và mẫu số phù hợp.

R2-03 có một HTTP probe thu trước event. File đó được giữ là `local-http-before-event.json`; probe dùng trong diagnosis được thu mới sau event và chuyển trong freshness. Đây là ghi nhận thao tác thu bổ sung trong cùng lượt, không phải chạy lại engine hoặc thay thế một lượt chẩn đoán xấu.

## Hồ sơ

Mỗi Run ID có log preflight, fault, rollback, problem/recovery API JSON, log CLI và report incident nếu có. History trong cửa sổ và toàn bộ trigger event truy cập được của ba host được xuất bổ sung. Bảng mỗi lượt khác với CSV incident: CSV incident có một dòng cho mỗi luật, còn bảng run có một dòng cho mỗi lần thực nghiệm.

Baseline trước đo là phiên ngắn 30 phút 06 giây theo lựa chọn người thực hiện; không ghi thành đủ bốn giờ. Phân tích kết quả phải giữ hạn chế này và cỡ mẫu ba lượt/kịch bản.

R5-03 chỉ tạo watcher; lệnh fault bị từ chối trước thực thi do giới hạn sử dụng khi duyệt tự động. File run.json gốc vẫn ghi no_detection do watcher hết hạn. Adjudication riêng phân loại aborted_before_fault, loại khỏi mẫu số fault hợp lệ; lượt thật dùng mã R5-03-retry1. Không coi timeout trước fault là lỗi phát hiện của Zabbix.

Trước R6-02/R6-03, lưu CPU history và trạng thái Problems riêng để xác nhận cửa sổ năm phút không còn mẫu CPU cao của lượt trước. Không thêm vCPU hoặc bỏ dependency để thúc ép trigger.

Các manifest checksums-after-R1-R2/after-R1-R3 là checkpoint tại thời điểm tương ứng, không đại diện cây thư mục cuối phiên khi đã thêm history/bảng tổng hợp/công cụ mới. Manifest cuối phiên kiểm tra bộ dữ liệu hoàn chỉnh. Backup SQLite giữ tại MON01 và Windows; hai nơi này cùng phụ thuộc laptop vật lý, chưa phải backup độc lập ngoài thiết bị.

Snapshot cuối `final-state-20261016T213953Z` giữ kết quả kiểm tra công cụ bị lệch phạm vi: 157 trigger toàn ba host so với 70 trigger trong supplement ban đầu, cùng macro của mọi template cài sẵn thay vì template liên kết lab. Xem comparison-review.json trong snapshot đó. Sau khi đối chiếu đúng tập trigger ID và host/template lab, snapshot `final-state-20261016T214108Z` xác nhận functions/macros/links khớp; fingerprint source và cấu hình hiệu lực đầy đủ vốn đã khớp ở cả hai lần. Không có thay đổi engine hoặc cấu hình Zabbix để xử lý lỗi kiểm tra này.

# Tuần 4 — Sáu phiếu thử và bảng 18 lượt chính thức

Ngày soạn: 08/10/2026. Trạng thái: kế hoạch trước freeze; chưa bắt đầu baseline hoặc lượt chính thức.

## 1. Phiên bản và căn cứ

- Source: `ca04071`; kiểm thử trên MON01: **280 passed**. Commit cấu hình: `978b4f9`.
- Cấu hình: `evidence/week4/freeze-20261008/zbx_export_hosts.yaml`, `zbx_export_templates.yaml`, `Zabbix server health.yaml`.
- Ba host và tất cả template liên kết của chúng đã có trong bộ export. Đây không phải backup database, cấu hình daemon, global settings hoặc toàn bộ VM.
- MON01 192.168.56.10; SRV01 192.168.56.20 (host ID 10683); CLI01 192.168.56.30 (host ID 10684).
- Engine chạy trên MON01: `~/do-an/diagnosis-engine`; Git ở Windows: `C:\Users\Darrys\do-an`.
- SRV01: giữ 1 vCPU, Processing Cap 100%, kernel 7.0.0-34-generic theo trạng thái đã xác nhận. Không đổi cấu hình giữa các lượt.
- NTP cả ba máy báo `NTP=yes`, `NTPSynchronized=yes`, timezone Etc/UTC ngày 08/10. Kiểm tra tuần tự không đo được chính xác độ lệch giữa các máy.
- Dữ liệu cấu hình căn cứ vào YAML đã đọc; trạng thái runtime cần kiểm tra khi bắt đầu phiên đo.

## 2. Những giới hạn đã chốt trước đo

1. R1: TCP80 `error`, errno 113 không được coi là timeout. `insufficient_evidence` được giữ nguyên và vẫn tính lượt đó trong tổng số thử nghiệm; không ghi là chẩn đoán đạt.
2. HTTP scope khai báo theo vai trò host: SRV01 `--http-service expected`; CLI01 `--http-service absent`. Không chọn scope theo kết quả muốn có.
3. `absent` làm R2/R5 trả `not_matched` với reasoning “Not applicable”. Khi phân tích loại các cặp host–luật này khỏi phép chấm HTTP, không gọi host khỏe vì điều đó.
4. Mặc định CLI là `unknown`: R2/R5 thiếu thông tin phạm vi. Hàm Python điều phối giữ mặc định `expected` để tương thích lời gọi cũ. Các lệnh đo phải truyền scope tường minh.
5. R4 nghi ngờ lỗi phân giải/đường truy cập DNS; NXDOMAIN không tự chứng minh resolver hỏng. Ca chính thức dùng timeout do chặn truy vấn cổng 53 trên CLI01, không gõ sai tên để tạo NXDOMAIN.
6. Zabbix CPU trigger dùng `min(CPU,5m)>90`, có dependency load high. R6 engine dùng mean >=90 cùng load >= CPU count và các kiểm tra chất lượng mẫu. Hai điều kiện không tương đương.
7. R5 là chặn truy cập HTTP từ MON01, thay phương án gateway. Mạng Host-only trực tiếp không có gateway chung làm trung gian giữa MON01 và SRV01.
8. Evidence là quan sát tại lúc collection, không tái dựng lịch sử tại event time. Ground truth thao tác gây lỗi lưu riêng, không đưa vào rule như bằng chứng tự chứng minh.
9. Hồ sơ dry run 13–18 giữ nguyên. Incident 18 có R2 matched thừa trước sửa; replay sau sửa không thay thế kết quả thực nghiệm cũ.

## 3. Cổng vào trước baseline / freeze

- [ ] Lưu và commit tài liệu này, ghi mã commit tài liệu vào nhật ký.
- [x] Đã xác nhận cú pháp `http_probe.py --help`; lệnh thu/chuyển HTTP evidence cho R2/R5 ở mục 7. Phải chạy probe trên SRV01, dùng IP dịch vụ; việc xác nhận cú pháp không thay thế kiểm tra file thực tế trong mỗi lượt.
- [x] Đã đối chiếu sáu item trên SRV01 trong UI ngày 08/10/2026; bảng sampling bên dưới. Không suy cấu hình host khác từ SRV01.
- [ ] Kiểm tra Nginx/Agent2 và dữ liệu mới; xác nhận không còn fault chủ động, lưu danh sách Problems nền. Không bắt buộc mọi cảnh báo nền đều biến mất nhưng phải giải thích/phân loại.
- [ ] Giữ nguồn điện, tắt chế độ sleep tự động trong phiên đo; không reboot/đổi CPU/kernel trong lượt. Nếu có cập nhật hoặc sự cố môi trường, ghi thành sai lệch điều kiện.
- [ ] Ghi `freeze_at_utc`, source/config/docs commit và thông số hiệu lực. Mọi thay đổi sau freeze phải tăng phiên bản, ghi lý do, không trộn kết quả như cùng phiên bản.
- [ ] Backup SQLite bằng cơ chế backup nhất quán trước đo, lưu đường dẫn; không coi YAML là backup incidents. Không sao chép nóng file SQLite tùy tiện nếu đang ghi.

### Sampling SRV01 đã xác nhận

| Key | Chu kỳ / nguồn cập nhật | Loại |
|---|---|---|
| `agent.ping` | 1m | Zabbix agent |
| `zabbix[host,agent,available]` | 1m | Zabbix internal |
| `system.cpu.util[,idle]` | 1m | Zabbix agent — master |
| `system.cpu.load[all,avg1]` | 1m | Zabbix agent |
| `system.cpu.num` | 1m | Zabbix agent |
| `system.cpu.util` | Theo master CPU idle; không polling riêng | Dependent item |

Bốn item ping, availability, load và CPU count được người vận hành xác nhận Enabled, History 31d, Trends 365d. CPU idle và dependent đã xác nhận ở ảnh trước đó. Interval 1m là chu kỳ cấu hình, không đảm bảo mỗi phút đều có mẫu lưu thành công. CPU count có Discard unchanged with heartbeat 1d theo bản export đã đối chiếu; giá trị không đổi có thể chỉ lưu lại theo heartbeat. Thời gian phát hiện còn phụ thuộc cửa sổ trigger, trạng thái availability và thời điểm phát sinh lỗi; không đồng nhất interval với detection delay.

## 4. Baseline không gây lỗi

Mục tiêu ít nhất 4 giờ nếu điều kiện cho phép; nếu ngắn hơn phải ghi rõ thời lượng và hạn chế, không tuyên bố đã đủ 4 giờ.

1. Ghi start/end UTC, uptime/kernel/CPU của lab, danh sách Problems đang mở, trạng thái NTP.
2. Để Zabbix thu bình thường, không chạy stress hoặc ngắt dịch vụ/network. Giữ lịch sử HTTP, DNS, availability, CPU/load, cùng các event mới phát sinh trong cửa sổ.
3. Kiểm tra cuối phiên: có khoảng mất dữ liệu, máy sleep, restart hoặc update không. Thời gian máy tắt không tính vào baseline quan sát hợp lệ.
4. Chỉ gọi một cảnh báo là false alert sau khi kiểm tra và có bằng chứng nó không phản ánh điều kiện được định nghĩa; cảnh báo đổi gói/reboot có thể là thật dù không thuộc sáu lỗi mục tiêu.
5. Phân biệt cảnh báo Zabbix và chẩn đoán engine: engine CLI hiện được gọi thủ công, nên baseline Zabbix không tự cho ra false-positive rate của engine. Muốn đo engine trên trạng thái khỏe cần bộ evidence khỏe và đánh giá riêng, không tạo incident giả.

| Baseline ID | Start UTC | End UTC | Phút quan sát hợp lệ | Mất dữ liệu/gián đoạn | Event mới và phân loại | Thư mục evidence |
|---|---|---|---|---|---|---|
| B01 | chưa chạy | | | | | |

## 5. Quy trình chung mỗi lượt

1. Một fault tại một thời điểm. Ghi RunID và kiểm tra điều kiện trước ca; chờ recovery và telemetry khỏe từ ca trước (đặc biệt CPU history cần cửa sổ đủ mẫu).
2. Bật transcript/log terminal riêng cho RunID. Ghi UTC ngay trước và ngay sau thao tác gây lỗi; khoảng này là biên thời điểm thực thi, không giả vờ là timestamp chính xác tuyệt đối.
3. Đặt rollback có hẹn giờ trước fault; ghi tên timer/table và lệnh rollback. Fault thất bại: giữ log, ghi run aborted, không chờ event giả.
4. Lấy event đúng host, đúng loại, còn problem; không lấy cảnh báo nền hoặc event ca cũ. Timeout theo phiếu: nếu không có event, ghi no_detection và rollback; giữ lượt thất bại.
5. Thu external probe sau khi có event để kịp freshness. Chạy engine khi fault còn tồn tại, external evidence tuổi <=180 giây; ghi CLI start/end, exit code và output.
6. Nếu engine lỗi, vẫn rollback. Không sửa hoặc thử đi thử lại đến khi matched rồi chỉ giữ lượt đẹp. Retry có ID riêng và liên kết lượt ban đầu.
7. Ghi rollback trước/sau; kiểm tra phục hồi độc lập. Lấy recovery Zabbix bằng problem event ID. Giới hạn chờ recovery đề xuất: 10 phút; quá hạn ghi pending và kiểm tra, không tự đánh dấu closed.
8. Export report bằng incident ID; giữ raw evidence, problem/recovery IDs và log. Báo cáo CSV của incident chứa các dòng luật, không thay bảng 18 run.

## 6. Sáu phiếu thử

### R1 — Mất kết nối Host-only của SRV01

- **Trước ca:** ping SRV01 và CLI01 từ MON01 thành công; HTTP SRV01 200; CLI01 làm đối chứng cùng subnet; có console VirtualBox SRV01.
- **Gây lỗi (SRV01/console):** ngắt `enp0s8` đã xác nhận mang IP 192.168.56.20, bằng `sudo ip link set dev enp0s8 down`. Trước đó đặt timer bật lại sau 10 phút. Không ngắt NAT enp0s3, không reboot thay cho ngắt card.
- **Zabbix mong đợi:** HTTP check failed trên SRV01, sampling 30s/timeout 5s; chưa có trigger ICMP riêng. Cửa sổ chờ event: tối đa 5 phút, sau đó rollback và ghi no_detection nếu chưa có.
- **Engine:** host 10683, target .20, control .30, scope expected; R1 là luật mục tiêu. Nếu ping no_reply + TCP80 timeout + control success: mong đợi matched. Nếu TCP errno 113: giới hạn hiện hành là insufficient_evidence, chấm abstention, không tính đúng.
- **Rollback:** `sudo ip link set dev enp0s8 up`; xác nhận IP, ping và HTTP; lưu recovery đúng event.
- **Evidence:** trạng thái card trước/sau, timer, ping target/control, TCP raw errno, event và incident.
- **Giới hạn:** CLI01 sống không chứng minh toàn bộ mạng khỏe; không phân biệt được host tắt với mọi dạng lỗi kết nối chỉ từ quan sát từ xa.

### R2 — Dừng Nginx trên SRV01

- **Trước ca:** Nginx active; HTTP từ MON01 và từ IP dịch vụ ngay trên SRV01 trả 200; agent còn dữ liệu mới.
- **Gây lỗi (SRV01):** đặt timer start nginx sau 10 phút rồi `sudo systemctl stop nginx`; ghi thời gian và trạng thái service/listener.
- **Zabbix:** SRV01 HTTP failed; chờ tối đa 5 phút.
- **Engine:** host 10683, target .20, control .30, scope expected; nhập HTTP evidence mới có observer srv01 từ probe tại SRV01. Mong đợi R2 matched; R5 không matched khi HTTP nội bộ thất bại.
- **Rollback:** `sudo systemctl start nginx`, xác nhận local/remote HTTP200, lưu recovery.
- **Evidence:** systemctl/ss, probe local, ping/TCP từ MON01, problem/recovery, report.
- **Giới hạn:** TCP refused đơn lẻ không chứng minh Nginx dừng; giữ thông tin firewall/listener còn thiếu trong kết luận engine.

### R3 — Dừng Agent2 trên SRV01

- **Trước ca:** Agent2 active, agent.ping mới; ping và HTTP200 vẫn thành công.
- **Gây lỗi (SRV01):** đặt timer start agent sau 15 phút rồi `sudo systemctl stop zabbix-agent2`.
- **Zabbix:** trigger availability `max(zabbix[host,agent,available],3m)=0`; không mô tả là trigger agent.ping nodata. Chờ tối đa 10 phút.
- **Engine:** host 10683, target .20, control .30, scope expected. Chỉ thu khi agent.ping cũ đã vượt freshness 180s. Mong đợi R3 matched với host ping success, không có agent data mới và TCP10050 refused/timeout theo logic luật.
- **Rollback:** start agent, kiểm tra active và dữ liệu mới; lưu recovery.
- **Evidence:** giờ stop/start, service state, ping/HTTP đối chứng, raw agent metric và TCP10050, event/report.
- **Giới hạn:** R6 thiếu history do agent dừng là thiếu evidence, không phải bằng chứng CPU khỏe hay lỗi CPU. Mode/allow-list/firewall vẫn là khả năng cần kiểm tra từ phía engine.

### R4 — Chặn truy vấn DNS trên CLI01

- **Trước ca:** default-resolver query example.com A thành công; CLI01 ping 1.1.1.1 thành công; item DNS có mẫu 1 mới; Agent2 còn hoạt động. Host ID 10684.
- **Gây lỗi (CLI01):** bảng nftables inet riêng có tên duy nhất, chain output policy accept, drop UDP và TCP đích port53. Hẹn xóa đúng bảng sau 10 phút trước khi thêm rule. Bao gồm truy vấn loopback tới 127.0.0.53, nên cached answer không né được rule này.
- **Zabbix:** key `net.dns[,example.com,A,2,1,udp]`, mỗi 30s, history7d, không trends; trigger max(#3)=0. Chờ tối đa 5 phút.
- **Engine:** host10684/target.30, control R1=.20, scope absent; DNS name example.com, observer cli01, DNS control1.1.1.1. Sau event, chạy dns_probe.py trên CLI01 rồi scp JSON bằng IP sang MON01 và chẩn đoán trong freshness.
- **Mong đợi:** R4 matched; R2/R5 không áp dụng. Ping đối chứng vẫn success. Không coi mọi luật khác đều phải matched.
- **Rollback:** xóa đúng bảng nft; date UTC; dig NOERROR; probe phục hồi mới nếu cần ghi nhận trạng thái rule trở lại; lưu recovery.
- **Evidence:** resolver settings, rules/counters, baseline và fault JSON, ping, thời điểm rollback, event/report.
- **Giới hạn:** fault nằm trên CLI01, không chứng minh Cloudflare/resolver upstream chết. example.com là tên thử nghiệm ngoài lab, không phải tên ứng dụng Nginx SRV01.

### R5 — Chặn HTTP từ MON01 vào SRV01

- **Trước ca:** Nginx active, local HTTP qua 192.168.56.20 trả 200, MON01 HTTP200/ping thành công; không còn bảng fault cũ.
- **Gây lỗi (SRV01):** bảng nft inet riêng, input chain policy accept; drop `ip saddr 192.168.56.10 tcp dport 80`; hẹn xóa bảng sau 10 phút trước khi thêm rule.
- **Zabbix:** SRV01 HTTP failed; chờ tối đa 5 phút.
- **Engine:** host10683/target.20/control.30/scope expected; bắt buộc HTTP probe fresh từ srv01 trên chính IP dịch vụ. Mong đợi ping success, remote TCP80 timeout (hoặc refused theo luật), local HTTP success; R5 matched và R2 not_matched.
- **Rollback:** xóa đúng bảng, xác nhận HTTP200 từ MON01 và lưu recovery.
- **Evidence:** rule/counter, local probe, remote TCP/ping/curl, event/report.
- **Giới hạn:** local request không qua cùng ingress path với MON01. Engine chỉ nghi filtering/access path, không chứng minh firewall là nguyên nhân duy nhất. Không gọi đây là lỗi gateway.

### R6 — CPU cao kéo dài trên SRV01

- **Trước ca:** giữ1vCPU/cap100%/kernel đã chốt; CPU/load baseline thấp, CPU history đủ >=240s, gap<=120s, newest<=180s, không có stress cũ hoặc cập nhật nền đang gây tải.
- **Gây lỗi (SRV01):** ghi thời gian; `stress-ng --cpu 1 --cpu-load 100 --timeout 12m --metrics-brief` trong terminal riêng. Đây là fault có tự hết hạn.
- **Zabbix:** CPU min5m>90, dependency load-high còn nguyên. Chờ tối đa 10 phút; nếu bị dependency chi phối, ghi sự kiện thực tế và lý do, không bỏ dependency để ép phát hiện.
- **Engine:** host10683/target.20/control.30/scope expected. R6 mục tiêu matched nếu mean>=90 và load>=CPUcount, đủ dữ liệu. CPUcount heartbeat1d được phép tuổi<=86580s; load<=180s.
- **Rollback:** Ctrl+C tại terminal đang chạy stress hoặc hết timeout; xác nhận không còn stress, CPU giảm và lưu recovery.
- **Evidence:** start/end stress, kernel/CPU count, history CPU/load/timestamps, các lỗi môi trường nếu có, event/report.
- **Giới hạn:** CPU cao và load không tự chứng minh dịch vụ chậm; muốn nói về suy giảm hiệu năng cần baseline response time. Không quy mọi CPU softirq cho stress-ng.

## 7. Hợp đồng lệnh chẩn đoán

Không sao chép ID của dry run cho lượt mới. Event ID phải được kiểm tra trước; report dùng incident ID khác với event ID.

SRV01 (R1/R2/R3/R5/R6), MON01/Bash:

```bash
read -r -p 'Problem event ID mới của SRV01: ' EVENT_ID
python app.py --event-id "$EVENT_ID" --host-id 10683 \
  --target-ip 192.168.56.20 --ruleset roadmap \
  --control-ip 192.168.56.30 --http-service expected --save
```

**R2/R5 dùng quy trình riêng bên dưới**, sau khi có problem và khi fault vẫn tồn tại. Cú pháp probe đã xác nhận qua `--help`.

SRV01 / Bash, tại thư mục chứa `http_probe.py`:

```bash
http_file="http-srv01-$(date -u +%Y%m%dT%H%M%SZ).json"
python3 http_probe.py --target-ip 192.168.56.20 \
  --observer srv01 --output "$http_file" && \
  scp "$http_file" phat@192.168.56.10:~/do-an/diagnosis-engine/
```

MON01 / Bash, tại `~/do-an/diagnosis-engine`, môi trường `.venv` đã kích hoạt:

```bash
read -r -p 'Problem event ID mới của SRV01: ' EVENT_ID
read -r -p 'Tên hoặc đường dẫn JSON HTTP vừa chép sang MON01: ' HTTP_FILE
if [ -f "$HTTP_FILE" ]; then
  python app.py --event-id "$EVENT_ID" --host-id 10683 \
    --target-ip 192.168.56.20 --ruleset roadmap \
    --control-ip 192.168.56.30 --http-service expected \
    --http-observer srv01 --http-evidence "$HTTP_FILE" --save
else
  echo 'File chưa tồn tại; chưa chạy chẩn đoán.'
fi
```

Chọn đúng file của lượt hiện tại, chạy chẩn đoán khi evidence tuổi <=180s. Nếu quá hạn, thu mới khi fault còn tồn tại; không sửa timestamp. Kiểm tra tên file, observer và kết quả import trong hồ sơ lượt. Không chạy các lệnh này ngay chỉ để hoàn thiện biểu mẫu.


R4, MON01/Bash (JSON thu mới trên CLI01):

```bash
read -r -p 'Problem event ID DNS mới của CLI01: ' EVENT_ID
read -r -p 'Đường dẫn JSON DNS vừa chép sang MON01: ' DNS_FILE
if [ -f "$DNS_FILE" ]; then
  python app.py --event-id "$EVENT_ID" --host-id 10684 \
    --target-ip 192.168.56.30 --ruleset roadmap \
    --control-ip 192.168.56.20 --http-service absent \
    --dns-name example.com --dns-observer cli01 \
    --dns-control-ip 1.1.1.1 --dns-evidence "$DNS_FILE" --save
else
  echo 'File chưa tồn tại; chưa chạy chẩn đoán.'
fi
```

File DNS >180s phải thu mới khi fault còn tồn tại, không sửa timestamp. Nếu fault đã phục hồi thì giữ lượt thu thiếu/failed, không giả lập lại trạng thái cũ.

## 8. Mốc thời gian và cách tính

Dùng UTC có múi giờ hoặc Unix epoch, không lấy giờ tin nhắn. Ghi timestamp trước/sau thao tác thay đổi để biểu diễn sai số thực thi.

| Trường | Ý nghĩa |
|---|---|
| fault_before / fault_after | Biên thời gian lệnh tạo lỗi; thêm fault_verified nếu có phép kiểm tra độc lập |
| problem_time / problem_event_id | Clock và ID lấy từ Zabbix |
| cli_start / cli_end / exit_code | Đầu/cuối tiến trình app; elapsed đo bằng monotonic nếu có |
| collection_start | Giá trị engine in/lưu; không thay thế cli_start nếu định nghĩa khác |
| rollback_before / rollback_after | Biên thực thi rollback |
| restoration_verified | Thời điểm kiểm tra độc lập thành công sau rollback |
| recovery_time / recovery_event_id | Clock và ID recovery Zabbix |
| recovery_saved_at | Lúc engine kiểm tra và lưu recovery; có độ trễ do người vận hành |

- Detection delay khoảng [problem_time - fault_after, problem_time - fault_before] khi thứ tự thời gian hợp lệ. Nếu âm hoặc đồng hồ không tin cậy, đánh dấu vấn đề đo lường; không ép về0.
- CLI elapsed = thời gian toàn tiến trình app (API + thu evidence + luật + lưu). Không gọi là thời gian riêng thuật toán chẩn đoán.
- Collection delay = collection_start - problem_time; gồm việc chờ và thao tác của người vận hành, không phải runtime.
- Recovery recognition delay có thể báo theo biên rollback tương tự; không dùng recovery_saved_at như recovery_time của Zabbix.
- Event interval = recovery_time - problem_time; không gọi là downtime thật.
- Muốn đo riêng runtime rules phải bổ sung instrumentation trước freeze; hiện không tự suy ra từ report.
- Độ chính xác đo không được vượt độ phân giải timestamp và bằng chứng đồng bộ giờ hiện có.

## 9. Chấm kết quả trước khi nhìn 18 lượt

Mỗi scenario có một luật mục tiêu R tương ứng. Scope HTTP được khai báo trước theo vai trò host, không thay đổi sau khi biết nhãn lỗi.

- Detection rate: số lượt có đúng problem event trong cửa sổ / số lượt fault thực thi hợp lệ. Lượt fault không tạo được ghi aborted riêng, không xóa.
- Target diagnosis success end-to-end: số lượt có luật mục tiêu matched bằng evidence hợp lệ / tổng lượt fault thực thi hợp lệ. Không có event/engine error/insufficient/not_matched đều không được tính vào tử số.
- Báo cáo riêng số abstention (`insufficient_evidence`), số engine error và số no_detection. Có thể tính accuracy có điều kiện trên các lượt engine hoàn tất nhưng phải công bố mẫu số, không thay chỉ số end-to-end bằng chỉ số đẹp hơn.
- Extra diagnosis: matched của luật khác không được thao tác/quan sát độc lập hỗ trợ; kiểm tra nguyên nhân trước khi gọi false positive. R2 trên CLI01 trong incident18 là ví dụ trước sửa.
- Không tính R2/R5 khi scope absent như true negatives để nâng accuracy. Không coi luật thiếu dữ liệu là healthy.
- Baseline false alerts: số event mới được xác minh không phản ánh điều kiện thực / số giờ quan sát hợp lệ. Đây là tần suất theo giờ, không phải false-positive rate chuẩn có mẫu số TN nếu chưa định nghĩa mẫu âm.
- Chỉ ba lượt mỗi scenario: báo số đếm, từng giá trị và khoảng dao động; không khẳng định độ tin cậy vận hành doanh nghiệp từ mẫu nhỏ này.
- Mọi retry giữ RunID riêng (ví dụ R1-01-retry1), nguyên nhân và kết quả; không thay thế âm thầm lượt ban đầu.

## 10. Bảng đăng ký 18 lượt — chưa có kết quả

Mỗi dòng trỏ tới một phiếu ghi chi tiết theo mẫu ở mục11. Source/config tham chiếu cố định trừ khi có phiên bản mới được ghi rõ.

| RunID | Host | Luật mục tiêu | Source | Config | Trạng thái | Problem/Recovery | Incident | Hồ sơ |
|---|---|---|---|---|---|---|---|---|
| R1-01 | SRV01 | R1 | ca04071 | 978b4f9 | chưa chạy | | | |
| R1-02 | SRV01 | R1 | ca04071 | 978b4f9 | chưa chạy | | | |
| R1-03 | SRV01 | R1 | ca04071 | 978b4f9 | chưa chạy | | | |
| R2-01 | SRV01 | R2 | ca04071 | 978b4f9 | chưa chạy | | | |
| R2-02 | SRV01 | R2 | ca04071 | 978b4f9 | chưa chạy | | | |
| R2-03 | SRV01 | R2 | ca04071 | 978b4f9 | chưa chạy | | | |
| R3-01 | SRV01 | R3 | ca04071 | 978b4f9 | chưa chạy | | | |
| R3-02 | SRV01 | R3 | ca04071 | 978b4f9 | chưa chạy | | | |
| R3-03 | SRV01 | R3 | ca04071 | 978b4f9 | chưa chạy | | | |
| R4-01 | CLI01 | R4 | ca04071 | 978b4f9 | chưa chạy | | | |
| R4-02 | CLI01 | R4 | ca04071 | 978b4f9 | chưa chạy | | | |
| R4-03 | CLI01 | R4 | ca04071 | 978b4f9 | chưa chạy | | | |
| R5-01 | SRV01 | R5 | ca04071 | 978b4f9 | chưa chạy | | | |
| R5-02 | SRV01 | R5 | ca04071 | 978b4f9 | chưa chạy | | | |
| R5-03 | SRV01 | R5 | ca04071 | 978b4f9 | chưa chạy | | | |
| R6-01 | SRV01 | R6 | ca04071 | 978b4f9 | chưa chạy | | | |
| R6-02 | SRV01 | R6 | ca04071 | 978b4f9 | chưa chạy | | | |
| R6-03 | SRV01 | R6 | ca04071 | 978b4f9 | chưa chạy | | | |

## 11. Mẫu phiếu ghi từng lượt

Sao chép mẫu cho từng RunID; ô chưa biết để trống hoặc ghi NA kèm lý do, không điền0.

- RunID / scenario / operator:
- Source commit / config commit / docs commit:
- Host ID / IP / observer / control IP / HTTP scope:
- Kernel / vCPU / cap / NTP:
- Điều kiện trước và Problems nền:
- Fault command / timer / rollback command:
- fault_before / fault_after / fault_verified UTC:
- problem_event_id / problem_time UTC:
- External probe path / observer / collected_at / freshness:
- cli_start / collection_start / cli_end / elapsed / exit_code:
- Incident ID / trạng thái luật mục tiêu / reasoning:
- Luật matched ngoài dự kiến / bằng chứng đối chiếu:
- rollback_before / rollback_after / restoration_verified UTC:
- recovery_event_id / recovery_time / recovery_saved_at:
- Kết quả detection / diagnosis / abstention / extra diagnosis:
- Sai lệch điều kiện, lỗi môi trường, retry và lý do:
- Raw logs / JSON / Markdown / CSV / ảnh / thư mục evidence:

## 12. Kết thúc phiên

Xác nhận rollback từng fault và không còn stress; giữ log của cả ca lỗi. Lưu report, probe gốc, cấu hình/phiếu và commit đúng file. Backup DB nhất quán. Working tree clean chỉ xác nhận Git local; chỉ ghi đã push sau khi có output push thành công.

Tài liệu này là kế hoạch và biểu mẫu, không chứng nhận baseline, freeze hay 18 run đã hoàn thành.

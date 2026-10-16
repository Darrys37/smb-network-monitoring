"""Create the requested .markdown handover from verified week-4 records."""
from collections import Counter
from datetime import datetime, timezone, timedelta
import csv
import json
from pathlib import Path
import sys

project=Path(sys.argv[1])
root=project/'evidence/week4/official-runs'
baseline=project/'evidence/week4/baseline-20261016T162549Z'
closure=project/'evidence/week4/closure-20261017'
summary=json.loads((root/'experiment-summary.json').read_text())
audit=json.loads((closure/'closure-audit.json').read_text())
live=json.loads((closure/'screenshots/closure-live-status.json').read_text())
assert live['available_hosts']==3 and live['open_problem_triggers']==0 and live['unsupported_items']==0
base=json.loads((baseline/'baseline-summary.json').read_text())
freeze=json.loads((baseline/'preflight.json').read_text())
state=json.loads((root/'final-state-20261016T214108Z/summary.json').read_text())
rows=list(csv.DictReader((root/'all-trials.csv').open(encoding='utf-8')))
assert summary['complete_18_valid_faults'] and audit['result']=='PASS'
tz=timezone(timedelta(hours=7))
now=datetime.now(tz).isoformat(timespec='seconds')
def t(value):
    return datetime.fromtimestamp(float(value),tz).strftime('%H:%M:%S') if value else 'NA'
def bound(a,b):
    return f'{float(a):g}–{float(b):g}' if a and b else 'NA'
def stat(d):
    return f"{d['median']:.3f} [{d['min']:.3f}–{d['max']:.3f}]" if d['n'] else 'NA'
counts=Counter()
for d in summary['scenarios'].values():
    for rule,result in d['all_rule_status_counts'].items(): counts.update(result)
md=[f'''# TỔNG HỢP VÀ NGHIỆM THU TUẦN 4 — ĐỒ ÁN GIÁM SÁT MẠNG

Ngày cập nhật: **{now}** (UTC+7, Asia/Bangkok).

**Kết luận:** hoàn thành phạm vi thực nghiệm tuần 4 đã thống nhất: sáu kịch bản, 18 fault hợp lệ, hồ sơ problem/evidence/diagnosis/recovery truy vết được, dữ liệu đã đối chiếu, ảnh lịch sử bổ sung và backup SQLite đã thử đọc phục hồi. **Ngoại lệ được công bố:** baseline được người thực hiện chọn phiên ngắn 30 phút 06 giây, không đạt mục tiêu bốn giờ ban đầu. Vì vậy không mô tả việc hoàn thành này như đã đáp ứng cả mục tiêu baseline bốn giờ hoặc đã hoàn thành tuần 5.

Bản chính: `C:\\Users\\Darrys\\do-an\\docs\\TONG_HOP_TUAN_4.markdown`. Project thật là `C:\\Users\\Darrys\\do-an`; thư mục `D:\\Study\\network-monitoring-project\\docs\\bangiao` lưu nhật ký. Liên kết tương đối trong tài liệu lấy bản chính trong repository làm gốc; các bảng số liệu bên dưới có thể đọc độc lập, còn ảnh và raw data đi kèm repository.

## 1. Mục tiêu, phạm vi và sản phẩm

Tuần 4 chuyển hệ thống đã triển khai thành bộ thực nghiệm có thể kiểm chứng: thiết kế fault, dry run, khóa phiên bản, quan sát nền, chạy mỗi kịch bản ba lần, giữ cả sai lệch và retry, rồi tổng hợp kết quả. Zabbix phát sinh problem/recovery; module Python CLI thu evidence hiện tại, áp dụng luật và lưu SQLite. Người vận hành điều khiển fault và rollback. Không có chức năng AI suy luận, daemon tự xử lý mọi event hoặc tự khắc phục trong engine.

| Đầu việc roadmap | Kết quả nghiệm thu | Căn cứ |
|---|---|---|
| Ngày 22 — sáu phiếu kịch bản | Đạt | Phiếu thử `4cabeb0`, có điều kiện trước, fault, rollback, evidence và giới hạn |
| Ngày 23 — dry run, sửa vấn đề | Đạt ở mốc trước đợt chính thức | Hồ sơ incident 13–18; sửa scope/observer và 280 tests pass trước baseline |
| Ngày 24 — khóa phiên bản/runtime | Đạt | Snapshot hiệu lực, source hashes, macro/template/functions bổ sung |
| Ngày 24 — baseline | Đạt phạm vi phiên ngắn đã chọn; ngoại lệ so với mục tiêu gốc | 1.806 giây; 31 poll; 963 history rows / 28 item; không ghi thành 4 giờ |
| Ngày 25 — R1–R3 | Đạt | Chín fault hợp lệ, chín incident và recovery |
| Ngày 26 — R4–R6 | Đạt | Chín fault hợp lệ, chín incident và recovery |
| Ngày 27 — đối chiếu/bù hồ sơ | Đạt | Giữ R5-03 aborted; R5-03-retry1 có mã riêng; 18 ảnh chi tiết lịch sử khớp event |
| Ngày 28 — tổng hợp và backup | Đạt cho bộ thử | CSV/JSON/biểu đồ, ba nhận xét, SHA256, SQLite integrity và tái tạo 18 report từ bản phục hồi |

Không cộng số file hay số tests thành số lần thực nghiệm. Bộ chính thức có **18 fault hợp lệ + 1 attempt bị hủy trước fault**. Screenshot được bổ sung sau đợt đo, không giả là ảnh lúc fault đang chạy.

## 2. Mô hình lab và kiến trúc thực tế

| Máy | Host ID | IP Host-only | Vai trò |
|---|---:|---|---|
| MON01 / tên Zabbix `Zabbix server` | 10084 | 192.168.56.10 | Zabbix server 7.0 LTS, MySQL, frontend Nginx cổng 8080, Agent 2, Python CLI/SQLite |
| SRV01 | 10683 | 192.168.56.20 | Nginx cổng 80, Agent 2; đích R1/R2/R3/R5/R6 |
| CLI01 | 10684 | 192.168.56.30 | Agent 2, observer DNS và host đối chứng; đích R4 |

Mỗi VM có NAT trên `enp0s3` và Host-only trên `enp0s8`; ba địa chỉ .56.x cùng subnet, giao tiếp trực tiếp. Không có gateway lab chung đứng giữa MON01 và SRV01. Vì vậy R5 dùng phương án firewall HTTP đã được chốt trước đo.

Thông số tại phiên đo: Ubuntu 26.04.1, kernel `7.0.0-34-generic`; Python 3.14.4 trên MON01. VirtualBox xác nhận MON01 2 vCPU/4096 MB, SRV01 **1 vCPU/3048 MB**, CLI01 1 vCPU/2048 MB; CPU cap 100%. Các VM báo NTP synchronized; không suy ra sai số clock bằng 0 chỉ từ trạng thái này. Frontend được hậu kiểm là Zabbix 7.0.30; không nâng cấp phần mềm để hoàn thiện hồ sơ.

```text
Zabbix Agent / HTTP scenario / DNS item
             ↓
Zabbix problem → API xác minh đúng host và còn mở
             ↓
Python: ICMP + TCP + metrics/history + external evidence đúng observer
             ↓
R1–R6: matched / not_matched / insufficient_evidence
             ↓
SQLite: incidents + evidence + diagnoses
             ↓
recovery.py xác minh cặp event → recoveries → report JSON/Markdown/CSV
```

`app.py` kiểm tra event trước và sau collection; evidence mô tả thời điểm thu, không tự tái dựng quá khứ tại event time. `save_incident_bundle` lưu transaction và từ chối trộn bundle đã có. Recovery được lưu bổ sung, giữ evidence/diagnosis gốc. Bộ ghi thử poll API khoảng 5 giây chỉ là công cụ ngoài engine, không biến sản phẩm thành dịch vụ chẩn đoán tự động.

## 3. Phiên bản và khóa cấu hình

| Thành phần | Mốc |
|---|---|
| Source tham chiếu | `ca04071` |
| Export host/template tham chiếu | `978b4f9` |
| Phiếu thử | `4cabeb0` |
| HEAD khi bắt đầu phiên | `{freeze['git_head']}` |
| Mốc chụp snapshot trước baseline (`prepared_at_utc`) | `{freeze['prepared_at_utc']}` |
| Fingerprint source/tests | `{freeze['source_sha256']}` |
| Fingerprint cấu hình hiệu lực | `{freeze['config_sha256']}` |
| Checkpoint bộ đo và báo cáo | `fcf4232` |
| Checkpoint checksum backup trước freeze | `e6ce1ae` |
| Biên bản shutdown sau đợt đo | `d519039` |

Snapshot hiệu lực là căn cứ của phiên, không chỉ tên thư mục `freeze-20261008`. Đã lưu delay, preprocessing, biểu thức trigger, dependencies, functions, web scenario và các macro quan trọng. API token đọc không thấy hết macro kế thừa nên bổ sung SELECT cục bộ chỉ đọc để kiểm tra host/template liên kết và threshold. Engine không dùng quyền MySQL này.

Snapshot cuối hợp lệ `final-state-20261016T214108Z` xác nhận: source, cấu hình hiệu lực, tập trigger functions đã đối chiếu, critical macros và template links không đổi; không có critical global override. Trước mỗi run cũng kiểm tra hash source. Không đổi luật, trigger hoặc sampling để ép kết quả matched.

Snapshot `final-state-20261016T213953Z` được giữ nguyên kèm `comparison-review.json`: công cụ ban đầu so 157 trigger với supplement 70 trigger, và macro toàn bộ template cài sẵn với template lab. Đây là lỗi phạm vi kiểm tra; sau khi sửa công cụ, đối chiếu cùng phạm vi đạt. Fingerprint cấu hình đầy đủ và source vốn đã khớp ở cả hai lần. Không sửa Zabbix để xử lý lỗi công cụ này.

## 4. Dry run và những điều đã chốt trước đo

Sáu hồ sơ dry run được giữ riêng: R5 incident 13, R2 incident 14, R6 incident 15, R1 incident 16, R3 incident 17, R4 incident 18. Không trộn chúng vào 18 lượt chính thức (incident 19–36).

Các điểm chốt quan trọng từ dry run/phiếu thử:

- HTTP scope phải khai báo theo vai trò host: SRV01 `expected`, CLI01 `absent`. R2/R5 trên CLI01 không áp dụng, không được tính thành true negatives.
- R2/R5 cần local HTTP từ SRV01, đúng IP dịch vụ, sau event và còn fresh. R4 cần DNS và IP control cùng observer CLI01.
- R1 giữ phân biệt TCP timeout với lỗi hệ thống như errno 113. Không đổi `error` thành timeout để chấm đạt.
- R4 không dùng gõ sai tên/NXDOMAIN làm bằng chứng resolver hỏng; fault là chặn UDP/TCP cổng 53.
- Trigger CPU `min(CPU,5m)>90` và luật CPU mean ≥90% + load ≥ CPU count là hai điều kiện khác nhau. Giữ dependency load-high của trigger.
- Incident 18 từng có R2 matched thừa trước sửa. Kết quả cũ được giữ; replay sau sửa không thay thế lịch sử dry run.
- Mốc kiểm tra trước baseline là **280 tests passed** trên MON01. Không gọi đó là 280 thử nghiệm fault thật hoặc là test mới chạy sau mọi lần reboot.

## 5. Baseline: thời lượng thật và chất lượng dữ liệu

| Chỉ tiêu | Giá trị |
|---|---|
| Baseline mới | `baseline-20261016T162549Z` |
| Bắt đầu UTC | `{base['start_utc']}` |
| Kết thúc UTC | `{base['end_utc']}` |
| Giờ UTC+7 | 16/10/2026 23:26:08–23:56:14 |
| Mục tiêu hiệu lực người thực hiện chọn | 1.800 giây |
| Quan sát hợp lệ thực tế | **1.806 giây = 30 phút 06 giây** |
| Poll / khoảng cách poll lớn nhất | 31 / 62 giây |
| History / item | 963 rows / 28 item |
| API errors / item errors được ghi nhận | 0 / 0 |
| Problem mới / problem mở đầu–cuối | 0 / 0–0 |
| Đánh giá | `accepted_short_baseline` |

Đã rà lịch sử event (kể cả event có thể đã recovery), khoảng mất mẫu và uptime; không thấy khoảng trống vượt ngưỡng kiểm tra hoặc uptime reset trong cửa sổ. CPU count không có history mới do discard-unchanged heartbeat một ngày; retained value đã được kiểm tra, không gán tự động là mất giám sát.

Phiên cũ 16/10/2026 04:12:30–04:15:08 UTC chỉ dài 158 giây và được giữ riêng. Không cộng với phiên mới để tuyên bố có baseline dài. `session.json` còn mục tiêu gốc 14.400 giây; `short-session-plan.json` ghi quyết định thay thành 1.800 giây. Không sửa hồi tố các bản ghi ban đầu.

Trong cửa sổ mới, tần suất problem mới quan sát = `0 / (1806/3600) = 0 event/giờ`. Không có event để phân loại false alert; số 0 này chỉ mô tả phiên ngắn. Không suy ra engine CLI không báo sai, không có false-positive rate chuẩn hoặc độ tin cậy qua đêm/nhiều ngày.

## 6. Sáu fault chính thức và rollback

| Mã | Fault thực thi | Evidence chính | Phục hồi/giới hạn |
|---|---|---|---|
| R1 | `ip link set dev enp0s8 down` trên SRV01 | Ping target no_reply, TCP80 timeout, CLI01 đối chứng còn trả lời; trạng thái card độc lập | Timer bật card khoảng 120s; failsafe 600s; log thật quyết định thời điểm |
| R2 | `systemctl stop nginx` trên SRV01 | Target ping được, TCP80 failed, local HTTP failed trên IP dịch vụ | Start Nginx sau khi engine lưu; failsafe 600s |
| R3 | `systemctl stop zabbix-agent2` trên SRV01 | Ping được, agent.ping không mới đủ lâu, TCP10050 refused/timeout | Start Agent; chờ dữ liệu mới, availability=1 và recovery; failsafe 900s |
| R4 | nft output CLI01 drop UDP/TCP đích 53, cả IPv4/IPv6/stub | DNS timeout nhưng ping IP 1.1.1.1 cùng CLI01 thành công; HTTP scope absent | Xóa đúng bảng nft riêng; failsafe 600s |
| R5 | nft input SRV01 drop TCP80 nguồn MON01 | Remote TCP fail, local HTTP200 trên IP dịch vụ; counters/rules độc lập | Xóa đúng bảng nft riêng; failsafe 600s |
| R6 | `stress-ng --cpu 1 --cpu-load 100 --timeout 12m --metrics-brief` | CPU history đủ độ phủ, mean ≥90%, load ≥1, CPU count=1 | SIGINT đúng PID, xác nhận không còn worker; timeout tự giới hạn 12m |

Một fault tại một thời điểm. Trước lượt tiếp theo, chờ recovery và telemetry khỏe; riêng R6-02/R6-03 có hồ sơ CPU history không còn mẫu cao từ lượt trước. Không tăng vCPU, đổi cap hoặc bỏ dependency giữa đợt.

R1 là ngắt Host-only, không phải đã thử mất nguồn VM. R4 kiểm chứng đường DNS bị chặn, không chứng minh resolver upstream hỏng. R5 là đường truy cập HTTP bị lọc; engine vẫn chỉ kết luận nghi ngờ filtering/access path, không tự đọc firewall để biết chính xác nguyên nhân. R6 gợi ý CPU/load cao, chưa chứng minh ứng dụng chậm do CPU nếu thiếu đối chứng response-time.

## 7. Cách đo và mẫu số

1. **Detection rate:** fault hợp lệ có đúng problem event / mọi fault hợp lệ. No detection vẫn ở mẫu số.
2. **Target success end-to-end:** fault hợp lệ có luật mục tiêu matched với evidence/hồ sơ qua kiểm tra / mọi fault hợp lệ. Không loại engine error hoặc abstention để làm tỷ lệ đẹp hơn.
3. **Detection bounds:** `[problem_clock − fault_after, problem_clock − fault_before]`. Timestamp fault/event theo giây; CSV có thêm cận ±1 giây cho lượng tử hóa, chưa gồm sai số đồng bộ clock chưa đo.
4. **CLI elapsed:** monotonic wall time từ gọi app đến kết thúc, gồm API, collection, luật và SQLite; không phải inference time thuần túy.
5. **Recovery recognition bounds:** `[recovery_clock − rollback_after, recovery_clock − rollback_before]`. Khoảng problem–recovery không phải downtime thật.
6. Evidence tại collection phải đúng observer/target/scope/freshness. Ground truth fault lưu riêng, không nhét vào luật như bằng chứng tự chứng minh.

Không có tập âm khỏe độc lập được định nghĩa. Vì vậy không tính specificity hay accuracy có true negatives. Một incident CSV có một dòng cho mỗi luật; `all-trials.csv` có một dòng cho mỗi lượt, không cộng hai kiểu dòng này thành số lần thử.

## 8. Kết quả chính thức theo kịch bản

Tất cả thống kê dưới đây có n=3 mỗi scenario. Detection mô tả cận dưới clock đã lưu; bảng từng lượt và CSV giữ cả hai cận.

| Mã | Fault hợp lệ | Detection | Target success | Abstention mục tiêu | Detection median [min–max] s | CLI median [min–max] s |
|---|---:|---:|---:|---:|---|---|''']
for scenario,d in summary['scenarios'].items():
    md.append(f"| {scenario} | {d['valid_faults']} | {d['detected']}/3 | {d['target_success_end_to_end']}/3 | {d['target_abstentions']} | {stat(d['detection_delay_lower_seconds'])} | {stat(d['cli_elapsed_seconds'])} |")
md += ['','**Tổng: detection 18/18; target success end-to-end 18/18; 0 no_detection trên fault hợp lệ; 0 engine error; 0 abstention của luật mục tiêu; cả 18 lifecycle closed.** Đây là kết quả trên bộ lỗi đã tạo, không phải accuracy vận hành tổng quát. Không có matched ngoài mục tiêu trong 18 lượt đã rà.','',
'| Mã | Recovery recognition cận dưới: median [min–max] s | Cận trên: median [min–max] s |','|---|---|---|']
for scenario,d in summary['scenarios'].items():
    md.append(f"| {scenario} | {stat(d['recovery_recognition_lower_seconds'])} | {stat(d['recovery_recognition_upper_seconds'])} |")
md += ['','![Từng thời gian phát hiện và chạy CLI](../evidence/week4/official-runs/figures/thoi-gian-phat-hien-va-cli.png)','','![Số lượt luật mục tiêu matched](../evidence/week4/official-runs/figures/ket-qua-luat-muc-tieu.png)','','Biểu đồ có bản PNG/SVG/PDF. Mỗi chấm là một lượt, vạch cam là median; không phải khoảng tin cậy. Nhãn 3/3 không được diễn giải thành độ tin cậy dài hạn.','',
'## 9. Bảng truy vết đủ 18 lượt','','Đơn vị thời gian: giây; CLI làm tròn ba số lẻ. Các khoảng detection/recovery là cận theo clock gốc, chưa cộng biên lượng tử ±1 giây. Mọi dòng có luật mục tiêu matched và lifecycle closed.','',
'| Run ID | Problem → Recovery | Incident | Detection [min–max] | CLI elapsed | Recovery recognition [min–max] | Scope | Ảnh event |','|---|---|---:|---|---:|---|---|---|']
for r in rows:
    md.append(f"| [{r['run_id']}](../evidence/week4/official-runs/{r['run_id']}/run.json) | {r['problem_event_id']} → {r['recovery_event_id']} | {r['incident_id']} | {bound(r['detection_delay_min_seconds'],r['detection_delay_max_seconds'])} | {float(r['cli_elapsed_seconds']):.3f} | {bound(r['recovery_recognition_min_seconds'],r['recovery_recognition_max_seconds'])} | {r['http_scope']} | [ảnh](../evidence/week4/closure-20261017/screenshots/event-{r['problem_event_id']}.jpg) |")
md += ['','Các timestamp dưới đây đều ngày **17/10/2026, UTC+7**. `before–after` biểu diễn khoảng thao tác thực tế; không bịa độ chính xác cao hơn timestamp giây. Raw JSON/CSV giữ epoch/UTC để tính lại.','','| Run ID | Fault before–after | Problem | Rollback before–after | Recovery |','|---|---|---|---|---|']
for r in rows:
    md.append(f"| {r['run_id']} | {t(r['fault_before_epoch'])}–{t(r['fault_after_epoch'])} | {t(r['problem_epoch'])} | {t(r['rollback_before_epoch'])}–{t(r['rollback_after_epoch'])} | {t(r['recovery_epoch'])} |")
md += [f'''

## 10. Các trạng thái thiếu dữ liệu cũng là kết quả

18 incident tạo **108 output luật**: {counts['matched']} matched, {counts['not_matched']} not_matched, {counts['insufficient_evidence']} insufficient_evidence. Đây không phải 108 thử nghiệm độc lập và không chứng minh 108 kết luận đúng. Matched gồm 18 luật mục tiêu; không có matched ngoài mục tiêu được ghi nhận. Các not_matched có cả kết quả không áp dụng theo scope, không đồng nghĩa host khỏe.

| Luật được đánh giá | Matched | Not matched | Insufficient evidence | Ghi chú |
|---|---:|---:|---:|---|''']
rules={}
for d in summary['scenarios'].values():
    for rule,statuses in d['all_rule_status_counts'].items(): rules.setdefault(rule,Counter()).update(statuses)
for rule,c in sorted(rules.items()):
    note='R2/R5 trên ba lượt CLI01 absent không được tính TN' if rule.startswith(('R2_','R5_')) else 'Không biến thiếu dữ liệu thành healthy negative'
    md.append(f"| {rule} | {c['matched']} | {c['not_matched']} | {c['insufficient_evidence']} | {note} |")
md += [f'''

R5-02 có R6 phụ `insufficient_evidence` vì span CPU chỉ **239 giây**, dưới tối thiểu 240 giây. Tiêu chí giữ nguyên; không chạy lại engine tới khi kết quả đẹp hơn. Nhiều ca không cung cấp external DNS nên R4 phụ thiếu evidence là phù hợp phạm vi collection, không phải kết luận DNS hỏng. JSON tổng hợp giữ ma trận trạng thái đầy đủ theo scenario.

## 11. Sai lệch, retry và lỗi công cụ đã xử lý

| Vấn đề | Xử lý và ảnh hưởng cách chấm |
|---|---|
| R5-03 watcher hết hạn nhưng fault chưa được chạy | Lệnh injection bị từ chối trước thực thi do giới hạn sử dụng khi duyệt tự động. Giữ `run.json` no_detection gốc và adjudication `aborted_before_fault`; không tính là detection failure, không đưa vào mẫu số fault hợp lệ |
| R5-03-retry1 | Mã mới, fault thật, event 973→974, incident 33; đủ điều kiện như các lượt R5 khác |
| R2-03 có HTTP probe trước event | Giữ `local-http-before-event.json`; diagnosis dùng `local-http.json` mới sau event. Chỉ gọi engine một lần, không chọn lại kết quả |
| CPU history span 239s ở luật phụ | Giữ abstention, không đổi ngưỡng 240s |
| Đối chiếu snapshot cuối ban đầu quá rộng | Giữ snapshot kiểm tra lỗi và giải thích; so đúng phạm vi mới xác nhận unchanged; không sửa cấu hình vận hành |
| Khoảng ngắt do giới hạn sử dụng giữa các lượt | Không gọi là thời gian baseline liên tục; kiểm tra lại preflight/NTP/services trước retry |
| UI khi bổ sung ảnh có cảnh báo sau reboot | Ngoài cửa sổ 00:00–05:00 của 18 lượt, không cộng vào kết quả chính thức hoặc baseline |

Các cảnh báo restart quan sát khi hậu kiểm là event 982 (MON01), 989 (CLI01), 991 (SRV01); có thêm load-high SRV01 event 993 đã resolved lúc 06:20:31 UTC+7. Không tự gọi cảnh báo ngoài kế hoạch là false alert: restart phù hợp trạng thái VM vừa bật; load-high nằm ngoài cửa sổ thử, không được dùng để thay event CPU của R6. Hồ sơ đo cũ giữ nguyên.

Hậu kiểm dashboard cuối lúc `{live['captured_at']}` xác nhận **3 host available, 0 problem trigger mở và 0 item unsupported**. Ảnh `05-dashboard-closure.jpg` cùng `closure-live-status.json` ghi trạng thái này. Cảnh báo sau boot đã tự recovery; không xóa hoặc manual-close để làm dashboard sạch, và không nối khoảng hậu kiểm vào baseline 30 phút.

## 12. Ba nhận xét có bằng chứng

1. **Trigger/cửa sổ chi phối detection:** R3 median 269s, R6 356s; R2 median 10s, R4 77s. Các nhóm dùng chu kỳ/biểu thức khác nhau nên không so như cùng một phép phát hiện. Agent có độ trễ availability rồi cửa sổ ba phút; CPU cần lịch sử cao kéo dài và phụ thuộc pha lấy mẫu. Dùng event thật để tính, không lấy lúc nhìn thấy CPU cao làm event time.
2. **Observer tách hai tổ hợp lỗi HTTP:** R2-01 local HTTP refused, R5-01 local HTTP200 khi remote thất bại; fault log/nft counters là kiểm chứng độc lập. Luật phân biệt được các tổ hợp này trong lab, nhưng output R5 vẫn chỉ nghi ngờ lọc/đường truy cập, chưa tự chứng minh riêng firewall là nguyên nhân.
3. **Abstention bảo toàn tính trung thực:** R5-02 span 239s chưa đủ ngưỡng nên giữ thiếu evidence; R6-01 span 241s, mean CPU100%, load1 và một vCPU nên matched. Chất lượng cửa sổ dữ liệu là một phần kết quả, không phải phần có thể bỏ để tăng tỷ lệ đẹp.

## 13. Ảnh minh chứng và cách đọc

Đã bổ sung **18 ảnh chi tiết event lịch sử**, mỗi ảnh ánh xạ đúng một problem ID trong bảng Run ID; thêm ảnh bảng lịch sử đầu/cuối, dashboard và ba host. `screenshots-index.json` ghi URL nguồn, thời điểm chụp và row lịch sử; `history-ui-rows.json` giữ 18 dòng UI đã resolved và timezone Asia/Bangkok. Đã đối chiếu tập event ID bằng audit, không chỉ đếm ảnh.

![Lịch sử thực nghiệm — phần đầu](../evidence/week4/closure-20261017/screenshots/02-history-top.jpg)

![Lịch sử thực nghiệm — phần cuối](../evidence/week4/closure-20261017/screenshots/03-history-bottom.jpg)

![Ví dụ chi tiết R6-03 / event 979](../evidence/week4/closure-20261017/screenshots/event-979.jpg)

Ảnh được chụp **sau đợt đo**, không hồi tố thành ảnh active fault. `Operational data` trên trang event có thể là giá trị **hiện tại** (ví dụ CPU đã giảm sau rollback), không thay thế CPU history đã thu lúc chẩn đoán. Các cột ngoài viewport được lưu bằng text UI và raw/report đi kèm; không sửa ảnh để làm sai nội dung. Không chụp màn hình nhập mật khẩu hoặc token; không ghi thông tin xác thực vào báo cáo.

## 14. Kiểm tra dữ liệu và backup

Đã chạy lại `verify_experiment.py` khi đóng tuần: 18 Run ID, 18 problem ID, 18 incident ID riêng; cặp problem/recovery đúng trigger/value/link; report, CSV và lifecycle nhất quán; history không trùng `(itemid, clock, ns)`; không có trigger event bổ sung cần phân loại trong các cửa sổ đã xuất.

- **535 file** trong `official-runs/checksums-final.json` và **43 file** trong baseline `checksums.json` khớp SHA256 (578 file trong hai manifest).
- Source và bốn file export/phiếu thử Windows khớp hash đầu phiên; Git không ghi nhận thay đổi source engine để đóng hồ sơ.
- Snapshot cuối: 0 problem mở tại thời điểm kết thúc đo; SQLite integrity `ok`; 36 incidents, 268 evidence, 154 diagnoses, 26 recoveries toàn DB, có cả lịch sử trước đợt chính thức.
- Backup cuối: `evidence/week4/official-runs/final-state-20261016T214108Z/diagnosis-final.db`.
- SHA256 backup: `{state['db_sha256']}`.
- Đã sao chép backup sang file scratch độc lập để kiểm tra: integrity `ok`, foreign key không vi phạm, module `report.load_report` tái tạo đúng **18/18 report** và bằng JSON đã chốt. Đây là thử sử dụng bản phục hồi SQLite, không phải diễn tập khôi phục toàn bộ VM/MySQL.
- Scan exact current API token trong 570 file evidence ở mốc cuối đợt đo có 0 hit; không chứng nhận token cũ hoặc toàn bộ lịch sử Git không từng lộ. Thông tin đăng nhập dùng khi bổ sung ảnh không được đưa vào file/tài liệu.

Backup database giữ cục bộ, `.gitignore` loại `.db`; checksum và report được commit. Clone Git không tự mang theo các backup `.db`: cần lấy file backup từ nơi lưu trước khi kiểm tra đầy đủ manifest. Hai bản Windows/MON01 trên cùng laptop không thay thế backup độc lập ngoài thiết bị. Export YAML chỉ mô tả host/template, không phải toàn bộ MySQL Zabbix hoặc daemon/global settings.

Manifest cũ R1–R2/R1–R3 là checkpoint sớm; một số bảng dẫn xuất/công cụ có bản mới sau đó. Dùng `checksums-final.json` cho cây dữ liệu chốt cuối. Hồ sơ bổ sung ảnh/nghiệm thu nằm trong `closure-20261017`, có manifest riêng để không sửa byte bộ đo đã freeze.

## 15. Đường dẫn bàn giao

| Đầu ra | Đường dẫn tính từ project |
|---|---|
| File tổng hợp này | `docs/TONG_HOP_TUAN_4.markdown` |
| Baseline mới | `evidence/week4/baseline-20261016T162549Z/` |
| Raw và report 18 lượt | `evidence/week4/official-runs/R*/` |
| CSV một dòng/lượt | [all-trials.csv](../evidence/week4/official-runs/all-trials.csv) |
| Thống kê/công thức/status matrix | [experiment-summary.json](../evidence/week4/official-runs/experiment-summary.json) |
| Biểu đồ PNG/SVG/PDF | `evidence/week4/official-runs/figures/` |
| Phụ lục vận hành/sai lệch | [PHU_LUC_VAN_HANH_THUC_NGHIEM.md](../evidence/week4/official-runs/PHU_LUC_VAN_HANH_THUC_NGHIEM.md) |
| Công cụ ghi/chấm/phân tích phiên | `evidence/week4/official-runs/tools/` — bản cuối; không nhầm checkpoint tool cũ ở thư mục cha |
| Ảnh và text UI hậu kiểm | `evidence/week4/closure-20261017/screenshots/` |
| Audit đóng tuần/backup phục hồi | [closure-audit.json](../evidence/week4/closure-20261017/closure-audit.json) |
| Chương 2/3 bản thảo | [Chương 2](CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md), [Chương 3](CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md) |
| Demo 10 phút | [KICH_BAN_DEMO_10_PHUT.md](KICH_BAN_DEMO_10_PHUT.md) |

Trên MON01, engine ở `/home/phat/do-an/diagnosis-engine`; evidence ở `/home/phat/do-an/evidence/week4/`. Lệnh minh họa report lịch sử (không chạy lại diagnosis cho event đã đóng):

```bash
cd ~/do-an/diagnosis-engine
.venv/bin/python report.py --incident-id 36 --format md
```

Không tái dùng Run ID cũ hoặc bỏ marker để tạo thử mới trong cùng thư mục raw. Muốn thu phiên mới phải có ID/root phiên mới và công bố phiên bản/điều kiện tương ứng.

## 16. Giới hạn phải giữ trong báo cáo và bảo vệ

- Chỉ một lab trên cùng laptop, ba lượt mỗi loại; chưa có tập kiểm tra âm/host/topology độc lập, nhiều fault đồng thời hoặc phân bố tải nền đa dạng.
- Baseline 30 phút 06 giây là ngoại lệ được chọn, chưa đáp ứng mục tiêu 4 giờ; không chứng minh độ ổn định dài hạn hoặc engine false-positive rate.
- Mean CPU là trung bình số học các mẫu, chưa là tích phân có trọng số thời gian. Trigger CPU phụ thuộc load-high; bộ một worker chưa bao phủ trường hợp master dependency trở thành problem và ảnh hưởng event CPU.
- Timestamp event/fault có độ phân giải giây, NTP synchronized không chứng minh clock offset bằng 0. Các con số CLI ba số lẻ không làm thời điểm fault chính xác đến mili giây.
- R2/R5 absent không tính TN; insufficient_evidence không biến thành healthy. 18/18 trên luật mục tiêu khác với accuracy trên lưu lượng vận hành.
- Screenshot hậu kiểm bổ sung khả năng trình bày, không thay thế raw probe/CPU history lúc fault. Không được dùng operational data hiện tại của UI để viết lại evidence lịch sử.
- Backup cùng laptop chưa chống mất/hỏng thiết bị; chưa diễn tập phục hồi toàn bộ Zabbix/MySQL hoặc toàn lab.

## 17. Chuyển sang tuần 5

Phần **thiết kế, đo, rà dữ liệu và tổng hợp tuần 4 đã chốt trong phạm vi baseline ngắn đã thống nhất**. Không còn thiếu lượt fault hợp lệ hoặc ảnh lịch sử của 18 problem. Mục tiêu baseline bốn giờ được giữ là hạn chế, không đánh dấu đã đo đủ.

Các đầu ra hỗ trợ tuần 5 đã có: dữ liệu sạch, median/min/max, hai biểu đồ, ba nhận xét, bản thảo Chương 2–3, README và kịch bản demo. Các việc sau **chưa được chứng nhận hoàn tất**:

1. Ghép Chương 1–3 theo mẫu trường; rà thuật ngữ, hình, tài liệu tham khảo và nội dung bảo vệ.
2. Làm slide; diễn tập demo ba lần sau reboot, ghi thời lượng/event/incident mới và rollback. Việc có script không đồng nghĩa đã diễn tập thành công.
3. Backup độc lập ngoài laptop; kiểm tra bộ nộp bao gồm repository, SQLite, cấu hình Zabbix, báo cáo và slide.
4. Kiểm tra tổng thể và tạo release cuối sau diễn tập. Các commit được ghi là local; không tuyên bố đã push khi chưa có output push thành công.

Biên bản shutdown lúc 17/10/2026 05:15 UTC+7 ghi cả ba VM poweroff sau đợt đo; khi bổ sung hồ sơ lần này, cả ba đã được bật lại từ trước. Không dùng biên bản shutdown cũ để mô tả trạng thái live hiện tại. Những cảnh báo mới sau reboot được ghi riêng, không sửa baseline hoặc 18 trial đã kết thúc.
''']
path=project/'docs/TONG_HOP_TUAN_4.markdown'
path.write_text('\n'.join(md),encoding='utf-8')
print(path)
print('Total output rule statuses:',dict(counts))

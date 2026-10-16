"""Write a traceable report draft only after the valid-fault dataset is complete."""
import csv
import json
from pathlib import Path
import sys

project=Path(sys.argv[1])
root=project/'evidence/week4/official-runs'
s=json.loads((root/'experiment-summary.json').read_text())
assert s['complete_18_valid_faults']
rows=list(csv.DictReader((root/'all-trials.csv').open(encoding='utf-8')))
docs=project/'docs'
docs.mkdir(exist_ok=True)
def interval(d):
    return f"{d['median']:.3f} [{d['min']:.3f}–{d['max']:.3f}]" if d['n'] else 'NA'
md=['# Chương 3. Thực nghiệm và đánh giá', '',
'Bản thảo từ bộ dữ liệu chính thức ngày 16–17/10/2026. Các số được tạo từ `all-trials.csv` và `experiment-summary.json`, không lấy từ dry run hoặc số unit test. Cần ghép vào mẫu báo cáo của trường trước khi nộp.', '',
'## 3.1. Mục tiêu và môi trường', '',
'Thực nghiệm đánh giá khả năng Zabbix phát hiện sáu điều kiện lỗi trong lab, khả năng luật mục tiêu của module Python khớp evidence khi fault còn tồn tại, và khả năng lưu recovery đúng liên kết event. Lab gồm MON01, SRV01 và CLI01 trên cùng laptop VirtualBox như Chương 2. Không có tập host độc lập hoặc đánh giá vận hành doanh nghiệp.', '',
'Source tham chiếu `ca04071`, export cấu hình `978b4f9`, phiếu thử `4cabeb0`. Trước đợt đo đã lưu snapshot hiệu lực, macro/template bổ sung, thông số runtime và hash source/tests. Trước mỗi trial, bộ ghi đối chiếu hash engine. Engine, trigger và sampling không được sửa giữa các lượt để khớp kết quả.', '',
'Mốc kiểm tra trước baseline có 280 tests passed. Đây là kiểm tra module, tách biệt khỏi kết quả 18 lượt fault thật. Các công cụ điều khiển fault/ghi thử không phải chức năng tự khắc phục của engine.', '',
'## 3.2. Baseline và điều kiện trước thử', '',
'Baseline mới bắt đầu 16/10/2026 16:26:08 UTC, kết thúc 16:56:14 UTC, tương ứng 23:26:08–23:56:14 UTC+7: tổng cộng 1.806 giây (30 phút 06 giây). Theo lựa chọn phiên ngắn, không gọi đây là baseline bốn giờ. Có 31 poll, 963 history rows của 28 item; đã đối chiếu lịch sử event, khoảng lấy mẫu, item errors và uptime. Không thấy problem mới trong cửa sổ quan sát đã kiểm tra.', '',
'Tần suất problem mới quan sát trong baseline là 0 / (1806/3600) = 0 sự kiện/giờ trong đúng cửa sổ ngắn này. Không có event để phân loại false alert; số 0 không ước lượng chắc chắn rủi ro dài hạn. Engine là CLI, không chạy liên tục trên tập âm nên baseline Zabbix không cung cấp tỷ lệ chẩn đoán sai của engine.', '',
'Trước mỗi fault, kiểm tra host reachable, HTTP 200, service đang chạy và không có problem nền trên host mục tiêu. Các VM báo NTP synchronized; chưa đo chính xác sai số clock giữa các VM. Trước lượt CPU tiếp theo, chờ history năm phút không còn mẫu CPU cao và không còn problem; lưu riêng bằng chứng precondition.', '',
'## 3.3. Sáu kịch bản và quy trình', '',
'| Kịch bản | Fault thực thi | Observer/đích và đối chứng | Rollback |',
'|---|---|---|---|',
'| R1 | Ngắt enp0s8 của SRV01 | MON01 → SRV01; CLI01 đối chứng cùng subnet | Timer bật lại card, có failsafe riêng |',
'| R2 | Dừng Nginx SRV01 | MON01 đo ping/TCP; SRV01 đo local HTTP | Start Nginx |',
'| R3 | Dừng Agent 2 SRV01 | MON01 đo ping, TCP10050 và agent history | Start Agent 2; chờ telemetry mới và recovery |',
'| R4 | Chặn UDP/TCP đích 53 tại output CLI01 | CLI01 đo example.com và ping 1.1.1.1; HTTP scope absent | Xóa đúng bảng nft riêng |',
'| R5 | Chặn TCP80 từ MON01 tại input SRV01 | MON01 đo remote; SRV01 đo HTTP trên IP dịch vụ | Xóa đúng bảng nft riêng |',
'| R6 | stress-ng, một worker CPU 100%, timeout 12 phút | History CPU/load của SRV01, một vCPU | Dừng đúng PID, xác nhận không còn worker |', '',
'R1 không mô phỏng đầy đủ mất nguồn VM; R4 không chứng minh resolver upstream hỏng; R5 dùng phương án firewall thay gateway theo phạm vi đã chốt. Vì vậy kết quả chỉ kiểm chứng những fault đã thực thi.', '',
'Mỗi lượt ghi timestamp trước/sau gây lỗi trên VM độc lập với MON01. Bộ ghi poll API khoảng năm giây, nhận đúng trigger đã chọn, chạy engine một lần, chờ recovery, đồng bộ SQLite và xuất report. Với R2/R5, HTTP JSON được thu tại SRV01 sau event; với R4, DNS và IP control được thu cùng observer CLI01 sau event. Các file phải còn fresh khi collection bắt đầu.', '',
'Có một lần R5-03 được tạo watcher nhưng lệnh gây fault bị chặn trước thực thi vì giới hạn sử dụng ở bước duyệt tự động. Hồ sơ timeout giữ nguyên, kèm adjudication `aborted_before_fault`; R5-03-retry1 là fault trial mới có mã riêng. Không tính lần bị hủy vào mẫu số detection. R2-03 có probe trước event được giữ riêng, còn diagnosis dùng probe mới sau event; engine không được chạy lại để chọn kết quả đẹp.', '',
'## 3.4. Chỉ số và cách chấm', '',
'- Detection rate = số fault hợp lệ có đúng problem / tổng fault hợp lệ.',
'- Target diagnosis success end-to-end = số fault hợp lệ có luật mục tiêu matched bằng evidence và hồ sơ qua kiểm tra / tổng fault hợp lệ. No detection, engine error và insufficient_evidence không bị loại khỏi mẫu số.',
'- Detection time nằm giữa `problem_clock − fault_after` và `problem_clock − fault_before`. Các timestamp có độ phân giải một giây; CSV bổ sung biên ±1 giây cho lượng tử hóa, chưa gồm sai số NTP chưa đo.',
'- CLI elapsed đo bằng monotonic clock từ khi gọi app tới khi kết thúc, gồm API, collection, luật và SQLite; không phải thời gian suy luận thuần túy.',
'- Recovery recognition nằm giữa `recovery_clock − rollback_after` và `recovery_clock − rollback_before`. Khoảng problem–recovery không phải downtime thật.',
'- Chỉ ba lượt mỗi loại: báo từng giá trị, median, min, max và cỡ mẫu; không suy ra độ tin cậy doanh nghiệp. Không có tập âm nên không tính specificity/accuracy có TN. HTTP scope absent và evidence thiếu không được tính thành healthy negative.', '',
'## 3.5. Kết quả', '',
'| Scenario | Fault hợp lệ | Detection | Target success | Abstention mục tiêu | Detection median [min–max] s | CLI median [min–max] s |',
'|---|---:|---:|---:|---:|---|---|']
for scenario,d in s['scenarios'].items():
    md.append(f"| {scenario} | {d['valid_faults']} | {d['detected']}/{d['valid_faults']} | {d['target_success_end_to_end']}/{d['valid_faults']} | {d['target_abstentions']} | {interval(d['detection_delay_lower_seconds'])} | {interval(d['cli_elapsed_seconds'])} |")
detected=sum(d['detected'] for d in s['scenarios'].values())
success=sum(d['target_success_end_to_end'] for d in s['scenarios'].values())
md += ['',f'Tổng cộng detection {detected}/18 và target success end-to-end {success}/18 trong bộ fault hợp lệ này. Số đếm này chỉ đo luật mục tiêu trên các lỗi được tạo; không phải accuracy phân loại trên lưu lượng vận hành bình thường.', '',
'![Từng thời gian phát hiện và CLI](../evidence/week4/official-runs/figures/thoi-gian-phat-hien-va-cli.png)', '',
'![Kết quả luật mục tiêu](../evidence/week4/official-runs/figures/ket-qua-luat-muc-tieu.png)', '',
'Bảng dùng cận dưới detection theo clock; CSV giữ cả cận trên và sai số lượng tử. Vạch median chỉ mô tả ba điểm, không phải ước lượng có khoảng tin cậy. Các file SVG/PDF tương ứng dùng để đưa hình vào bản nộp.', '',
'## 3.6. Ba nhận xét dựa trên dữ liệu', '',
f"1. Cơ chế trigger ảnh hưởng lớn tới detection. R3 có median {s['scenarios']['R3']['detection_delay_lower_seconds']['median']:.0f} giây, so với R2 {s['scenarios']['R2']['detection_delay_lower_seconds']['median']:.0f} giây và R4 {s['scenarios']['R4']['detection_delay_lower_seconds']['median']:.0f} giây. R3 phải chờ availability và cửa sổ ba phút; không thể so độ trễ các nhóm như thể chúng dùng cùng chu kỳ và biểu thức.",
'2. Remote HTTP thất bại chưa đủ phân biệt lỗi service với lọc truy cập. R2-01 có local HTTP refused; R5-01 có local HTTP 200 trong khi bảng nft độc lập ghi rule chặn MON01. Luật phân biệt được hai tổ hợp evidence trong các lượt này, nhưng riêng output R5 vẫn chỉ là nghi ngờ filtering/đường truy cập, chưa tự đọc firewall hoặc xác định chính xác nguyên nhân.',
'3. Chất lượng và cửa sổ dữ liệu là một phần kết quả. R5-02 có R6 phụ insufficient_evidence vì CPU history span 239 giây thay vì tối thiểu 240 giây; không sửa luật hoặc chạy lại engine để loại kết quả này. Trong R6-01, history đạt span 241 giây, mean CPU 100%, load 1 và một vCPU nên luật mục tiêu matched. Cần phân biệt abstention do độ phủ dữ liệu với bằng chứng host khỏe.', '',
'## 3.7. Giới hạn và việc chưa được chứng minh', '',
'Lab dùng một laptop, một topology nhỏ và ba lượt lặp cho mỗi fault, không có tập kiểm tra độc lập. Lượt CPU có nghỉ giữa các fault nhưng vẫn cùng host và cấu hình; chưa đánh giá phân bố tải nền khác, jitter lớn, packet loss hỗn hợp hoặc nhiều fault đồng thời. Baseline ngắn chưa đủ phản ánh hoạt động qua đêm hoặc nhiều ngày.', '',
'R6 cho thấy CPU/load cao theo luật, chưa chứng minh tác động ứng dụng vì chưa có đối chứng response-time đầy đủ. Dữ liệu CPU count có heartbeat một ngày; tuổi mẫu lớn không tự là mất giám sát nếu phù hợp preprocessing. Các luật ngoài mục tiêu có insufficient_evidence được giữ trong JSON; không đếm thành true negative.', '',
'Mean CPU của luật là trung bình số học các mẫu, chưa dùng trọng số theo khoảng thời gian. Trigger CPU còn có dependency với load-high; bộ thử một worker chưa bao phủ trường hợp load-high trở thành problem và ảnh hưởng event CPU. Không suy rộng ba lượt này thành phát hiện mọi tình huống quá tải hoặc mọi tổ hợp trigger.', '',
'Dữ liệu thô và event API thay cho việc chép tay số từ dashboard. Bộ này chưa cung cấp trọn bộ screenshot dashboard/Problems đã che thông tin theo mẫu nộp. Chưa chứng nhận ba lần demo thành công sau reboot, chưa tạo release cuối, và chưa có backup độc lập ngoài laptop. Đây là công việc hoàn thiện tuần 5.', '',
'## 3.8. Truy vết từng lượt', '',
'| Run ID | Problem → Recovery | Incident | Luật mục tiêu | Hồ sơ |',
'|---|---|---:|---|---|']
for r in rows:
    md.append(f"| {r['run_id']} | {r['problem_event_id']} → {r['recovery_event_id']} | {r['incident_id']} | {r['target_diagnosis_status']} | [raw](../evidence/week4/official-runs/{r['run_id']}/run.json) |")
md += ['', '[CSV toàn bộ lượt](../evidence/week4/official-runs/all-trials.csv) · [JSON công thức, cỡ mẫu và thống kê](../evidence/week4/official-runs/experiment-summary.json) · [Phụ lục vận hành](../evidence/week4/official-runs/PHU_LUC_VAN_HANH_THUC_NGHIEM.md)', '']
(docs/'CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md').write_text('\n'.join(md),encoding='utf-8')
print(docs/'CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md')

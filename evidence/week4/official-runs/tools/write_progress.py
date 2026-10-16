"""Journal entry generated from final reviewed evidence, not planned deadlines."""
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sys

project=Path(sys.argv[1])
root=project/'evidence/week4/official-runs'
summary=json.loads((root/'experiment-summary.json').read_text())
verification=json.loads((project/'docs/KIEM_TRA_DU_LIEU_20261017.json').read_text(encoding='utf-8-sig'))
assert summary['complete_18_valid_faults'] and verification['result']=='PASS'
folder=sorted(root.glob('final-state-*'))[-1]
state=json.loads((folder/'summary.json').read_text())
scan=json.loads((folder/'credential-scan.json').read_text())
assert all(state[k] for k in ('source_unchanged','config_unchanged','trigger_functions_unchanged','critical_thresholds_unchanged','template_links_unchanged','critical_global_overrides_absent'))
now=datetime.now(timezone(timedelta(hours=7))).isoformat(timespec='seconds')
md=['# Báo cáo tiếp tục roadmap — 17/10/2026', '',f'Cập nhật thực tế: {now}. Project: `C:\\Users\\Darrys\\do-an`. Tài liệu D: là nhật ký lưu trữ; bộ evidence/code hiện hành nằm trong project này và bản sao MON01.', '',
'## Kết quả đã kiểm chứng', '',
'Đã có 18 fault hợp lệ, ba lượt mỗi R1–R6, cùng một phiên bản engine/trigger/sampling. R5-03 bị hủy trước fault do giới hạn sử dụng ở bước duyệt lệnh, giữ riêng adjudication; R5-03-retry1 là lượt thật tiếp theo. Không bỏ kết quả timeout gốc và không tính nó như một lỗi phát hiện.', '',
'| Scenario | Detection | Target success end-to-end | Abstention mục tiêu | Review issues |',
'|---|---:|---:|---:|---:|']
for scenario,data in summary['scenarios'].items():
    md.append(f"| {scenario} | {data['detected']}/{data['valid_faults']} | {data['target_success_end_to_end']}/{data['valid_faults']} | {data['target_abstentions']} | {len(data['review_issues'])} |")
md += ['',
'Source `ca04071`, config export `978b4f9`, protocol `4cabeb0`. Hash source/tests, cấu hình hiệu lực, trigger functions, critical macros và template links cuối phiên đều khớp snapshot đầu phiên. Không sửa luật hoặc trigger để làm đẹp số liệu. Mốc trước baseline có 280 tests passed; không dùng số tests thay số lượt thực nghiệm.', '',
'Baseline mới: 16/10/2026 16:26:08–16:56:14 UTC, 1.806 giây, 31 poll, 963 history rows / 28 item, không có problem mới trong cửa sổ đã rà lịch sử. Phiên cũ dừng sớm riêng là 158 giây. Không gọi hai phiên này thành một baseline bốn giờ.', '',
f"Kiểm tra cuối: {state['open_problem_count']} problem mở; SQLite integrity `{state['sqlite_integrity_check']}`; exact current API token scan có {scan['hit_count']} hit trong {scan['files_scanned']} file evidence đã quét. Scan này không chứng nhận toàn bộ token cũ hoặc lịch sử Git.", '',
f"Đối chiếu bản sao: {verification['unique_problem_ids']} problem ID và {verification['unique_incident_ids']} incident ID riêng; {verification['checksum_files_verified']['checksums-final.json']} file checksum cuối và {verification['checksum_files_verified']['checksums.json']} file baseline khớp SHA256. Không có trigger event bổ sung trong các cửa sổ đã xuất cần phân loại.", '',
f"SQLite backup cuối: `../evidence/week4/official-runs/{folder.name}/diagnosis-final.db`; SHA256 `{state['db_sha256']}`. Bản backup nhất quán và bộ dữ liệu được giữ ở MON01 và Windows. Đây vẫn là hai nơi trên cùng laptop, chưa phải backup độc lập ngoài thiết bị.", '',
'## Đầu ra và tiến độ roadmap', '',
'- [Bảng tổng hợp](../evidence/week4/official-runs/TONG_HOP_THUC_NGHIEM_TUAN4.md), [CSV 18 lượt](../evidence/week4/official-runs/all-trials.csv), [JSON công thức/thống kê](../evidence/week4/official-runs/experiment-summary.json).',
'- Log fault/rollback, event/recovery API, history CSV, external probe, CLI và report trong từng Run ID; source công cụ cuối trong `official-runs/tools`.',
'- [Chương 2](CHUONG_2_KIEN_TRUC_VA_TRIEN_KHAI.md) và [Chương 3](CHUONG_3_THUC_NGHIEM_VA_DANH_GIA.md) là bản thảo kỹ thuật. Có hai biểu đồ PNG/SVG/PDF từ chính CSV và kịch bản [demo 10 phút](KICH_BAN_DEMO_10_PHUT.md). README đã cập nhật theo hệ thống thật.',
'- Phần đo, rà và tổng hợp tuần 4 đã có dữ liệu. Đã tiến sang phần làm sạch/bảng/hình tuần 5; Chương 2/3 và demo đang ở mức bản thảo, chưa phải bản nộp đã duyệt.', '',
'## Những giới hạn cần giữ khi bảo vệ', '',
'N=3 mỗi loại trên một lab; target success trên fault khác với accuracy có true negatives. HTTP absent không được tính TN; luật thiếu dữ liệu không được tính khỏe. R5-02 có R6 phụ insufficient_evidence vì CPU span 239 giây <240; giữ nguyên kết quả. Trigger CPU có dependency load-high, bộ một worker chưa bao phủ mọi tổ hợp tải/trigger. R6 chưa có đủ đối chứng response-time để chứng minh tác động ứng dụng.', '',
'R1 là ngắt Host-only, R4 là chặn đường DNS, R5 là firewall HTTP; không mô tả thành đã kiểm chứng tắt nguồn VM, resolver upstream hỏng hay gateway chung. Detection time, CLI elapsed và recovery recognition là ba phép đo riêng; problem–recovery không phải downtime thật.', '',
'## Công việc tiếp theo', '',
'1. Ghép Chương 1 với hai bản thảo theo mẫu trường; rà bảng/hình và bổ sung screenshot dashboard/Problems có timestamp, che thông tin cần thiết.',
'2. Chuẩn bị slide và diễn tập demo ba lần sau reboot; mỗi lần có log, event/incident mới, thời lượng và xác nhận rollback. Chưa chạy các lần diễn tập này.',
'3. Backup độc lập ngoài laptop, gồm repository, SQLite, cấu hình Zabbix và bản báo cáo; xác minh khả năng phục hồi. Export YAML không thay thế toàn bộ MySQL Zabbix.',
'4. Sau khi các bước trên đạt mới đóng gói và tạo release cuối. Chưa công bố đã push hoặc đã hoàn thành bản nộp.', '']
path=project/'docs/BAO_CAO_TIEN_DO_20261017.md'
path.write_text('\n'.join(md),encoding='utf-8')
print(path)

# Kết quả baseline ngắn — 16/10/2026

- Đánh giá: **accepted_short_baseline**.
- Bắt đầu: 16/10/2026 23:26:08 UTC+7; kết thúc: 16/10/2026 23:56:14 UTC+7.
- Thời lượng quan sát: **1806 giây (30 phút 06 giây)**; mục tiêu đã đổi thành 30 phút theo lựa chọn người thực hiện.
- `session.json` giữ nguyên mục tiêu bốn giờ ban đầu và `stopped_early=true`; `short-session-plan.json` ghi yêu cầu thay đổi. Bản tóm tắt này đánh giá theo mục tiêu mới, không sửa bản ghi gốc.
- 31 lần thu, 0 lỗi API; khoảng cách lớn nhất 62 giây.
- 963 mẫu history, 28 item; 0 event mới; 0 problem mới.
- Không có problem mở đầu/cuối phiên hoặc trong các lần kiểm tra; không có cảnh báo mới cần phân loại. Tần suất cảnh báo sai quan sát được: 0 / 0,5017 giờ, không suy rộng ra dài hạn.
- Source, cấu hình snapshot, hàm trigger bổ sung, các ngưỡng quan trọng và liên kết template không đổi ở các lần đối chiếu.

## Kiểm tra liên tục

| Host | Item | Số mẫu | Gap lớn nhất (s) | Ghi chú |
|---|---|---:|---:|---|
| MON01 | `agent.ping` | 30 | 60 | Đã đối chiếu |
| MON01 | `system.uptime` | 60 | 32 | Đã đối chiếu |
| MON01 | `system.cpu.load[all,avg1]` | 31 | 62 | Đã đối chiếu |
| MON01 | `system.cpu.num` | 0 | NA | discard unchanged; heartbeat 1d |
| MON01 | `system.cpu.util[,idle]` | 30 | 61 | Đã đối chiếu |
| MON01 | `zabbix[host,agent,available]` | 30 | 60 | Đã đối chiếu |
| MON01 | `system.cpu.util` | 30 | 61 | Đã đối chiếu |
| MON01 | `vm.memory.util` | 30 | 61 | Đã đối chiếu |
| SRV01 | `agent.ping` | 30 | 62 | Đã đối chiếu |
| SRV01 | `system.cpu.load[all,avg1]` | 30 | 63 | Đã đối chiếu |
| SRV01 | `system.cpu.num` | 0 | NA | discard unchanged; heartbeat 1d |
| SRV01 | `system.cpu.util[,idle]` | 30 | 61 | Đã đối chiếu |
| SRV01 | `system.uptime` | 60 | 32 | Đã đối chiếu |
| SRV01 | `zabbix[host,agent,available]` | 30 | 61 | Đã đối chiếu |
| SRV01 | `system.cpu.util` | 30 | 61 | Đã đối chiếu |
| SRV01 | `vm.memory.util` | 30 | 62 | Đã đối chiếu |
| CLI01 | `agent.ping` | 31 | 60 | Đã đối chiếu |
| CLI01 | `system.cpu.load[all,avg1]` | 30 | 62 | Đã đối chiếu |
| CLI01 | `system.cpu.num` | 0 | NA | discard unchanged; heartbeat 1d |
| CLI01 | `system.cpu.util[,idle]` | 30 | 62 | Đã đối chiếu |
| CLI01 | `system.uptime` | 60 | 31 | Đã đối chiếu |
| CLI01 | `zabbix[host,agent,available]` | 30 | 60 | Đã đối chiếu |
| CLI01 | `system.cpu.util` | 30 | 62 | Đã đối chiếu |
| CLI01 | `vm.memory.util` | 30 | 61 | Đã đối chiếu |
| SRV01 | `web.test.fail[SRV01 HTTP]` | 60 | 33 | Đã đối chiếu |
| SRV01 | `web.test.rspcode[SRV01 HTTP,Homepage]` | 60 | 33 | Đã đối chiếu |
| SRV01 | `web.test.time[SRV01 HTTP,Homepage,resp]` | 60 | 33 | Đã đối chiếu |
| CLI01 | `net.dns[,example.com,A,2,1,udp]` | 61 | 31 | Đã đối chiếu |

Không phát hiện uptime reset, chênh lệch uptime bất thường hoặc khoảng trống vượt chu kỳ + 5 giây trong các item định kỳ đã kiểm tra. Ba item CPU count không lưu lại giá trị không đổi; retained value hợp lệ và còn trong heartbeat một ngày.

## Giới hạn và việc tiếp theo

Đây là baseline ngắn, chưa đạt mục tiêu bốn giờ của roadmap. Kết quả chỉ áp dụng cho cửa sổ quan sát và độ phân giải lấy mẫu. Baseline Zabbix không đo độ chính xác hoặc tỷ lệ chẩn đoán sai của engine CLI.

Tiếp theo: giữ nguyên phiên bản đã ghi, thực hiện R1–R3 mỗi kịch bản ba lượt rồi R4–R6 mỗi kịch bản ba lượt theo phiếu. Hiện bộ thực nghiệm chính thức vẫn 0/18. Giữ cả lượt không phát hiện, thiếu bằng chứng hoặc chẩn đoán không đạt.

Dữ liệu gốc: `session.json`, `short-session-plan.json`, `observations.jsonl`, `events.json`, `history.csv`. Tổng hợp: `baseline.csv`, `continuity.csv`, `baseline-summary.json`.

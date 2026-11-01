# Đợt pilot đầu: bảy trạng thái

Có 10 attempt: 7 hợp lệ và 3 uncertain, giữ nguyên log. CSV gồm một cửa sổ cuối cho mỗi lượt hợp lệ thuộc pilot-v2-s01.

| label | ping_status | tcp80_status | tcp10050_status | local_http_status | dns_status | agent_status | cpu_mean |
|---|---|---|---|---|---|---|---|
| healthy | success | success | success | http_200 | success | success | 9.8652214 |
| cpu_stress | success | success | success | http_200 | success | success | 100.0 |
| dns_egress_blocked | success | success | success | http_200 | timeout | success | 10.149204600000004 |
| remote_http_filtered | success | timeout | success | http_200 | success | success | unknown |
| agent_stopped | success | success | refused | http_200 | success | no_data | unknown |
| interface_down | no_reply | unknown | timeout | unknown | unknown | success | unknown |
| nginx_stopped | success | refused | success | failed | success | success | unknown |

Kho evidence toàn bộ có 24 windows, gồm smoke và lượt Nginx cũ; không gọi là 24 sự cố độc lập.

Chỉ có một lượt hợp lệ mỗi trạng thái trong block mới. Đây là pilot kiểm tra protocol, không phải tập test độc lập và chưa được dùng công bố accuracy.

Source errors HTTP/DNS ở interface-down được giữ thật: observer mất kết nối nên không đo được. Không đổi chúng thành HTTP/DNS đã thất bại.

Các attempt uncertain còn nguyên; retry có parent và ID riêng. Lượt CPU có lỗi cleanup timer sau khi đã khôi phục, đã được review riêng cùng log lỗi. Cơ chế dọn timer và kiểm tra thứ tự thời gian đã được bổ sung kiểm thử hồi quy.

Code để tiếp tục: run_pilot.py; đọc README.md về resume, batch và retry. Lịch đầy đủ vẫn là 42 lượt; vòng hiện tại mới hoàn thành lượt đầu của bảy trạng thái trong session 1.

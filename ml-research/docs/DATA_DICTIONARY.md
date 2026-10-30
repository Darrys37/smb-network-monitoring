# Data dictionary v2.0

Một observation là cửa sổ thu có thời điểm kết thúc `decision_time`, không phải snapshot nguyên tử. Tệp observation chứa schema_version=2, session_id/run_id/window_id, collector_version, profile, started_at/decision_time, sources và evidence. Nhãn bị cấm ở profile và observation.

| Trường | Kiểu/ý nghĩa | Vai trò |
|---|---|---|
| session_id/run_id/window_id | ID an toàn, tối đa 80 ký tự | Chia nhóm/audit; không predictor |
| profile.host_id/target_ip | Danh tính Zabbix/IP, phải xác minh API mapping | Thu dữ liệu; không predictor ID |
| profile.http_service | expected hoặc absent | Scope xác định trước, không phụ thuộc fault |
| profile.observer | Host thực hiện HTTP/DNS | Bảo đảm đúng góc nhìn |
| profile.control_ip | Peer khác target | Không gọi là parent/gateway |
| profile.topology_version | Phiên bản topology | Chia tập/audit |
| sources | monitor/local_http/dns; ok/error/not_applicable | Giữ lỗi nguồn và exception class, không log secret |
| evidence.check_type/target | Kiểu phép đo và đích | Dựng feature |
| evidence.collected_at | Unix giây của phép thu | Không được sau decision_time |
| evidence.result.sample_clock | Thời điểm mẫu metric nếu có | Tính tuổi mẫu, kiểm tra pre-fault |
| evidence.result | Kết quả gốc, units, observer, trạng thái và history | Nguồn feature, chưa phải predictor đã chuẩn hóa |

Monitor thu ping target, TCP80, TCP10050, sáu item/CPU history của engine và ping control. HTTP local chạy tại target nếu profile expected. DNS và IP control luôn được thu tại target observer ở cả healthy lẫn mọi fault. Đây là đổi protocol có chủ ý so với dữ liệu cũ chỉ dùng DNS observer CLI01.

Feature tương lai: ICMP; TCP; HTTP; DNS; CPU/RAM/history; Agent; control. Số cột thực tế phải công bố. Không gộp stale/not_collected/tool_error/not_applicable thành 0. Không dùng tên event, nhãn, ID, đường dẫn hoặc recovery làm predictor. Không gọi duration tổng của lệnh DNS là latency phản hồi thành công.

Label map nằm ở config/labels.json. Registry lưu planned_labels; review lưu nhãn xác minh riêng và tham chiếu log bằng SHA256. Planned labels không phải ground truth hợp lệ. Các revision review được lưu append-only; nếu có nhiều revision, exporter phải yêu cầu chọn revision rõ ràng, không tự chọn nhãn thuận lợi.

Các trạng thái collector hiện được kiểm tra bằng validator trong mlv2/core.py. Contract này không tuyên bố raw result đã đủ cho mô hình: feature builder còn phải kiểm tra units/freshness/observer, tương thích scope và khả năng diễn giải từng protocol.

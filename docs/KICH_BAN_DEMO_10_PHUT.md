# Kịch bản demo 10 phút

Kịch bản thuyết trình10 phút; kết quả diễn tập kỹ thuật thật được lưu riêng trong biên bản tuần5. Chọn một lỗi HTTP đơn giản; không chạy đồng thời CPU, DNS hoặc ngắt card mạng. Dữ liệu 18 trial là bằng chứng dự phòng, không trình bày lại như một fault đang xảy ra.

## 0:00–2:00 — Bài toán và trạng thái nền

Giới thiệu MON01 giám sát SRV01/CLI01; Zabbix phát hiện problem, module Python CLI thu bằng chứng và giải thích theo luật. Cho xem topology và dashboard có timestamp mới. Nêu scope lab: R5 là firewall HTTP, không có gateway chung giữa ba host.

Sau reboot, chờ các problem uptime<10m phục hồi và quan sát nhiều poll liên tiếp không còn problem. Kiểm tra cả ba VM đang chạy, đồng bộ giờ và không còn fault/stress; SRV01 ping được, nginx/agent active, HTTP 200 và Problems nền đã được phân loại. Mở sẵn terminal MON01/SRV01 và giao diện Zabbix `http://192.168.56.10:8080/` bằng tài khoản đã cấu hình. Không đưa token hoặc mật khẩu lên màn hình chia sẻ.

## 2:00–3:00 — Gây lỗi có rollback dự phòng

Trên SRV01, tạo timer bật Nginx trước khi dừng service:

```bash
DEMO_UNIT="demo-nginx-$(date -u +%Y%m%dT%H%M%SZ)"
sudo systemd-run --unit="$DEMO_UNIT" --on-active=300s \
  --timer-property=AccuracySec=1s /usr/bin/systemctl start nginx
date -u -Is
sudo systemctl stop nginx
date -u -Is
systemctl is-active nginx
```

Lưu log đầu/cuối và timer vào folder demo mới. Lệnh `is-active` trả inactive/nonzero là trạng thái fault dự kiến, không phải lý do bỏ timer. Không tái sử dụng Run ID của 18 trial.

## 3:00–6:00 — Problem và evidence

Chờ problem HTTP mới trên SRV01, chỉ ra event ID và timestamp. Trên MON01:

```bash
cd ~/do-an/diagnosis-engine
source .venv/bin/activate
python app.py --host-id 10683
```

Sau khi problem mở, thu local HTTP mới trên SRV01:

```bash
HTTP_FILE="$HOME/demo-http-$(date -u +%Y%m%dT%H%M%SZ).json"
python3 ~/http_probe.py --target-ip 192.168.56.20 --observer srv01 \
  --output "$HTTP_FILE"
scp "$HTTP_FILE" phat@192.168.56.10:/home/phat/
```

Tên file/đường dẫn trên MON01 phải trùng file vừa chuyển. Nếu cấu hình SSH đặt UserKnownHostsFile=/dev/null, dùng file known_hosts đã xác minh như trong thực nghiệm; không tắt kiểm tra host key để demo. Không dùng lại evidence cũ đã hết 180 giây.

Trên MON01:

```bash
read -r -p 'Problem event ID mới: ' EVENT_ID
read -r -p 'Đường dẫn HTTP JSON mới trên MON01: ' HTTP_FILE
python app.py --event-id "$EVENT_ID" --host-id 10683 \
  --target-ip 192.168.56.20 --ruleset roadmap \
  --control-ip 192.168.56.30 --http-service expected \
  --http-observer srv01 --http-evidence "$HTTP_FILE" --save
```

Chỉ ra ping thành công, remote TCP80 refused và local HTTP thất bại; giải thích vì sao R2 có cơ sở còn R5 không khớp. Đọc cả missing_info/next_actions. Module được người vận hành gọi; không nói đã có action tự chẩn đoán hoặc tự sửa nếu chưa triển khai chức năng đó.

Nếu timer đã tự khôi phục và event đóng trước khi thu, engine phải từ chối đánh giá problem không còn mở. Ghi nhận tình huống và dùng hồ sơ dự phòng để giải thích; không sửa event ID hoặc dùng evidence cũ để ép lưu.

## 6:00–8:00 — Recovery và hồ sơ lịch sử

Trên SRV01:

```bash
date -u -Is
sudo systemctl start nginx
date -u -Is
curl --fail --max-time 5 -s -o /dev/null -w '%{http_code}\n' http://192.168.56.20/
sudo systemctl stop "$DEMO_UNIT.timer"
```

Chờ recovery thật trong Zabbix. Trên MON01:

```bash
python recovery.py --event-id "$EVENT_ID"
read -r -p 'Incident ID vừa lưu: ' INCIDENT_ID
python report.py --incident-id "$INCIDENT_ID" --format md
```

Chỉ ra cặp problem/recovery liên kết và lifecycle closed. Diagnosis/evidence gốc vẫn giữ nguyên sau recovery.

## 8:00–10:00 — Kết quả và giới hạn

Mở bảng 18 trial và hai hình kết quả trong bộ evidence. Nêu rõ mẫu số fault hợp lệ, lần R5-03 bị hủy trước fault, n=3 mỗi loại và baseline 30 phút 06 giây. Phân biệt detection time, CLI elapsed và recovery recognition. Nêu một abstention thực tế: CPU history span 239 giây ở R5-02 chưa đủ ngưỡng 240 giây.

Kết thúc bằng đóng góp có trong code: xác minh problem, evidence có timestamp/observer/scope, sáu luật có trạng thái thiếu dữ liệu, SQLite chống trộn bundle, recovery đã đối chiếu và report truy vết được. Hướng mở rộng: tập âm độc lập, baseline dài hơn, nhiều topology/tải và đo response-time đầy đủ.

## Hồ sơ dự phòng và nghiệm thu diễn tập

- R2-01: problem 939, recovery 940, incident 22; mở `evidence/week4/official-runs/R2-01/incident.md` khi cần minh họa hồ sơ lịch sử.
- `all-trials.csv`, `experiment-summary.json` và `figures/` cung cấp số liệu/hình dự phòng; không giả là màn hình live.
- Kết quả ba lượt kỹ thuật sau reboot phải có Run ID, thời lượng, event/incident/recovery mới và rollback. Xem biên bản cuối tuần5; không suy thời lượng luồng tự động thành thời lượng nói10 phút.
- Cần chụp dashboard/Problems có timestamp và che thông tin nhạy cảm; kiểm tra backup ngoài laptop trước khi đóng gói bản nộp.

## Kết quả thực hiện tuần5

Ba luồng kỹ thuật live sau reboot đã có bằng chứng problem→diagnosis→rollback→recovery/closed: [bảng thời lượng](../evidence/week5/final-20261017/rehearsal-times.csv). Lượt bị chặn trước fault do problem reboot giữ riêng; lỗi hypervisor và khôi phục MON01 ghi trong biên bản. Thời lượng này không bao gồm phần nói, thao tác trình chiếu hoặc đánh giá trình bày10 phút.

# Cài đặt, chạy và khôi phục lab

Hướng dẫn cho bộ triển khai Zabbix 7.0 LTS, Ubuntu Server, ba VM VirtualBox đã được kiểm chứng. Bản export host/template không chứa toàn bộ hệ điều hành, MySQL hoặc cấu hình daemon; muốn dựng lại hoàn toàn cần VM snapshot/backup hạ tầng hoặc cài Zabbix theo gói phù hợp hệ điều hành. Không dùng file YAML như một bản backup VM.

## 1. Điều kiện triển khai

| Máy | Host-only /24 | Dịch vụ cần có | Template / điểm đo |
|---|---|---|---|
| MON01 | 192.168.56.10 | Zabbix server 7.0, frontend Nginx:8080, MySQL, Agent2, Python3 + venv | Linux by Zabbix agent và Zabbix server health; Agent interface 127.0.0.1:10050 |
| SRV01 | 192.168.56.20 | Nginx:80, Agent2, Python3, iproute2, ping | Linux by Zabbix agent, passive interface .20:10050 |
| CLI01 | 192.168.56.30 | Agent2, Python3, dig, ping | Linux by Zabbix agent, passive interface .30:10050; DNS observer |

VirtualBox: adapter1 NAT, adapter2 Host-only, tên Linux enp0s3/enp0s8 trong lab. Dùng 2 CPU/4096 MB cho MON01, 1 CPU/3048 MB cho SRV01, 1 CPU/2048 MB cho CLI01 theo cấu hình đã đo. Cấp tài nguyên theo máy thật; đây không phải thông số tối thiểu được benchmark.

Đầu vào hạ tầng cần chuẩn bị là Zabbix 7.0/MySQL/frontend đang hoạt động và Agent2 trên từng host. Hướng dẫn này không tự thay nguồn APT hoặc cài package từ phiên bản Ubuntu khác. Phiên bản/source APT đang dùng được lưu trong hồ sơ cuối để tham khảo phục hồi đúng lab, không phải khuyến nghị trộn kho gói khi dựng mới.

Trên SRV01/CLI01, cấu hình Agent2 `Server=192.168.56.10`, `Hostname=SRV01` hoặc `CLI01`; MON01 dùng `Server=127.0.0.1`, `Hostname=Zabbix server`. Dịch vụ phải enabled/active, firewall cho phép luồng lab cần dùng. Khai báo ServerActive riêng không biến template passive thành active.

## 2. Zabbix và quyền API

1. Dùng giao diện cấu hình Zabbix 7.0 để tạo/đối chiếu ba host và interface, liên kết template như Chương 2. Có thể import YAML trong `evidence/week5/final-20261017/zabbix-hosts-week5.yaml`; giữ backup trước khi import và xem diff trước khi cập nhật host đã tồn tại.
2. Host ID có thể đổi khi cài mới. Lấy ID thật qua `host.get`; các lệnh lab dùng 10084, 10683, 10684 chỉ đúng trên lab hiện tại.
3. Web scenario `SRV01 HTTP`: Homepage URL `http://192.168.56.20/`, required status200, delay30s, timeout5s, retries1. Trigger last fail >0. DNS item CLI01 `net.dns[,example.com,A,2,1,udp]`, delay30s; trigger max của ba mẫu =0.
4. Kiểm tra CPU util là dependent từ idle với `100-value`; Agent timeout3m; CPU crit90; load/vCPU warn1,5. CPU count heartbeat1d. Xem inventory và SQL kiểm chứng trong hồ sơ ngày31.
5. Tạo user/role và token API đủ quyền đọc đúng host và phương thức dùng bởi engine: problem.get, event.get, item.get, history.get. Quyền phục vụ export/kiểm chứng cấu hình có thể khác quyền vận hành engine. Không cấp MySQL cho engine.

## 3. Cài module trên MON01

Chuyển thư mục `diagnosis-engine` của bản nộp vào `/home/phat/do-an/diagnosis-engine`. Các lệnh dưới chạy trong thư mục đó; dùng Python có venv/pip sẵn trên VM.

```bash
cd ~/do-an/diagnosis-engine
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp -n .env.example .env
chmod 600 .env
```

Sửa `.env` bằng editor cục bộ: khóa phải là `ZABBIX_URL` và `ZABBIX_API_TOKEN`; nhập token thật ngoài Git và ngoài màn hình trình chiếu. URL lab là `http://192.168.56.10:8080/api_jsonrpc.php`. Không đưa token vào tham số dòng lệnh. Mẫu đã sửa lỗi cũ `ZABBIX_URLL`.

```bash
.venv/bin/python -m pytest -q
.venv/bin/python app.py --host-id 10683
```

Lệnh app không event chỉ liệt kê problem, không tạo incident. Không copy diagnosis.db runtime theo kiểu ghi đè dữ liệu đang dùng; chọn DB mới bằng --db nếu đang kiểm thử cài mới.

## 4. Chạy chẩn đoán và probe

Chép `http_probe.py` sang `/home/phat/http_probe.py` trên SRV01; DNS probe trên CLI01 cần `dns_probe.py`, `evidence.py`, `models.py` cùng thư mục. Không cần token Zabbix ở hai máy này. `dig`/`ping`/`ip` phải gọi được.

```bash
# SRV01, khi problem còn mở, chọn tên mới mỗi lần
HTTP_FILE="$HOME/http-$(date -u +%Y%m%dT%H%M%SZ).json"
python3 ~/http_probe.py --target-ip 192.168.56.20 --observer srv01 --output "$HTTP_FILE"
scp "$HTTP_FILE" phat@192.168.56.10:/home/phat/
```

Trên MON01, dùng đúng file vừa chuyển, còn mới ≤180s. Kiểm tra host key SSH theo lab; không tắt host-key checking để né lỗi.

```bash
cd ~/do-an/diagnosis-engine
read -r -p 'Problem event ID đang mở: ' EVENT_ID
read -r -p 'Đường dẫn HTTP JSON mới trên MON01: ' HTTP_FILE
.venv/bin/python app.py --event-id "$EVENT_ID" --host-id 10683 \
  --target-ip 192.168.56.20 --ruleset roadmap --control-ip 192.168.56.30 \
  --http-service expected --http-observer srv01 --http-evidence "$HTTP_FILE" --save
```

DNS chạy trên CLI01: `python3 dns_probe.py --name example.com --control-ip 1.1.1.1 --output <tên-mới.json>`. Chuyển JSON về MON01, chọn host10684, target.30, control.20, scope absent, tên example.com, observer cli01 và DNS control1.1.1.1 theo README. Giữ observer/target/scope thực tế; không sửa JSON để ép matched.

Sau rollback và khi API có recovery thật:

```bash
.venv/bin/python recovery.py --event-id "$EVENT_ID"
read -r -p 'Incident ID đã lưu: ' INCIDENT_ID
.venv/bin/python report.py --incident-id "$INCIDENT_ID" --format md
```

## 5. Demo Nginx và rollback

Chạy đúng [kịch bản demo 10 phút](KICH_BAN_DEMO_10_PHUT.md). Tạo timer bật lại Nginx sau300s trước lệnh dừng. Ghi timestamp trước/sau, event mới, local probe mới, CLI một lần, incident ID và recovery. Chờ không còn problem nền sau reboot (cảnh báo uptime có cửa sổ10m); một lần poll rỗng chưa đủ chứng minh đã ổn định.

Khôi phục khẩn cấp trên SRV01: `sudo systemctl start nginx`; xác nhận HTTP200 và Agent active. Chỉ dừng timer đúng tên đã tạo sau khi service phục hồi; không xóa mọi timer hoặc mọi bảng firewall. Nếu event đóng trước collection, engine từ chối là hành vi đúng; giữ attempt, tạo Run ID mới nếu thử lại.

## 6. Phục hồi dữ liệu và kiểm tra

- Git bundle: `git clone <bundle> <thư-mục-mới>`; đối chiếu tag/commit và SHA256 trước khi dùng.
- SQLite: đóng mọi tiến trình ghi hoặc dùng SQLite backup API; backup cuối nằm ngoài Git, kèm checksum. Mở bản phục hồi trong thư mục riêng, `PRAGMA integrity_check`, `PRAGMA foreign_key_check`, so sánh số hàng và report. Không nối DB backup vào MySQL.
- Zabbix YAML: cấu hình host/template, không phục hồi lịch sử event/metric hoặc user/token. Muốn phục hồi toàn bộ Zabbix cần backup MySQL/hạ tầng riêng; bản nộp kỹ thuật không chứa secret daemon.
- Dữ liệu immutable: chạy kiểm tra các manifest; không tự normalize newline ở thư mục evidence. Những ảnh event lịch sử là fallback đã ghi ngày chụp, không giả thành fault live.
- Lỗi thường gặp: sai khóa URL trong .env; token thiếu host permissions; service chưa lên sau reboot; probe quá180s/sai observer; event đã recovered; bundle trùng bị từ chối; CLI thiếu dig/ping. Đọc lỗi, sửa điều kiện vận hành rồi dùng event mới khi cần; không sửa rule tại buổi demo.

Hướng dẫn này đã được dùng để đối chiếu các lệnh trên lab hiện có. Việc dựng Zabbix hoàn toàn từ một OS trống chưa được diễn tập trong tuần5; ghi đúng giới hạn khi bàn giao cho người khác.

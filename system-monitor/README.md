# Hệ thống chuyên gia và tương quan cảnh báo v3

Luồng mới hoạt động trên **đúng ba VM MON01, SRV01, CLI01**. Worker đọc Zabbix bằng token chỉ đọc, thu bằng chứng, đánh giá bảng quyết định SQLite và gom cảnh báo theo topology. Xem [báo cáo nghiệm thu](../docs/HOAN_THIEN_HE_THONG_20261103.md) để biết bằng chứng và giới hạn.

```text
Zabbix → cursor + hàng đợi SQLite → thu bằng chứng → 8 luật chuyên gia trong SQLite
                              └→ topology + trạng thái gateway → nhóm sự cố
```

**ML vẫn là nhánh nghiên cứu riêng trong `ml-research`.** Mô hình cũ dùng 12 features, profile SRV01 `192.168.56.20`. Worker v3 xuất bảy nhóm features theo schema mới; không đưa vector mới vào mô hình cũ, không train lại hay tự kích hoạt luật ML.

## Dùng ngay trên laptop lab hiện tại

Bật ba VM bằng VirtualBox, giữ máy cắm sạc. Gateway overlay và worker tự khởi động bằng systemd. Mở PowerShell ở thư mục repository:

```powershell
python .\system-monitor\system_lab.py status
python .\system-monitor\system_lab.py demo --fault nginx
python .\system-monitor\system_lab.py demo --fault gateway
python .\system-monitor\system_lab.py demo --fault multi
python .\system-monitor\system_lab.py demo --fault storm
```

Chạy **một demo mỗi lần**. Lệnh `demo` cố ý tạo lỗi; nhập mật khẩu SSH khi được hỏi, mật khẩu chỉ giữ trong RAM. Host keys phải có trong `~/.ssh/known_hosts`. Wrapper dùng `tools/lab.local.json` để tìm Paramiko và thư mục khóa dùng chung với demo ML. Nó giữ màn hình thức tạm thời, kiểm baseline trước lỗi và lưu `before/detected/recovered` dưới `evidence/system-v3/demos/<thời điểm>`.

Chưa cần train hoặc nạp token quản trị để chạy các demo nginx/gateway/multi. Demo storm dùng `.env.admin` **trên MON01** để gửi giá trị vào đúng 20 kênh cảnh báo thử. Đây là 20 cảnh báo được bơm vào Zabbix, không phải 20 VM hay 20 lỗi vật lý.

Nếu demo bị ngắt:

```powershell
python .\system-monitor\system_lab.py recover
```

Nginx/gateway có timer rollback systemd độc lập 120 giây, được xác nhận hoạt động trước khi tạo lỗi. Wrapper có `finally` để khôi phục sớm và đợi các cảnh báo phục hồi. Demo storm có timer trả kênh thử về 0 sau 100 giây. Không chạy demo ML đồng thời với demo hệ thống; hai wrapper dùng chung khóa.

## Xem trực tiếp trên MON01

```bash
cd /home/phat/do-an/diagnosis-engine
systemctl status do-an-monitor-v3.service --no-pager
.venv/bin/python ../system-monitor/report.py
.venv/bin/python ../system-monitor/report.py --json
journalctl -u do-an-monitor-v3.service -n 10 --no-pager
```

`report.py` chỉ đọc trạng thái, không chạy thêm worker. Các số cần xem: `active events`, số nhóm sự cố, cảnh báo phụ thuộc bị ức chế và `pending jobs`. Sau phục hồi cần chờ chu kỳ item/trigger Zabbix; dịch vụ chạy lại chưa có nghĩa cảnh báo cũ đã được cập nhật ngay.

Mỗi worker giữ một file lock. Lệnh `monitor.py once` sẽ từ chối nếu `watch` đang giữ cùng runtime DB. Khi cần chạy một lần để sửa lỗi, dừng service trước rồi khởi động lại sau; không chạy hai worker vào cùng DB.

## Dữ liệu và bảng quyết định

| File | Vai trò |
|---|---|
| `config/expert_seed.json` | Nguồn có thể review: 7 nhóm, 8 luật, 40 hàng quyết định, mỗi luật 3 giả thuyết |
| `build_catalog.py` | Tạo catalog SQLite mới; từ chối ghi đè |
| `catalog/expert_rules.sqlite` | Bảng metadata, expert_rules, decision_rows, hypotheses; runtime mở chỉ đọc |
| `config/lab.json` | Profile, topology có căn cứ, host IDs và đường dẫn khóa SSH; không chứa khóa/token |
| `config/provisioned.json` | IDs của hai host logic/item/trigger v3 đã tạo trong lab |
| `runtime/monitoring.sqlite` | Sự kiện gốc, cursor, jobs, diagnoses, batches, trạng thái node; bỏ qua Git |

Các nhóm: Ping; HTTP (hai luật: dịch vụ và đường truy cập); DNS; Agent; Resource; Gateway; Alert Storm. Chọn hàng đầu tiên khớp trong từng luật; các luật được đánh giá độc lập nên có thể đồng thời khớp. Điều kiện và kết luận nằm trong SQLite, Python chịu trách nhiệm thu/chuẩn hóa bằng chứng và thực thi bộ so khớp chung.

Các điểm 85/65/45% là **điểm ưu tiên điều tra do chuyên gia gán**, không phải xác suất chẩn đoán đúng đã được đo/hiệu chỉnh. `matched` nghĩa là khớp dấu hiệu; `not_matched` không đồng nghĩa toàn hệ thống khỏe; `insufficient_evidence` là chưa đủ bằng chứng.

Muốn sửa ngưỡng/luật: sao lưu catalog hiện tại, sửa seed, tạo **catalog ở đường dẫn mới**, kiểm thử rồi đổi đường dẫn và restart worker. Catalog được cache một lần mỗi phiên, không tự tải lại giữa chừng. Mỗi thay đổi cần phiên bản mới để có thể truy nguyên.

```powershell
python .\system-monitor\build_catalog.py
python -m unittest discover -s .\system-monitor\tests -v
python .\system-monitor\monitor.py rules
```

`build_catalog.py` chỉ cần ở lần cài mới. Nếu catalog đã tồn tại thì dùng file đó; không xóa DB để chạy lệnh này lại. Các bài regression lịch sử cần cây repository và dữ liệu `evidence/ml-v2` hiện có.

## Topology thật trong lab

```text
MON01 192.168.56.10
  → route 172.30.20.0/24 via 192.168.56.30
CLI01 192.168.56.30 / 172.30.20.1   [gateway]
  → internal network do-an-v3-backend
SRV01 172.30.20.20                 [địa chỉ dịch vụ được giám sát]
```

SRV01 vẫn có `192.168.56.20` để quản trị/thu bằng chứng tại máy. Đường trả lời từ nguồn `172.30.20.20` dùng bảng route 203 qua CLI01; các đường quản trị cũ giữ nguyên. Hai host Zabbix mới `CLI01-Gateway`, `SRV01-Routed` là hai đối tượng giám sát trên ba VM hiện có.

Gateway được kiểm tra forwarding, interface và route, không chỉ ping. Cửa sổ correlation 30 giây so thời điểm các sự kiện; parent phải có bằng chứng down còn mới. Cảnh báo cũ có trước parent quá 30 giây không bị quy ngược cho parent. Lỗi CPU/DNS hoặc dịch vụ được đo độc lập vẫn giữ riêng. HTTP từ xa cùng đợt với lỗi Nginx cục bộ được gom về nhóm dịch vụ khi không có parent hỏng phù hợp. Không xóa/sửa cảnh báo nguồn trong Zabbix.

SSH của worker dùng khóa riêng trên MON01, giới hạn nguồn MON01 và forced command chỉ cho phép probe đọc HTTP/DNS/routing. Private key và `.env*` không đưa vào Git hay gói source. Probe HTTP kiểm tra IP thực sự thuộc máy quan sát.

## Cài lại thành phần hoặc quay về baseline

Các VM hiện tại đã được cấu hình. Khi phục hồi bản VM cũ hoặc cài lại source, xem [hướng dẫn triển khai](deployment/README.md). Không chạy script cài mạng khi NIC3 đang phục vụ một mạng khác.

Muốn tắt riêng workflow mới trên MON01:

```bash
sudo systemctl disable --now do-an-monitor-v3.service
```

Muốn gỡ đường mạng thử: dừng worker; trên MON01, SRV01 rồi CLI01 chạy `sudo systemctl disable --now do-an-network-v3.service`. `ExecStop` gỡ đúng route/rule/address/nft table do module tạo và phục hồi sysctl ban đầu. Giữ file state `/var/lib/do-an-system-v3/network-before.json` tới khi gỡ xong. Baseline/ML cũ vẫn dùng các IP `192.168.56.x`.

Backup toàn VM có sẵn trong `D:\Study\network-monitoring-project\VM_BACKUP`; backup source riêng trong `SOURCE_BACKUP`. Bản cold VM trước v3 không tự có mạng thử mới: dùng lại source và quy trình triển khai. GitHub lưu source/tài liệu/bằng chứng công khai, không thay thế backup đĩa VM, MySQL, cấu hình và secrets.

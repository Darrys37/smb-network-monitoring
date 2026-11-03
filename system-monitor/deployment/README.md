# Triển khai lại trên lab hiện có

Hướng dẫn này giả định ba VM đã có Ubuntu/Zabbix/Agent2/Nginx như baseline của đồ án. Đây không phải trình cài mới một Zabbix Server trống. Sao lưu trước và đối chiếu IP/host IDs nếu dùng môi trường khác.

1. Khi SRV01 và CLI01 đã **poweroff**, kiểm tra NIC3 chưa dùng. Thêm NIC3 Internal Network `do-an-v3-backend`, Intel PRO/1000 MT Desktop, MAC SRV01 `080027D30120`, CLI01 `080027D30130`. Giữ NIC1/NIC2. Bật lại hai VM. Không tạo VM thứ tư.
2. Chép thư mục `system-monitor` vào `/home/phat/do-an/system-monitor` trên cả ba VM. Giữ quyền sở hữu `phat`. Không chép `.env` hoặc private key qua Git.
3. Chạy trên CLI01, tiếp SRV01, cuối cùng MON01:

   ```bash
   sudo python3 /home/phat/do-an/system-monitor/deployment/install_network.py
   ```

   Script nhận đúng hostname lab, lưu state trước khi đổi và bật service `do-an-network-v3`. Nếu báo prefix/table/rule đã dùng thì dừng và kiểm tra; không xóa cấu hình khác để chạy tiếp.
4. Trên SRV01 và CLI01:

   ```bash
   sudo python3 /home/phat/do-an/system-monitor/deployment/install_agent.py
   ```

   Nó tạo đúng file `do-an-system-v3.conf`, helper root-owned, rồi restart Agent2. CLI01 có `diag.router.ready`, `diag.dns.json`; SRV01 có `diag.service.nginx`. Các file Agent2 gốc giữ nguyên.
5. Trên MON01, tạo khóa riêng ED25519 `~/.ssh/do-an-v3-probe` (không ghi private key ra chat). Lấy **public key**, thêm vào `authorized_keys` của phat trên SRV01/CLI01 với tiền tố:

   ```text
   from="192.168.56.10",restrict,command="python3 /home/phat/do-an/system-monitor/probe_dispatcher.py" PUBLIC_KEY
   ```

   Thay `PUBLIC_KEY` bằng dòng public key thực tế. `~/.ssh` mode700, private key/authorized_keys mode600. Pin host keys của hai VM trong MON01 `known_hosts` sau khi đối chiếu fingerprint với máy đã xác thực; không dùng `StrictHostKeyChecking=no`.
6. MON01 giữ `.env` token chỉ đọc trong `diagnosis-engine`. Token cấu hình riêng nằm ở `.env.admin`, biến `ZABBIX_ADMIN_API_TOKEN`, mode600. Từ thư mục engine:

   ```bash
   .venv/bin/python ../system-monitor/provision_zabbix.py
   ```

   Script tạo bổ sung hai host logic trong group Linux servers ID2; từ chối host trùng tên không có tag sở hữu. Ghi `config/provisioned.json`. Kiểm tra IDs trong `config/lab.json` khớp kết quả mới, đặc biệt `event_host_ids`, `metrics_host_id`, `agent_host_id` và ánh xạ trigger HTTP gốc. Config trong Git là IDs của lab đã kiểm chứng, không phải IDs phổ quát.
7. MON01:

   ```bash
   cd /home/phat/do-an/diagnosis-engine
   .venv/bin/python ../system-monitor/build_catalog.py
   .venv/bin/python ../system-monitor/storm_control.py 0
   sudo python3 ../system-monitor/deployment/install_worker.py
   .venv/bin/python ../system-monitor/report.py
   ```

   Chỉ tạo catalog khi chưa có. Chờ Zabbix nạp cấu hình và thu đủ mẫu. Cần tất cả nguồn `ok`, SRV01 HTTP200, parent up, không có cảnh báo hoạt động. Worker chạy bằng phat, dùng token đọc; không dùng `.env.admin`.
8. MON01 phải có route dịch vụ qua CLI01:

   ```bash
   ip route get 172.30.20.20
   ping -c 1 -t 1 172.30.20.20
   curl --max-time 3 -o /dev/null -s -w '%{http_code}\n' http://172.30.20.20/
   ```

   Lệnh TTL1 phải nhận Time Exceeded từ `192.168.56.30` (ping exit1 trong phép thử này là kết quả dự kiến). HTTP phải200. Sau đó mới chạy demo theo README chính.

Các installer ghi đúng file/unit mang tên module v3. Dùng `systemctl disable --now do-an-network-v3` để gỡ phần mạng sở hữu; không flush firewall hoặc xóa route toàn hệ thống. Muốn bỏ các đối tượng Zabbix mới, đối chiếu `config/provisioned.json` và export cấu hình trước; không xóa ba host baseline.

# Hồ sơ sự cố #11

- Event ID: 458
- Tên sự cố: SRV01: HTTP check failed
- Mức độ severity: 3
- Thời điểm event (Unix): 1790858551
- Số evidence: 6
- Số kết quả luật: 5

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 459; thời điểm Unix 1790858671; khoảng cách hai event 120 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

## Kết quả chẩn đoán

### HTTP_PORT_REFUSED — matched

Nhận định: 192.168.56.20 responds to ping, but TCP port 80 refuses the connection.

Nguyên nhân khả dĩ: No service listening on TCP port 80, or the connection is actively rejected.

**Thông tin còn thiếu:**

- Listening sockets and owning processes on the target.
- Web service status and firewall rules on the target.

**Kiểm tra tiếp theo:**

- On the target: sudo ss -lntp
- On the target: systemctl status nginx --no-pager
- Inspect firewall rules for TCP port 80.

### REACHABILITY_SUSPECTED — not_matched

Nhận định: 192.168.56.20: ping=success, TCP port 80=refused.

### CPU_HIGH — not_matched

Nhận định: CPU utilization is 0.47%; threshold is 90%.

### MEMORY_HIGH — not_matched

Nhận định: Memory utilization is 15.46%; threshold is 90%.

### ROOT_DISK_HIGH — not_matched

Nhận định: Filesystem / usage is 48.65%; threshold is 90%.

## Bằng chứng đã lưu

### Evidence #1 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1790858637

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=1.09 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.086/1.086/1.086/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 8.21
}
```

### Evidence #2 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1790858637

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "[Errno 111] Connection refused",
  "errno": 111,
  "status": "refused",
  "duration_ms": 1.59
}
```

### Evidence #3 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1790858637

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 0.4746370000000013,
  "sample_clock": 1790858617,
  "age_seconds": 20,
  "item_id": "50822",
  "raw_value": "0.4746370000000013",
  "error": ""
}
```

### Evidence #4 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1790858637

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 15.460963000000007,
  "sample_clock": 1790858579,
  "age_seconds": 58,
  "item_id": "50823",
  "raw_value": "15.460963000000007",
  "error": ""
}
```

### Evidence #5 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1790858637

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 0.039062,
  "sample_clock": 1790858611,
  "age_seconds": 26,
  "item_id": "50791",
  "raw_value": "0.039062",
  "error": ""
}
```

### Evidence #6 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1790858637

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 48.646115695535194,
  "sample_clock": 1790858637,
  "age_seconds": 0,
  "item_id": "50856",
  "raw_value": "48.646115695535194",
  "error": ""
}
```



# Hồ sơ sự cố #39

- Event ID: 1052
- Tên sự cố: SRV01: HTTP check failed
- Mức độ severity: 3
- Thời điểm event (Unix): 1792204951
- Số evidence: 11
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 1059; thời điểm Unix 1792204981; khoảng cách hai event 30 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

## Kết quả chẩn đoán

### R1_HOST_OR_LOCAL_CONNECTIVITY — not_matched

Nhận định: Target responded to ICMP or TCP.

### R2_HTTP_SERVICE_SUSPECTED — matched

Nhận định: Host ping works; TCP80=refused; local HTTP=failed. Service/listener or active rejection suspected.

Nguyên nhân khả dĩ: Host ping works; TCP80=refused; local HTTP=failed. Service/listener or active rejection suspected.

**Thông tin còn thiếu:**

- Service state, listening sockets and firewall policy; refusal alone does not prove nginx stopped.

**Kiểm tra tiếp theo:**

- On target inspect systemctl status nginx, ss -lntp and firewall rules.

### R3_AGENT_UNAVAILABLE — not_matched

Nhận định: A recent agent.ping sample exists.

### R4_DNS_RESOLVER_SUSPECTED — insufficient_evidence

Nhận định: DNS target not configured.

**Thông tin còn thiếu:**

- Actual application name and CLI01 DNS evidence.

### R5_HTTP_ACCESS_FILTER_SUSPECTED — not_matched

Nhận định: Remote ping=success, TCP80=refused; HTTP on target's own service IP=failed. The evidence does not meet R5 conditions for suspected filtering/access-path failure.

### R6_SUSTAINED_CPU_HIGH — not_matched

Nhận định: Mean CPU=12.88%; below 90%.

## Bằng chứng đã lưu

### Evidence #291 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792204959

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=0.909 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 0.909/0.909/0.909/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 7.28
}
```

### Evidence #292 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792204959

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

### Evidence #293 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792204959

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 13.819469999999995,
  "sample_clock": 1792204958,
  "age_seconds": 1,
  "item_id": "50822",
  "raw_value": "13.819469999999995",
  "error": ""
}
```

### Evidence #294 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792204959

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 14.854641,
  "sample_clock": 1792204919,
  "age_seconds": 40,
  "item_id": "50823",
  "raw_value": "14.854641",
  "error": ""
}
```

### Evidence #295 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792204959

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 0.106445,
  "sample_clock": 1792204951,
  "age_seconds": 8,
  "item_id": "50791",
  "raw_value": "0.106445",
  "error": ""
}
```

### Evidence #296 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792204959

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 53.73320459202855,
  "sample_clock": 1792204917,
  "age_seconds": 42,
  "item_id": "50856",
  "raw_value": "53.73320459202855",
  "error": ""
}
```

### Evidence #297 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792204959

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 1.29
}
```

### Evidence #298 — agent_metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792204959

```json
{
  "key": "agent.ping",
  "status": "success",
  "max_age_seconds": 180,
  "item": {
    "itemid": "50782",
    "key_": "agent.ping",
    "value_type": "3",
    "status": "0",
    "units": "",
    "state": "0",
    "error": "",
    "lastclock": "1792204942",
    "lastvalue": "1"
  },
  "sample_clock": 1792204942
}
```

### Evidence #299 — cpu_history

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792204959

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1792204717,
      "value": 8.791612999999998
    },
    {
      "clock": 1792204777,
      "value": 9.335560999999998
    },
    {
      "clock": 1792204837,
      "value": 14.820386999999997
    },
    {
      "clock": 1792204897,
      "value": 17.657014000000004
    },
    {
      "clock": 1792204958,
      "value": 13.819469999999995
    }
  ],
  "support_items": {
    "system.cpu.num": {
      "itemid": "50793",
      "key_": "system.cpu.num",
      "value_type": "3",
      "status": "0",
      "units": "",
      "state": "0",
      "error": "",
      "lastclock": "1792204714",
      "lastvalue": "1"
    },
    "system.cpu.load[all,avg1]": {
      "itemid": "50791",
      "key_": "system.cpu.load[all,avg1]",
      "value_type": "0",
      "status": "0",
      "units": "",
      "state": "0",
      "error": "",
      "lastclock": "1792204951",
      "lastvalue": "0.106445"
    }
  },
  "item_id": "50822"
}
```

### Evidence #300 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792204959

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=0.928 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 0.928/0.928/0.928/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 4.87
}
```

### Evidence #301 — local_http

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792204955

```json
{
  "observer": "srv01",
  "port": 80,
  "path": "/",
  "local_address_verified": true,
  "status": "failed",
  "http_status": null,
  "error": "[Errno 111] Connection refused"
}
```



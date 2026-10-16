# Hồ sơ sự cố #23

- Event ID: 941
- Tên sự cố: SRV01: HTTP check failed
- Mức độ severity: 3
- Thời điểm event (Unix): 1792171171
- Số evidence: 11
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 942; thời điểm Unix 1792171231; khoảng cách hai event 60 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

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

### R6_SUSTAINED_CPU_HIGH — insufficient_evidence

Nhận định: CPU history is sparse, stale or invalid.

**Thông tin còn thiếu:**

- At least 240s coverage, max 120s gap, latest sample <=180s old.

## Bằng chứng đã lưu

### Evidence #118 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792171213

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=0.909 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 0.909/0.909/0.909/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 11.48
}
```

### Evidence #119 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792171213

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "[Errno 111] Connection refused",
  "errno": 111,
  "status": "refused",
  "duration_ms": 1.6
}
```

### Evidence #120 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792171213

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 15.702927000000003,
  "sample_clock": 1792171177,
  "age_seconds": 36,
  "item_id": "50822",
  "raw_value": "15.702927000000003",
  "error": ""
}
```

### Evidence #121 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792171213

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 16.086411999999996,
  "sample_clock": 1792171199,
  "age_seconds": 14,
  "item_id": "50823",
  "raw_value": "16.086411999999996",
  "error": ""
}
```

### Evidence #122 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792171213

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 0.012207,
  "sample_clock": 1792171171,
  "age_seconds": 42,
  "item_id": "50791",
  "raw_value": "0.012207",
  "error": ""
}
```

### Evidence #123 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792171213

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 53.12869737762006,
  "sample_clock": 1792171197,
  "age_seconds": 16,
  "item_id": "50856",
  "raw_value": "53.12869737762006",
  "error": ""
}
```

### Evidence #124 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792171213

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 2.09
}
```

### Evidence #125 — agent_metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792171213

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
    "lastclock": "1792171162",
    "lastvalue": "1"
  },
  "sample_clock": 1792171162
}
```

### Evidence #126 — cpu_history

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792171213

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1792170966,
      "value": 13.266256999999996
    },
    {
      "clock": 1792170997,
      "value": 17.742524000000003
    },
    {
      "clock": 1792171057,
      "value": 13.151137000000006
    },
    {
      "clock": 1792171117,
      "value": 15.098786000000004
    },
    {
      "clock": 1792171177,
      "value": 15.702927000000003
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
      "lastclock": "1792166793",
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
      "lastclock": "1792171171",
      "lastvalue": "0.012207"
    }
  },
  "item_id": "50822"
}
```

### Evidence #127 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792171213

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=0.920 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 0.920/0.920/0.920/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 7.04
}
```

### Evidence #128 — local_http

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792171202

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


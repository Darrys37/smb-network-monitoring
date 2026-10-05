# Hồ sơ sự cố #17

- Event ID: 777
- Tên sự cố: Linux: Zabbix agent is not available (for 3m)
- Mức độ severity: 3
- Thời điểm event (Unix): 1791202321
- Số evidence: 10
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 788; thời điểm Unix 1791202501; khoảng cách hai event 180 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

## Kết quả chẩn đoán

### R1_HOST_OR_LOCAL_CONNECTIVITY — not_matched

Nhận định: Target responded to ICMP or TCP.

### R2_HTTP_SERVICE_SUSPECTED — not_matched

Nhận định: Target ping=success, TCP80=success.

### R3_AGENT_UNAVAILABLE — matched

Nhận định: Host ping=success, agent.ping has no recent data, TCP10050=refused.

Nguyên nhân khả dĩ: Host ping=success, agent.ping has no recent data, TCP10050=refused.

**Thông tin còn thiếu:**

- Agent mode, Server allow-list, service and firewall state.

**Kiểm tra tiếp theo:**

- Inspect zabbix-agent2 service and its logs; do not assume service stopped.

### R4_DNS_RESOLVER_SUSPECTED — insufficient_evidence

Nhận định: DNS target not configured.

**Thông tin còn thiếu:**

- Actual application name and CLI01 DNS evidence.

### R5_HTTP_ACCESS_FILTER_SUSPECTED — not_matched

Nhận định: No isolated remote HTTP connection failure with working ICMP.

### R6_SUSTAINED_CPU_HIGH — insufficient_evidence

Nhận định: CPU history is sparse, stale or invalid.

**Thông tin còn thiếu:**

- At least 240s coverage, max 120s gap, latest sample <=180s old.

## Bằng chứng đã lưu

### Evidence #55 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791202442

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=1.31 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.308/1.308/1.308/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 14.46
}
```

### Evidence #56 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791202442

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 2.05
}
```

### Evidence #57 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791202442

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "stale",
  "value": 12.307974000000002,
  "sample_clock": 1791202117,
  "age_seconds": 325,
  "item_id": "50822",
  "raw_value": "12.307974000000002",
  "error": ""
}
```

### Evidence #58 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791202442

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "stale",
  "value": 15.241113999999996,
  "sample_clock": 1791202079,
  "age_seconds": 363,
  "item_id": "50823",
  "raw_value": "15.241113999999996",
  "error": ""
}
```

### Evidence #59 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791202442

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "stale",
  "value": 0.103516,
  "sample_clock": 1791202111,
  "age_seconds": 331,
  "item_id": "50791",
  "raw_value": "0.103516",
  "error": ""
}
```

### Evidence #60 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791202442

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "stale",
  "value": 53.04819216973744,
  "sample_clock": 1791202077,
  "age_seconds": 365,
  "item_id": "50856",
  "raw_value": "53.04819216973744",
  "error": ""
}
```

### Evidence #61 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791202442

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "[Errno 111] Connection refused",
  "errno": 111,
  "status": "refused",
  "duration_ms": 2.92
}
```

### Evidence #62 — agent_metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791202442

```json
{
  "key": "agent.ping",
  "status": "no_data",
  "max_age_seconds": 180,
  "item": {
    "itemid": "50782",
    "key_": "agent.ping",
    "value_type": "3",
    "status": "0",
    "units": "",
    "state": "0",
    "error": "",
    "lastclock": "1791202102",
    "lastvalue": "1"
  },
  "sample_clock": 1791202102
}
```

### Evidence #63 — cpu_history

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791202442

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [],
  "support_items": {
    "system.cpu.num": {
      "itemid": "50793",
      "key_": "system.cpu.num",
      "value_type": "3",
      "status": "0",
      "units": "",
      "state": "0",
      "error": "",
      "lastclock": "1791195633",
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
      "lastclock": "1791202111",
      "lastvalue": "0.103516"
    }
  },
  "item_id": "50822"
}
```

### Evidence #64 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1791202442

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=1.40 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.401/1.401/1.401/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 9.85
}
```



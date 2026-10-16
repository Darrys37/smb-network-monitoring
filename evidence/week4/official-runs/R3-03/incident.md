# Hồ sơ sự cố #27

- Event ID: 957
- Tên sự cố: Linux: Zabbix agent is not available (for 3m)
- Mức độ severity: 3
- Thời điểm event (Unix): 1792172581
- Số evidence: 10
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 962; thời điểm Unix 1792172701; khoảng cách hai event 120 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

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

### Evidence #160 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792172581

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=1.76 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.764/1.764/1.764/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 8.4
}
```

### Evidence #161 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792172581

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 2.06
}
```

### Evidence #162 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792172581

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "stale",
  "value": 13.669195000000002,
  "sample_clock": 1792172257,
  "age_seconds": 324,
  "item_id": "50822",
  "raw_value": "13.669195000000002",
  "error": ""
}
```

### Evidence #163 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792172581

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "stale",
  "value": 15.542432000000005,
  "sample_clock": 1792172279,
  "age_seconds": 302,
  "item_id": "50823",
  "raw_value": "15.542432000000005",
  "error": ""
}
```

### Evidence #164 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792172581

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "stale",
  "value": 0.073242,
  "sample_clock": 1792172311,
  "age_seconds": 270,
  "item_id": "50791",
  "raw_value": "0.073242",
  "error": ""
}
```

### Evidence #165 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792172581

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "stale",
  "value": 53.12963097949559,
  "sample_clock": 1792172277,
  "age_seconds": 304,
  "item_id": "50856",
  "raw_value": "53.12963097949559",
  "error": ""
}
```

### Evidence #166 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792172581

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "[Errno 111] Connection refused",
  "errno": 111,
  "status": "refused",
  "duration_ms": 1.12
}
```

### Evidence #167 — agent_metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792172581

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
    "lastclock": "1792172302",
    "lastvalue": "1"
  },
  "sample_clock": 1792172302
}
```

### Evidence #168 — cpu_history

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792172581

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
      "lastclock": "1792172311",
      "lastvalue": "0.073242"
    }
  },
  "item_id": "50822"
}
```

### Evidence #169 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792172581

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=2.15 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 2.150/2.150/2.150/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 24.07
}
```


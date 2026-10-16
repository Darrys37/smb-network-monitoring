# Hồ sơ sự cố #19

- Event ID: 933
- Tên sự cố: SRV01: HTTP check failed
- Mức độ severity: 3
- Thời điểm event (Unix): 1792170336
- Số evidence: 10
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 934; thời điểm Unix 1792170451; khoảng cách hai event 115 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

## Kết quả chẩn đoán

### R1_HOST_OR_LOCAL_CONNECTIVITY — matched

Nhận định: Target ping=no_reply, TCP=timeout; control host ping=success.

Nguyên nhân khả dĩ: Target ping=no_reply, TCP=timeout; control host ping=success.

**Thông tin còn thiếu:**

- Target console, route and firewall state; compare from CLI01.

**Kiểm tra tiếp theo:**

- Inspect target console and local network path.

### R2_HTTP_SERVICE_SUSPECTED — not_matched

Nhận định: Target ping=no_reply, TCP80=timeout.

### R3_AGENT_UNAVAILABLE — not_matched

Nhận định: A recent agent.ping sample exists.

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

### Evidence #77 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792170339

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 1,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 0 received, 100% packet loss, time 0ms",
  "stderr": "",
  "status": "no_reply",
  "duration_ms": 2020.46
}
```

### Evidence #78 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792170341

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "timed out",
  "errno": null,
  "status": "timeout",
  "duration_ms": 2003.89
}
```

### Evidence #79 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792170343

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 12.998712999999995,
  "sample_clock": 1792170277,
  "age_seconds": 66,
  "item_id": "50822",
  "raw_value": "12.998712999999995",
  "error": ""
}
```

### Evidence #80 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792170343

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 15.761125000000007,
  "sample_clock": 1792170299,
  "age_seconds": 44,
  "item_id": "50823",
  "raw_value": "15.761125000000007",
  "error": ""
}
```

### Evidence #81 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792170343

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 0.179199,
  "sample_clock": 1792170271,
  "age_seconds": 72,
  "item_id": "50791",
  "raw_value": "0.179199",
  "error": ""
}
```

### Evidence #82 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792170343

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 53.1275842369223,
  "sample_clock": 1792170297,
  "age_seconds": 46,
  "item_id": "50856",
  "raw_value": "53.1275842369223",
  "error": ""
}
```

### Evidence #83 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792170343

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "timed out",
  "errno": null,
  "status": "timeout",
  "duration_ms": 2013.46
}
```

### Evidence #84 — agent_metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792170345

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
    "lastclock": "1792170262",
    "lastvalue": "1"
  },
  "sample_clock": 1792170262
}
```

### Evidence #85 — cpu_history

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792170345

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1792170097,
      "value": 12.852722
    },
    {
      "clock": 1792170157,
      "value": 12.407173
    },
    {
      "clock": 1792170217,
      "value": 15.506271999999996
    },
    {
      "clock": 1792170277,
      "value": 12.998712999999995
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
      "lastclock": "1792170271",
      "lastvalue": "0.179199"
    }
  },
  "item_id": "50822"
}
```

### Evidence #86 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792170346

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=0.920 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 0.920/0.920/0.920/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 8.89
}
```


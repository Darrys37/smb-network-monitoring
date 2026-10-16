# Hồ sơ sự cố #21

- Event ID: 937
- Tên sự cố: SRV01: HTTP check failed
- Mức độ severity: 3
- Thời điểm event (Unix): 1792170816
- Số evidence: 10
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 938; thời điểm Unix 1792170931; khoảng cách hai event 115 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

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

### Evidence #97 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792170821

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 1,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 0 received, 100% packet loss, time 0ms",
  "stderr": "",
  "status": "no_reply",
  "duration_ms": 2013.77
}
```

### Evidence #98 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792170823

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "timed out",
  "errno": null,
  "status": "timeout",
  "duration_ms": 2004.14
}
```

### Evidence #99 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792170825

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 16.013013,
  "sample_clock": 1792170757,
  "age_seconds": 68,
  "item_id": "50822",
  "raw_value": "16.013013",
  "error": ""
}
```

### Evidence #100 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792170825

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 15.962549999999993,
  "sample_clock": 1792170780,
  "age_seconds": 45,
  "item_id": "50823",
  "raw_value": "15.962549999999993",
  "error": ""
}
```

### Evidence #101 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792170825

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 0.0,
  "sample_clock": 1792170752,
  "age_seconds": 73,
  "item_id": "50791",
  "raw_value": "0",
  "error": ""
}
```

### Evidence #102 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792170825

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 53.12808694562451,
  "sample_clock": 1792170777,
  "age_seconds": 48,
  "item_id": "50856",
  "raw_value": "53.12808694562451",
  "error": ""
}
```

### Evidence #103 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792170825

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "timed out",
  "errno": null,
  "status": "timeout",
  "duration_ms": 2014.25
}
```

### Evidence #104 — agent_metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792170827

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
    "lastclock": "1792170742",
    "lastvalue": "1"
  },
  "sample_clock": 1792170742
}
```

### Evidence #105 — cpu_history

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792170827

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1792170577,
      "value": 15.096727999999999
    },
    {
      "clock": 1792170722,
      "value": 12.920837000000006
    },
    {
      "clock": 1792170757,
      "value": 16.013013
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
      "lastclock": "1792170752",
      "lastvalue": "0"
    }
  },
  "item_id": "50822"
}
```

### Evidence #106 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792170827

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=0.591 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 0.591/0.591/0.591/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 8.64
}
```


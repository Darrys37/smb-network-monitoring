# Hồ sơ sự cố #34

- Event ID: 975
- Tên sự cố: Linux: High CPU utilization (over 90% for 5m)
- Mức độ severity: 2
- Thời điểm event (Unix): 1792185278
- Số evidence: 10
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 976; thời điểm Unix 1792185337; khoảng cách hai event 59 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

## Kết quả chẩn đoán

### R1_HOST_OR_LOCAL_CONNECTIVITY — not_matched

Nhận định: Target responded to ICMP or TCP.

### R2_HTTP_SERVICE_SUSPECTED — not_matched

Nhận định: Target ping=success, TCP80=success.

### R3_AGENT_UNAVAILABLE — not_matched

Nhận định: A recent agent.ping sample exists.

### R4_DNS_RESOLVER_SUSPECTED — insufficient_evidence

Nhận định: DNS target not configured.

**Thông tin còn thiếu:**

- Actual application name and CLI01 DNS evidence.

### R5_HTTP_ACCESS_FILTER_SUSPECTED — not_matched

Nhận định: No isolated remote HTTP connection failure with working ICMP.

### R6_SUSTAINED_CPU_HIGH — matched

Nhận định: Mean CPU=100.00% over 241s; threshold=90%; load=1.00, CPUs=1.

Nguyên nhân khả dĩ: Mean CPU=100.00% over 241s; threshold=90%; load=1.00, CPUs=1.

**Thông tin còn thiếu:**

- Response-time baseline and top processes; CPU and load suggest but do not prove overload.

**Kiểm tra tiếp theo:**

- Compare load and response time; inspect top processes.

## Bằng chứng đã lưu

### Evidence #239 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792185279

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=3.49 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 3.494/3.494/3.494/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 10.07
}
```

### Evidence #240 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792185279

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 1.85
}
```

### Evidence #241 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792185279

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 100.0,
  "sample_clock": 1792185278,
  "age_seconds": 1,
  "item_id": "50822",
  "raw_value": "100",
  "error": ""
}
```

### Evidence #242 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792185279

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 15.360212000000004,
  "sample_clock": 1792185239,
  "age_seconds": 40,
  "item_id": "50823",
  "raw_value": "15.360212000000004",
  "error": ""
}
```

### Evidence #243 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792185279

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 1.0,
  "sample_clock": 1792185271,
  "age_seconds": 8,
  "item_id": "50791",
  "raw_value": "1",
  "error": ""
}
```

### Evidence #244 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792185279

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 53.13167772206888,
  "sample_clock": 1792185238,
  "age_seconds": 41,
  "item_id": "50856",
  "raw_value": "53.13167772206888",
  "error": ""
}
```

### Evidence #245 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792185279

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 1.5
}
```

### Evidence #246 — agent_metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792185279

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
    "lastclock": "1792185262",
    "lastvalue": "1"
  },
  "sample_clock": 1792185262
}
```

### Evidence #247 — cpu_history

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792185279

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1792185037,
      "value": 100.0
    },
    {
      "clock": 1792185097,
      "value": 100.0
    },
    {
      "clock": 1792185157,
      "value": 100.0
    },
    {
      "clock": 1792185217,
      "value": 100.0
    },
    {
      "clock": 1792185278,
      "value": 100.0
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
      "lastclock": "1792185271",
      "lastvalue": "1"
    }
  },
  "item_id": "50822"
}
```

### Evidence #248 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792185279

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=1.70 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.698/1.698/1.698/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 5.68
}
```


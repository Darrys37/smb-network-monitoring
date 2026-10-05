# Hồ sơ sự cố #15

- Event ID: 742
- Tên sự cố: Linux: High CPU utilization (over 90% for 5m)
- Mức độ severity: 2
- Thời điểm event (Unix): 1791197317
- Số evidence: 10
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 744; thời điểm Unix 1791197497; khoảng cách hai event 180 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

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

Nhận định: Mean CPU=100.00% over 240s; threshold=90%; load=1.09, CPUs=1.

Nguyên nhân khả dĩ: Mean CPU=100.00% over 240s; threshold=90%; load=1.09, CPUs=1.

**Thông tin còn thiếu:**

- Response-time baseline and top processes; CPU and load suggest but do not prove overload.

**Kiểm tra tiếp theo:**

- Compare load and response time; inspect top processes.

## Bằng chứng đã lưu

### Evidence #35 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791197466

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=2.16 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 2.159/2.159/2.159/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 24.02
}
```

### Evidence #36 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791197466

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 3.5
}
```

### Evidence #37 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791197467

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 100.0,
  "sample_clock": 1791197437,
  "age_seconds": 30,
  "item_id": "50822",
  "raw_value": "100",
  "error": ""
}
```

### Evidence #38 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791197467

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 15.265529,
  "sample_clock": 1791197459,
  "age_seconds": 8,
  "item_id": "50823",
  "raw_value": "15.265529",
  "error": ""
}
```

### Evidence #39 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791197467

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 1.087402,
  "sample_clock": 1791197431,
  "age_seconds": 36,
  "item_id": "50791",
  "raw_value": "1.087402",
  "error": ""
}
```

### Evidence #40 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791197467

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 53.0461813349286,
  "sample_clock": 1791197457,
  "age_seconds": 10,
  "item_id": "50856",
  "raw_value": "53.0461813349286",
  "error": ""
}
```

### Evidence #41 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791197467

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 4.07
}
```

### Evidence #42 — agent_metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791197467

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
    "lastclock": "1791197422",
    "lastvalue": "1"
  },
  "sample_clock": 1791197422
}
```

### Evidence #43 — cpu_history

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791197467

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1791197197,
      "value": 100.0
    },
    {
      "clock": 1791197257,
      "value": 100.0
    },
    {
      "clock": 1791197317,
      "value": 100.0
    },
    {
      "clock": 1791197377,
      "value": 100.0
    },
    {
      "clock": 1791197437,
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
      "lastclock": "1791197431",
      "lastvalue": "1.087402"
    }
  },
  "item_id": "50822"
}
```

### Evidence #44 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1791197467

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 1,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 0 received, 100% packet loss, time 0ms",
  "stderr": "",
  "status": "no_reply",
  "duration_ms": 2011.27
}
```



# Hồ sơ sự cố #36

- Event ID: 979
- Tên sự cố: Linux: High CPU utilization (over 90% for 5m)
- Mức độ severity: 2
- Thời điểm event (Unix): 1792186717
- Số evidence: 10
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 980; thời điểm Unix 1792186777; khoảng cách hai event 60 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

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

Nhận định: Mean CPU=100.00% over 300s; threshold=90%; load=1.02, CPUs=1.

Nguyên nhân khả dĩ: Mean CPU=100.00% over 300s; threshold=90%; load=1.02, CPUs=1.

**Thông tin còn thiếu:**

- Response-time baseline and top processes; CPU and load suggest but do not prove overload.

**Kiểm tra tiếp theo:**

- Compare load and response time; inspect top processes.

## Bằng chứng đã lưu

### Evidence #259 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792186717

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=3.41 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 3.410/3.410/3.410/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 10.13
}
```

### Evidence #260 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792186717

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 2.6
}
```

### Evidence #261 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792186717

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 100.0,
  "sample_clock": 1792186717,
  "age_seconds": 0,
  "item_id": "50822",
  "raw_value": "100",
  "error": ""
}
```

### Evidence #262 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792186717

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 15.370036999999996,
  "sample_clock": 1792186679,
  "age_seconds": 38,
  "item_id": "50823",
  "raw_value": "15.370036999999996",
  "error": ""
}
```

### Evidence #263 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792186717

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 1.022461,
  "sample_clock": 1792186711,
  "age_seconds": 6,
  "item_id": "50791",
  "raw_value": "1.022461",
  "error": ""
}
```

### Evidence #264 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792186717

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 53.13221633853553,
  "sample_clock": 1792186677,
  "age_seconds": 40,
  "item_id": "50856",
  "raw_value": "53.13221633853553",
  "error": ""
}
```

### Evidence #265 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792186717

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 3.27
}
```

### Evidence #266 — agent_metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792186717

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
    "lastclock": "1792186702",
    "lastvalue": "1"
  },
  "sample_clock": 1792186702
}
```

### Evidence #267 — cpu_history

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792186717

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1792186417,
      "value": 100.0
    },
    {
      "clock": 1792186477,
      "value": 100.0
    },
    {
      "clock": 1792186537,
      "value": 100.0
    },
    {
      "clock": 1792186597,
      "value": 100.0
    },
    {
      "clock": 1792186657,
      "value": 100.0
    },
    {
      "clock": 1792186717,
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
      "lastclock": "1792186711",
      "lastvalue": "1.022461"
    }
  },
  "item_id": "50822"
}
```

### Evidence #268 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792186717

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=0.547 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 0.547/0.547/0.547/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 7.3
}
```


# Hồ sơ sự cố #30

- Event ID: 967
- Tên sự cố: CLI01: DNS resolution failed for example.com
- Mức độ severity: 2
- Thời điểm event (Unix): 1792173582
- Số evidence: 12
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 968; thời điểm Unix 1792173731; khoảng cách hai event 149 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

## Kết quả chẩn đoán

### R1_HOST_OR_LOCAL_CONNECTIVITY — not_matched

Nhận định: Target responded to ICMP or TCP.

### R2_HTTP_SERVICE_SUSPECTED — not_matched

Nhận định: Not applicable: HTTP service is declared absent on this host. This does not establish overall host health.

### R3_AGENT_UNAVAILABLE — not_matched

Nhận định: A recent agent.ping sample exists.

### R4_DNS_RESOLVER_SUSPECTED — matched

Nhận định: IP control works on cli01; DNS status=timeout, rcode=None.

Nguyên nhân khả dĩ: IP control works on cli01; DNS status=timeout, rcode=None.

**Thông tin còn thiếu:**

- Expected name/IP, intended resolver and resolver configuration; NXDOMAIN may be a spelling/name issue.

**Kiểm tra tiếp theo:**

- Compare CLI01 resolver settings and query the intended resolver.

### R5_HTTP_ACCESS_FILTER_SUSPECTED — not_matched

Nhận định: Not applicable: HTTP service is declared absent on this host. This does not establish overall host health.

### R6_SUSTAINED_CPU_HIGH — not_matched

Nhận định: Mean CPU=13.62%; below 90%.

## Bằng chứng đã lưu

### Evidence #194 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792173697

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=1.82 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.822/1.822/1.822/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 74.8
}
```

### Evidence #195 — tcp

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792173697

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "[Errno 111] Connection refused",
  "errno": 111,
  "status": "refused",
  "duration_ms": 18.54
}
```

### Evidence #196 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173697

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 12.150557000000006,
  "sample_clock": 1792173689,
  "age_seconds": 8,
  "item_id": "50934",
  "raw_value": "12.150557000000006",
  "error": ""
}
```

### Evidence #197 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173697

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 24.256027000000003,
  "sample_clock": 1792173651,
  "age_seconds": 46,
  "item_id": "50935",
  "raw_value": "24.256027000000003",
  "error": ""
}
```

### Evidence #198 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173697

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 0.066895,
  "sample_clock": 1792173683,
  "age_seconds": 14,
  "item_id": "50903",
  "raw_value": "0.066895",
  "error": ""
}
```

### Evidence #199 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173697

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 55.268244800115724,
  "sample_clock": 1792173649,
  "age_seconds": 48,
  "item_id": "50968",
  "raw_value": "55.268244800115724",
  "error": ""
}
```

### Evidence #200 — tcp

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792173697

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 2.77
}
```

### Evidence #201 — agent_metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173697

```json
{
  "key": "agent.ping",
  "status": "success",
  "max_age_seconds": 180,
  "item": {
    "itemid": "50894",
    "key_": "agent.ping",
    "value_type": "3",
    "status": "0",
    "units": "",
    "state": "0",
    "error": "",
    "lastclock": "1792173674",
    "lastvalue": "1"
  },
  "sample_clock": 1792173674
}
```

### Evidence #202 — cpu_history

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173697

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1792173449,
      "value": 13.730804000000006
    },
    {
      "clock": 1792173509,
      "value": 16.289511000000005
    },
    {
      "clock": 1792173569,
      "value": 10.953608000000003
    },
    {
      "clock": 1792173629,
      "value": 14.972307
    },
    {
      "clock": 1792173689,
      "value": 12.150557000000006
    }
  ],
  "support_items": {
    "system.cpu.num": {
      "itemid": "50905",
      "key_": "system.cpu.num",
      "value_type": "3",
      "status": "0",
      "units": "",
      "state": "0",
      "error": "",
      "lastclock": "1792166744",
      "lastvalue": "1"
    },
    "system.cpu.load[all,avg1]": {
      "itemid": "50903",
      "key_": "system.cpu.load[all,avg1]",
      "value_type": "0",
      "status": "0",
      "units": "",
      "state": "0",
      "error": "",
      "lastclock": "1792173683",
      "lastvalue": "0.066895"
    }
  },
  "item_id": "50934"
}
```

### Evidence #203 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792173697

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=1.03 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.032/1.032/1.032/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 9.26
}
```

### Evidence #204 — dns

- Đích kiểm tra: example.com
- Thời điểm thu thập (Unix): 1792173675

```json
{
  "record_type": "A",
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "status": "timeout",
  "dns_status": null,
  "addresses": [],
  "returncode": 9,
  "stdout": ";; communications error to 127.0.0.53#53: timed out\n\n; <<>> DiG 9.20.24-1ubuntu0.3-Ubuntu <<>> -r +time=2 +tries=1 -q example.com. -t A\n;; global options: +cmd\n;; no servers could be reached",
  "stderr": "",
  "duration_ms": 2033.32,
  "observer": "cli01"
}
```

### Evidence #205 — dns_control_ping

- Đích kiểm tra: 1.1.1.1
- Thời điểm thu thập (Unix): 1792173677

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=64 time=47.8 ms\n\n--- 1.1.1.1 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 47.830/47.830/47.830/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 61.18,
  "observer": "cli01"
}
```


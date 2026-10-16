# Hồ sơ sự cố #28

- Event ID: 963
- Tên sự cố: CLI01: DNS resolution failed for example.com
- Mức độ severity: 2
- Thời điểm event (Unix): 1792172951
- Số evidence: 12
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 964; thời điểm Unix 1792173101; khoảng cách hai event 150 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

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

Nhận định: Mean CPU=13.34%; below 90%.

## Bằng chứng đã lưu

### Evidence #170 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792173073

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=0.762 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 0.762/0.762/0.762/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 12.01
}
```

### Evidence #171 — tcp

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792173073

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "[Errno 111] Connection refused",
  "errno": 111,
  "status": "refused",
  "duration_ms": 1.93
}
```

### Evidence #172 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173073

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 14.850599000000003,
  "sample_clock": 1792173029,
  "age_seconds": 44,
  "item_id": "50934",
  "raw_value": "14.850599000000003",
  "error": ""
}
```

### Evidence #173 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173073

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 24.251748000000006,
  "sample_clock": 1792173051,
  "age_seconds": 22,
  "item_id": "50935",
  "raw_value": "24.251748000000006",
  "error": ""
}
```

### Evidence #174 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173073

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 0.023926,
  "sample_clock": 1792173023,
  "age_seconds": 50,
  "item_id": "50903",
  "raw_value": "0.023926",
  "error": ""
}
```

### Evidence #175 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173073

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 55.26754218286647,
  "sample_clock": 1792173049,
  "age_seconds": 24,
  "item_id": "50968",
  "raw_value": "55.26754218286647",
  "error": ""
}
```

### Evidence #176 — tcp

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792173073

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 2.3
}
```

### Evidence #177 — agent_metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173073

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
    "lastclock": "1792173014",
    "lastvalue": "1"
  },
  "sample_clock": 1792173014
}
```

### Evidence #178 — cpu_history

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173074

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1792172789,
      "value": 12.789636999999999
    },
    {
      "clock": 1792172849,
      "value": 13.352580000000003
    },
    {
      "clock": 1792172909,
      "value": 14.792685000000006
    },
    {
      "clock": 1792172969,
      "value": 10.903768999999997
    },
    {
      "clock": 1792173029,
      "value": 14.850599000000003
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
      "lastclock": "1792173023",
      "lastvalue": "0.023926"
    }
  },
  "item_id": "50934"
}
```

### Evidence #179 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792173074

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=1.17 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.170/1.170/1.170/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 10.86
}
```

### Evidence #180 — dns

- Đích kiểm tra: example.com
- Thời điểm thu thập (Unix): 1792173048

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
  "duration_ms": 2043.37,
  "observer": "cli01"
}
```

### Evidence #181 — dns_control_ping

- Đích kiểm tra: 1.1.1.1
- Thời điểm thu thập (Unix): 1792173050

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=64 time=47.7 ms\n\n--- 1.1.1.1 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 47.720/47.720/47.720/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 55.76,
  "observer": "cli01"
}
```


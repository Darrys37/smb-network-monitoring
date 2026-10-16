# Hồ sơ sự cố #29

- Event ID: 965
- Tên sự cố: CLI01: DNS resolution failed for example.com
- Mức độ severity: 2
- Thời điểm event (Unix): 1792173251
- Số evidence: 12
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 966; thời điểm Unix 1792173371; khoảng cách hai event 120 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

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

Nhận định: Mean CPU=13.80%; below 90%.

## Bằng chứng đã lưu

### Evidence #182 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792173339

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=0.950 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 0.950/0.950/0.950/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 9.8
}
```

### Evidence #183 — tcp

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792173339

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "[Errno 111] Connection refused",
  "errno": 111,
  "status": "refused",
  "duration_ms": 1.86
}
```

### Evidence #184 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173339

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 15.162390000000002,
  "sample_clock": 1792173329,
  "age_seconds": 10,
  "item_id": "50934",
  "raw_value": "15.162390000000002",
  "error": ""
}
```

### Evidence #185 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173339

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 24.252223,
  "sample_clock": 1792173291,
  "age_seconds": 48,
  "item_id": "50935",
  "raw_value": "24.252223",
  "error": ""
}
```

### Evidence #186 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173339

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 0.095703,
  "sample_clock": 1792173323,
  "age_seconds": 16,
  "item_id": "50903",
  "raw_value": "0.095703",
  "error": ""
}
```

### Evidence #187 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173339

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 55.26787282627789,
  "sample_clock": 1792173289,
  "age_seconds": 50,
  "item_id": "50968",
  "raw_value": "55.26787282627789",
  "error": ""
}
```

### Evidence #188 — tcp

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792173339

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 1.32
}
```

### Evidence #189 — agent_metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173339

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
    "lastclock": "1792173314",
    "lastvalue": "1"
  },
  "sample_clock": 1792173314
}
```

### Evidence #190 — cpu_history

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1792173339

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1792173089,
      "value": 13.172882999999999
    },
    {
      "clock": 1792173149,
      "value": 14.11636
    },
    {
      "clock": 1792173209,
      "value": 15.520346000000004
    },
    {
      "clock": 1792173269,
      "value": 11.017723000000004
    },
    {
      "clock": 1792173329,
      "value": 15.162390000000002
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
      "lastclock": "1792173323",
      "lastvalue": "0.095703"
    }
  },
  "item_id": "50934"
}
```

### Evidence #191 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792173339

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=1.50 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.499/1.499/1.499/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 9.08
}
```

### Evidence #192 — dns

- Đích kiểm tra: example.com
- Thời điểm thu thập (Unix): 1792173321

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
  "duration_ms": 2031.76,
  "observer": "cli01"
}
```

### Evidence #193 — dns_control_ping

- Đích kiểm tra: 1.1.1.1
- Thời điểm thu thập (Unix): 1792173323

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=64 time=50.2 ms\n\n--- 1.1.1.1 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 50.162/50.162/50.162/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 61.55,
  "observer": "cli01"
}
```


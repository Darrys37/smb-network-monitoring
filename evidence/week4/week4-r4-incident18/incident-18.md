# Hồ sơ sự cố #18

- Event ID: 835
- Tên sự cố: CLI01: DNS resolution failed for example.com
- Mức độ severity: 2
- Thời điểm event (Unix): 1791465701
- Số evidence: 12
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 836; thời điểm Unix 1791465941; khoảng cách hai event 240 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

## Kết quả chẩn đoán

### R1_HOST_OR_LOCAL_CONNECTIVITY — not_matched

Nhận định: Target responded to ICMP or TCP.

### R2_HTTP_SERVICE_SUSPECTED — matched

Nhận định: Host ping works; TCP80=refused; local HTTP=None. Service/listener or active rejection suspected.

Nguyên nhân khả dĩ: Host ping works; TCP80=refused; local HTTP=None. Service/listener or active rejection suspected.

**Thông tin còn thiếu:**

- Service state, listening sockets and firewall policy; refusal alone does not prove nginx stopped.

**Kiểm tra tiếp theo:**

- On target inspect systemctl status nginx, ss -lntp and firewall rules.

### R3_AGENT_UNAVAILABLE — not_matched

Nhận định: A recent agent.ping sample exists.

### R4_DNS_RESOLVER_SUSPECTED — matched

Nhận định: IP control works on cli01; DNS status=timeout, rcode=None.

Nguyên nhân khả dĩ: IP control works on cli01; DNS status=timeout, rcode=None.

**Thông tin còn thiếu:**

- Expected name/IP, intended resolver and resolver configuration; NXDOMAIN may be a spelling/name issue.

**Kiểm tra tiếp theo:**

- Compare CLI01 resolver settings and query the intended resolver.

### R5_HTTP_ACCESS_FILTER_SUSPECTED — insufficient_evidence

Nhận định: Need remote ping/TCP and fresh HTTP evidence from the service host.

**Thông tin còn thiếu:**

- Run http_probe.py on SRV01 and import its fresh JSON with --http-evidence.

### R6_SUSTAINED_CPU_HIGH — not_matched

Nhận định: Mean CPU=12.86%; below 90%.

## Bằng chứng đã lưu

### Evidence #65 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1791465907

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=1.02 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.023/1.023/1.023/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 9.35
}
```

### Evidence #66 — tcp

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1791465907

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "[Errno 111] Connection refused",
  "errno": 111,
  "status": "refused",
  "duration_ms": 0.97
}
```

### Evidence #67 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1791465907

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 12.277514999999994,
  "sample_clock": 1791465869,
  "age_seconds": 38,
  "item_id": "50934",
  "raw_value": "12.277514999999994",
  "error": ""
}
```

### Evidence #68 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1791465907

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 24.746005999999994,
  "sample_clock": 1791465891,
  "age_seconds": 16,
  "item_id": "50935",
  "raw_value": "24.746005999999994",
  "error": ""
}
```

### Evidence #69 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1791465907

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 0.0,
  "sample_clock": 1791465863,
  "age_seconds": 44,
  "item_id": "50903",
  "raw_value": "0",
  "error": ""
}
```

### Evidence #70 — metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1791465907

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 55.33569605604406,
  "sample_clock": 1791465889,
  "age_seconds": 18,
  "item_id": "50968",
  "raw_value": "55.33569605604406",
  "error": ""
}
```

### Evidence #71 — tcp

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1791465907

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 1.86
}
```

### Evidence #72 — agent_metric

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1791465907

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
    "lastclock": "1791465854",
    "lastvalue": "1"
  },
  "sample_clock": 1791465854
}
```

### Evidence #73 — cpu_history

- Đích kiểm tra: 10684
- Thời điểm thu thập (Unix): 1791465907

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1791465629,
      "value": 15.476629000000003
    },
    {
      "clock": 1791465689,
      "value": 11.537755000000004
    },
    {
      "clock": 1791465749,
      "value": 14.383685
    },
    {
      "clock": 1791465809,
      "value": 10.622376000000003
    },
    {
      "clock": 1791465869,
      "value": 12.277514999999994
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
      "lastclock": "1791454424",
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
      "lastclock": "1791465863",
      "lastvalue": "0"
    }
  },
  "item_id": "50934"
}
```

### Evidence #74 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791465907

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=1.11 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.110/1.110/1.110/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 8.93
}
```

### Evidence #75 — dns

- Đích kiểm tra: example.com
- Thời điểm thu thập (Unix): 1791465796

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
  "duration_ms": 2029.11,
  "observer": "cli01"
}
```

### Evidence #76 — dns_control_ping

- Đích kiểm tra: 1.1.1.1
- Thời điểm thu thập (Unix): 1791465798

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=64 time=60.7 ms\n\n--- 1.1.1.1 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 60.730/60.730/60.730/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 67.74,
  "observer": "cli01"
}
```



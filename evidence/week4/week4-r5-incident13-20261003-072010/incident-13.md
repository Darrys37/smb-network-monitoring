# Hồ sơ sự cố #13

- Event ID: 632
- Tên sự cố: SRV01: HTTP check failed
- Mức độ severity: 3
- Thời điểm event (Unix): 1791011436
- Số evidence: 11
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 636; thời điểm Unix 1791011671; khoảng cách hai event 235 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

## Kết quả chẩn đoán

### R1_HOST_OR_LOCAL_CONNECTIVITY — not_matched

Nhận định: Target responded to ICMP or TCP.

### R2_HTTP_SERVICE_SUSPECTED — not_matched

Nhận định: HTTP200 on the target's own service IP; a simple stopped-service hypothesis is not supported. Check R5.

### R3_AGENT_UNAVAILABLE — not_matched

Nhận định: A recent agent.ping sample exists.

### R4_DNS_RESOLVER_SUSPECTED — insufficient_evidence

Nhận định: DNS target not configured.

**Thông tin còn thiếu:**

- Actual application name and CLI01 DNS evidence.

### R5_HTTP_ACCESS_FILTER_SUSPECTED — matched

Nhận định: Remote ping=success, TCP80=timeout; HTTP on target's own service IP=success. Filtering/access-path failure is suspected, not proven firewall causation.

Nguyên nhân khả dĩ: Remote ping=success, TCP80=timeout; HTTP on target's own service IP=success. Filtering/access-path failure is suspected, not proven firewall causation.

**Thông tin còn thiếu:**

- Read firewall rules and relevant packet counters; compare another remote observer. Local HTTP does not traverse the same ingress path.

**Kiểm tra tiếp theo:**

- Inspect SRV01 firewall and routes; compare HTTP from CLI01 before attributing cause.

### R6_SUSTAINED_CPU_HIGH — insufficient_evidence

Nhận định: CPU history is sparse, stale or invalid.

**Thông tin còn thiếu:**

- At least 240s coverage, max 120s gap, latest sample <=180s old.

## Bằng chứng đã lưu

### Evidence #13 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791011652

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=0.772 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 0.772/0.772/0.772/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 9.84
}
```

### Evidence #14 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791011652

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "timed out",
  "errno": null,
  "status": "timeout",
  "duration_ms": 2002.33
}
```

### Evidence #15 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791011654

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 2.1398130000000037,
  "sample_clock": 1791011617,
  "age_seconds": 37,
  "item_id": "50822",
  "raw_value": "2.1398130000000037",
  "error": ""
}
```

### Evidence #16 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791011654

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 14.788692999999995,
  "sample_clock": 1791011639,
  "age_seconds": 15,
  "item_id": "50823",
  "raw_value": "14.788692999999995",
  "error": ""
}
```

### Evidence #17 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791011654

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 0.007324,
  "sample_clock": 1791011611,
  "age_seconds": 43,
  "item_id": "50791",
  "raw_value": "0.007324",
  "error": ""
}
```

### Evidence #18 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791011654

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 48.74324619835521,
  "sample_clock": 1791011637,
  "age_seconds": 17,
  "item_id": "50856",
  "raw_value": "48.74324619835521",
  "error": ""
}
```

### Evidence #19 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791011654

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 6.15
}
```

### Evidence #20 — agent_metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791011654

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
    "lastclock": "1791011602",
    "lastvalue": "1"
  },
  "sample_clock": 1791011602
}
```

### Evidence #21 — cpu_history

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791011654

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1791011377,
      "value": 2.492801
    },
    {
      "clock": 1791011437,
      "value": 8.773016999999996
    },
    {
      "clock": 1791011564,
      "value": 2.232635000000002
    },
    {
      "clock": 1791011617,
      "value": 2.1398130000000037
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
      "lastclock": "1791011013",
      "lastvalue": "2"
    },
    "system.cpu.load[all,avg1]": {
      "itemid": "50791",
      "key_": "system.cpu.load[all,avg1]",
      "value_type": "0",
      "status": "0",
      "units": "",
      "state": "0",
      "error": "",
      "lastclock": "1791011611",
      "lastvalue": "0.007324"
    }
  },
  "item_id": "50822"
}
```

### Evidence #22 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1791011654

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=1.02 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.023/1.023/1.023/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 9.36
}
```

### Evidence #23 — local_http

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791011594

```json
{
  "observer": "srv01",
  "port": 80,
  "path": "/",
  "local_address_verified": true,
  "status": "success",
  "http_status": 200,
  "error": ""
}
```



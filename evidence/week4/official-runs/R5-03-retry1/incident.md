# Hồ sơ sự cố #33

- Event ID: 973
- Tên sự cố: SRV01: HTTP check failed
- Mức độ severity: 3
- Thời điểm event (Unix): 1792184886
- Số evidence: 11
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 974; thời điểm Unix 1792184941; khoảng cách hai event 55 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

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

### R6_SUSTAINED_CPU_HIGH — not_matched

Nhận định: Mean CPU=10.47%; below 90%.

## Bằng chứng đã lưu

### Evidence #228 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792184913

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=1.17 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.170/1.170/1.170/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 7.47
}
```

### Evidence #229 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792184913

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "timed out",
  "errno": null,
  "status": "timeout",
  "duration_ms": 2001.81
}
```

### Evidence #230 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792184915

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 12.194204,
  "sample_clock": 1792184857,
  "age_seconds": 58,
  "item_id": "50822",
  "raw_value": "12.194204",
  "error": ""
}
```

### Evidence #231 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792184915

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 15.906276000000005,
  "sample_clock": 1792184879,
  "age_seconds": 36,
  "item_id": "50823",
  "raw_value": "15.906276000000005",
  "error": ""
}
```

### Evidence #232 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792184915

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 0.041992,
  "sample_clock": 1792184911,
  "age_seconds": 4,
  "item_id": "50791",
  "raw_value": "0.041992",
  "error": ""
}
```

### Evidence #233 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792184915

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 53.13135455218888,
  "sample_clock": 1792184877,
  "age_seconds": 38,
  "item_id": "50856",
  "raw_value": "53.13135455218888",
  "error": ""
}
```

### Evidence #234 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792184915

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 1.74
}
```

### Evidence #235 — agent_metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792184915

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
    "lastclock": "1792184902",
    "lastvalue": "1"
  },
  "sample_clock": 1792184902
}
```

### Evidence #236 — cpu_history

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792184915

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1792184617,
      "value": 8.999441000000004
    },
    {
      "clock": 1792184677,
      "value": 9.979326999999998
    },
    {
      "clock": 1792184737,
      "value": 10.395947000000007
    },
    {
      "clock": 1792184797,
      "value": 10.791233000000005
    },
    {
      "clock": 1792184857,
      "value": 12.194204
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
      "lastclock": "1792184911",
      "lastvalue": "0.041992"
    }
  },
  "item_id": "50822"
}
```

### Evidence #237 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792184915

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=0.882 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 0.882/0.882/0.882/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 9.24
}
```

### Evidence #238 — local_http

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792184905

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


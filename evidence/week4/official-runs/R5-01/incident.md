# Hồ sơ sự cố #31

- Event ID: 969
- Tên sự cố: SRV01: HTTP check failed
- Mức độ severity: 3
- Thời điểm event (Unix): 1792173816
- Số evidence: 11
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 970; thời điểm Unix 1792173931; khoảng cách hai event 115 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

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

Nhận định: Mean CPU=13.41%; below 90%.

## Bằng chứng đã lưu

### Evidence #206 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792173870

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=1.78 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.776/1.776/1.776/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 12.42
}
```

### Evidence #207 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792173870

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "timed out",
  "errno": null,
  "status": "timeout",
  "duration_ms": 2015.72
}
```

### Evidence #208 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792173872

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 15.518792000000005,
  "sample_clock": 1792173818,
  "age_seconds": 54,
  "item_id": "50822",
  "raw_value": "15.518792000000005",
  "error": ""
}
```

### Evidence #209 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792173872

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 15.534987999999998,
  "sample_clock": 1792173839,
  "age_seconds": 33,
  "item_id": "50823",
  "raw_value": "15.534987999999998",
  "error": ""
}
```

### Evidence #210 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792173872

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 0.0,
  "sample_clock": 1792173871,
  "age_seconds": 1,
  "item_id": "50791",
  "raw_value": "0",
  "error": ""
}
```

### Evidence #211 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792173872

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 53.1301336881978,
  "sample_clock": 1792173839,
  "age_seconds": 33,
  "item_id": "50856",
  "raw_value": "53.1301336881978",
  "error": ""
}
```

### Evidence #212 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792173872

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 3.29
}
```

### Evidence #213 — agent_metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792173872

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
    "lastclock": "1792173862",
    "lastvalue": "1"
  },
  "sample_clock": 1792173862
}
```

### Evidence #214 — cpu_history

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792173872

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1792173578,
      "value": 12.284876999999994
    },
    {
      "clock": 1792173637,
      "value": 13.504765000000006
    },
    {
      "clock": 1792173697,
      "value": 14.003236000000001
    },
    {
      "clock": 1792173757,
      "value": 11.744292000000002
    },
    {
      "clock": 1792173818,
      "value": 15.518792000000005
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
      "lastclock": "1792173871",
      "lastvalue": "0"
    }
  },
  "item_id": "50822"
}
```

### Evidence #215 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792173872

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=1.13 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.132/1.132/1.132/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 11.42
}
```

### Evidence #216 — local_http

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792173858

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


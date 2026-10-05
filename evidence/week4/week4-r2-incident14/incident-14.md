# Hồ sơ sự cố #14

- Event ID: 637
- Tên sự cố: SRV01: HTTP check failed
- Mức độ severity: 3
- Thời điểm event (Unix): 1791012331
- Số evidence: 11
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 638; thời điểm Unix 1791012451; khoảng cách hai event 120 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

## Kết quả chẩn đoán

### R1_HOST_OR_LOCAL_CONNECTIVITY — not_matched

Nhận định: Target responded to ICMP or TCP.

### R2_HTTP_SERVICE_SUSPECTED — matched

Nhận định: Host ping works; TCP80=refused; local HTTP=failed. Service/listener or active rejection suspected.

Nguyên nhân khả dĩ: Host ping works; TCP80=refused; local HTTP=failed. Service/listener or active rejection suspected.

**Thông tin còn thiếu:**

- Service state, listening sockets and firewall policy; refusal alone does not prove nginx stopped.

**Kiểm tra tiếp theo:**

- On target inspect systemctl status nginx, ss -lntp and firewall rules.

### R3_AGENT_UNAVAILABLE — not_matched

Nhận định: A recent agent.ping sample exists.

### R4_DNS_RESOLVER_SUSPECTED — insufficient_evidence

Nhận định: DNS target not configured.

**Thông tin còn thiếu:**

- Actual application name and CLI01 DNS evidence.

### R5_HTTP_ACCESS_FILTER_SUSPECTED — not_matched

Nhận định: Remote ping=success, TCP80=refused; HTTP on target's own service IP=failed. Filtering/access-path failure is suspected, not proven firewall causation.

### R6_SUSTAINED_CPU_HIGH — insufficient_evidence

Nhận định: CPU history is sparse, stale or invalid.

**Thông tin còn thiếu:**

- At least 240s coverage, max 120s gap, latest sample <=180s old.

## Bằng chứng đã lưu

### Evidence #24 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791012404

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=1.92 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.916/1.916/1.916/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 20.64
}
```

### Evidence #25 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791012404

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "[Errno 111] Connection refused",
  "errno": 111,
  "status": "refused",
  "duration_ms": 2.32
}
```

### Evidence #26 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791012404

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 9.883876,
  "sample_clock": 1791012397,
  "age_seconds": 7,
  "item_id": "50822",
  "raw_value": "9.883876",
  "error": ""
}
```

### Evidence #27 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791012404

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 14.971383000000003,
  "sample_clock": 1791012359,
  "age_seconds": 45,
  "item_id": "50823",
  "raw_value": "14.971383000000003",
  "error": ""
}
```

### Evidence #28 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791012404

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 0.0,
  "sample_clock": 1791012391,
  "age_seconds": 13,
  "item_id": "50791",
  "raw_value": "0",
  "error": ""
}
```

### Evidence #29 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791012404

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 48.74335392164854,
  "sample_clock": 1791012357,
  "age_seconds": 47,
  "item_id": "50856",
  "raw_value": "48.74335392164854",
  "error": ""
}
```

### Evidence #30 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791012404

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "",
  "errno": null,
  "status": "success",
  "duration_ms": 2.59
}
```

### Evidence #31 — agent_metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791012404

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
    "lastclock": "1791012382",
    "lastvalue": "1"
  },
  "sample_clock": 1791012382
}
```

### Evidence #32 — cpu_history

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791012404

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1791012159,
      "value": 8.174632000000003
    },
    {
      "clock": 1791012217,
      "value": 7.939797999999996
    },
    {
      "clock": 1791012277,
      "value": 7.174256999999997
    },
    {
      "clock": 1791012337,
      "value": 8.943162000000001
    },
    {
      "clock": 1791012397,
      "value": 9.883876
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
      "lastclock": "1791012391",
      "lastvalue": "0"
    }
  },
  "item_id": "50822"
}
```

### Evidence #33 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1791012404

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=0.846 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 0.846/0.846/0.846/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 13.46
}
```

### Evidence #34 — local_http

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791012374

```json
{
  "observer": "srv01",
  "port": 80,
  "path": "/",
  "local_address_verified": true,
  "status": "failed",
  "http_status": null,
  "error": "[Errno 111] Connection refused"
}
```



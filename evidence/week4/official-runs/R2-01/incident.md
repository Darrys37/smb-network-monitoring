# Hồ sơ sự cố #22

- Event ID: 939
- Tên sự cố: SRV01: HTTP check failed
- Mức độ severity: 3
- Thời điểm event (Unix): 1792171081
- Số evidence: 11
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 940; thời điểm Unix 1792171141; khoảng cách hai event 60 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

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

Nhận định: Remote ping=success, TCP80=refused; HTTP on target's own service IP=failed. The evidence does not meet R5 conditions for suspected filtering/access-path failure.

### R6_SUSTAINED_CPU_HIGH — insufficient_evidence

Nhận định: CPU history is sparse, stale or invalid.

**Thông tin còn thiếu:**

- At least 240s coverage, max 120s gap, latest sample <=180s old.

## Bằng chứng đã lưu

### Evidence #107 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792171104

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n64 bytes from 192.168.56.20: icmp_seq=1 ttl=64 time=1.38 ms\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 1.381/1.381/1.381/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 8.3
}
```

### Evidence #108 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792171104

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "[Errno 111] Connection refused",
  "errno": 111,
  "status": "refused",
  "duration_ms": 1.79
}
```

### Evidence #109 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792171104

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 13.151137000000006,
  "sample_clock": 1792171057,
  "age_seconds": 47,
  "item_id": "50822",
  "raw_value": "13.151137000000006",
  "error": ""
}
```

### Evidence #110 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792171104

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 16.075543999999994,
  "sample_clock": 1792171079,
  "age_seconds": 25,
  "item_id": "50823",
  "raw_value": "16.075543999999994",
  "error": ""
}
```

### Evidence #111 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792171104

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 0.113281,
  "sample_clock": 1792171051,
  "age_seconds": 53,
  "item_id": "50791",
  "raw_value": "0.113281",
  "error": ""
}
```

### Evidence #112 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792171104

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 53.12855374656228,
  "sample_clock": 1792171077,
  "age_seconds": 27,
  "item_id": "50856",
  "raw_value": "53.12855374656228",
  "error": ""
}
```

### Evidence #113 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792171104

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

### Evidence #114 — agent_metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792171104

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
    "lastclock": "1792171102",
    "lastvalue": "1"
  },
  "sample_clock": 1792171102
}
```

### Evidence #115 — cpu_history

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1792171104

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1792170966,
      "value": 13.266256999999996
    },
    {
      "clock": 1792170997,
      "value": 17.742524000000003
    },
    {
      "clock": 1792171057,
      "value": 13.151137000000006
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
      "lastclock": "1792171051",
      "lastvalue": "0.113281"
    }
  },
  "item_id": "50822"
}
```

### Evidence #116 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1792171104

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=0.970 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 0.970/0.970/0.970/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 9.25
}
```

### Evidence #117 — local_http

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1792171094

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


# Hồ sơ sự cố #16

- Event ID: 767
- Tên sự cố: SRV01: HTTP check failed
- Mức độ severity: 3
- Thời điểm event (Unix): 1791201456
- Số evidence: 10
- Số kết quả luật: 6

> Báo cáo dựa trên bằng chứng đã lưu lúc chạy chẩn đoán; không mặc định phản ánh đúng trạng thái tại thời điểm event.

> Trạng thái hồ sơ: closed. Recovery event 769; thời điểm Unix 1791201691; khoảng cách hai event 235 giây. Không phải thời gian downtime chính xác hay xác nhận sức khỏe hiện tại.

## Kết quả chẩn đoán

### R1_HOST_OR_LOCAL_CONNECTIVITY — insufficient_evidence

Nhận định: Cannot isolate target/local connectivity.

**Thông tin còn thiếu:**

- Fresh target ping/TCP and a distinct same-subnet control host ping.

### R2_HTTP_SERVICE_SUSPECTED — insufficient_evidence

Nhận định: Missing usable ping/TCP evidence.

**Thông tin còn thiếu:**

- Fresh ping and TCP port 80.

### R3_AGENT_UNAVAILABLE — not_matched

Nhận định: Host ping=no_reply, agent.ping has no recent data, TCP10050=timeout.

### R4_DNS_RESOLVER_SUSPECTED — insufficient_evidence

Nhận định: DNS target not configured.

**Thông tin còn thiếu:**

- Actual application name and CLI01 DNS evidence.

### R5_HTTP_ACCESS_FILTER_SUSPECTED — not_matched

Nhận định: No isolated remote HTTP connection failure with working ICMP.

### R6_SUSTAINED_CPU_HIGH — insufficient_evidence

Nhận định: CPU history is sparse, stale or invalid.

**Thông tin còn thiếu:**

- At least 240s coverage, max 120s gap, latest sample <=180s old.

## Bằng chứng đã lưu

### Evidence #45 — ping

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791201568

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 1,
  "stdout": "PING 192.168.56.20 (192.168.56.20) 56(84) bytes of data.\n\n--- 192.168.56.20 ping statistics ---\n1 packets transmitted, 0 received, 100% packet loss, time 0ms",
  "stderr": "",
  "status": "no_reply",
  "duration_ms": 2010.3
}
```

### Evidence #46 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791201570

```json
{
  "port": 80,
  "timeout_seconds": 2,
  "error": "[Errno 113] No route to host",
  "errno": 113,
  "status": "error",
  "duration_ms": 1080.81
}
```

### Evidence #47 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791201571

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 14.389270999999994,
  "sample_clock": 1791201397,
  "age_seconds": 174,
  "item_id": "50822",
  "raw_value": "14.389270999999994",
  "error": ""
}
```

### Evidence #48 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791201571

```json
{
  "key": "vm.memory.util",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 14.964955000000003,
  "sample_clock": 1791201419,
  "age_seconds": 152,
  "item_id": "50823",
  "raw_value": "14.964955000000003",
  "error": ""
}
```

### Evidence #49 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791201571

```json
{
  "key": "system.cpu.load[all,avg1]",
  "units": "",
  "max_age_seconds": 180,
  "status": "success",
  "value": 1.405762,
  "sample_clock": 1791201391,
  "age_seconds": 180,
  "item_id": "50791",
  "raw_value": "1.405762",
  "error": ""
}
```

### Evidence #50 — metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791201571

```json
{
  "key": "vfs.fs.dependent.size[/,pused]",
  "units": "%",
  "max_age_seconds": 180,
  "status": "success",
  "value": 53.04808444644411,
  "sample_clock": 1791201417,
  "age_seconds": 154,
  "item_id": "50856",
  "raw_value": "53.04808444644411",
  "error": ""
}
```

### Evidence #51 — tcp

- Đích kiểm tra: 192.168.56.20
- Thời điểm thu thập (Unix): 1791201571

```json
{
  "port": 10050,
  "timeout_seconds": 2,
  "error": "timed out",
  "errno": null,
  "status": "timeout",
  "duration_ms": 2003.3
}
```

### Evidence #52 — agent_metric

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791201573

```json
{
  "key": "agent.ping",
  "status": "no_data",
  "max_age_seconds": 180,
  "item": {
    "itemid": "50782",
    "key_": "agent.ping",
    "value_type": "3",
    "status": "0",
    "units": "",
    "state": "0",
    "error": "",
    "lastclock": "1791201390",
    "lastvalue": "1"
  },
  "sample_clock": 1791201390
}
```

### Evidence #53 — cpu_history

- Đích kiểm tra: 10683
- Thời điểm thu thập (Unix): 1791201573

```json
{
  "key": "system.cpu.util",
  "units": "%",
  "status": "success",
  "window_seconds": 300,
  "samples": [
    {
      "clock": 1791201390,
      "value": 15.044247999999996
    },
    {
      "clock": 1791201397,
      "value": 14.389270999999994
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
      "lastclock": "1791195633",
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
      "lastclock": "1791201391",
      "lastvalue": "1.405762"
    }
  },
  "item_id": "50822"
}
```

### Evidence #54 — ping

- Đích kiểm tra: 192.168.56.30
- Thời điểm thu thập (Unix): 1791201573

```json
{
  "timeout_seconds": 2,
  "process_timeout_seconds": 3,
  "returncode": 0,
  "stdout": "PING 192.168.56.30 (192.168.56.30) 56(84) bytes of data.\n64 bytes from 192.168.56.30: icmp_seq=1 ttl=64 time=2.01 ms\n\n--- 192.168.56.30 ping statistics ---\n1 packets transmitted, 1 received, 0% packet loss, time 0ms\nrtt min/avg/max/mdev = 2.010/2.010/2.010/0.000 ms",
  "stderr": "",
  "status": "success",
  "duration_ms": 15.05
}
```



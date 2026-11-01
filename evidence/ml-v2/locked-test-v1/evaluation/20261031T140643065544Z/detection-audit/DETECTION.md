# Zabbix detection coverage

Problem events are read from event.get for the target host; this is separate from prediction accuracy.

| Scenario | Runs | Configured related triggers | Detected during intervention | By selected observation |
|---|---:|---:|---:|---:|
| agent_stopped | 6 | 1 | 1 | 1 |
| cpu_stress | 6 | 2 | 1 | 1 |
| dns_egress_blocked | 6 | 0 | 0 | 0 |
| healthy | 6 | 0 | 0 | 0 |
| interface_down | 6 | 3 | 6 | 6 |
| nginx_stopped | 6 | 1 | 6 | 6 |
| remote_http_filtered | 6 | 1 | 6 | 6 |

Healthy has no expected fault trigger; significant events in intended-healthy windows are reported separately and require review before calling them false positives.

SRV01 has no dedicated DNS or ICMP trigger in the captured inventory. Network loss may produce HTTP/Agent/link symptoms. Related trigger events do not prove a unique root cause.

Strict integer-second boundaries and a separate 1-second-tolerance field are retained. Event clock delta is not a sub-second causal latency measurement.

The experiment invokes collection on a fixed fault schedule, regardless of Zabbix alerts. It does not by itself verify production alert-to-process dispatch latency.

[event.get 7.0](https://www.zabbix.com/documentation/7.0/en/manual/api/reference/event/get) and [trigger.get 7.0](https://www.zabbix.com/documentation/7.0/en/manual/api/reference/trigger/get).

# Luật học được — chỉ thống kê train

| Thuật toán | Rule ID | Nhãn lab | IF | Số lượt train hỗ trợ | Thống kê train |
|---|---|---|---|---:|---|
| CART | cart-leaf-11 | healthy | `dns_status = success AND agent_status = success AND tcp80_status = success AND cpu_percent != high_ge90` | 6 | leaf class fraction=100.0% |
| CART | cart-leaf-12 | cpu_stress | `dns_status = success AND agent_status = success AND tcp80_status = success AND cpu_percent = high_ge90` | 6 | leaf class fraction=100.0% |
| CART | cart-leaf-2 | interface_down | `dns_status != success AND local_http_status != http_200` | 6 | leaf class fraction=100.0% |
| CART | cart-leaf-3 | dns_egress_blocked | `dns_status != success AND local_http_status = http_200` | 6 | leaf class fraction=100.0% |
| CART | cart-leaf-5 | agent_stopped | `dns_status = success AND agent_status != success` | 6 | leaf class fraction=100.0% |
| CART | cart-leaf-8 | remote_http_filtered | `dns_status = success AND agent_status = success AND tcp80_status != success AND local_http_status != failed` | 6 | leaf class fraction=100.0% |
| CART | cart-leaf-9 | nginx_stopped | `dns_status = success AND agent_status = success AND tcp80_status != success AND local_http_status = failed` | 6 | leaf class fraction=100.0% |
| FP-Growth | fp-0000 | agent_stopped | `agent_status=no_data` | 6 | support=0.143; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0001 | cpu_stress | `cpu_percent=high_ge90` | 6 | support=0.143; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0002 | dns_egress_blocked | `dns_status=timeout` | 6 | support=0.143; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0003 | nginx_stopped | `local_http_status=failed` | 6 | support=0.143; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0004 | interface_down | `ping_status=no_reply` | 6 | support=0.143; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0005 | agent_stopped | `tcp10050_status=refused` | 6 | support=0.143; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0006 | nginx_stopped | `tcp80_status=refused` | 6 | support=0.143; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0007 | cpu_stress | `cpu_mean=high_ge90` | 5 | support=0.119; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0008 | interface_down | `tcp10050_status=timeout` | 5 | support=0.119; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0009 | remote_http_filtered | `tcp80_status=timeout` | 6 | support=0.143; association confidence=85.7%; lift=6.000 |
| FP-Growth | fp-0010 | remote_http_filtered | `dns_status=success AND tcp80_status=timeout` | 6 | support=0.143; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0011 | remote_http_filtered | `local_http_status=http_200 AND tcp80_status=timeout` | 6 | support=0.143; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0012 | remote_http_filtered | `ping_status=success AND tcp80_status=timeout` | 6 | support=0.143; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0013 | remote_http_filtered | `tcp10050_status=success AND tcp80_status=timeout` | 6 | support=0.143; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0014 | remote_http_filtered | `cpu_coverage_seconds=sufficient AND tcp80_status=timeout` | 4 | support=0.095; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0015 | remote_http_filtered | `cpu_max_gap_seconds=gap_large AND tcp80_status=timeout` | 2 | support=0.048; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0016 | remote_http_filtered | `cpu_mean=below90 AND tcp80_status=timeout` | 2 | support=0.048; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0017 | healthy | `cpu_percent=below90 AND dns_status=success AND tcp80_status=success` | 6 | support=0.143; association confidence=100.0%; lift=7.000 |
| FP-Growth | fp-0018 | healthy | `cpu_coverage_seconds=short AND dns_status=success AND tcp80_status=success` | 3 | support=0.071; association confidence=100.0%; lift=7.000 |

Các phần trăm trên không phải xác suất chẩn đoán đã hiệu chỉnh. Kết quả test nằm trong báo cáo chính; nhãn mô tả kịch bản lab, không chứng minh nguyên nhân vật lý duy nhất.

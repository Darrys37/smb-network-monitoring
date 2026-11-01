# Pilot data quality

Registered: 54; valid: 43; windows: 105.

| Label | Valid runs |
|---|---:|
| agent_stopped | 6 |
| cpu_stress | 6 |
| dns_egress_blocked | 6 |
| healthy | 6 |
| interface_down | 6 |
| nginx_stopped | 7 |
| remote_http_filtered | 6 |

Source errors are retained. A failed SSH probe during interface-down is missing evidence, not a successful negative measurement.

Inspect pre-intervention metric samples before building supervised features. Valid injection labels do not imply every window is stable.

The old single Nginx trial, smoke session and scheduled pilot are separate groups; do not treat them as three randomized sessions.

No test accuracy can be claimed from this audit. Complete the planned independent sessions before model evaluation.

# Pilot data quality

Registered: 13; valid: 8; windows: 24.

| Label | Valid runs |
|---|---:|
| agent_stopped | 1 |
| cpu_stress | 1 |
| dns_egress_blocked | 1 |
| healthy | 1 |
| interface_down | 1 |
| nginx_stopped | 2 |
| remote_http_filtered | 1 |

Source errors are retained. A failed SSH probe during interface-down is missing evidence, not a successful negative measurement.

Inspect pre-intervention metric samples before building supervised features. Valid injection labels do not imply every window is stable.

The old single Nginx trial, smoke session and scheduled pilot are separate groups; do not treat them as three randomized sessions.

No test accuracy can be claimed from this audit. Complete the planned independent sessions before model evaluation.

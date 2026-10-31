"""Fixed lab fault plans. Rollback touches only the resource owned by a run."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class FaultPlan:
    label: str
    hold_seconds: int
    inject: str
    rollback: str
    verify: str


def plan(label, token):
    if not re.fullmatch('[a-f0-9]{12}', token):
        raise ValueError('Unsafe run token')
    table = 'mlv2_'+token
    stress = 'mlv2-stress-'+token
    delete_table = f'''tables="$(nft list tables)"
if printf '%s\\n' "$tables" | grep -Fxq 'table inet {table}'; then
  nft delete table inet {table}
fi'''
    stop_stress = f'''if [ "$(systemctl show --property=LoadState --value {stress}.service)" != not-found ]; then
  systemctl stop {stress}.service
fi'''
    definitions = {
        'healthy': FaultPlan(label, 30, ':', ':', 'systemctl is-active nginx zabbix-agent2'),
        'nginx_stopped': FaultPlan(label, 40, 'systemctl stop nginx', 'systemctl start nginx',
                                  'test "$(systemctl is-active nginx)" = inactive'),
        'agent_stopped': FaultPlan(label, 210, 'systemctl stop zabbix-agent2', 'systemctl start zabbix-agent2',
                                  'test "$(systemctl is-active zabbix-agent2)" = inactive'),
        'interface_down': FaultPlan(label, 55, 'ip link set dev enp0s8 down', 'ip link set dev enp0s8 up',
                                   'ip -j link show dev enp0s8 | python3 -c \'import json,sys; assert "UP" not in json.load(sys.stdin)[0]["flags"]\''),
        'remote_http_filtered': FaultPlan(label, 40,
            f'''nft add table inet {table}
nft 'add chain inet {table} input {{ type filter hook input priority 0; policy accept; }}'
nft add rule inet {table} input ip saddr 192.168.56.10 tcp dport 80 counter drop''',
            delete_table, f'nft list table inet {table}'),
        'dns_egress_blocked': FaultPlan(label, 40,
            f'''nft add table inet {table}
nft 'add chain inet {table} output {{ type filter hook output priority 0; policy accept; }}'
nft add rule inet {table} output udp dport 53 counter drop
nft add rule inet {table} output tcp dport 53 counter drop''',
            delete_table, f'nft list table inet {table}'),
        'cpu_stress': FaultPlan(label, 330,
            f'systemd-run --unit={stress} --property=RuntimeMaxSec=450s /usr/bin/stress-ng --cpu "$(nproc)" --cpu-load 100 --timeout 420s --metrics-brief',
            stop_stress, f'sleep 1; systemctl is-active {stress}.service'),
    }
    if label not in definitions:
        raise ValueError('Unsupported intervention')
    return definitions[label]


def scripts(spec, directory):
    if not re.fullmatch(r'/home/phat/ml-experiments/[a-zA-Z0-9_-]+', directory):
        raise ValueError('Unsafe remote trial directory')
    header = '#!/bin/bash\nset -euo pipefail\n'
    guard = '''test "$(hostname -s)" = srv01
ip -j -4 address show dev enp0s8 | python3 -c 'import json,sys; assert any(a.get("local")=="192.168.56.20" for link in json.load(sys.stdin) for a in link.get("addr_info",[]))'
'''
    # Let systemd-run acknowledge before disrupting its own SSH transport.
    delay = 'sleep 3\n' if spec.label=='interface_down' else ''
    fault = header + f'''exec >>{directory}/fault.log 2>&1
{guard}
echo FAULT_BEFORE $(date -u +%s)
{delay}
{spec.inject}
{spec.verify}
echo FAULT_VERIFIED $(date -u +%s)
'''
    # Idempotent rollback: failed verification is visible, not suppressed.
    rollback = header + f'''exec >>{directory}/rollback.log 2>&1
echo ROLLBACK_BEFORE $(date -u +%s)
{spec.rollback}
echo ROLLBACK_AFTER $(date -u +%s)
'''
    return fault, rollback

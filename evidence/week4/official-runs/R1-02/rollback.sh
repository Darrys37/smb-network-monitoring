#!/bin/bash
set -eu
base="$(dirname "$0")"
exec >>"$base/rollback.log" 2>&1
echo "ROLLBACK_BEFORE $(date -u -Is)"
/usr/sbin/ip link set dev enp0s8 up
echo "ROLLBACK_AFTER $(date -u -Is)"
/usr/sbin/ip -j -4 address show dev enp0s8
/usr/bin/systemctl is-active nginx zabbix-agent2
/usr/bin/curl --max-time 5 -s -o /dev/null -w 'LOCAL_HTTP %{http_code}\n' http://192.168.56.20/
echo "RESTORATION_LOCAL_VERIFIED $(date -u -Is)"

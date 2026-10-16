#!/bin/bash
set -eu
base="$(dirname "$0")"
exec >>"$base/rollback.log" 2>&1
echo "ROLLBACK_BEFORE $(date -u -Is)"
pid="$(cat "$base/stress.pid")"
if [[ -r /proc/$pid/comm ]] && [[ $(cat "/proc/$pid/comm") == stress-ng ]]; then
    kill -INT "$pid"
fi
for attempt in {1..10}; do
    if ! pgrep -x stress-ng; then break; fi
    sleep 1
done
echo "ROLLBACK_AFTER $(date -u -Is)"
if pgrep -a stress-ng; then exit 5; fi
systemctl is-active nginx zabbix-agent2
curl --fail --max-time 5 -s -o /dev/null -w 'LOCAL_HTTP %{http_code}\n' http://192.168.56.20/
echo "RESTORATION_LOCAL_VERIFIED $(date -u -Is)"

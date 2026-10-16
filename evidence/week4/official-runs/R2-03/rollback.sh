#!/bin/bash
set -eu
exec >>"/home/phat/do-an/evidence/week4/official-runs/R2-03/rollback.log" 2>&1
echo "ROLLBACK_BEFORE $(date -u -Is)"
/usr/bin/systemctl start "nginx"
echo "ROLLBACK_AFTER $(date -u -Is)"
/usr/bin/systemctl is-active nginx zabbix-agent2
/usr/bin/curl --fail --max-time 5 -s -o /dev/null -w 'LOCAL_HTTP %{http_code}\n' http://192.168.56.20/
echo "RESTORATION_LOCAL_VERIFIED $(date -u -Is)"
/usr/bin/systemctl stop "r2-03-failsafe.timer"

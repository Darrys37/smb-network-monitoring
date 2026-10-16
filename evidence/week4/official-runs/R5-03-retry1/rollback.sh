#!/bin/bash
set -eu
exec >>"/home/phat/do-an/evidence/week4/official-runs/R5-03-retry1/rollback.log" 2>&1
echo "ROLLBACK_BEFORE $(date -u -Is)"
/usr/sbin/nft delete table inet "trial_r5_03_retry1"
echo "ROLLBACK_AFTER $(date -u -Is)"
/usr/sbin/nft list tables
/usr/bin/systemctl is-active zabbix-agent2
/usr/bin/systemctl is-active nginx
/usr/bin/curl --fail --max-time 5 -s -o /dev/null -w 'LOCAL_HTTP %{http_code}\n' http://192.168.56.20/
echo "RESTORATION_LOCAL_VERIFIED $(date -u -Is)"
/usr/bin/systemctl stop "r5-03-retry1-failsafe.timer"

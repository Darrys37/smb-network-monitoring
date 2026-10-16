#!/bin/bash
set -eu
exec >>"/home/phat/do-an/evidence/week4/official-runs/R4-02/rollback.log" 2>&1
echo "ROLLBACK_BEFORE $(date -u -Is)"
/usr/sbin/nft delete table inet "trial_r4_02"
echo "ROLLBACK_AFTER $(date -u -Is)"
/usr/sbin/nft list tables
/usr/bin/systemctl is-active zabbix-agent2
/usr/bin/dig +time=2 +tries=1 example.com A | /usr/bin/grep 'status: NOERROR'
echo "RESTORATION_LOCAL_VERIFIED $(date -u -Is)"
/usr/bin/systemctl stop "r4-02-failsafe.timer"

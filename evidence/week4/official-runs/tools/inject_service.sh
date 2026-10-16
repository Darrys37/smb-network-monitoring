#!/bin/bash
set -euo pipefail
runid="$1"
[[ "$runid" =~ ^R[23]-0[123]$ ]] || exit 2
[[ $(hostname -s) == srv01 ]] || exit 3
base="/home/phat/do-an/evidence/week4/official-runs/$runid"
mkdir -p "$base"
exec >>"$base/fault.log" 2>&1
test ! -e "$base/fault-started.marker"
if [[ "$runid" == R2-* ]]; then
    service=nginx
    seconds=600
else
    service=zabbix-agent2
    seconds=900
fi
date -u -Is
hostname
uname -r
nproc
timedatectl show -p NTPSynchronized
systemctl is-active nginx zabbix-agent2
[[ -z $(nft list tables) ]]
if pgrep -x stress-ng; then exit 4; fi
curl --fail --max-time 5 -s -o /dev/null -w 'LOCAL_HTTP_BEFORE %{http_code}\n' http://192.168.56.20/
cat >"$base/rollback.sh" <<ROLLBACK
#!/bin/bash
set -eu
exec >>"$base/rollback.log" 2>&1
echo "ROLLBACK_BEFORE \$(date -u -Is)"
/usr/bin/systemctl start "$service"
echo "ROLLBACK_AFTER \$(date -u -Is)"
/usr/bin/systemctl is-active nginx zabbix-agent2
/usr/bin/curl --fail --max-time 5 -s -o /dev/null -w 'LOCAL_HTTP %{http_code}\\n' http://192.168.56.20/
echo "RESTORATION_LOCAL_VERIFIED \$(date -u -Is)"
/usr/bin/systemctl stop "${runid,,}-failsafe.timer"
ROLLBACK
systemd-run --unit="${runid,,}-failsafe" --on-active="${seconds}s" --timer-property=AccuracySec=1s /bin/bash "$base/rollback.sh"
systemctl list-timers "${runid,,}-failsafe.timer" --no-pager
touch "$base/fault-started.marker"
echo "FAULT_BEFORE $(date -u -Is)"
systemctl stop "$service"
echo "FAULT_AFTER $(date -u -Is)"
systemctl is-active "$service" || true
ss -lntp

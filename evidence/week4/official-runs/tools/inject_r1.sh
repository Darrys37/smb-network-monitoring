#!/bin/bash
set -euo pipefail
runid="$1"
[[ "$runid" =~ ^R1-0[123]$ ]] || exit 2
[[ $(hostname -s) == srv01 ]] || exit 3
base="/home/phat/do-an/evidence/week4/official-runs/$runid"
mkdir -p "$base"
exec >>"$base/fault.log" 2>&1
test ! -e "$base/fault-started.marker"
date -u -Is
hostname
uname -r
nproc
timedatectl show -p NTPSynchronized
systemctl is-active nginx zabbix-agent2
ip -j -4 address show dev enp0s8
ip -4 address show dev enp0s8 | /usr/bin/grep -q '192.168.56.20/24'
[[ -z $(nft list tables) ]]
if pgrep -x stress-ng; then exit 4; fi
cat >"$base/rollback.sh" <<'ROLLBACK'
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
ROLLBACK
unit="${runid,,}"
# Independent operator-planned rollback at 120s; 600s timer is the protocol failsafe.
# This is fault-control infrastructure, not diagnosis-engine remediation.
systemd-run --unit="$unit-failsafe" --on-active=600s --timer-property=AccuracySec=1s /usr/sbin/ip link set dev enp0s8 up
systemd-run --unit="$unit-rollback" --on-active=120s --timer-property=AccuracySec=1s /bin/bash "$base/rollback.sh"
systemctl list-timers "$unit-rollback.timer" "$unit-failsafe.timer" --no-pager
touch "$base/fault-started.marker"
echo "FAULT_BEFORE $(date -u -Is)"
ip link set dev enp0s8 down
echo "FAULT_AFTER $(date -u -Is)"
ip -j link show dev enp0s8

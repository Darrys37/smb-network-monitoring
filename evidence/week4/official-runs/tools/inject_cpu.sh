#!/bin/bash
set -euo pipefail
runid="$1"
[[ "$runid" =~ ^R6-0[123]$ ]] || exit 2
[[ $(hostname -s) == srv01 && $(nproc) == 1 ]] || exit 3
base="/home/phat/do-an/evidence/week4/official-runs/$runid"
mkdir -p "$base"
exec >>"$base/fault.log" 2>&1
test ! -e "$base/fault-started.marker"
command -v stress-ng
date -u -Is
hostname
uname -r
nproc
uptime
timedatectl show -p NTPSynchronized
systemctl is-active nginx zabbix-agent2
[[ -z $(nft list tables) ]]
if pgrep -x stress-ng; then exit 4; fi
cat >"$base/rollback.sh" <<'ROLLBACK'
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
ROLLBACK
touch "$base/fault-started.marker"
echo "FAULT_BEFORE $(date -u -Is)"
stress-ng --cpu 1 --cpu-load 100 --timeout 12m --metrics-brief >"$base/stress.log" 2>&1 &
worker=$!
echo "$worker" >"$base/stress.pid"
echo "FAULT_AFTER $(date -u -Is)"
ps -p "$worker" -o pid,ppid,args
set +e
wait "$worker"
rc=$?
echo "FAULT_PROCESS_END $(date -u -Is) EXIT=$rc"
exit "$rc"

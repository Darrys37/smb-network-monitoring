#!/bin/bash
set -euo pipefail
runid="$1"
[[ "$runid" =~ ^R[45]-0[123](-retry[1-9][0-9]*)?$ ]] || exit 2
base="/home/phat/do-an/evidence/week4/official-runs/$runid"
table="trial_${runid,,}"
table="${table//-/_}"
if [[ "$runid" == R4-* ]]; then expected_host=cli01; else expected_host=srv01; fi
[[ $(hostname -s) == "$expected_host" ]] || exit 3
mkdir -p "$base"
exec >>"$base/fault.log" 2>&1
test ! -e "$base/fault-started.marker"
date -u -Is
hostname
uname -r
timedatectl show -p NTPSynchronized
systemctl is-active zabbix-agent2
[[ -z $(nft list tables) ]]
if [[ "$runid" == R4-* ]]; then
    resolvectl status
    dig +time=2 +tries=1 example.com A | grep 'status: NOERROR'
    ping -c 2 -W 2 1.1.1.1
else
    systemctl is-active nginx
    curl --fail --max-time 5 -s -o /dev/null -w 'LOCAL_HTTP_BEFORE %{http_code}\n' http://192.168.56.20/
    ss -lntp
fi
cat >"$base/rollback.sh" <<ROLLBACK
#!/bin/bash
set -eu
exec >>"$base/rollback.log" 2>&1
echo "ROLLBACK_BEFORE \$(date -u -Is)"
/usr/sbin/nft delete table inet "$table"
echo "ROLLBACK_AFTER \$(date -u -Is)"
/usr/sbin/nft list tables
/usr/bin/systemctl is-active zabbix-agent2
ROLLBACK
if [[ "$runid" == R4-* ]]; then
    cat >>"$base/rollback.sh" <<'ROLLBACK'
/usr/bin/dig +time=2 +tries=1 example.com A | /usr/bin/grep 'status: NOERROR'
ROLLBACK
else
    cat >>"$base/rollback.sh" <<'ROLLBACK'
/usr/bin/systemctl is-active nginx
/usr/bin/curl --fail --max-time 5 -s -o /dev/null -w 'LOCAL_HTTP %{http_code}\n' http://192.168.56.20/
ROLLBACK
fi
cat >>"$base/rollback.sh" <<ROLLBACK
echo "RESTORATION_LOCAL_VERIFIED \$(date -u -Is)"
/usr/bin/systemctl stop "${runid,,}-failsafe.timer"
ROLLBACK
systemd-run --unit="${runid,,}-failsafe" --on-active=600s --timer-property=AccuracySec=1s /bin/bash "$base/rollback.sh"
nft add table inet "$table"
if [[ "$runid" == R4-* ]]; then
    nft "add chain inet $table output { type filter hook output priority 0; policy accept; }"
    touch "$base/fault-started.marker"
    echo "FAULT_BEFORE $(date -u -Is)"
    nft add rule inet "$table" output udp dport 53 counter drop
    nft add rule inet "$table" output tcp dport 53 counter drop
else
    nft "add chain inet $table input { type filter hook input priority 0; policy accept; }"
    touch "$base/fault-started.marker"
    echo "FAULT_BEFORE $(date -u -Is)"
    nft add rule inet "$table" input ip saddr 192.168.56.10 tcp dport 80 counter drop
fi
echo "FAULT_AFTER $(date -u -Is)"
nft list table inet "$table"

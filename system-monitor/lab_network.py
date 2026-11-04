"""Owned, reversible routed overlay for three existing VMs; management stays intact."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import socket
import subprocess
import time

NETWORK = "172.30.20.0/24"
SERVER = "172.30.20.20"
GATEWAY = "172.30.20.1"
MONITOR = "192.168.56.10"
GATEWAY_MANAGEMENT = "192.168.56.30"
TABLE = "doan_route_v3"
POLICY_TABLE = "203"
POLICY_PRIORITY = "20300"
MACS = {"srv01": "08:00:27:d3:01:20", "cli01": "08:00:27:d3:01:30"}
STATE = Path("/var/lib/do-an-system-v3/network-before.json")


def command(*args, check=True, input=None):
    return subprocess.run(list(args), input=input, capture_output=True, text=True, timeout=10, check=check)


def interface_for(host):
    links = json.loads(command("ip", "-j", "link").stdout)
    names = [row["ifname"] for row in links if row.get("address", "").lower() == MACS[host]]
    if len(names) != 1:
        raise ValueError("Expected dedicated backend NIC is missing")
    return names[0]


def exists_table():
    value = command("nft", "list", "tables").stdout
    return ("table inet " + TABLE) in value.splitlines()


def status(host):
    result = {"host": host, "routes": json.loads(command("ip", "-j", "route").stdout)}
    if host in MACS:
        interface = interface_for(host)
        result.update(interface=interface, addresses=json.loads(command("ip", "-j", "address", "show", "dev", interface).stdout))
    result["forwarding"] = Path("/proc/sys/net/ipv4/ip_forward").read_text().strip()
    result["source_policy"] = json.loads(command("ip", "-j", "rule").stdout)
    return result


def apply(host):
    initial = status(host)
    interface = initial.get("interface")
    if not STATE.exists():
        if host == "mon01" and any(row.get("dst") == NETWORK for row in initial["routes"]):
            raise ValueError("The routed test prefix is already in use")
        if host == "srv01":
            if any(str(row.get("priority")) == POLICY_PRIORITY for row in initial["source_policy"]):
                raise ValueError("Policy priority is already in use")
            prior = command("ip", "-j", "route", "show", "table", POLICY_TABLE, check=False)
            if prior.returncode == 0 and json.loads(prior.stdout):
                raise ValueError("Policy table is already in use")
        if host == "cli01" and exists_table():
            raise ValueError("The forwarding table name is already in use")
        initial["host"] = host
        initial["version"] = 1
        if interface:
            initial["rp_filter"] = Path("/proc/sys/net/ipv4/conf/" + interface + "/rp_filter").read_text().strip()
            initial["interface_was_up"] = "UP" in initial["addresses"][0].get("flags", [])
            if any(item.get("family") == "inet" for link in initial["addresses"] for item in link.get("addr_info", [])):
                raise ValueError("Dedicated backend NIC already has an IPv4 address")
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.parent.chmod(0o700)
        STATE.write_text(json.dumps(initial, indent=2), encoding="utf-8")
        STATE.chmod(0o600)
    if host == "mon01":
        command("ip", "route", "replace", NETWORK, "via", GATEWAY_MANAGEMENT, "dev", "enp0s8")
    else:
        command("ip", "link", "set", "dev", interface, "up")
        address = GATEWAY if host == "cli01" else SERVER
        command("ip", "address", "replace", address + "/24", "dev", interface)
        if host == "cli01":
            prefix = "delete table inet " + TABLE + "\n" if exists_table() else ""
            rules = prefix + f'''table inet {TABLE} {{
 chain forward {{
  type filter hook forward priority -20; policy accept;
  iifname "enp0s8" oifname "{interface}" ip saddr {MONITOR} ip daddr {SERVER} accept
  iifname "{interface}" oifname "enp0s8" ip saddr {SERVER} ip daddr {MONITOR} accept
  iifname "{interface}" drop
  oifname "{interface}" drop
 }}
}}
'''
            command("nft", "-f", "-", input=rules)
            command("sysctl", "-w", "net.ipv4.ip_forward=1")
        else:
            command("sysctl", "-w", "net.ipv4.conf." + interface + ".rp_filter=2")
            command("ip", "route", "replace", "table", POLICY_TABLE, NETWORK, "dev", interface, "src", SERVER)
            command("ip", "route", "replace", "table", POLICY_TABLE, "192.168.56.0/24", "via", GATEWAY, "dev", interface)
            rules = json.loads(command("ip", "-j", "rule").stdout)
            if not any(str(row.get("priority")) == POLICY_PRIORITY for row in rules):
                command("ip", "rule", "add", "priority", POLICY_PRIORITY, "from", SERVER + "/32", "lookup", POLICY_TABLE)
    return status(host)


def remove(host):
    before = json.loads(STATE.read_text())
    if before["host"] != host:
        raise ValueError("Network ownership snapshot belongs to another host")
    if host == "mon01":
        command("ip", "route", "del", NETWORK, "via", GATEWAY_MANAGEMENT, "dev", "enp0s8", check=False)
    else:
        interface = before["interface"]
        if host == "cli01":
            if exists_table():
                command("nft", "delete", "table", "inet", TABLE)
            command("sysctl", "-w", "net.ipv4.ip_forward=" + before["forwarding"])
        else:
            command("ip", "rule", "del", "priority", POLICY_PRIORITY, "from", SERVER + "/32", "lookup", POLICY_TABLE, check=False)
            command("ip", "route", "del", "table", POLICY_TABLE, "192.168.56.0/24", "via", GATEWAY, "dev", interface, check=False)
            command("ip", "route", "del", "table", POLICY_TABLE, NETWORK, "dev", interface, check=False)
            command("sysctl", "-w", "net.ipv4.conf." + interface + ".rp_filter=" + before["rp_filter"])
        address = GATEWAY if host == "cli01" else SERVER
        command("ip", "address", "del", address + "/24", "dev", interface, check=False)
        if not before["interface_was_up"]:
            command("ip", "link", "set", "dev", interface, "down")
    return status(host)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["apply", "remove", "status"])
    args = parser.parse_args()
    host = socket.gethostname().split(".")[0].lower()
    if host not in {"mon01", "srv01", "cli01"}:
        raise ValueError("This overlay belongs to the three named lab VMs only")
    if args.operation == "status":
        output = status(host)
    else:
        if os.geteuid() != 0:
            raise PermissionError("Network configuration requires sudo")
        with open("/run/lock/do-an-network-v3.lock", "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            output = apply(host) if args.operation == "apply" else remove(host)
    print(json.dumps(output))


if __name__ == "__main__":
    main()

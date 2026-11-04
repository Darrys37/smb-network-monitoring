"""Read-only Linux probes; DNS wire query time stays distinct from tool elapsed time."""
import ipaddress
import json
from pathlib import Path
import re
import socket
import subprocess
import time
import urllib.error
import urllib.request


def record(kind, target, result, *, observer=None, clock=None):
    return {"check_type": kind, "target": str(target), "collected_at": int(time.time()) if clock is None else clock,
            "result": {**result, **({"observer": observer} if observer else {})}}


def ping(target, observer=None):
    ipaddress.IPv4Address(target)
    try:
        value = subprocess.run(["ping", "-n", "-c", "1", "-W", "1", target], capture_output=True, text=True, timeout=3)
        status = {0: "success", 1: "no_reply"}.get(value.returncode, "error")
    except (OSError, subprocess.SubprocessError):
        status = "error"
    return record("ping", target, {"status": status}, observer=observer)


def tcp(target, port, observer=None):
    ipaddress.IPv4Address(target)
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("Invalid TCP port")
    try:
        with socket.create_connection((target, port), timeout=2):
            status = "success"
    except ConnectionRefusedError:
        status = "refused"
    except (TimeoutError, socket.timeout):
        status = "timeout"
    except OSError:
        status = "error"
    return record("tcp", target, {"status": status, "port": port}, observer=observer)


def parse_dns(output, returncode):
    code = re.search(r"status:\s*([A-Z]+)", output)
    query = re.search(r"Query time:\s*(\d+)\s*msec", output)
    addresses = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) >= 5 and fields[-2] == "A":
            try:
                addresses.append(str(ipaddress.IPv4Address(fields[-1])))
            except ipaddress.AddressValueError:
                pass
    rcode = code.group(1) if code else None
    if rcode == "NOERROR":
        status = "success" if addresses else "no_answer"
    elif rcode == "NXDOMAIN":
        status = "nxdomain"
    elif rcode:
        status = "dns_error"
    elif returncode == 9:
        status = "timeout"
    else:
        status = "error"
    return {"status": status, "record_type": "A", "dns_status": rcode, "addresses": sorted(set(addresses)),
            "response_time_ms": int(query.group(1)) if rcode and query else None}


def dns(name, observer):
    if not isinstance(name, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9.-]{0,251}[a-zA-Z0-9]", name):
        raise ValueError("Invalid DNS query name")
    before = time.perf_counter()
    try:
        value = subprocess.run(["dig", "+time=2", "+tries=1", "+comments", "+answer", "+stats", name, "A"], capture_output=True, text=True, timeout=4)
        result = parse_dns(value.stdout, value.returncode)
    except subprocess.TimeoutExpired:
        result = {"status": "timeout", "record_type": "A", "dns_status": None, "addresses": [], "response_time_ms": None}
    except OSError:
        result = {"status": "error", "record_type": "A", "dns_status": None, "addresses": [], "response_time_ms": None}
    result["tool_elapsed_ms"] = round((time.perf_counter() - before) * 1000, 3)
    return record("dns", name.lower().rstrip("."), result, observer=observer)


def local_addresses():
    value = subprocess.run(["ip", "-j", "-4", "address"], capture_output=True, text=True, timeout=3, check=True)
    return {address["local"] for link in json.loads(value.stdout) for address in link.get("addr_info", []) if address.get("family") == "inet"}


def local_http(target, observer):
    ipaddress.IPv4Address(target)
    if target not in local_addresses():
        raise ValueError("HTTP target is not assigned to this observer")
    code = None
    try:
        with urllib.request.urlopen("http://" + target + "/", timeout=3) as response:
            code = response.status
        status = "success" if code == 200 else "failed"
    except urllib.error.HTTPError as error:
        code, status = error.code, "failed"
    except (urllib.error.URLError, OSError):
        status = "failed"
    return record("local_http", target, {"status": status, "http_status": code, "port": 80, "path": "/", "local_address_verified": True}, observer=observer)


def services(target, observer):
    if target not in local_addresses():
        raise ValueError("Service target is not assigned to this observer")
    output = []
    for service in ("nginx", "zabbix-agent2"):
        value = subprocess.run(["systemctl", "is-active", service], capture_output=True, text=True, timeout=3)
        state = value.stdout.strip()
        output.append(record("service_state", target, {"status": "success" if state in {"active", "inactive", "failed", "activating", "deactivating"} else "error",
                                                       "service": service, "state": state}, observer=observer))
    return output


def routing(interface, target, observer):
    if not isinstance(interface, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.:-]{0,31}", interface):
        raise ValueError("Invalid interface")
    ipaddress.IPv4Address(target)
    forwarding = Path("/proc/sys/net/ipv4/ip_forward").read_text().strip() == "1"
    value = subprocess.run(["ip", "-j", "link", "show", "dev", interface], capture_output=True, text=True, timeout=3)
    links = json.loads(value.stdout) if value.returncode == 0 else []
    up = bool(links and "UP" in links[0].get("flags", []) and links[0].get("operstate") == "UP")
    route = subprocess.run(["ip", "-j", "route", "get", target], capture_output=True, text=True, timeout=3)
    routes = json.loads(route.stdout) if route.returncode == 0 else []
    correct_route = bool(routes and routes[0].get("dev") == interface)
    return {"observer": observer, "forwarding_enabled": forwarding, "interface": interface, "interface_up": up,
            "route_target": target, "route_uses_interface": correct_route, "ready": forwarding and up and correct_route}


def dispatch(request):
    observer = socket.gethostname().split(".")[0].lower()
    if request.get("expected_observer") != observer:
        raise ValueError("Unexpected observer")
    operation = request.get("operation")
    if operation == "http":
        return [local_http(request["target"], observer), *services(request["target"], observer)]
    if operation == "dns":
        query = dns(request["name"], observer)
        control = ping(request["control_ip"], observer)
        control["check_type"] = "dns_control_ping"
        tls = tcp(request["control_ip"], 443, observer)
        tls["check_type"] = "dns_control_tcp"
        return [query, control, tls]
    if operation == "routing":
        return routing(request["interface"], request["target"], observer)
    raise ValueError("Unsupported read-only probe")

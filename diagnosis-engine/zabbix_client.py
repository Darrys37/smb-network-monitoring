import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

ZABBIX_URL = os.getenv("ZABBIX_URL")
ZABBIX_API_TOKEN = os.getenv("ZABBIX_API_TOKEN")

def call_api(method, params, requests_id, use_token=True):
    if not ZABBIX_URL:
        raise RuntimeError("Missing ZABBIX_URL; configure .env")
    if use_token and not ZABBIX_API_TOKEN:
        raise RuntimeError("Missing ZABBIX_API_TOKEN; configure .env")
    payload = {"jsonrpc": "2.0", "method": method,
               "params": params, "id": requests_id}
    headers = {"Authorization": f"Bearer {ZABBIX_API_TOKEN}"} if use_token else {}
    try:
        response = requests.post(ZABBIX_URL, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("Zabbix API timeout after 5 seconds; database unchanged") from exc
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError("Zabbix API HTTP error; check URL and access permissions") from exc
    except requests.exceptions.RequestException as exc:
        # Do not print exception URLs or remote response bodies (may contain secrets).
        raise RuntimeError("Zabbix API connection error; check connectivity and URL") from exc
    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError("Zabbix API returned invalid JSON") from exc
    if not isinstance(data, dict) or data.get("jsonrpc") != "2.0":
        raise RuntimeError("Invalid Zabbix JSON-RPC response envelope")
    if data.get("id") != requests_id:
        raise RuntimeError("Zabbix response ID mismatch")
    if "error" in data:
        error = data["error"]
        code = error.get("code") if isinstance(error, dict) else None
        raise RuntimeError(f"Zabbix JSON-RPC error code {code}; check method, parameters and permissions")
    if "result" not in data:
        raise RuntimeError("Zabbix API response does not contain result")
    return data["result"]

def get_api_version():
    return call_api(
      method = "apiinfo.version",
      params = [],
      requests_id=1,
      use_token=False
    )


def get_hosts():
    params = {
    "output": [
      "hostid",
      "host",
      "name",
     ]
    }
    return call_api(
       method="host.get",
       params=params,
       requests_id=2
    )
def get_recent_events():
    params = {
      "output": [
          "eventid",
          "clock",
          "name",
          "severity",
          "value"
        ],
        "source": 0,
        "object": 0,
        "value": 1,
        "selectHosts": [
          "hostid",
          "host",
          "name"
        ],
       "sortfield": [
         "clock",
         "eventid"
        ],
       "sortorder": "DESC",
       "limit": 10
     }

    return call_api(
        method="event.get",
        params=params,
        requests_id=3
    )

def get_host_metrics(host_id):
    return call_api(
        "item.get",
        {
            "hostids": [str(host_id)],
            "filter": {
                "key_": [
                    "system.cpu.util",
                    "vm.memory.util",
                    "system.cpu.load[all,avg1]",
                    "vfs.fs.dependent.size[/,pused]",
                ]
            },
            "output": [
                "itemid", "name", "key_", "units",
                "lastvalue", "lastclock",
                "status", "state", "error",
            ],
        },
        requests_id=7,
    )
if __name__ == "__main__":
    try:
      version = get_api_version()
      print(f"Zabbix API version: {version}")

      events = get_recent_events()

      print("\nRecent problem events:")

      if not events:
        print("No problem events found.")

      for event in events:
        hosts = event.get("hosts", [])

        if hosts:
          host_name = hosts[0]["name"]
        else:
          host_name = "Unknown"

        timestamp = datetime.fromtimestamp(
          int(event["clock"])
        ).strftime("%Y-%m-%d %H:%M:%S")

        print(
          f'eventid={event["eventid"]}, '
          f'host={host_name}, '
          f'severity={event["severity"]}, '
          f'time={timestamp}, '
          f'name={event["name"]}'
        )

      hosts = get_hosts()

      print("\nHost:")
      for host in hosts:
        print(
          f'- ID={host["hostid"]}, '
          f'host={host["host"]}, '
          f'name={host["name"]}'
        )

    except RuntimeError as exc:
      print(f"ERROR: {exc}")
def get_open_problems(host_id):
    params = {
        "output": [
            "eventid",
            "objectid",
            "clock",
            "name",
            "severity",
            "r_eventid",
        ],
        "source": 0,
        "object": 0,
        "hostids": [str(host_id)],
        "recent": False,
        "sortfield": ["eventid"],
        "sortorder": "DESC",
    }

    return call_api(
        method="problem.get",
        params=params,
        requests_id=5,
    )
def get_event_by_id(event_id):
    params = {
        "output": [
            "eventid", "source", "object", "objectid",
            "clock",
            "name",
            "severity",
            "value",
            "r_eventid",
        ],
        "source": 0,
        "object": 0,
        "eventids": [str(event_id)],
        "selectHosts": ["hostid", "host", "name"],
    }

    events = call_api(
        method="event.get",
        params=params,
        requests_id=6,
    )

    if len(events) != 1:
        raise ValueError(
            f"Expected one accessible event for ID {event_id}; "
            f"received {len(events)}"
        )

    return events[0]


def get_items_by_keys(host_id, keys):
    items = call_api("item.get", {
        "hostids": [str(host_id)], "filter": {"key_": list(keys)},
        "output": ["itemid", "key_", "value_type", "lastclock", "lastvalue",
                   "status", "state", "error", "units"],
    }, requests_id=8)
    if not isinstance(items, list):
        raise RuntimeError("Invalid item.get result")
    return items


def get_item_history(item, start, end):
    value_type = int(item["value_type"])
    if value_type not in (0, 3):
        raise ValueError("Numeric history required")
    rows = call_api("history.get", {
        "itemids": [str(item["itemid"])], "history": value_type,
        "time_from": int(start), "time_till": int(end),
        "output": ["itemid", "clock", "value", "ns"],
        "sortfield": ["clock", "ns"], "sortorder": "ASC", "limit": 10000,
    }, requests_id=9)
    if not isinstance(rows, list) or len(rows) >= 10000:
        raise RuntimeError("Invalid or truncated history result")
    return rows

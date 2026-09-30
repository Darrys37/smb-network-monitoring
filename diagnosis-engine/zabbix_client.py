import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

ZABBIX_URL = os.getenv("ZABBIX_URL")
ZABBIX_API_TOKEN = os.getenv("ZABBIX_API_TOKEN")

def call_api(method, params, requests_id, use_token=True):
  payload = {
    "jsonrpc": "2.0",
    "method": method,
    "params": params,
    "id": requests_id
  }

  headers = {}
  if use_token:
    headers["authorization"] = f"Bearer {ZABBIX_API_TOKEN}"

  try:
    response = requests.post(
      ZABBIX_URL,
      json=payload,
      headers=headers,
      timeout=5
    )

    response.raise_for_status()
  except requests.exceptions.Timeout as exc:
    raise RuntimeError(
      "Zabbix API timeout affer 5 seconds"
    ) from exc
  except requests.exceptions.HTTPError as exc:
    raise RuntimeError(
      f"Zabbix API HTTP error: {exc}"
    ) from exc
  except requests.exceptions.RequestException as exc:
    raise RuntimeError(
      f"Zabbix API connection error: {exc}"
    ) from exc
  try:
    data = response.json()
  except ValueError as exc:
    raise RuntimeError(
      "Zabbix API returred invalid JSON"
    ) from exc

  if "error" in data:
    error = data["error"]

    raise RuntimeError(
      f'Zabbix JSON_RPC error {error.get("code")}: '
      f'{error.get("message")} - '
      f'{error.get("data")}'
   )

  if "result" not in data:
    raise RuntimeError(
      "Zabbix API response does not contain result"
    )
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

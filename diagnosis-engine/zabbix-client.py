"""Legacy filename. Prefer zabbix_client.py."""
import runpy

if __name__ == "__main__":
    runpy.run_module("zabbix_client", run_name="__main__")

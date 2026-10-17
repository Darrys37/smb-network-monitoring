"""Importing a manual helper must not unexpectedly access the lab."""

import runpy
from pathlib import Path
from unittest.mock import Mock

import zabbix_client


def test_smoke(monkeypatch):
    request = Mock(side_effect=AssertionError("Unexpected API call on import"))
    monkeypatch.setattr(zabbix_client.requests, "post", request)
    runpy.run_path(str(Path(__file__).parents[1] / "check_events.py"))
    request.assert_not_called()

from unittest.mock import patch

import pytest

from evidence import collect_metrics


@pytest.fixture
def cpu_item():
    return {
        "itemid": "50822",
        "key_": "system.cpu.util",
        "units": "%",
        "lastvalue": "12.5",
        "lastclock": "1700000190",
        "status": "0",
        "state": "0",
        "error": "",
    }


def collect_fake(items):
    with patch("evidence.get_host_metrics", return_value=items):
        with patch("evidence.time.time", return_value=1700000200):
            return collect_metrics("10683")


def test_fresh_metric_and_missing_items(cpu_item):
    records = collect_fake([cpu_item])
    by_key = {record.result["key"]: record for record in records}

    assert len(records) == 4
    cpu = by_key["system.cpu.util"]
    assert cpu.target == "10683"
    assert cpu.check_type == "metric"
    assert cpu.collected_at == 1700000200
    assert cpu.result["status"] == "success"
    assert cpu.result["value"] == 12.5
    assert cpu.result["age_seconds"] == 10
    assert by_key["vm.memory.util"].result["status"] == "missing"
    assert by_key["system.cpu.load[all,avg1]"].result["status"] == "missing"


@pytest.mark.parametrize(
    "clock, expected_status",
    [
        ("1700000020", "success"),
        ("1700000019", "stale"),
        ("1700000201", "clock_error"),
        ("0", "no_data"),
    ],
)
def test_metric_sample_time(cpu_item, clock, expected_status):
    cpu_item["lastclock"] = clock
    record = collect_fake([cpu_item])[0]

    assert record.result["status"] == expected_status


@pytest.mark.parametrize(
    "field, value, expected_status",
    [
        ("status", "1", "disabled"),
        ("state", "1", "unsupported"),
        ("lastvalue", "abc", "invalid"),
        ("lastvalue", "nan", "invalid"),
        ("lastvalue", "101", "invalid"),
        ("units", "B", "invalid"),
    ],
)
def test_unusable_metric(cpu_item, field, value, expected_status):
    cpu_item[field] = value
    record = collect_fake([cpu_item])[0]

    assert record.result["status"] == expected_status


@pytest.mark.parametrize("max_age", [0, -1, True, 1.5])
def test_invalid_max_age(max_age):
    with patch("evidence.get_host_metrics") as get_metrics:
        with pytest.raises(ValueError):
            collect_metrics("10683", max_age=max_age)

    get_metrics.assert_not_called()

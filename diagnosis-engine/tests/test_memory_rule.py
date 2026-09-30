import pytest

from models import EvidenceRecord
from rules import diagnose_memory


NOW = 1700000200
HOST_ID = "10683"


def memory(value=95, clock=NOW, target=HOST_ID,
           key="vm.memory.util", status="success"):
    return EvidenceRecord(
        check_type="metric",
        target=target,
        collected_at=NOW,
        result={
            "key": key,
            "units": "%",
            "value": value,
            "sample_clock": clock,
            "status": status,
        },
    )


@pytest.mark.parametrize(
    "value, expected",
    [
        (14.58, "not_matched"),
        (89.99, "not_matched"),
        (90, "matched"),
        (100, "matched"),
    ],
)
def test_memory_threshold(value, expected):
    diagnosis = diagnose_memory(HOST_ID, [memory(value)], now=NOW)

    assert diagnosis.rule_id == "MEMORY_HIGH"
    assert diagnosis.status == expected
    if expected == "matched":
        assert diagnosis.probable_cause is not None
        assert diagnosis.missing_info
        assert diagnosis.next_actions
    else:
        assert diagnosis.probable_cause is None


@pytest.mark.parametrize(
    "records",
    [
        [],
        [memory(target="10684")],
        [memory(clock=NOW - 181)],
        [memory(clock=NOW + 1)],
        [memory(status="unsupported")],
        [memory(key="vm.memory.size[pavailable]")],
        [memory(key="system.cpu.util")],
        [memory(value=None)],
        [memory(value=101)],
    ],
)
def test_memory_requires_usable_evidence(records):
    diagnosis = diagnose_memory(HOST_ID, records, now=NOW)

    assert diagnosis.status == "insufficient_evidence"
    assert diagnosis.probable_cause is None
    assert diagnosis.missing_info


def test_memory_accepts_age_boundary():
    diagnosis = diagnose_memory(
        HOST_ID, [memory(clock=NOW - 180)], now=NOW
    )

    assert diagnosis.status == "matched"

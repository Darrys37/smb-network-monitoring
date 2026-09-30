import pytest

from models import EvidenceRecord
from rules import diagnose_cpu


NOW = 1700000200
HOST_ID = "10683"


def cpu(value=95, sample_clock=NOW, collected_at=NOW,
        status="success", target=HOST_ID):
    return EvidenceRecord(
        check_type="metric",
        target=target,
        collected_at=collected_at,
        result={
            "key": "system.cpu.util",
            "units": "%",
            "value": value,
            "sample_clock": sample_clock,
            "status": status,
        },
    )


@pytest.mark.parametrize(
    "value, expected",
    [
        (89.99, "not_matched"),
        (90, "matched"),
        (100, "matched"),
    ],
)
def test_cpu_threshold(value, expected):
    diagnosis = diagnose_cpu(HOST_ID, [cpu(value)], now=NOW)

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
        [cpu(target="10684")],
        [cpu(sample_clock=NOW - 181)],
        [cpu(sample_clock=NOW + 1)],
        [cpu(collected_at=NOW - 181)],
        [cpu(status="unsupported")],
        [cpu(value=None)],
        [cpu(value=True)],
        [cpu(value=float("nan"))],
    ],
)
def test_cpu_requires_usable_evidence(records):
    diagnosis = diagnose_cpu(HOST_ID, records, now=NOW)

    assert diagnosis.status == "insufficient_evidence"
    assert diagnosis.probable_cause is None
    assert diagnosis.missing_info


def test_cpu_accepts_age_boundary():
    diagnosis = diagnose_cpu(
        HOST_ID,
        [cpu(sample_clock=NOW - 180)],
        now=NOW,
    )

    assert diagnosis.status == "matched"


def test_cpu_uses_latest_evidence():
    records = [
        cpu(value=20, collected_at=NOW),
        cpu(value=95, collected_at=NOW - 10, sample_clock=NOW - 10),
    ]

    diagnosis = diagnose_cpu(HOST_ID, records, now=NOW)

    assert diagnosis.status == "not_matched"

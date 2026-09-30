import pytest

from models import EvidenceRecord
from rules import diagnose_disk


NOW = 1700000200
HOST_ID = "10683"


def disk(value=95, clock=NOW, target=HOST_ID,
         key="vfs.fs.dependent.size[/,pused]", status="success"):
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
        (48.24, "not_matched"),
        (89.99, "not_matched"),
        (90, "matched"),
        (100, "matched"),
    ],
)
def test_disk_threshold(value, expected):
    diagnosis = diagnose_disk(HOST_ID, [disk(value)], now=NOW)

    assert diagnosis.rule_id == "ROOT_DISK_HIGH"
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
        [disk(target="10684")],
        [disk(clock=NOW - 181)],
        [disk(clock=NOW + 1)],
        [disk(status="unsupported")],
        [disk(key="vfs.fs.dependent.size[/boot,pused]")],
        [disk(key="vfs.fs.dependent.size[/,pfree]")],
        [disk(value=None)],
        [disk(value=101)],
    ],
)
def test_disk_requires_usable_evidence(records):
    diagnosis = diagnose_disk(HOST_ID, records, now=NOW)

    assert diagnosis.status == "insufficient_evidence"
    assert diagnosis.probable_cause is None
    assert diagnosis.missing_info


def test_disk_accepts_age_boundary():
    diagnosis = diagnose_disk(
        HOST_ID, [disk(clock=NOW - 180)], now=NOW
    )

    assert diagnosis.status == "matched"

import pytest

from models import EvidenceRecord
from rules import diagnose_reachability


NOW = 1700000200
TARGET = "192.168.56.20"


def ping(status="no_reply", target=TARGET, clock=NOW):
    return EvidenceRecord(
        check_type="ping",
        target=target,
        collected_at=clock,
        result={"status": status},
    )


def tcp(status="timeout", target=TARGET, port=80, clock=NOW):
    return EvidenceRecord(
        check_type="tcp",
        target=target,
        collected_at=clock,
        result={"status": status, "port": port},
    )


def test_reachability_matches():
    diagnosis = diagnose_reachability(
        TARGET, [ping(), tcp()], now=NOW
    )

    assert diagnosis.rule_id == "REACHABILITY_SUSPECTED"
    assert diagnosis.status == "matched"
    assert diagnosis.probable_cause is not None
    assert diagnosis.missing_info
    assert diagnosis.next_actions


@pytest.mark.parametrize(
    "ping_status, tcp_status",
    [
        ("success", "success"),
        ("success", "timeout"),
        ("no_reply", "success"),
        ("no_reply", "refused"),
    ],
)
def test_reachability_does_not_match(ping_status, tcp_status):
    diagnosis = diagnose_reachability(
        TARGET,
        [ping(ping_status), tcp(tcp_status)],
        now=NOW,
    )

    assert diagnosis.status == "not_matched"
    assert diagnosis.probable_cause is None


@pytest.mark.parametrize(
    "records",
    [
        [],
        [ping()],
        [ping(), tcp(target="192.168.56.30")],
        [ping(), tcp(port=22)],
        [ping(clock=NOW - 181), tcp()],
        [ping(), tcp(clock=NOW + 1)],
        [ping(status="timeout"), tcp()],
        [ping(), tcp(status="error")],
    ],
)
def test_reachability_requires_usable_evidence(records):
    diagnosis = diagnose_reachability(TARGET, records, now=NOW)

    assert diagnosis.status == "insufficient_evidence"
    assert diagnosis.probable_cause is None
    assert diagnosis.missing_info


def test_reachability_uses_latest_result():
    records = [
        ping(),
        tcp(status="success", clock=NOW),
        tcp(status="timeout", clock=NOW - 10),
    ]

    diagnosis = diagnose_reachability(TARGET, records, now=NOW)

    assert diagnosis.status == "not_matched"

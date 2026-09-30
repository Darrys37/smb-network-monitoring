import pytest

from models import EvidenceRecord
from rules import diagnose_http_port


TARGET = "192.168.56.20"
NOW = 1700000200


def ping(status="success", target=TARGET, clock=NOW):
    return EvidenceRecord(
        check_type="ping",
        target=target,
        collected_at=clock,
        result={"status": status},
    )


def tcp(status="refused", target=TARGET, port=80, clock=NOW):
    return EvidenceRecord(
        check_type="tcp",
        target=target,
        collected_at=clock,
        result={"status": status, "port": port},
    )


def test_rule_matches():
    diagnosis = diagnose_http_port(
        TARGET, [ping(), tcp()], now=NOW
    )

    assert diagnosis.rule_id == "HTTP_PORT_REFUSED"
    assert diagnosis.status == "matched"
    assert diagnosis.probable_cause is not None
    assert diagnosis.missing_info
    assert diagnosis.next_actions


@pytest.mark.parametrize(
    "ping_status, tcp_status",
    [
        ("success", "success"),
        ("success", "timeout"),
        ("no_reply", "refused"),
    ],
)
def test_rule_does_not_match(ping_status, tcp_status):
    diagnosis = diagnose_http_port(
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
        [ping(), tcp(clock=NOW - 181)],
        [ping(), tcp(clock=NOW + 1)],
        [ping(), tcp(status="error")],
    ],
)
def test_rule_requires_usable_evidence(records):
    diagnosis = diagnose_http_port(TARGET, records, now=NOW)

    assert diagnosis.status == "insufficient_evidence"
    assert diagnosis.probable_cause is None
    assert diagnosis.missing_info


def test_rule_accepts_age_boundary():
    diagnosis = diagnose_http_port(
        TARGET,
        [ping(clock=NOW - 180), tcp(clock=NOW - 180)],
        now=NOW,
    )

    assert diagnosis.status == "matched"


def test_rule_uses_latest_result():
    diagnosis = diagnose_http_port(
        TARGET,
        [
            ping(),
            tcp(status="success", clock=NOW),
            tcp(status="refused", clock=NOW - 10),
        ],
        now=NOW,
    )

    assert diagnosis.status == "not_matched"


def test_rule_does_not_hide_latest_error():
    diagnosis = diagnose_http_port(
        TARGET,
        [
            ping(),
            tcp(status="error", clock=NOW),
            tcp(status="refused", clock=NOW - 10),
        ],
        now=NOW,
    )

    assert diagnosis.status == "insufficient_evidence"

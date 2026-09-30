import pytest

from models import EvidenceRecord
from rules import diagnose_dns_name


NOW = 1700000200
TARGET = "example.com"


def dns(status="nxdomain", dns_status="NXDOMAIN",
        target=TARGET, clock=NOW, record_type="A"):
    return EvidenceRecord(
        check_type="dns",
        target=target,
        collected_at=clock,
        result={
            "status": status,
            "dns_status": dns_status,
            "record_type": record_type,
        },
    )


def test_dns_rule_matches():
    diagnosis = diagnose_dns_name(TARGET, [dns()], now=NOW)

    assert diagnosis.rule_id == "DNS_NAME_NOT_FOUND"
    assert diagnosis.status == "matched"
    assert diagnosis.probable_cause is not None
    assert diagnosis.missing_info
    assert diagnosis.next_actions


@pytest.mark.parametrize("status", ["success", "no_answer"])
def test_dns_rule_does_not_match_noerror(status):
    diagnosis = diagnose_dns_name(
        TARGET, [dns(status, "NOERROR")], now=NOW
    )

    assert diagnosis.status == "not_matched"
    assert diagnosis.probable_cause is None


@pytest.mark.parametrize(
    "records",
    [
        [],
        [dns(target="other.example")],
        [dns(clock=NOW - 181)],
        [dns(clock=NOW + 1)],
        [dns(status="timeout", dns_status=None)],
        [dns(status="dns_error", dns_status="SERVFAIL")],
        [dns(status="nxdomain", dns_status="NOERROR")],
        [dns(record_type="AAAA")],
    ],
)
def test_dns_rule_requires_usable_evidence(records):
    diagnosis = diagnose_dns_name(TARGET, records, now=NOW)

    assert diagnosis.status == "insufficient_evidence"
    assert diagnosis.probable_cause is None
    assert diagnosis.missing_info


def test_dns_rule_normalizes_name():
    diagnosis = diagnose_dns_name(
        "EXAMPLE.COM.", [dns()], now=NOW
    )

    assert diagnosis.status == "matched"


def test_dns_rule_uses_latest_response():
    records = [
        dns(status="success", dns_status="NOERROR", clock=NOW),
        dns(clock=NOW - 10),
    ]

    diagnosis = diagnose_dns_name(TARGET, records, now=NOW)

    assert diagnosis.status == "not_matched"


def test_dns_rule_does_not_hide_latest_timeout():
    records = [
        dns(status="timeout", dns_status=None, clock=NOW),
        dns(clock=NOW - 10),
    ]

    diagnosis = diagnose_dns_name(TARGET, records, now=NOW)

    assert diagnosis.status == "insufficient_evidence"

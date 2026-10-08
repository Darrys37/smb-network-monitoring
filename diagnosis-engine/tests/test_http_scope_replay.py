import json
from pathlib import Path

import pytest

from models import EvidenceRecord
from roadmap_rules import diagnose_roadmap


@pytest.mark.parametrize("scope,r2_status,r5_status", [
    ("expected", "matched", "insufficient_evidence"),
    ("absent", "not_matched", "not_matched"),
    ("unknown", "insufficient_evidence", "insufficient_evidence"),
])
def test_incident18_http_scope_preserves_dns(scope, r2_status, r5_status):
    path = Path(__file__).parent / "fixtures" / "incident18_http_scope.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    records = [
        EvidenceRecord(
            check_type=row["check_type"],
            target=row["target"],
            collected_at=row["collected_at"],
            result=row["result"],
        )
        for row in data["evidence"]
    ]

    # Historical replay only; never treat this snapshot as live evidence.
    replay_time = max(r.collected_at for r in records)
    diagnoses = diagnose_roadmap(
        "10684", "192.168.56.30", records,
        control="192.168.56.20",
        dns_name="example.com",
        dns_observer="cli01",
        control_ip="1.1.1.1",
        now=replay_time,
        http_service=scope,
    )
    by_rule = {d.rule_id: d for d in diagnoses}

    assert len(diagnoses) == 6
    assert by_rule["R2_HTTP_SERVICE_SUSPECTED"].status == r2_status
    assert by_rule["R5_HTTP_ACCESS_FILTER_SUSPECTED"].status == r5_status
    assert by_rule["R4_DNS_RESOLVER_SUSPECTED"].status == "matched"

    if scope == "absent":
        for rule in ("R2_HTTP_SERVICE_SUSPECTED",
                     "R5_HTTP_ACCESS_FILTER_SUSPECTED"):
            assert "Not applicable" in by_rule[rule].reasoning
            assert by_rule[rule].probable_cause is None

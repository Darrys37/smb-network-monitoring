"""The CLI and public Python dispatcher must share HTTP applicability policy."""

import pytest
from test_roadmap_rules import HOST, NOW, TARGET, healthy

import app
from roadmap_rules import diagnose_roadmap


@pytest.mark.parametrize("scope", [None, "unknown", "expected", "absent"])
def test_cli_and_dispatcher_produce_same_results(scope):
    options = [] if scope is None else ["--http-service", scope]
    args = app.build_parser().parse_args(options)
    records = healthy()
    direct_options = {} if scope is None else {"http_service": scope}
    direct = diagnose_roadmap(HOST, TARGET, records, now=NOW, **direct_options)
    through_cli = app.evaluate_evidence(args, records, now=NOW)
    assert through_cli == direct
    if scope in (None, "unknown"):
        assert direct[1].status == direct[4].status == "insufficient_evidence"
    else:
        assert direct[1].status == direct[4].status == "not_matched"


def test_invalid_http_scope_is_rejected():
    with pytest.raises(ValueError, match="scope"):
        diagnose_roadmap(HOST, TARGET, [], http_service="guess", now=NOW)

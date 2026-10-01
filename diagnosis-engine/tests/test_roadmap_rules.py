from dataclasses import replace
import pytest
from models import EvidenceRecord
from roadmap_rules import diagnose_roadmap

NOW = 1700000600
TARGET, PEER, GATEWAY = "192.168.56.20", "192.168.56.30", "192.168.56.1"
HOST = "10683"


def record(kind, target, **result):
    return EvidenceRecord(kind, target, NOW, result)


def healthy():
    return [record("ping", ip, status="success") for ip in (TARGET, PEER, GATEWAY)] + [
        record("tcp", TARGET, status="success", port=80),
        record("tcp", TARGET, status="success", port=10050),
        record("agent_metric", HOST, status="success", key="agent.ping"),
        record("dns", "service.test", observer="cli01", record_type="A", status="success", dns_status="NOERROR", addresses=[TARGET]),
        record("dns_control_ping", TARGET, observer="cli01", status="success"),
        record("cpu_history", HOST, status="success", key="system.cpu.util", units="%",
               samples=[{"clock": NOW-i, "value": 10} for i in (240, 180, 120, 60, 0)],
               support_items={k: {"status":"0", "state":"0", "lastclock":str(NOW), "lastvalue":v}
                              for k,v in [("system.cpu.num","2"),("system.cpu.load[all,avg1]","3")]}),
    ]


def change(records, kind, target, port=None, **updates):
    for i,r in enumerate(records):
        if r.check_type == kind and r.target == target and (port is None or r.result.get("port") == port):
            records[i] = replace(r, result={**r.result, **updates})


def evaluate(records):
    return diagnose_roadmap(HOST, TARGET, records, gateway=GATEWAY, peer=PEER,
                           dns_name="service.test", now=NOW)


@pytest.mark.parametrize("index", range(6))
def test_six_rules_healthy(index):
    assert evaluate(healthy())[index].status == "not_matched"


@pytest.mark.parametrize("index", range(6))
def test_six_rules_missing(index):
    assert evaluate([])[index].status == "insufficient_evidence"


@pytest.mark.parametrize("index", range(6))
def test_six_rule_matching_fixtures(index):
    rs = healthy()
    if index == 0:
        change(rs,"ping",TARGET,status="no_reply")
        change(rs,"tcp",TARGET,80,status="timeout")
    elif index == 1:
        change(rs,"tcp",TARGET,80,status="refused")
    elif index == 2:
        change(rs,"agent_metric",HOST,status="no_data")
        change(rs,"tcp",TARGET,10050,status="refused")
    elif index == 3:
        change(rs,"dns","service.test",status="timeout",dns_status=None,addresses=[])
    elif index == 4:
        for ip in (TARGET, PEER, GATEWAY):
            change(rs,"ping",ip,status="no_reply")
        change(rs,"tcp",TARGET,80,status="timeout")
    elif index == 5:
        change(rs,"cpu_history",HOST,samples=[{"clock":NOW-i,"value":95} for i in (240,180,120,60,0)])
    out = evaluate(rs)[index]
    assert out.status == "matched"
    assert out.probable_cause and out.missing_info and out.next_actions


@pytest.mark.parametrize("delta", [-181, 1])
def test_stale_and_future_evidence_rejected(delta):
    rs = [replace(r,collected_at=NOW+delta) for r in healthy()]
    assert all(r.status == "insufficient_evidence" for r in evaluate(rs))


def test_no_route_is_not_silently_changed_to_timeout():
    rs = healthy()
    change(rs,"ping",TARGET,status="no_reply")
    change(rs,"tcp",TARGET,80,status="error",errno=113)
    assert evaluate(rs)[0].status == "insufficient_evidence"


def test_latest_error_not_hidden_by_old_success():
    rs = healthy()
    old = next(r for r in rs if r.check_type=="tcp" and r.result["port"]==80)
    rs.append(replace(old,collected_at=NOW+1,result={"port":80,"status":"error"}))
    assert evaluate(rs)[1].status == "insufficient_evidence"


@pytest.mark.parametrize("status", ["disabled", "unsupported", "missing", "invalid"])
def test_agent_bad_config_not_service_failure(status):
    rs=healthy()
    change(rs,"agent_metric",HOST,status=status)
    change(rs,"tcp",TARGET,10050,status="refused")
    assert evaluate(rs)[2].status == "insufficient_evidence"


def test_dns_requires_correct_observer_and_ip_control():
    rs=healthy()
    change(rs,"dns","service.test",observer="mon01",status="timeout")
    assert evaluate(rs)[3].status == "insufficient_evidence"
    change(rs,"dns","service.test",observer="cli01")
    change(rs,"dns_control_ping",TARGET,status="no_reply")
    assert evaluate(rs)[3].status == "insufficient_evidence"


def test_dns_local_error_not_resolver_failure():
    rs=healthy()
    change(rs,"dns","service.test",status="error",dns_status=None)
    assert evaluate(rs)[3].status == "insufficient_evidence"


def test_gateway_requires_distinct_targets():
    assert diagnose_roadmap(HOST,TARGET,healthy(),gateway=TARGET,peer=PEER,now=NOW)[4].status == "insufficient_evidence"


@pytest.mark.parametrize("samples", [
    [{"clock":NOW,"value":99}],
    [{"clock":NOW-i,"value":float("nan")} for i in (240,180,120,60,0)],
    [{"clock":NOW-i,"value":99} for i in (240,0)],
    [{"clock":NOW,"value":99}]*5,
])
def test_cpu_sparse_invalid_history(samples):
    rs=healthy();change(rs,"cpu_history",HOST,samples=samples)
    assert evaluate(rs)[5].status == "insufficient_evidence"


def test_cpu_requires_load_corroboration():
    rs=healthy()
    change(rs,"cpu_history",HOST,samples=[{"clock":NOW-i,"value":99} for i in (240,180,120,60,0)],support_items={})
    assert evaluate(rs)[5].status == "insufficient_evidence"

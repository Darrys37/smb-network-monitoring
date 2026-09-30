import pytest

from event_parser import parse_event
from models import EventRecord, HostRecord

@pytest.fixture
def sample_event():
    return{
        "eventid": "90001",
        "clock": "1700000000",
"name": "TEST: HTTP check failed",
        "severity":"3",
        "value": "1",
        "hosts": [
            {
                "hostid":"10683",
                "host":"SRV01",
                "name":"SRV01",
            }
        ],
     }

def test_parse_complete_event(sample_event):
    result = parse_event(sample_event)

    expected = EventRecord(
        event_id="90001",
        clock=1700000000,
        name="TEST: HTTP check failed",
        severity=3,
        value=1,
        hosts=(
            HostRecord(
                host_id="10683",
                host="SRV01",
                name="SRV01",
            ),
        ),
    )

    assert result == expected
    assert type(result.clock) is int
    assert type(result.severity) is int
    assert type(result.value) is int

def test_reject_missing_severity(sample_event):
    del sample_event["severity"]

    with pytest.raises(ValueError, match="severity"):
        parse_event(sample_event)

def test_reject_invalid_severity(sample_event):
    sample_event["severity"] = "abc"

    with pytest.raises(ValueError, match="severity"):
       parse_event(sample_event)

@pytest.mark.parametrize("bad_value",[-1, 6, 3.5, True, None])
def test_reject_bad_severity(sample_event, bad_value):
    sample_event["severity"] = bad_value

    with pytest.raises(ValueError, match="severity"):
        parse_event(sample_event)

@pytest.mark.parametrize("severity", ["0","5"])
def test_accept_severity_boundaries(sample_event, severity):
    sample_event["severity"] = severity

    result = parse_event(sample_event)

    assert result.severity == int(severity)

def test_reject_missing_hosts(sample_event):
    del sample_event["hosts"]

    with pytest.raises(ValueError, match="hosts"):
        parse_event(sample_event)

def test_preserve_multiple_hosts(sample_event):
    sample_event["hosts"].append({
        "hostid": "10684",
        "host":"CLI01",
        "name":"CLI01",
    })

    result = parse_event(sample_event)

    assert result.hosts == (
        HostRecord(host_id="10683", host="SRV01", name ="SRV01"),
        HostRecord(host_id="10684", host="CLI01", name ="CLI01"),
    )
def test_accpet_empty_hosts(sample_event):
    sample_event["hosts"] = []
    result = parse_event(sample_event)
    assert result.hosts == ()

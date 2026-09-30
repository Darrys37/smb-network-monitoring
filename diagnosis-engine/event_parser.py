from models import EventRecord, HostRecord


def _required(data, key):
    if key not in data:
        raise ValueError(f"Missing field: {key}")
    return data[key]

def _text(data, key):
    value = _required(data,key)
    if not isinstance(value,str) or not value.strip():
        raise ValueError(f"{key}: expeted non-empty text")
    return value

def _integer(data, key, minimum=0, maximum=None):
    value = _required(data,key)

    if type(value) is int:
        number = value
    elif isinstance(value, str) and value.isascii() and value.isdecimal():
        number = int(value)
    else:
        raise ValueError(f"{key}: expected an integer")

    if number < minimum:
        raise ValueError(f"{key}: must be >= {minimum}")
    if maximum is not None and number > maximum:
        raise ValueError(f"{key}: musbe <= {maximum}")

    return number

def parse_event(raw):
    if not isinstance(raw, dict):
        raise ValueError("event must be a dicitonary")
    event_id = str(_integer(raw, "eventid",minimum=1))
    clock = _integer(raw, "clock")
    name = _text(raw,"name")
    severity = _integer(raw, "severity", maximum=5)
    value = _integer(raw,"value", maximum=1)

    raw_hosts = _required(raw, "hosts")
    if not isinstance(raw_hosts, list):
        raise ValueError("hosts: expected a list")

    hosts =[]
    for index, raw_host in enumerate(raw_hosts):
        if not isinstance(raw_host, dict):
            raise ValueError(f"hosts[{index}]: expected a dicionary")
        try:
            host_record = HostRecord(
                host_id=str(_integer(raw_host, "hostid", minimum=1)),
                host=_text(raw_host, "host"),
                name=_text(raw_host, "name"),
            )
        except ValueError as exc:
            raise ValueError(f"hosts[{index}]: {exc}") from exc
        hosts.append(host_record)
    return EventRecord(
        event_id=event_id,
        clock=clock,
        name=name,
        severity=severity,
        value=value,
        hosts=tuple(hosts),
    )

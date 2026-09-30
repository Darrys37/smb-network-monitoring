from dataclasses import dataclass

@dataclass(frozen=True)
class HostRecord:
    host_id: std
    host: str
    name: str

@dataclass(frozen=True)
class EventRecord:
    event_id: str
    clock: int
    name: str
    severity: int
    value: int
    hosts: tuple[HostRecord, ...]


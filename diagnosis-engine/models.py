from dataclasses import dataclass

@dataclass(frozen=True)
class HostRecord:
    host_id: str
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

@dataclass(frozen=True)
class EvidenceRecord:
    check_type: str
    target: str
    collected_at: int
    result: dict

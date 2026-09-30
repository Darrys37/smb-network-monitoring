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
@dataclass(frozen=True)
class DiagnosisRecord:
    rule_id: str
    status: str
    probable_cause: str | None
    reasoning: str
    missing_info: tuple[str, ...]
    next_actions: tuple[str, ...]

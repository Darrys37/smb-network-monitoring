"""Shared records between API parsing, collection, rules and storage."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HostRecord:
    """Zabbix host identity, distinct from a target network address."""

    host_id: str
    host: str
    name: str


@dataclass(frozen=True)
class EventRecord:
    """Normalized event; recovery re-reads raw API linkage fields."""

    event_id: str
    clock: int
    name: str
    severity: int
    value: int
    hosts: tuple[HostRecord, ...]


@dataclass(frozen=True)
class EvidenceRecord:
    """A timestamped observation; result retains protocol-specific raw fields."""

    check_type: str
    target: str
    collected_at: int
    result: dict


@dataclass(frozen=True)
class DiagnosisRecord:
    """One rule outcome with explanation, limitations and suggested checks."""

    rule_id: str
    status: str
    probable_cause: str | None
    reasoning: str
    missing_info: tuple[str, ...]
    next_actions: tuple[str, ...]

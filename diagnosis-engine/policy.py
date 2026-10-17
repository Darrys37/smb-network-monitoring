"""Shared roadmap policy; changing thresholds changes diagnosis semantics.

Collector windows and sample-age limits have different purposes. Keep these
values aligned with the documented experiments, rather than merging them.
"""

HTTP_SERVICE_SCOPES = ("expected", "absent", "unknown")
DEFAULT_HTTP_SERVICE = "unknown"
EVIDENCE_MAX_AGE_SECONDS = 180
PROBE_MAX_BYTES = 64 * 1024
PROBE_SCHEMA_VERSION = 1

CPU_HISTORY_WINDOW_SECONDS = 300
CPU_SAMPLE_MAX_AGE_SECONDS = CPU_HISTORY_WINDOW_SECONDS + EVIDENCE_MAX_AGE_SECONDS
CPU_MIN_SAMPLES = 3
CPU_MIN_COVERAGE_SECONDS = 240
CPU_MAX_GAP_SECONDS = 120
CPU_HIGH_PERCENT = 90
CPU_COUNT_MAX_AGE_SECONDS = 86400 + EVIDENCE_MAX_AGE_SECONDS

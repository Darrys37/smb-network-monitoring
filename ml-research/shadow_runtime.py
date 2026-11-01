"""Reuse one verified candidate snapshot; retain the frozen v2 decision semantics."""
from copy import deepcopy
from dataclasses import asdict
import importlib
from pathlib import Path
import sys
from threading import RLock

from candidate_v2 import ABSTAIN, cart_predict, discrete_row, fp_predict, load_database
from mlv2.core import sha
from mlv2.features import CATEGORICAL, FEATURES, NUMERIC, extract

_IMPORT_LOCK = RLock()


def load_expert(engine_source):
    """Import once without growing sys.path or silently using another engine."""
    engine_source = Path(engine_source).resolve()
    with _IMPORT_LOCK:
        for name in ("models", "policy", "roadmap_rules"):
            module = sys.modules.get(name)
            if module is not None and Path(getattr(module, "__file__", "")).resolve() != engine_source / (name + ".py"):
                raise ValueError("Another engine is already imported; use a separate Python process")
        previous = sys.path[:]
        try:
            sys.path.insert(0, str(engine_source))
            models = importlib.import_module("models")
            rules = importlib.import_module("roadmap_rules")
        finally:
            sys.path[:] = previous
    return models.EvidenceRecord, rules.diagnose_roadmap


class CandidateRuntime:
    """One session = one model snapshot. Construct a new session to reload it.

    Only immutable candidate data are cached; observations and predictions are
    recomputed each time. No SQLite writer, SSH, training or activation is used.
    """

    def __init__(self, database, engine_source, *, expected_sha256):
        self.database = Path(database).resolve()
        self.candidate_sha256 = sha(self.database)
        if self.candidate_sha256 != expected_sha256:
            raise ValueError("Released model artifact changed")
        self._metadata, self._rules = load_database(self.database)
        if sha(self.database) != self.candidate_sha256:
            raise ValueError("Model changed while it was being loaded")
        if (self._metadata.get("features") != FEATURES
                or self._metadata.get("categorical") != CATEGORICAL
                or self._metadata.get("numeric") != NUMERIC):
            raise ValueError("Candidate feature contract mismatch")
        if not self._rules["CART"] or not self._rules["FP-Growth"]:
            raise ValueError("Released candidate rules are empty")
        self._record, self._diagnose = load_expert(engine_source)

    def assess(self, observation):
        features = extract(observation)
        row = discrete_row(features, CATEGORICAL, NUMERIC)
        profile = observation["profile"]
        expert = self._diagnose(
            profile["host_id"], profile["target_ip"],
            [self._record(**e) for e in observation["evidence"]],
            control=profile["control_ip"], http_observer=profile["observer"],
            dns_name=profile["dns_name"], dns_observer=profile["observer"],
            control_ip=profile["dns_control_ip"], http_service=profile["http_service"],
            now=observation["decision_time"],
        )
        scope = profile == self._metadata["profile"]
        missing_core = [key for key in ("ping_status", "tcp80_status", "tcp10050_status", "control_ping_status")
                        if row[key] == "unknown"]
        if scope and not missing_core:
            suggestions = {"CART": cart_predict(self._rules["CART"], row),
                           "FP-Growth": fp_predict(self._rules["FP-Growth"], row)}
        else:
            suggestions = {name: {"label": ABSTAIN, "reason": "Outside pilot profile or incomplete core probes"}
                           for name in self._rules}
        return {
            "mode": "offline_candidate_comparison", "decision_time": observation["decision_time"],
            "expert_diagnoses": [asdict(value) for value in expert],
            "features": features, "discrete_features": row,
            # Matched rules must not expose mutable cached dictionaries to callers.
            "ml_suggestions": deepcopy(suggestions), "scope_gate_passed": scope and not missing_core,
            "limitations": ["Single-fault pilot on SRV01; no generalization claim",
                            "Association confidence and leaf fraction describe training data",
                            "No automatic remediation, alert mutation or rule activation"],
        }

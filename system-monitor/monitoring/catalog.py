"""Versioned, read-only runtime catalog. JSON predicates are data, not Python."""
import json
from pathlib import Path
import sqlite3
from contextlib import closing
from copy import deepcopy

from .expressions import matches, render, validate
from .facts import extract

APPLICATION_ID = 0x534D4233


def create_catalog(path, seed):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    with closing(sqlite3.connect(path)) as db, db:
        db.execute(f"PRAGMA application_id={APPLICATION_ID}")
        db.execute("PRAGMA user_version=1")
        db.executescript("""
        CREATE TABLE metadata(key TEXT PRIMARY KEY,value_json TEXT NOT NULL);
        CREATE TABLE expert_rules(rule_id TEXT PRIMARY KEY,position INTEGER UNIQUE NOT NULL,group_name TEXT NOT NULL,title TEXT NOT NULL);
        CREATE TABLE decision_rows(rule_id TEXT NOT NULL REFERENCES expert_rules(rule_id),priority INTEGER NOT NULL,condition_json TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('matched','not_matched','insufficient_evidence')),reason TEXT NOT NULL,missing_json TEXT NOT NULL,actions_json TEXT NOT NULL,PRIMARY KEY(rule_id,priority));
        CREATE TABLE hypotheses(rule_id TEXT NOT NULL REFERENCES expert_rules(rule_id),rank INTEGER NOT NULL,label TEXT NOT NULL,priority_score_pct INTEGER NOT NULL CHECK(priority_score_pct BETWEEN 0 AND 100),explanation TEXT NOT NULL,PRIMARY KEY(rule_id,rank));
        """)
        db.executemany("INSERT INTO metadata VALUES(?,?)", [(key, json.dumps(value)) for key, value in seed["metadata"].items()])
        for position, rule in enumerate(seed["rules"]):
            db.execute("INSERT INTO expert_rules VALUES(?,?,?,?)", (rule["rule_id"], position, rule["group"], rule["title"]))
            for priority, row in enumerate(rule["rows"]):
                validate(row["when"])
                db.execute("INSERT INTO decision_rows VALUES(?,?,?,?,?,?,?)", (rule["rule_id"], priority, json.dumps(row["when"]), row["status"], row["reason"], json.dumps(row.get("missing", [])), json.dumps(row.get("actions", []))))
            for rank, hypothesis in enumerate(rule.get("hypotheses", []), 1):
                db.execute("INSERT INTO hypotheses VALUES(?,?,?,?,?)", (rule["rule_id"], rank, hypothesis["label"], hypothesis["priority_score_pct"], hypothesis["explanation"]))
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or db.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Invalid expert catalog")


class ExpertCatalog:
    def __init__(self, path):
        with closing(sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)) as db:
            if db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID or db.execute("PRAGMA user_version").fetchone()[0] != 1:
                raise ValueError("Unsupported expert rule database")
            self.metadata = {key: json.loads(value) for key, value in db.execute("SELECT * FROM metadata")}
            self.rules = []
            for rule_id, position, group, title in db.execute("SELECT * FROM expert_rules ORDER BY position"):
                decisions = []
                for priority, condition, status, reason, missing, actions in db.execute("SELECT priority,condition_json,status,reason,missing_json,actions_json FROM decision_rows WHERE rule_id=? ORDER BY priority", (rule_id,)):
                    decisions.append({"when": validate(json.loads(condition)), "status": status, "reason": reason, "missing": json.loads(missing), "actions": json.loads(actions)})
                if not decisions or decisions[-1]["when"] != {"op": "always"}:
                    raise ValueError("Every rule requires an explicit fallback")
                hypotheses = [{"label": label, "priority_score_pct": score, "explanation": explanation}
                              for label, score, explanation in db.execute("SELECT label,priority_score_pct,explanation FROM hypotheses WHERE rule_id=? ORDER BY rank", (rule_id,))]
                self.rules.append({"rule_id": rule_id, "group": group, "title": title, "rows": decisions, "hypotheses": hypotheses})

    def assess(self, profile, evidence, now, *, parent_status="unknown", window_alert_count=0):
        facts = extract(profile, evidence, now, self.metadata["policy"], parent_status=parent_status, window_alert_count=window_alert_count)
        output = []
        for rule in self.rules:
            row = next(row for row in rule["rows"] if matches(row["when"], facts))
            reason = render(row["reason"], facts)
            output.append({"rule_id": rule["rule_id"], "group": rule["group"], "status": row["status"],
                           "probable_cause": reason if row["status"] == "matched" else None, "reasoning": reason,
                           "missing_info": [render(value, facts) for value in row["missing"]],
                           "next_actions": [render(value, facts) for value in row["actions"]],
                           "hypotheses": deepcopy(rule["hypotheses"]) if row["status"] == "matched" else [],
                           "confidence_kind": "expert_priority_score_not_calibrated_probability"})
        return {"catalog_version": self.metadata["version"], "facts": facts, "diagnoses": output}

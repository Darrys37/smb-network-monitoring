"""Versioned research registry; immutable rule artifacts remain separate from incidents."""
import hashlib
import json
from pathlib import Path
import sqlite3
import time


def write_registry(path, candidate_db, freeze, test_sources, evaluation, equivalence):
    path=Path(path)
    if path.exists():raise FileExistsError(path)
    checksum=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    artifact=checksum(candidate_db)
    db=sqlite3.connect(path)
    db.execute('PRAGMA foreign_keys=ON')
    try:
        db.executescript('''
        PRAGMA user_version=1;
        CREATE TABLE datasets(dataset_id TEXT PRIMARY KEY,role TEXT CHECK(role IN ('development','locked_test')),manifest_json TEXT NOT NULL);
        CREATE TABLE experiments(experiment_id TEXT PRIMARY KEY,protocol_json TEXT NOT NULL,created_at INTEGER NOT NULL);
        CREATE TABLE models(model_id TEXT PRIMARY KEY,experiment_id TEXT NOT NULL REFERENCES experiments,algorithm TEXT NOT NULL,artifact_sha256 TEXT NOT NULL,config_json TEXT NOT NULL);
        CREATE TABLE rules(rule_id TEXT PRIMARY KEY,model_id TEXT NOT NULL REFERENCES models,local_rule_id TEXT NOT NULL,conditions_json TEXT NOT NULL,label TEXT NOT NULL,training_runs INTEGER NOT NULL,train_statistics_json TEXT NOT NULL);
        CREATE TABLE rule_evaluations(model_id TEXT PRIMARY KEY REFERENCES models,test_dataset_id TEXT NOT NULL REFERENCES datasets,metrics_json TEXT NOT NULL,equivalence_json TEXT NOT NULL);
        CREATE TABLE rule_lifecycle(sequence INTEGER PRIMARY KEY AUTOINCREMENT,model_id TEXT NOT NULL REFERENCES models,state TEXT CHECK(state IN ('candidate','validated','active','retired')),at INTEGER NOT NULL,reason_json TEXT NOT NULL);
        CREATE TRIGGER preserve_lifecycle_update BEFORE UPDATE ON rule_lifecycle BEGIN SELECT RAISE(ABORT,'append-only lifecycle'); END;
        CREATE TRIGGER preserve_lifecycle_delete BEFORE DELETE ON rule_lifecycle BEGIN SELECT RAISE(ABORT,'append-only lifecycle'); END;
        CREATE TRIGGER preserve_rules_update BEFORE UPDATE ON rules BEGIN SELECT RAISE(ABORT,'immutable versioned rules'); END;
        CREATE TRIGGER preserve_rules_delete BEFORE DELETE ON rules BEGIN SELECT RAISE(ABORT,'immutable versioned rules'); END;
        ''')
        dump=lambda value:json.dumps(value,ensure_ascii=False,allow_nan=False)
        db.execute('INSERT INTO datasets VALUES(?,?,?)',('development','development',dump(freeze['train'])))
        db.execute('INSERT INTO datasets VALUES(?,?,?)',('locked-test','locked_test',dump(test_sources)))
        db.execute('INSERT INTO experiments VALUES(?,?,?)',('locked-test-v1',dump(freeze),int(time.time())))
        source=sqlite3.connect(Path(candidate_db).resolve().as_uri()+'?mode=ro',uri=True)
        try:
            for algorithm,method in [('CART','cart_discrete'),('FP-Growth','fp_classifier')]:
                model=algorithm+':'+artifact[:20]
                db.execute('INSERT INTO models VALUES(?,?,?,?,?)',(model,'locked-test-v1',algorithm,artifact,dump(freeze['config'])))
                db.execute('INSERT INTO rule_lifecycle(model_id,state,at,reason_json) VALUES(?,?,?,?)',
                           (model,'candidate',int(time.time()),dump({'artifact':str(candidate_db),'scope':freeze['scope']})))
                for rid,conditions,label,count,stats in source.execute('SELECT rule_id,conditions_json,label,training_runs,statistics_json FROM candidates WHERE algorithm=?',(algorithm,)):
                    db.execute('INSERT INTO rules VALUES(?,?,?,?,?,?,?)',(model+':'+rid,model,rid,conditions,label,count,stats))
                db.execute('INSERT INTO rule_evaluations VALUES(?,?,?,?)',(model,'locked-test',dump(evaluation[method]),dump(equivalence)))
                if equivalence.get('test_rows',0)>0 and equivalence.get(algorithm) is True:
                    db.execute('INSERT INTO rule_lifecycle(model_id,state,at,reason_json) VALUES(?,?,?,?)',
                        (model,'validated',int(time.time()),dump({'meaning':'serialization and held-out evaluation recorded; research shadow only',
                             'production_effectiveness_approved':False,'auto_activation':False})))
        finally:source.close()
        db.commit()
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        assert db.execute("SELECT COUNT(*) FROM rule_lifecycle WHERE state='active'").fetchone()[0]==0
    finally:db.close()

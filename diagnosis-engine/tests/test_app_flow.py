import json
import sqlite3
from unittest.mock import Mock
import pytest
import app
from models import EvidenceRecord
from report import load_report
from repository import init_db, save_event
from event_parser import parse_event

EVENT={'eventid':'458','clock':'1700000000','name':'HTTP failed','severity':'3','value':'1','r_eventid':'0',
       'hosts':[{'hostid':'10683','host':'SRV01','name':'SRV01'}]}


def setup(monkeypatch):
    monkeypatch.setattr(app,'get_open_problems',lambda _: [{'eventid':'458'}])
    monkeypatch.setattr(app,'get_event_by_id',lambda _:dict(EVENT))
    monkeypatch.setattr(app.time,'time',lambda:1700000086)
    monkeypatch.setattr(app,'collect_ping',lambda ip:EvidenceRecord('ping',ip,1700000086,{'status':'success'}))
    monkeypatch.setattr(app,'collect_tcp',lambda ip,port:EvidenceRecord('tcp',ip,1700000086,{'status':'refused','port':port}))
    monkeypatch.setattr(app,'collect_metrics',lambda _:[])
    monkeypatch.setattr(app,'collect_agent_metric',lambda h:EvidenceRecord('agent_metric',h,1700000086,{'key':'agent.ping','status':'missing'}))
    monkeypatch.setattr(app,'collect_cpu_history',lambda h:EvidenceRecord('cpu_history',h,1700000086,{'key':'system.cpu.util','status':'missing'}))


def test_full_app_saves_six_roadmap_results(tmp_path,monkeypatch):
    setup(monkeypatch);db=tmp_path/'test.db'
    monkeypatch.setattr('sys.argv',['app.py','--event-id','458','--save','--db',str(db)])
    app.main()
    report=load_report(1,db)
    assert len(report['diagnoses'])==6
    assert report['diagnoses'][1]['status']=='matched'
    assert report['diagnoses'][3]['status']=='insufficient_evidence'
    assert report['diagnoses'][4]['status']=='insufficient_evidence'
    before=db.read_bytes()
    with pytest.raises(ValueError,match='already has'):app.main()
    assert db.read_bytes()==before


def test_app_api_failure_does_not_mutate_existing_db(tmp_path,monkeypatch):
    setup(monkeypatch);db=tmp_path/'test.db';init_db(db);save_event(parse_event(EVENT),db)
    before=db.read_bytes()
    def fail(_):raise RuntimeError('Zabbix API connection error')
    monkeypatch.setattr(app,'collect_metrics',fail)
    monkeypatch.setattr('sys.argv',['app.py','--event-id','458','--save','--db',str(db)])
    with pytest.raises(RuntimeError):app.main()
    assert db.read_bytes()==before


def test_recovery_during_collection_does_not_save(tmp_path,monkeypatch):
    setup(monkeypatch);db=tmp_path/'test.db'
    calls=iter([[{'eventid':'458'}],[]])
    monkeypatch.setattr(app,'get_open_problems',lambda _:next(calls))
    monkeypatch.setattr('sys.argv',['app.py','--event-id','458','--save','--db',str(db)])
    with pytest.raises(ValueError):app.main()
    assert not db.exists()


def test_preview_does_not_create_db(tmp_path,monkeypatch):
    setup(monkeypatch);db=tmp_path/'test.db'
    monkeypatch.setattr('sys.argv',['app.py','--event-id','458','--db',str(db)])
    app.main();assert not db.exists()

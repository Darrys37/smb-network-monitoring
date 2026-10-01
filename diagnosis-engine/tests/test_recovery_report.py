import csv
import io
import json
import sqlite3
from contextlib import closing
import pytest
import recovery as sync
from models import EventRecord, HostRecord, EvidenceRecord, DiagnosisRecord
from repository import init_db, save_incident_bundle, save_recovery
from report import load_report, render_csv, render_markdown

@pytest.fixture
def case(tmp_path):
    path=tmp_path/'old.db'
    init_db(path)
    event=EventRecord('458',1700000000,'HTTP failed',3,1,(HostRecord('10683','SRV01','SRV01'),))
    eid=save_incident_bundle(event,[EvidenceRecord('tcp','192.168.56.20',1700000086,{'port':80,'status':'refused'})],
        [DiagnosisRecord('HTTP_PORT_REFUSED','matched','Maybe service','Line one,\nline two',('Need sockets',),('Inspect',))],path)
    p={'eventid':'458','value':'1','clock':'1700000000','r_eventid':'459','source':'0','object':'0','objectid':'123',
       'hosts':[{'hostid':'10683','host':'SRV01','name':'SRV01'}]}
    r={**p,'eventid':'459','value':'0','clock':'1700000120','r_eventid':'0'}
    return path,eid,p,r

def dump(path):
    with closing(sqlite3.connect(path)) as c:return '\n'.join(c.iterdump())

def test_additive_recovery_keeps_original_records(case):
    path,eid,p,r=case
    before=load_report(eid,path)
    assert before['lifecycle_status']=='unverified'
    assert save_recovery(p,r,path)==eid
    after=load_report(eid,path)
    for key in ('incident','evidence','diagnoses'):assert after[key]==before[key]
    assert after['lifecycle_status']=='closed'
    snapshot=dump(path);save_recovery(p,r,path);assert dump(path)==snapshot
    rows=list(csv.DictReader(io.StringIO(render_csv(after))))
    assert rows[0]['event_interval_seconds']=='120'
    assert rows[0]['recovery_event_id']=='459'
    assert json.loads(rows[0]['evidence_json'])==before['evidence']
    assert rows[0]['reasoning']=='Line one,\nline two'
    md=render_markdown(after)
    assert 'closed' in md and '120 giây' in md
    assert 'chưa ghi nhận thông tin recovery' not in md

@pytest.mark.parametrize('which,key,value',[
    ('p','r_eventid','999'),('r','value','1'),('r','objectid','999'),
    ('r','source','1'),('r','clock','1699999999'),('p','clock','1700000001'),
    ('r','hosts',[{'hostid':'999'}]),('r','eventid','458'),('r','clock','9999999999')])
def test_invalid_link_never_mutates_database(case,which,key,value):
    path,eid,p,r=case;before=dump(path)
    (p if which=='p' else r)[key]=value
    with pytest.raises(ValueError):save_recovery(p,r,path)
    assert dump(path)==before

def test_conflicting_recovery_does_not_overwrite(case):
    path,eid,p,r=case;save_recovery(p,r,path);before=dump(path)
    p['r_eventid']='460';r['eventid']='460'
    with pytest.raises(ValueError,match='Conflicting'):save_recovery(p,r,path)
    assert dump(path)==before

def test_api_failure_during_sync_keeps_database(case,monkeypatch):
    path,eid,p,r=case;before=dump(path)
    def fail(_):raise RuntimeError('API unavailable')
    monkeypatch.setattr(sync,'get_event_by_id',fail)
    with pytest.raises(RuntimeError):sync.sync_recovery('458',path)
    assert dump(path)==before

def test_sync_retrieves_linked_event(case,monkeypatch):
    path,eid,p,r=case
    monkeypatch.setattr(sync,'get_event_by_id',lambda x:{'458':p,'459':r}[x])
    assert sync.sync_recovery('458',path)==eid

def test_no_link_is_not_closed(case,monkeypatch):
    path,eid,p,r=case;p['r_eventid']='0';before=dump(path)
    monkeypatch.setattr(sync,'get_event_by_id',lambda x:p)
    assert sync.sync_recovery('458',path) is None
    assert dump(path)==before

def test_read_missing_db_does_not_create(tmp_path):
    path=tmp_path/'missing.db'
    with pytest.raises(ValueError):load_report(1,path)
    assert not path.exists()

def test_csv_formula_text_is_escaped(case):
    path,eid,p,r=case;report=load_report(eid,path)
    report['diagnoses'][0]['reasoning']='=DANGEROUS()'
    row=list(csv.DictReader(io.StringIO(render_csv(report))))[0]
    assert row['reasoning']=="'=DANGEROUS()" and row['recovery_clock']==''

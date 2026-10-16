"""Verify frozen week-4 records, historical UI joins and usability of a restored DB copy."""
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
from urllib.parse import urlparse, parse_qs

project=Path(sys.argv[1])
closure=project/'evidence/week4/closure-20261017'
root=project/'evidence/week4/official-runs'
rows=list(csv.DictReader((root/'all-trials.csv').open(encoding='utf-8')))
assert len(rows)==18
ui=json.loads((closure/'screenshots/screenshots-index.json').read_text())
ui_rows=json.loads((closure/'screenshots/history-ui-rows.json').read_text())['rows']
assert len(ui['event_screenshots'])==len(ui_rows)==18
expected={r['problem_event_id'] for r in rows}
assert {e['event_id'] for e in ui['event_screenshots']}==expected
assert {parse_qs(urlparse(r['href']).query)['eventid'][0] for r in ui_rows}==expected
assert all('RESOLVED' in r['row'] for r in ui_rows)
for e in ui['event_screenshots']:
    path=closure/'screenshots'/e['file']
    assert path.read_bytes()[:3]==b'\xff\xd8\xff',path
final=root/'final-state-20261016T214108Z'
db=final/'diagnosis-final.db'
state=json.loads((final/'summary.json').read_text())
assert hashlib.sha256(db.read_bytes()).hexdigest()==state['db_sha256']
# Restore to a separate scratch file; never alter the frozen backup or live runtime DB.
restored=Path.cwd()/'week4-restored-check.db'
assert not restored.exists(), 'Use a new scratch filename if rerunning the recovery check.'
shutil.copyfile(db,restored)
sys.path.insert(0,str(project/'diagnosis-engine'))
from report import load_report
with sqlite3.connect('file:'+str(restored)+'?mode=ro',uri=True) as conn:
    assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not conn.execute('PRAGMA foreign_key_check').fetchall()
    count=conn.execute('SELECT count(*) FROM incidents').fetchone()[0]
for row in rows:
    incident=load_report(int(row['incident_id']),restored)
    assert incident['incident']['event_id']==row['problem_event_id']
    assert incident['recovery']['recovery_event_id']==row['recovery_event_id']
    assert incident['lifecycle_status']=='closed'
    original=json.loads((root/row['run_id']/'incident.json').read_text())
    assert incident==original,row['run_id']
result={'verified_at_utc':datetime.now(timezone.utc).isoformat(),
 'raw_manifest_verification':'See docs/KIEM_TRA_DU_LIEU_20261017.json and rerun verify_experiment.py',
 'official_fault_trials':18,'unique_problem_ids':len(expected),'historical_ui_events_joined':len(ui_rows),
 'historical_event_screenshots':len(ui['event_screenshots']),
 'all_historical_ui_rows_resolved':True,'screenshot_format':'JPEG verified by magic bytes',
 'sqlite_backup_sha256':state['db_sha256'],'restored_database_integrity_check':'ok',
 'restored_database_foreign_key_check':'no violations','restored_database_incident_count':count,
 'official_reports_reproduced_from_restored_copy':18,'reports_equal_frozen_json':True,
 'source_or_trigger_changes_for_closure':False,
 'limitations':['Historical screenshots were captured after the trials, not during active faults.',
    'Restored SQLite copy was read with the report module; this is not a full VM/MySQL disaster-recovery drill.',
    'Original baseline was user-approved short observation of 1806 seconds, not 4 hours.'],
 'result':'PASS'}
(closure/'closure-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))

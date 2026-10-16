"""Final read-only lab snapshot and consistent SQLite backup after all trials."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
sys.path.insert(0, '/home/phat/do-an/evidence/week4')
import baseline_session as b

root=Path(sys.argv[1])
baseline=Path('/home/phat/do-an/evidence/week4/baseline-20261016T162549Z')
folder=root/('final-state-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
folder.mkdir(exist_ok=False)
cfg,items=b.config()
source=b.source_hashes()
functions=b.api('trigger.get',{'hostids':b.HOSTS,'output':['triggerid','description','expression'],
    'selectFunctions':'extend','selectDependencies':['triggerid'],'sortfield':'triggerid'})
opened=b.problems()
b.save(folder/'effective-config.json',cfg)
b.save(folder/'items.json',items)
b.save(folder/'source-hashes.json',source)
b.save(folder/'trigger-functions.json',functions)
b.save(folder/'open-problems.json',opened)
queries={
 'critical-thresholds': "SELECT h.host,m.macro,m.value FROM hostmacro m JOIN hosts h ON h.hostid=m.hostid WHERE m.type=0 AND (h.hostid IN (10084,10683,10684) OR h.hostid IN (SELECT templateid FROM hosts_templates WHERE hostid IN (10084,10683,10684))) AND m.macro IN ('{$AGENT.TIMEOUT}','{$CPU.UTIL.CRIT}','{$LOAD_AVG_PER_CPU.MAX.WARN}') ORDER BY h.host,m.macro",
 'template-links': "SELECT h.host,t.host AS linked_template FROM hosts_templates ht JOIN hosts h ON h.hostid=ht.hostid JOIN hosts t ON t.hostid=ht.templateid WHERE h.hostid IN (10084,10683,10684) ORDER BY h.hostid,t.hostid",
 'global-thresholds': "SELECT macro,value FROM globalmacro WHERE type=0 AND macro IN ('{$AGENT.TIMEOUT}','{$CPU.UTIL.CRIT}','{$LOAD_AVG_PER_CPU.MAX.WARN}') ORDER BY macro"}
for name,sql in queries.items():
    result=subprocess.run(['sudo','-n','mysql','--batch','zabbix','-e',sql],capture_output=True,text=True,check=True)
    (folder/(name+'.tsv')).write_text(result.stdout)
with sqlite3.connect('file:'+str(b.PROJECT/'diagnosis.db')+'?mode=ro',uri=True) as src:
    with sqlite3.connect(folder/'diagnosis-final.db') as dest:
        src.backup(dest)
        integrity=dest.execute('PRAGMA integrity_check').fetchone()[0]
        counts={name:dest.execute('SELECT count(*) FROM '+name).fetchone()[0] for name in ('incidents','evidence','diagnoses','recoveries')}
before=json.loads((baseline/'preflight.json').read_text())
def canonical_functions(rows):
    return sorted([{**r,'functions':sorted(r['functions'],key=lambda f:f['functionid']),
        'dependencies':sorted(r['dependencies'],key=lambda d:d['triggerid'])} for r in rows],key=lambda r:r['triggerid'])
before_functions=json.loads((baseline/'trigger-functions-end-supplement.json').read_text())
before_ids={r['triggerid'] for r in before_functions}
same_scope_functions=[r for r in functions if r['triggerid'] in before_ids]
functions_unchanged=canonical_functions(same_scope_functions)==canonical_functions(before_functions)
b.save(folder/'trigger-functions-baseline-scope.json',same_scope_functions)
critical_unchanged=set((folder/'critical-thresholds.tsv').read_text().splitlines())==set((baseline/'effective-critical-thresholds-end.tsv').read_text().splitlines())
links_unchanged=(folder/'template-links.tsv').read_text().strip()==(baseline/'template-links-global-thresholds-end.tsv').read_text().strip()
global_overrides_absent=not (folder/'global-thresholds.tsv').read_text().strip()
summary={'captured_at_utc':datetime.now(timezone.utc).isoformat(),
 'source_unchanged':b.fingerprint(source)==before['source_sha256'],
 'config_unchanged':b.fingerprint(cfg)==before['config_sha256'],
 'trigger_functions_unchanged':functions_unchanged,'critical_thresholds_unchanged':critical_unchanged,
 'template_links_unchanged':links_unchanged,
 'critical_global_overrides_absent':global_overrides_absent,
 'open_problem_count':len(opened),'sqlite_integrity_check':integrity,'sqlite_row_counts':counts,
 'db_sha256':hashlib.sha256((folder/'diagnosis-final.db').read_bytes()).hexdigest(),
 'note':'API token cannot see inherited template macros; critical text macros and links also exported by read-only local SQL. No credentials exported.'}
b.save(folder/'summary.json',summary)
from zabbix_client import ZABBIX_API_TOKEN
needle=ZABBIX_API_TOKEN.encode()
assert needle
scan_roots=[root,baseline]
scanned=0
hits=[]
for scan_root in scan_roots:
    for path in scan_root.rglob('*'):
        if path.is_file():
            scanned+=1
            if needle in path.read_bytes(): hits.append(str(path.relative_to(scan_root)))
b.save(folder/'credential-scan.json',{'exact_current_api_token_only':True,'files_scanned':scanned,
    'hit_count':len(hits),'hit_paths':hits,'note':'Does not certify absence of old unknown credentials or Git history leaks.'})
print(folder)
print(json.dumps(summary,indent=2))
assert not hits and summary['source_unchanged'] and summary['config_unchanged'] and functions_unchanged and critical_unchanged and links_unchanged and global_overrides_absent and not opened and integrity=='ok'

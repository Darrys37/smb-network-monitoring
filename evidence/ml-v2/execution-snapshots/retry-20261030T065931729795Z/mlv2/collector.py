"""Same source schedule for every fault label; remote Python only performs reads.

runner(observer, source) returns JSON from the named host. No labels/registry are
accepted here. Credentials and transport are outside the observation contract.
"""
from pathlib import Path
import time
import uuid

from .core import VERSION, identifier, validate_profile, validate_observation


def portable(engine):
    # These modules have only standard-library imports for the probe functions.
    sources = {name: (Path(engine)/(name+'.py')).read_text(encoding='utf-8')
               for name in ['models', 'evidence', 'http_probe']}
    return "import sys,types,json,socket\n" + ''.join(
        f"m=types.ModuleType({name!r});sys.modules[{name!r}]=m;exec({source!r},m.__dict__)\n"
        for name, source in sources.items())


def collect(profile, engine, session, run, runner, clock=time.time):
    validate_profile(profile); identifier(session); identifier(run)
    start = int(clock())
    p = profile
    monitor = f'''import sys,json,socket
sys.path.insert(0,{str(Path(engine))!r})
from dataclasses import asdict
from evidence import collect_ping,collect_tcp
from roadmap_evidence import collect_roadmap_metrics
from zabbix_client import call_api
interfaces=call_api('hostinterface.get',{{'hostids':[{p['host_id']!r}],'output':['ip','useip']}},901)
if not any(i.get('useip')=='1' and i.get('ip')=={p['target_ip']!r} for i in interfaces):
 raise ValueError('Host/IP mapping is not verified')
rows=[collect_ping({p['target_ip']!r}),collect_tcp({p['target_ip']!r},80),collect_tcp({p['target_ip']!r},10050)]
rows+=collect_roadmap_metrics({p['host_id']!r})
rows.append(collect_ping({p['control_ip']!r}))
data=[asdict(r) for r in rows]
for row in data: row['result']['observer']=socket.gethostname().split('.')[0].lower()
print(json.dumps(data))
'''
    # Remote path for MON01, local path for reading portable source may differ.
    monitor = monitor.replace(repr(str(Path(engine))), repr('/home/phat/do-an/diagnosis-engine'), 1)
    shared = portable(engine)
    http = shared + f"\nprint(json.dumps([sys.modules['http_probe'].collect_local_http({p['target_ip']!r},{p['observer']!r})]))\n"
    dns = shared + f'''
from dataclasses import asdict,replace
from evidence import collect_dns,collect_ping
observer=socket.gethostname().split('.')[0].lower()
if observer!={p['observer']!r}: raise ValueError('Wrong DNS observer')
rows=[collect_dns({p['dns_name']!r}),replace(collect_ping({p['dns_control_ip']!r}),check_type='dns_control_ping')]
data=[asdict(r) for r in rows]
for row in data: row['result']['observer']=observer
print(json.dumps(data))
'''
    evidence, outcomes = [], {}
    schedule = [('monitor', 'mon01', monitor), ('local_http', p['observer'], http), ('dns', p['observer'], dns)]
    for source, host, program in schedule:
        if source == 'local_http' and p['http_service'] == 'absent':
            outcomes[source] = {'status': 'not_applicable', 'error_type': None}
            continue
        try:
            rows = runner(host, program)
            if not isinstance(rows, list):
                raise ValueError('Probe returned no evidence list')
            evidence.extend(rows)
            outcomes[source] = {'status': 'ok', 'error_type': None}
        except Exception as exc:
            # Never forward remote stderr or API exceptions containing secrets.
            outcomes[source] = {'status': 'error', 'error_type': type(exc).__name__}
    value = {'schema_version': 2, 'session_id': session, 'run_id': run,
             'window_id': 'w-'+uuid.uuid4().hex, 'collector_version': VERSION,
             'profile': dict(profile), 'started_at': start, 'decision_time': int(clock()),
             'sources': outcomes, 'evidence': evidence}
    return validate_observation(value)

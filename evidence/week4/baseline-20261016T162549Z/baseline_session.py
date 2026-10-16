"""Read-only Zabbix baseline recorder; run with the existing MON01 venv.

Writes evidence only. Does not run diagnosis, modify Zabbix, or inject faults.
"""
import argparse
import csv
import hashlib
import json
import os
import re
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone

PROJECT = Path('/home/phat/do-an/diagnosis-engine')
sys.path.insert(0, str(PROJECT))
os.chdir(PROJECT)
from zabbix_client import call_api

HOSTS = ['10084', '10683', '10684']
KEYS = ['system.uptime', 'agent.ping', 'zabbix[host,agent,available]',
        'system.cpu.util', 'system.cpu.util[,idle]', 'system.cpu.load[all,avg1]',
        'system.cpu.num', 'vm.memory.util', 'web.test.fail[SRV01 HTTP]',
        'web.test.rspcode[SRV01 HTTP,Homepage]',
        'web.test.time[SRV01 HTTP,Homepage,resp]', 'net.dns[,example.com,A,2,1,udp]']
ITEM_FIELDS = ['itemid', 'hostid', 'name', 'key_', 'type', 'value_type', 'delay',
               'history', 'trends', 'status', 'state', 'error', 'lastclock',
               'lastvalue', 'units', 'master_itemid']
stop_requested = False

def utc(epoch=None):
    return datetime.fromtimestamp(time.time() if epoch is None else epoch, timezone.utc).isoformat()

def save(path, obj):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    tmp.replace(path)

def api(method, params):
    return call_api(method, params, 120)

def items():
    return api('item.get', {'hostids': HOSTS, 'webitems': True, 'filter': {'key_': KEYS},
                           'output': ITEM_FIELDS, 'selectPreprocessing': 'extend'})

def source_hashes():
    files = list(PROJECT.glob('*.py')) + list((PROJECT / 'tests').rglob('*.py'))
    files += [PROJECT / 'requirements.txt', PROJECT / 'pytest.ini']
    return {str(p.relative_to(PROJECT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files)}

def config():
    data = items()
    # Runtime values/state/error are excluded from configuration fingerprint.
    item_config = [{k: v for k, v in row.items()
                    if k not in ('lastvalue', 'lastclock', 'state', 'error')}
                   for row in data]
    triggers = api('trigger.get', {'hostids': HOSTS,
        'output': ['triggerid', 'description', 'expression', 'recovery_expression',
                   'priority', 'status', 'type', 'manual_close'],
        'selectDependencies': ['triggerid'], 'selectHosts': ['hostid'],
        'selectFunctions': ['functionid', 'itemid', 'function', 'parameter']})
    web = api('httptest.get', {'hostids': HOSTS, 'output':
        ['httptestid', 'hostid', 'name', 'delay', 'retries', 'status'],
        'selectSteps': ['name', 'url', 'timeout', 'status_codes']})
    expressions = '\n'.join(t['expression'] + '\n' + t['recovery_expression'] for t in triggers)
    used_macros = sorted(set(re.findall(r'\{\$[^}]+\}', expressions)))
    macros = []
    if used_macros:
        for global_scope in (False, True):
            fields = ['macro', 'value', 'type'] if global_scope else ['hostid', 'macro', 'value', 'type']
            macros.extend(api('usermacro.get', {'globalmacro': global_scope,
                'filter': {'macro': used_macros, 'type': '0'}, 'output': fields}))
    result = {'items': sorted(item_config, key=lambda r: int(r['itemid'])),
              'triggers': sorted(triggers, key=lambda r: int(r['triggerid'])),
              'web_scenarios': sorted(web, key=lambda r: int(r['httptestid'])),
              'referenced_text_macros': sorted(macros, key=lambda r: (r.get('hostid', ''), r['macro']))}
    return result, data

def fingerprint(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()

def problems():
    return api('problem.get', {'hostids': HOSTS, 'source': 0, 'object': 0,
                              'recent': False, 'output': 'extend'})

def export_history(folder, initial_items, start, end):
    counts = {}
    with (folder / 'history.csv').open('x', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['hostid', 'key_', 'itemid', 'clock', 'ns', 'value'])
        writer.writeheader()
        # Hourly chunks keep each single item's history safely below API limits.
        for item in initial_items:
            if item['value_type'] not in ('0', '3'):
                continue
            counts[item['itemid']] = 0
            for lower in range(start, end + 1, 3600):
                rows = api('history.get', {'itemids': [item['itemid']],
                    'history': int(item['value_type']), 'time_from': lower,
                    'time_till': min(end, lower + 3599), 'output': 'extend',
                    'sortfield': ['clock', 'ns'], 'sortorder': 'ASC', 'limit': 10000})
                if len(rows) >= 10000:
                    raise RuntimeError('History limit reached; export must be split further')
                for row in rows:
                    writer.writerow({k: row.get(k, item.get(k, '')) for k in writer.fieldnames})
                counts[item['itemid']] += len(rows)
    return counts

def prepare(folder):
    folder.mkdir(parents=True, exist_ok=False)
    cfg, data = config()
    save(folder / 'effective-config-start.json', cfg)
    save(folder / 'items-start.json', data)
    save(folder / 'source-hashes-start.json', source_hashes())
    save(folder / 'problems-preflight.json', problems())
    runtime = subprocess.run(['bash', '-c',
        'date -u -Is; uname -a; uptime; timedatectl show -p NTPSynchronized; '
        'systemctl is-active zabbix-server mysql nginx zabbix-agent2'],
        capture_output=True, text=True, timeout=15)
    (folder / 'mon01-runtime.txt').write_text(runtime.stdout + runtime.stderr)
    # Backup SQLite using its supported online backup API, without modifying source DB.
    with sqlite3.connect('file:' + str(PROJECT / 'diagnosis.db') + '?mode=ro', uri=True) as src:
        with sqlite3.connect(folder / 'diagnosis-pre-baseline.db') as dst:
            src.backup(dst)
            check = dst.execute('PRAGMA integrity_check').fetchone()[0]
    if check != 'ok':
        raise RuntimeError('SQLite backup integrity check failed')
    save(folder / 'preflight.json', {'prepared_at_utc': utc(), 'config_sha256': fingerprint(cfg),
        'source_sha256': fingerprint(source_hashes()), 'sqlite_integrity_check': check,
        'source_commit': 'ca04071', 'config_export_commit': '978b4f9',
        'protocol_commit': '4cabeb0', 'git_head': '4cabeb0d891cdc32444e773eaf81927d0b686e79',
        'freeze_note': 'Effective configuration snapshot is authoritative for this session; reference export is older.',
        'scope': 'Zabbix baseline only; no engine false-positive rate inferred'})
    print('Prepared', folder, flush=True)
    print(json.dumps({'items': [{k: r.get(k) for k in ('hostid','key_','delay','state','lastclock','lastvalue')} for r in data],
                      'open_problems': problems()}, indent=2), flush=True)

def run(folder, duration, interval):
    global stop_requested
    signal.signal(signal.SIGTERM, lambda *_: globals().__setitem__('stop_requested', True))
    signal.signal(signal.SIGINT, lambda *_: globals().__setitem__('stop_requested', True))
    if (folder / 'session.json').exists():
        raise RuntimeError('Session already started; choose a new folder')
    before = json.loads((folder / 'preflight.json').read_text())
    cfg, data = config()
    if fingerprint(cfg) != before['config_sha256'] or fingerprint(source_hashes()) != before['source_sha256']:
        raise RuntimeError('Source/config changed since preflight')
    start = int(time.time())
    manifest = {'status': 'running', 'start_epoch': start, 'start_utc': utc(start),
        'planned_end_utc': utc(start + duration), 'duration_target_seconds': duration,
        'freeze_at_utc': utc(start), 'poll_interval_seconds': interval,
        'pid': os.getpid(), 'preflight': before}
    save(folder / 'session.json', manifest)
    save(folder / 'problems-start.json', problems())
    print('BASELINE START', manifest['start_utc'], 'PLANNED END', manifest['planned_end_utc'], flush=True)
    with (folder / 'observations.jsonl').open('x', encoding='utf-8') as stream:
        while True:
            stamp = int(time.time())
            row = {'observed_at': stamp, 'observed_utc': utc(stamp)}
            try:
                row['items'] = items()
                row['open_problems'] = problems()
                row['status'] = 'ok'
            except Exception as exc:
                row.update(status='error', error_type=type(exc).__name__, error=str(exc))
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
            stream.flush()
            save(folder / 'heartbeat.json', {'observed_at': stamp, 'status': row['status'], 'pid': os.getpid()})
            if stop_requested or time.time() >= start + duration:
                break
            time.sleep(min(interval, max(0, start + duration - time.time())))
    end = int(time.time())
    manifest.update(status='exporting', end_epoch=end, end_utc=utc(end),
                    wall_seconds=end-start, stopped_early=stop_requested)
    save(folder / 'session.json', manifest)
    try:
        events = api('event.get', {'hostids': HOSTS, 'source': 0, 'object': 0,
            'time_from': start, 'time_till': end, 'output': 'extend',
            'selectHosts': ['hostid', 'host', 'name'], 'sortfield': ['eventid'],
            'sortorder': 'ASC', 'limit': 10000})
        if len(events) >= 10000:
            raise RuntimeError('Event limit reached; export incomplete')
        save(folder / 'events.json', events)
        with (folder / 'events.csv').open('x', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=['eventid','clock','value','r_eventid','name','severity','objectid'])
            writer.writeheader()
            writer.writerows({k: e.get(k, '') for k in writer.fieldnames} for e in events)
        save(folder / 'history-counts.json', export_history(folder, data, start, end))
        save(folder / 'problems-end.json', problems())
        final_config, final_items = config()
        save(folder / 'effective-config-end.json', final_config)
        save(folder / 'items-end.json', final_items)
        save(folder / 'source-hashes-end.json', source_hashes())
        manifest.update(status='recorded_pending_review',
            config_unchanged=fingerprint(final_config) == before['config_sha256'],
            source_unchanged=fingerprint(source_hashes()) == before['source_sha256'],
            review_required='Check sample gaps, uptime resets, configuration, and classify every new problem before reporting valid duration or false alerts.')
    except Exception as exc:
        manifest.update(status='export_error', error_type=type(exc).__name__, error=str(exc))
    save(folder / 'session.json', manifest)
    print(json.dumps(manifest, indent=2), flush=True)

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['prepare', 'run'])
    p.add_argument('--folder', type=Path, required=True)
    p.add_argument('--duration', type=int, default=14400)
    p.add_argument('--interval', type=int, default=60)
    a = p.parse_args()
    if a.action == 'prepare':
        prepare(a.folder)
    else:
        run(a.folder, a.duration, a.interval)

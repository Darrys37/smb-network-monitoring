"""Strict observation contract and append-only experiment registry."""
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import time
import uuid

VERSION = 'ml-observation-v2.0'
PROFILE_KEYS = {'schema_version', 'profile_id', 'host_id', 'target_ip', 'observer',
                'control_ip', 'http_service', 'dns_name', 'dns_control_ip', 'topology_version'}
LABELS = {'healthy', 'interface_down', 'nginx_stopped', 'agent_stopped',
          'dns_egress_blocked', 'remote_http_filtered', 'cpu_stress'}


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value):
        raise ValueError('Invalid identifier')
    return value


def validate_profile(profile):
    if set(profile) != PROFILE_KEYS or type(profile['schema_version']) is not int or profile['schema_version'] != 1:
        raise ValueError('Profile fields/version do not match contract')
    for key in ['profile_id', 'observer', 'topology_version']:
        identifier(profile[key])
    if not isinstance(profile['host_id'], str) or not profile['host_id'].isdigit():
        raise ValueError('host_id must be a numeric string')
    for key in ['target_ip', 'control_ip', 'dns_control_ip']:
        ipaddress.IPv4Address(profile[key])
    if profile['target_ip'] == profile['control_ip']:
        raise ValueError('Control must differ from target')
    if profile['http_service'] not in ['expected', 'absent']:
        raise ValueError('Research profile requires explicit HTTP scope')
    if not isinstance(profile['dns_name'], str) or not re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,251}[a-z0-9]', profile['dns_name']):
        raise ValueError('Invalid DNS name')
    return profile


def save_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_observation(value):
    keys = {'schema_version', 'session_id', 'run_id', 'window_id', 'collector_version',
            'profile', 'started_at', 'decision_time', 'sources', 'evidence'}
    if set(value) != keys or value['schema_version'] != 2 or type(value['schema_version']) is not int:
        raise ValueError('Invalid observation fields/version; labels are forbidden')
    validate_profile(value['profile'])
    if value['collector_version'] != VERSION:
        raise ValueError('Unsupported collector version')
    for name in ['session_id', 'run_id', 'window_id']:
        identifier(value[name])
    start, end = value['started_at'], value['decision_time']
    if type(start) is not int or type(end) is not int or not 0 <= start <= end:
        raise ValueError('Invalid observation interval')
    if not isinstance(value['sources'], dict) or set(value['sources']) != {'monitor', 'local_http', 'dns'}:
        raise ValueError('All scheduled sources must report a status')
    for source in value['sources'].values():
        if set(source) != {'status', 'error_type'} or source['status'] not in {'ok', 'error', 'not_applicable'}:
            raise ValueError('Invalid source outcome')
        if source['error_type'] is not None and not isinstance(source['error_type'], str):
            raise ValueError('Invalid error type')
    if not isinstance(value['evidence'], list):
        raise ValueError('Evidence must be a list')
    for row in value['evidence']:
        if set(row) != {'check_type', 'target', 'collected_at', 'result'}:
            raise ValueError('Invalid evidence fields')
        if type(row['collected_at']) is not int or not 0 <= row['collected_at'] <= end:
            raise ValueError('Evidence from the future is forbidden')
        if not isinstance(row['result'], dict) or not all(isinstance(row[k], str) for k in ['check_type', 'target']):
            raise ValueError('Invalid evidence types')
    return value


def register(root, session, run, planned_labels):
    identifier(session); identifier(run)
    if not planned_labels or not set(planned_labels) <= LABELS or ('healthy' in planned_labels and len(planned_labels) != 1):
        raise ValueError('Invalid planned label set')
    row = {'schema_version': 1, 'session_id': session, 'run_id': run,
           'planned_labels': sorted(set(planned_labels)), 'registered_at': int(time.time()), 'validity': 'pending'}
    save_new(Path(root)/'registry'/session/run/'registration.json', row)
    return row


def review(root, session, run, validity, labels, references):
    identifier(session); identifier(run)
    registration = read(Path(root)/'registry'/session/run/'registration.json')
    if validity not in {'valid', 'invalid', 'uncertain'} or not set(labels) <= LABELS:
        raise ValueError('Invalid review')
    if validity == 'valid' and (not labels or not references):
        raise ValueError('Valid labels require independent evidence references')
    if 'healthy' in labels and len(labels) != 1:
        raise ValueError('Healthy cannot coexist with fault labels')
    # Store review evidence content-addressed; never rewrite the original labels.
    refs = []
    for path in references:
        p = Path(path)
        content = p.read_bytes()
        checksum = hashlib.sha256(content).hexdigest()
        copy = Path(root)/'review-evidence'/checksum
        if not copy.exists():
            copy.parent.mkdir(parents=True, exist_ok=True)
            with copy.open('xb') as stream:
                stream.write(content)
        refs.append({'sha256': checksum, 'original_name': p.name})
    result = {'schema_version': 1, 'session_id': session, 'run_id': run,
              'registration_sha256': sha(Path(root)/'registry'/session/run/'registration.json'),
              'reviewed_at': int(time.time()), 'validity': validity,
              'labels': sorted(set(labels)), 'references': refs}
    save_new(Path(root)/'registry'/session/run/('review-'+uuid.uuid4().hex+'.json'), result)
    return result

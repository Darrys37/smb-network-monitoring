"""Audit experiment evidence without training or silently deleting bad rows."""
from collections import Counter
import csv
import json
from pathlib import Path

from .core import read,sha,validate_observation


def audit(root, output):
    root,output=Path(root),Path(output)
    output.mkdir(parents=True,exist_ok=True)
    runs=[];windows=[];issues=[]
    for registration in sorted((root/'registry').glob('*/*/registration.json')):
        item=read(registration)
        session,run=item['session_id'],item['run_id']
        reviews=list(registration.parent.glob('review-*.json'))
        review=read(reviews[0]) if len(reviews)==1 else None
        validity=review['validity'] if review else ('pending' if not reviews else 'ambiguous_review')
        if review:
            try:
                if review['registration_sha256']!=sha(registration):raise ValueError('Registration hash mismatch')
                for reference in review['references']:
                    if sha(root/'review-evidence'/reference['sha256'])!=reference['sha256']:
                        raise ValueError('Review evidence hash mismatch')
            except (OSError,ValueError):
                validity='invalid_provenance'
                issues.append({'run_id':run,'issue':'invalid_review_provenance'})
        labels=review['labels'] if review else []
        rows=list((root/'observations'/session/run).glob('*.json'))
        if validity=='valid' and not rows:
            issues.append({'run_id':run,'issue':'valid_intervention_without_observation'})
        runs.append({'session_id':session,'run_id':run,'validity':validity,'labels':labels,'windows':len(rows)})
        verified=None
        log=root/'trial-logs'/session/run/'independent-logs.json'
        if log.exists():
            points=[int(x.split()[1]) for x in read(log)['fault.log'].splitlines() if x.startswith('FAULT_VERIFIED ')]
            if points:verified=points[0]
        for path in rows:
            value=validate_observation(read(path))
            errors=[key for key,item in value['sources'].items() if item['status']=='error']
            before=0;future_samples=0
            for e in value['evidence']:
                stamp=e['result'].get('sample_clock')
                if type(stamp) is int:
                    if verified is not None and stamp<verified:before+=1
                    if stamp>value['decision_time']:future_samples+=1
            row={'session_id':session,'run_id':run,'window_id':value['window_id'],'validity':validity,
                 'labels':';'.join(labels),'profile':value['profile']['profile_id'],
                 'evidence_count':len(value['evidence']),'source_errors':';'.join(errors),
                 'collection_seconds':value['decision_time']-value['started_at'],
                 'metric_samples_before_intervention':before,'future_metric_samples':future_samples}
            windows.append(row)
            if errors:issues.append({'run_id':run,'window_id':value['window_id'],'issue':'source_unavailable','sources':errors})
            if future_samples:issues.append({'run_id':run,'window_id':value['window_id'],'issue':'future_metric_sample'})
    summary={'registered_runs':len(runs),'valid_runs':sum(r['validity']=='valid' for r in runs),
             'validity_counts':dict(Counter(r['validity'] for r in runs)),
             'valid_runs_per_label':dict(Counter(label for r in runs if r['validity']=='valid' for label in r['labels'])),
             'sessions':sorted({r['session_id'] for r in runs}), 'observation_windows':len(windows),
             'issues':issues,'note':'Windows from the same run are dependent; this is not model accuracy.'}
    (output/'quality.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    if windows:
        with (output/'window_quality.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(windows[0]));writer.writeheader();writer.writerows(windows)
    lines=['# Pilot data quality','',f"Registered: {len(runs)}; valid: {summary['valid_runs']}; windows: {len(windows)}.",'',
           '| Label | Valid runs |','|---|---:|']
    lines += [f'| {label} | {n} |' for label,n in sorted(summary['valid_runs_per_label'].items())]
    lines += ['', 'Source errors are retained. A failed SSH probe during interface-down is missing evidence, not a successful negative measurement.',
              '', 'Inspect pre-intervention metric samples before building supervised features. Valid injection labels do not imply every window is stable.',
              '', 'The old single Nginx trial, smoke session and scheduled pilot are separate groups; do not treat them as three randomized sessions.',
              '', 'No test accuracy can be claimed from this audit. Complete the planned independent sessions before model evaluation.','']
    (output/'QUALITY.md').write_text('\n'.join(lines),encoding='utf-8')
    return summary

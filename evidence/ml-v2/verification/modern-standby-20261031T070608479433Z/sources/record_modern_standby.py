"""Persist actual power events and temporary host-mitigation provenance."""
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
from pathlib import Path

WORK=Path(__file__).resolve().parent
ROOT=Path(r'C:\Users\Darrys\do-an\evidence\ml-v2')
command="""Get-WinEvent -FilterHashtable @{LogName='System';ProviderName='Microsoft-Windows-Kernel-Power';StartTime=(Get-Date).AddHours(-2);Id=506,507} -ErrorAction Stop | ForEach-Object { [pscustomobject]@{at_utc=$_.TimeCreated.ToUniversalTime().ToString('o');id=$_.Id;message=$_.Message} } | ConvertTo-Json -Compress"""
result=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
if result.returncode:raise RuntimeError('Cannot capture the power-event evidence')
events=json.loads(result.stdout)
out=ROOT/'verification'/('modern-standby-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
out.mkdir(parents=True)
(out/'power-events.json').write_text(json.dumps(events,indent=2),encoding='utf-8')
files={}
for name in ['lab_host_guard.py','display_guard_diagnostic.py','wake_lab_display_once.py','verify_lab_guard.py',Path(__file__).name]:
    source=WORK/name;target=out/'sources'/name;target.parent.mkdir(exist_ok=True)
    shutil.copyfile(source,target);files['sources/'+name]=hashlib.sha256(target.read_bytes()).hexdigest()
for pattern in ['display-guard-*.json','display-wake-*.json','lab-wake-tests-*.json','ml-slow-ssh-20261031*.json']:
    for source in (WORK/'verification').glob(pattern):
        target=out/source.name;shutil.copyfile(source,target);files[source.name]=hashlib.sha256(target.read_bytes()).hexdigest()
record={'recorded_at':datetime.now(timezone.utc).isoformat(),
        'finding':'Windows logged Modern Standby/Idle Timeout at 2026-10-31 13:48:37 UTC+7 during trial recovery; SSH failed on all three VMs. User confirmed screen had been off/locked and woke it.',
        'wake':'Windows logged exit at 14:01:48 UTC+7 (SC_MONITORPOWER), a brief re-entry, then exit at 14:01:51 (Input Keyboard).',
        'mitigation':'Temporary display+system wake request renewed every 10/15 seconds; normal-exit cleanup, no power-plan/lock/security/VM hardware change.',
        'limits':'Temporal association and user confirmation support the idle explanation for this episode, not proof that every historical RCU stall has the same cause. Model features/parameters/validity gates are unchanged.',
        'source_sha256':files}
(out/'FINDING.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({'status':'POWER_EVENT_EVIDENCE_SAVED','output':str(out)},ensure_ascii=True),flush=True)

"""Bounded wake guard during repair between coordinator runs."""
import json,time
from pathlib import Path
from lab_host_guard import lab_host_guard

WORK=Path(__file__).resolve().parent
with lab_host_guard() as profile:
    print(json.dumps({'status':'MAINTENANCE_WAKE_GUARD_ACTIVE','maximum_seconds':1200,'profile':profile}),flush=True)
    deadline=time.monotonic()+1200
    while time.monotonic()<deadline:
        state=json.loads((WORK/'verification/full-ml-status.json').read_text(encoding='utf-8'))
        if state['phase'] in ['PAUSED_BY_USER','COMPLETE_INITIAL_VM_ML']:break
        time.sleep(10)
print(json.dumps({'status':'MAINTENANCE_WAKE_GUARD_CLEARED'}),flush=True)

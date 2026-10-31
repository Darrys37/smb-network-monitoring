"""Temporary display/system wake request to investigate idle-associated lab stalls."""
import ctypes
from ctypes import wintypes
from datetime import datetime,timezone
import json
from pathlib import Path
import time

WORK=Path(__file__).resolve().parent
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
kernel.SetThreadExecutionState.argtypes=[wintypes.DWORD]
kernel.SetThreadExecutionState.restype=wintypes.DWORD
previous=kernel.SetThreadExecutionState(0x80000003)
if not previous:raise ctypes.WinError(ctypes.get_last_error())
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
record={'started_at':datetime.now(timezone.utc).isoformat(),'mode':'temporary_display_and_system_required',
        'purpose':'Investigate idle/display-associated VM stalls; not an established cause',
        'settings_changed':False,'maximum_seconds':6*3600,'previous_thread_state':previous}
path=WORK/'verification'/('display-guard-'+stamp+'.json')
path.write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record),flush=True)
try:
    deadline=time.monotonic()+6*3600
    while time.monotonic()<deadline:
        # Modern Standby/resume can require renewing an existing wake request.
        if not kernel.SetThreadExecutionState(0x80000003):
            raise ctypes.WinError(ctypes.get_last_error())
        state=json.loads((WORK/'verification/full-ml-status.json').read_text(encoding='utf-8'))
        if state['phase'] in ['COMPLETE_INITIAL_VM_ML','STOPPED_REQUIRES_REVIEW','PAUSED_BY_USER']:break
        time.sleep(10)
finally:
    kernel.SetThreadExecutionState(0x80000000)
    record['ended_at']=datetime.now(timezone.utc).isoformat()
    record['request_cleared']=True
    path.write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record),flush=True)

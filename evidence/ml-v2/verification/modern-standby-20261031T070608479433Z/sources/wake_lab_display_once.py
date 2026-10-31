"""Request display power-on once; do not send input, unlock Windows or change policy."""
import ctypes
from ctypes import wintypes
from datetime import datetime,timezone
import json
from pathlib import Path

user=ctypes.WinDLL('user32',use_last_error=True)
send=user.SendMessageTimeoutW
send.argtypes=[wintypes.HWND,wintypes.UINT,ctypes.c_size_t,ctypes.c_ssize_t,
               wintypes.UINT,wintypes.UINT,ctypes.POINTER(ctypes.c_size_t)]
send.restype=ctypes.c_ssize_t
response=ctypes.c_size_t()
result=send(0xffff,0x0112,0xf170,-1,2,100,ctypes.byref(response))
record={'at':datetime.now(timezone.utc).isoformat(),'action':'WM_SYSCOMMAND/SC_MONITORPOWER/power-on',
        'request_sent':bool(result),'win32_last_error':ctypes.get_last_error(),
        'scope':'Display power only; no simulated input, no unlock, no permanent policy change',
        'reference':'https://learn.microsoft.com/en-us/windows/win32/menurc/wm-syscommand'}
path=Path(__file__).resolve().parent/'verification'/('display-wake-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
path.write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record),flush=True)

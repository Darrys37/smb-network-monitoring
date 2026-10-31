"""Temporary host scheduling guard for these three lab VMs; restores on exit."""
import ctypes
from ctypes import wintypes
from contextlib import contextmanager
import json,re,struct
import threading
from pathlib import Path


def cpu_sets():
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    function=kernel.GetSystemCpuSetInformation
    function.argtypes=[ctypes.c_void_p,wintypes.ULONG,ctypes.POINTER(wintypes.ULONG),wintypes.HANDLE,wintypes.ULONG]
    function.restype=wintypes.BOOL
    size=wintypes.ULONG();function(None,0,ctypes.byref(size),None,0)
    if not size.value:raise OSError('CPU set information unavailable')
    buffer=ctypes.create_string_buffer(size.value)
    if not function(buffer,size,ctypes.byref(size),None,0):raise ctypes.WinError(ctypes.get_last_error())
    data=buffer.raw;offset=0;rows=[]
    while offset<len(data):
        length,kind=struct.unpack_from('<II',data,offset)
        if length<8:raise ValueError('Invalid CPU set structure')
        if kind==0:
            values=struct.unpack_from('<IIIHBBBBBBIQ',data,offset)
            rows.append({'id':values[2],'group':values[3],'logical_index':values[4],
                         'core_index':values[5],'efficiency_class':values[8],'flags':values[9]})
        offset+=length
    return rows


def performance_mask(rows):
    if not rows or any(row['group']!=0 for row in rows):raise ValueError('This guard supports one CPU group')
    best=max(row['efficiency_class'] for row in rows)
    return sum(1<<row['logical_index'] for row in rows if row['efficiency_class']==best)


def vm_pids():
    result={}
    for name in ['MON01','SRV01','CLI01']:
        path=Path.home()/'VirtualBox VMs'/name/'Logs/VBox.log'
        text='\n'.join(path.read_text(encoding='utf-8',errors='replace').splitlines()[:60])
        found=re.search(r'Process ID:\s*(\d+)',text)
        if not found:raise ValueError('VM process ID missing: '+name)
        result[name]=int(found.group(1))
    return result


@contextmanager
def lab_host_guard(pin_performance=False):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.GetProcessAffinityMask.argtypes=[wintypes.HANDLE,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)]
    kernel.SetProcessAffinityMask.argtypes=[wintypes.HANDLE,ctypes.c_size_t]
    kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    kernel.SetThreadExecutionState.argtypes=[wintypes.DWORD];kernel.SetThreadExecutionState.restype=wintypes.DWORD
    wake_flags=0x80000003 # Keep display/system awake during the bounded lab operation.
    previous=kernel.SetThreadExecutionState(wake_flags)
    if not previous:raise ctypes.WinError(ctypes.get_last_error())
    stop_refresh=threading.Event()
    refresh_errors=[]
    def renew_wake_request():
        try:
            while not stop_refresh.wait(15):
                if not kernel.SetThreadExecutionState(wake_flags):
                    refresh_errors.append(ctypes.get_last_error())
        finally:
            kernel.SetThreadExecutionState(0x80000000)
    refresher=threading.Thread(target=renew_wake_request,name='lab-wake-request',daemon=True)
    refresher.start()
    opened=[];changes=[]
    try:
        rows=cpu_sets();mask=performance_mask(rows)
        for name,pid in (vm_pids().items() if pin_performance else []):
            handle=kernel.OpenProcess(0x1600,False,pid)
            if not handle:raise ctypes.WinError(ctypes.get_last_error())
            original=ctypes.c_size_t();system=ctypes.c_size_t()
            opened.append((handle,None))
            image=ctypes.create_unicode_buffer(32768);length=wintypes.DWORD(len(image))
            if not kernel.QueryFullProcessImageNameW(handle,0,image,ctypes.byref(length)):
                raise ctypes.WinError(ctypes.get_last_error())
            if Path(image.value).name.lower()!='virtualboxvm.exe':raise ValueError('Unexpected VM process image')
            if not kernel.GetProcessAffinityMask(handle,ctypes.byref(original),ctypes.byref(system)):
                raise ctypes.WinError(ctypes.get_last_error())
            desired=mask&system.value
            if not desired:raise ValueError('No eligible performance CPUs')
            opened[-1]=(handle,original.value)
            if not kernel.SetProcessAffinityMask(handle,desired):raise ctypes.WinError(ctypes.get_last_error())
            changes.append({'vm':name,'pid':pid,'old_mask':hex(original.value),'temporary_mask':hex(desired)})
        yield {'cpu_sets':rows,'vm_affinity':changes,'power_request':'ES_CONTINUOUS|ES_SYSTEM_REQUIRED|ES_DISPLAY_REQUIRED',
               'mode':'performance_affinity' if pin_performance else 'display_and_system_awake',
               'refresh_seconds':15,'refresh_errors':refresh_errors,
               'scope':'Temporary display/system wake request, renewed after idle/resume. Affinity remains optional/off; power plan and lock policy are unchanged.'}
    finally:
        stop_refresh.set();refresher.join(timeout=2)
        for handle,original in reversed(opened):
            if original is not None:kernel.SetProcessAffinityMask(handle,original)
            kernel.CloseHandle(handle)
        kernel.SetThreadExecutionState(0x80000000)


if __name__=='__main__':
    print(json.dumps({'cpu_sets':cpu_sets(),'performance_mask':hex(performance_mask(cpu_sets())),'vm_pids':vm_pids()},ensure_ascii=True))

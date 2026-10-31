"""Start one hidden one-off supervisor without credentials in argv or files."""
import getpass
import json
from pathlib import Path
import subprocess
import sys
import time

work=Path(__file__).resolve().parent
password=getpass.getpass('VM SSH password (not logged): ')
log=work/'verification/ml-supervisor.log'
with log.open('ab',buffering=0) as stream:
    child=subprocess.Popen([sys.executable,'-u',str(work/'ml_supervisor.py'),sys.argv[1]],
        cwd=work,stdin=subprocess.PIPE,stdout=stream,stderr=stream,
        creationflags=subprocess.CREATE_NO_WINDOW|subprocess.DETACHED_PROCESS)
    child.stdin.write((password+'\n').encode('utf-8'));child.stdin.flush();child.stdin.close()
password=None
time.sleep(2)
if child.poll() is not None:raise RuntimeError('Supervisor exited; inspect its log')
print(json.dumps({'status':'SUPERVISOR_STARTED','pid':child.pid,'log':str(log),'credentials':'memory-only anonymous pipe'}))

"""Local submission audit; secrets stay in memory and never enter output."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
import week5_rehearse as w
project=Path(r'C:\Users\Darrys\do-an');out=w.ROOT
def git(*args):return subprocess.check_output(['git','-C',str(project),*args])
# Remote secret is returned only to this process, not to the transcript or disk.
token=w.py('mon01','from zabbix_client import ZABBIX_API_TOKEN;assert ZABBIX_API_TOKEN;print(ZABBIX_API_TOKEN)')['stdout'].strip().encode()
assert len(token)>=16
work_files=[];work_hits=[];pattern_hits=[]
pattern=re.compile(rb'(?:ZABBIX_API_TOKEN|api_token)\s*(?:=|:)\s*[\x22\x27]([a-fA-F0-9]{32,128})[\x22\x27]',re.I)
for p in project.rglob('*'):
    if not p.is_file() or '.git' in p.relative_to(project).parts or p.name=='.env' or p.suffix=='.db':continue
    if '.venv' in p.parts or '__pycache__' in p.parts:continue
    data=p.read_bytes();name=str(p.relative_to(project));work_files.append(name)
    if token in data:work_hits.append(name)
    if pattern.search(data):pattern_hits.append(name)
oids=[line.split(b' ',1)[0] for line in git('rev-list','--objects','--all').splitlines()]
proc=subprocess.Popen(['git','-C',str(project),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
history_hits=[];history_pattern_hits=[];blobcount=0
for oid in dict.fromkeys(oids):
    proc.stdin.write(oid+b'\n');proc.stdin.flush();header=proc.stdout.readline().split()
    if len(header)!=3:continue
    data=proc.stdout.read(int(header[2]));proc.stdout.read(1)
    if header[1]!=b'blob':continue
    blobcount+=1
    if token in data:history_hits.append(oid.decode())
    if pattern.search(data):history_pattern_hits.append(oid.decode())
proc.stdin.close();proc.wait()
tracked=git('ls-files','-z').split(b'\0')
env_tracked=any(n and Path(n.decode()).name=='.env' for n in tracked)
report={'result':'PASS' if not (work_hits or pattern_hits or history_hits or history_pattern_hits or env_tracked) else 'REVIEW_REQUIRED','files_scanned':len(work_files),'reachable_blobs_scanned':blobcount,'current_token_working_hits':len(work_hits),'current_token_reachable_history_hits':len(history_hits),'literal_hex_token_assignment_working_hits':pattern_hits,'literal_hex_token_assignment_history_blob_ids':history_pattern_hits,'env_tracked':env_tracked,'image_review':'Three selected fallback screenshots visually inspected; no token/password shown. Only private lab IPs/loopback visible; retained to explain topology.','limitation':'Exact current token and high-signal hex assignments only; unknown old credentials, unreachable Git objects, external refs and arbitrary OCR not certified.'}
w.save(out/'credential-audit.json',report);print(json.dumps(report,indent=2));assert report['result']=='PASS'

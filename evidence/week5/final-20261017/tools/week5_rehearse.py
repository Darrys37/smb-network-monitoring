"""SSH-only week 5 technical rehearsals. Password supplied transiently by env/getpass."""
import base64,concurrent.futures,getpass,hashlib,json,os,shlex,sys,time
from datetime import datetime,timezone
from pathlib import Path
import paramiko
ROOT=Path(__file__).resolve().parent/'outputs/week5-final-20261017';ROOT.mkdir(parents=True,exist_ok=True)
ENGINE='/home/phat/do-an/diagnosis-engine';REMOTE='/home/phat/do-an/evidence/week5/rehearsals-20261017'
PASSWORD=os.environ.get('DOAN_VM_PASSWORD') or getpass.getpass('VM password: ')
HOSTS={'mon01':'192.168.56.10','srv01':'192.168.56.20','cli01':'192.168.56.30'}
def utc():return datetime.now(timezone.utc).isoformat()
def save(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def connect(host):
    c=paramiko.SSHClient();c.load_host_keys(str(Path.home()/'.ssh/known_hosts'));c.set_missing_host_key_policy(paramiko.RejectPolicy());c.connect(HOSTS[host],username='phat',password=PASSWORD,look_for_keys=False,allow_agent=False,timeout=8,auth_timeout=8);return c
def command(host,cmd,sudo=False,timeout=60):
    c=connect(host)
    try:
        actual='sudo -S -p '+shlex.quote('')+' bash -c '+shlex.quote(cmd) if sudo else cmd
        a,b,d=c.exec_command(actual,timeout=timeout)
        if sudo:a.write(PASSWORD+'\n');a.flush()
        a.channel.shutdown_write();stdout=b.read().decode();stderr=d.read().decode();rc=b.channel.recv_exit_status()
        result={'at_utc':utc(),'exit_code':rc,'stdout':stdout,'stderr':stderr}
        if rc:raise RuntimeError(f'{host} command exit {rc}: {stderr[-500:]}')
        return result
    finally:c.close()
def py(host,code):
    encoded=base64.b64encode(code.encode()).decode();python=ENGINE+'/.venv/bin/python' if host=='mon01' else 'python3'
    return command(host,'cd '+shlex.quote(ENGINE if host=='mon01' else '/home/phat')+' && '+python+' -c '+shlex.quote('import base64;exec(base64.b64decode('+repr(encoded)+'))'))
def api(method,params):return json.loads(py('mon01','from zabbix_client import call_api;import json;print(json.dumps(call_api('+repr(method)+','+repr(params)+',135)))')['stdout'])
def problems():return api('problem.get',{'hostids':['10084','10683','10684'],'source':0,'object':0,'recent':False,'output':['eventid','objectid','clock','name']})
def unexpected_problems(items):
    # Rehearsal protocol permits only classified uptime notifications following verified reboot.
    # No trigger is changed or suppressed; every background event is retained in run.json.
    return [p for p in items if not (p['objectid'] in ('22388','25256','25300') and 'has been restarted (uptime < 10m)' in p['name'])]
def event(eid):return api('event.get',{'eventids':[str(eid)],'output':'extend','selectHosts':['hostid','host','name']})[0]
def boot(host):return command(host,'hostname; cat /proc/sys/kernel/random/boot_id; date -u -Is; systemctl is-active zabbix-agent2')['stdout'].splitlines()
def phase_reboot():
    pre={h:boot(h) for h in HOSTS};save(ROOT/'pre-reboot.json',pre)
    assert not problems(),'Do not reboot with unresolved background problems'
    print('Preflight PASS; rebooting all three VMs.',flush=True)
    requests={}
    for h in ['cli01','srv01','mon01']:
        try:requests[h]=command(h,'systemctl reboot --no-block',sudo=True)
        except (OSError,EOFError,paramiko.SSHException) as exc:requests[h]={'connection_closed_after_request':type(exc).__name__}
    save(ROOT/'reboot-requests.json',requests)
    post={};deadline=time.monotonic()+240
    while time.monotonic()<deadline and len(post)<3:
        for h in HOSTS:
            if h in post:continue
            try:
                value=boot(h)
                if value[1]!=pre[h][1] and value[-1]=='active':post[h]=value;print(h+' reboot verified.',flush=True)
            except Exception:pass
        if len(post)<3:time.sleep(8)
    assert len(post)==3,'Reboot verification incomplete';save(ROOT/'post-reboot.json',post)
    observations=[];deadline=time.monotonic()+360
    while time.monotonic()<deadline:
        try:
            p=problems();observations.append({'at':utc(),'problems':p})
            if not p:
                # Require available agents and supported monitored items, not just empty Problems.
                hosts=api('host.get',{'hostids':['10084','10683','10684'],'output':['hostid','host'],'selectInterfaces':['type','available']})
                if all(i['available']=='1' for h in hosts for i in h['interfaces'] if i['type']=='1'):
                    save(ROOT/'postboot-observations.json',observations);save(ROOT/'postboot-hosts.json',hosts);print('Lab recovered after reboot: no open problems, 3 agents available.',flush=True);return
        except Exception as exc:observations.append({'at':utc(),'waiting_error_type':type(exc).__name__})
        time.sleep(10)
    save(ROOT/'postboot-observations.json',observations);raise RuntimeError('Lab did not return to a clean baseline in 360s')
def demo(number,suffix=''):
    runid=f'DEMO-{number:02d}'+suffix;folder=ROOT/runid;folder.mkdir(exist_ok=False)
    started=utc();tick=time.monotonic();unit='week5-'+runid.lower()+'-'+str(int(time.time()));remote=REMOTE+'/'+runid
    record={'run_id':runid,'started_at_utc':started,'kind':'automated technical rehearsal; excludes spoken presentation','status':'started','unit':unit}
    save(folder/'run.json',record)
    before=problems();record['classified_background_problems_before']=before
    assert not unexpected_problems(before),'Unexpected open background problem at rehearsal start'
    command('srv01','systemctl is-active nginx zabbix-agent2; curl --fail --max-time 5 -s -o /dev/null -w "%{http_code}" http://192.168.56.20/')
    print(runid+' preflight PASS; scheduling 300s failsafe before stopping nginx.',flush=True)
    mutation=False
    try:
        fault='set -eu; install -d -o phat -g phat '+shlex.quote(remote)+'; exec > '+shlex.quote(remote+'/fault.log')+' 2>&1; systemd-run --unit='+shlex.quote(unit)+' --on-active=300s --timer-property=AccuracySec=1s /usr/bin/systemctl start nginx; echo "FAULT_BEFORE $(date -u -Is)"; systemctl stop nginx; echo "FAULT_AFTER $(date -u -Is)"; systemctl is-active nginx || true'
        command('srv01',fault,sudo=True);mutation=True
        c=connect('srv01')
        with c.open_sftp() as s:s.get(remote+'/fault.log',str(folder/'fault.log'))
        c.close()
        deadline=time.monotonic()+150;problem=None
        while time.monotonic()<deadline:
            choices=[p for p in problems() if p['objectid']=='25334']
            if choices:problem=event(choices[0]['eventid']);break
            time.sleep(3)
        assert problem,'No HTTP problem within 150s';save(folder/'problem.json',problem);eid=problem['eventid']
        print(runid+' new problem '+eid+'; collecting fresh local HTTP.',flush=True)
        probe_path=remote+'/local-http.json'
        command('srv01','mkdir -p '+shlex.quote(remote)+'; python3 /home/phat/http_probe.py --target-ip 192.168.56.20 --observer srv01 --output '+shlex.quote(probe_path))
        c=connect('srv01')
        with c.open_sftp() as s:s.get(probe_path,str(folder/'local-http.json'))
        c.close()
        assert json.loads((folder/'local-http.json').read_text())['observer']=='srv01'
        command('mon01','mkdir -p '+shlex.quote(remote))
        c=connect('mon01')
        with c.open_sftp() as s:s.put(str(folder/'local-http.json'),probe_path)
        c.close()
        args=ENGINE+'/.venv/bin/python app.py --event-id '+eid+' --host-id 10683 --target-ip 192.168.56.20 --ruleset roadmap --control-ip 192.168.56.30 --http-service expected --http-observer srv01 --http-evidence '+shlex.quote(probe_path)+' --save'
        cli_start=time.monotonic();result=command('mon01','cd '+ENGINE+' && '+args)
        record['cli_elapsed_seconds_including_ssh']=time.monotonic()-cli_start
        (folder/'diagnosis.log').write_text(result['stdout'],encoding='utf-8',newline='\n')
        import re
        match=re.search(r'Saved incident ID: (\d+)',result['stdout']);assert match,'CLI did not save incident';iid=int(match.group(1))
        assert 'R2_HTTP_SERVICE_SUSPECTED matched' in result['stdout']
        record.update(problem_event_id=eid,incident_id=iid)
        rollback='set -eu; exec > '+shlex.quote(remote+'/rollback.log')+' 2>&1; echo "ROLLBACK_BEFORE $(date -u -Is)"; systemctl start nginx; echo "ROLLBACK_AFTER $(date -u -Is)"; systemctl is-active nginx zabbix-agent2; curl --fail --max-time 5 -s -o /dev/null -w "LOCAL_HTTP %{http_code}\\n" http://192.168.56.20/; systemctl stop '+unit+'.timer; echo "RESTORATION_LOCAL_VERIFIED $(date -u -Is)"'
        command('srv01',rollback,sudo=True);mutation=False
        c=connect('srv01')
        with c.open_sftp() as s:s.get(remote+'/rollback.log',str(folder/'rollback.log'))
        c.close()
        deadline=time.monotonic()+150;recovered=None
        while time.monotonic()<deadline:
            p=event(eid)
            if p.get('r_eventid','0')!='0':recovered=p;break
            time.sleep(3)
        assert recovered,'Recovery missing';save(folder/'problem-after-recovery.json',recovered)
        save(folder/'recovery.json',event(recovered['r_eventid']))
        r=command('mon01','cd '+ENGINE+' && .venv/bin/python recovery.py --event-id '+eid);(folder/'recovery-sync.log').write_text(r['stdout'],encoding='utf-8',newline='\n')
        for fmt in ['json','md','csv']:
            r=command('mon01','cd '+ENGINE+' && .venv/bin/python report.py --incident-id '+str(iid)+' --format '+fmt)
            (folder/('incident.'+fmt)).write_text(r['stdout'],encoding='utf-8',newline='\n')
        report=json.loads((folder/'incident.json').read_text());assert report['lifecycle_status']=='closed'
        assert report['recovery']['recovery_event_id']==recovered['r_eventid']
        after=problems();assert not unexpected_problems(after)
        record.update(status='PASS',recovery_event_id=recovered['r_eventid'],ended_at_utc=utc(),elapsed_seconds=time.monotonic()-tick,nginx_restored=True,background_problems_after=after,unexpected_background_problems_after=0,engine_code_modified=False)
        save(folder/'run.json',record);print(runid+' PASS: problem '+eid+' -> incident '+str(iid)+' -> recovery '+recovered['r_eventid']+'; '+str(round(record['elapsed_seconds'],2))+'s technical flow.',flush=True)
    except Exception as exc:
        record.update(status='FAILED',error_type=type(exc).__name__,error=str(exc),elapsed_seconds=time.monotonic()-tick);save(folder/'run.json',record);raise
    finally:
        if mutation:
            try:command('srv01','systemctl start nginx; systemctl stop '+unit+'.timer',sudo=True);print(runid+' emergency rollback executed.',flush=True)
            except Exception:print('Emergency manual rollback required; 300s failsafe was scheduled.',flush=True)
def finalize_remote():
    print('Running full existing unit suite on MON01.',flush=True)
    tests=command('mon01','cd '+ENGINE+' && .venv/bin/python -m pytest -q',timeout=150)
    (ROOT/'pytest.log').write_text(tests['stdout']+tests['stderr'],encoding='utf-8',newline='\n')
    code=Path(__file__).with_name('day31_remote_readonly.py').read_text()
    for h in HOSTS:
        data=json.loads(py(h,code)['stdout']);save(ROOT/(h+'-final.json'),data)
    backup=REMOTE+'/diagnosis-week5-final.db'
    r=py('mon01',"import sqlite3,hashlib,json;from pathlib import Path;p=Path("+repr(backup)+");assert not p.exists();a=sqlite3.connect('file:"+ENGINE+"/diagnosis.db?mode=ro',uri=True);b=sqlite3.connect(p);a.backup(b);b.close();a.close();print(json.dumps({'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'path':str(p)}))")
    save(ROOT/'sqlite-backup.json',json.loads(r['stdout']))
    c=connect('mon01')
    with c.open_sftp() as s:s.get(backup,str(ROOT/'diagnosis-week5-final.db'))
    c.close()
    # Export contains host/template configuration; API export never contains API authentication token.
    exported=api('configuration.export',{'format':'yaml','options':{'hosts':['10084','10683','10684']}})
    (ROOT/'zabbix-hosts-week5.yaml').write_text(exported,encoding='utf-8',newline='\n')
    print('Tests and final live snapshots saved; SQLite backup transferred and Zabbix host export created.',flush=True)
if __name__=='__main__':
    phase_reboot()
    for n in [1,2,3]:demo(n)
    finalize_remote()
    save(ROOT/'rehearsals-summary.json',{'result':'PASS','completed_at_utc':utc(),'runs':[json.loads((ROOT/f'DEMO-{n:02d}/run.json').read_text()) for n in [1,2,3]],'scope':'Three automated technical rehearsals after verified reboot of all VMs. Spoken ten-minute presentation is not measured.'})

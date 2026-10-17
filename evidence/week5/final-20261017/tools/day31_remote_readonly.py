"""Read-only live architecture inspection; run through SSH, never print credentials."""
import hashlib,json,os,socket,sqlite3,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
def cmd(args):
    r=subprocess.run(args,capture_output=True,text=True,timeout=20)
    return {'exit_code':r.returncode,'stdout':r.stdout.strip(),'stderr':r.stderr.strip()}
host=socket.gethostname().lower().split('.')[0]
root=Path('/home/phat/do-an/diagnosis-engine')
result={'captured_at_utc':datetime.now(timezone.utc).isoformat(),'hostname':host,'os_release':Path('/etc/os-release').read_text(),'kernel':cmd(['uname','-r']),'python':sys.version,'interfaces':cmd(['ip','-j','address']),'routes':cmd(['ip','-j','route']),'ntp':cmd(['timedatectl','show','-p','NTPSynchronized']),'listeners':cmd(['ss','-lnt']),'resolver':cmd(['resolvectl','status'])}
services=['zabbix-agent2']+(['zabbix-server','mysql','nginx'] if host=='mon01' else ['nginx'] if host=='srv01' else [])
result['services']={s:cmd(['systemctl','is-active',s]) for s in services}
result['http']=cmd(['curl','--fail','--max-time','5','-s','-o','/dev/null','-w','%{http_code}','http://192.168.56.20/'])
result['agent_settings']={}
for p in [Path('/etc/zabbix/zabbix_agent2.conf'),*Path('/etc/zabbix/zabbix_agent2.d').glob('*.conf')]:
    try:
        for line in p.read_text().splitlines():
            if any(line.startswith(k+'=') for k in ['Server','ServerActive','Hostname','ListenPort','ListenIP']):result['agent_settings'].setdefault(p.name,[]).append(line)
    except PermissionError:pass
if host=='mon01':
    os.chdir(root);sys.path.insert(0,str(root))
    from zabbix_client import call_api,get_api_version
    api=lambda m,p:call_api(m,p,131)
    hosts=['10084','10683','10684']
    fields=['itemid','hostid','name','key_','type','value_type','delay','history','trends','status','state','error','lastclock','lastvalue','units','master_itemid']
    keys=['system.uptime','agent.ping','zabbix[host,agent,available]','system.cpu.util','system.cpu.util[,idle]','system.cpu.load[all,avg1]','system.cpu.num','vm.memory.util','web.test.fail[SRV01 HTTP]','web.test.rspcode[SRV01 HTTP,Homepage]','web.test.time[SRV01 HTTP,Homepage,resp]','net.dns[,example.com,A,2,1,udp]']
    items=api('item.get',{'hostids':hosts,'webitems':True,'filter':{'key_':keys},'output':fields,'selectPreprocessing':'extend'})
    cfg={'items':sorted([{k:v for k,v in row.items() if k not in ('lastvalue','lastclock','state','error')} for row in items],key=lambda r:int(r['itemid']))}
    cfg['triggers']=sorted(api('trigger.get',{'hostids':hosts,'output':['triggerid','description','expression','recovery_expression','priority','status','type','manual_close'],'selectDependencies':['triggerid'],'selectHosts':['hostid'],'selectFunctions':['functionid','itemid','function','parameter']}),key=lambda r:int(r['triggerid']))
    cfg['web_scenarios']=sorted(api('httptest.get',{'hostids':hosts,'output':['httptestid','hostid','name','delay','retries','status'],'selectSteps':['name','url','timeout','status_codes']}),key=lambda r:int(r['httptestid']))
    # Same read scope as the baseline: never request secret macro values.
    import re
    used=sorted(set(re.findall(r'\{\$[^}]+\}','\n'.join(t['expression']+'\n'+t['recovery_expression'] for t in cfg['triggers']))))
    macros=[]
    for scope in [False,True]:
        macros+=api('usermacro.get',{'globalmacro':scope,'filter':{'macro':used,'type':'0'},'output':['macro','value','type'] if scope else ['hostid','macro','value','type']})
    cfg['referenced_text_macros']=sorted(macros,key=lambda r:(r.get('hostid',''),r['macro']))
    result.update(api_version=get_api_version(),effective_config=cfg,items_runtime=items,hosts=api('host.get',{'hostids':hosts,'output':['hostid','host','name','status'],'selectInterfaces':['type','ip','port','useip','available'],'selectParentTemplates':['templateid','host','name']}),open_problems=api('problem.get',{'hostids':hosts,'source':0,'object':0,'recent':False,'output':['eventid','objectid','clock','name']}))
    files=list(root.glob('*.py'))+list((root/'tests').rglob('*.py'))+[root/'requirements.txt',root/'pytest.ini']
    result['source_hashes']={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    db=root/'diagnosis.db'
    with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as conn:
        conn.execute('BEGIN')
        result['sqlite']={'integrity_check':conn.execute('PRAGMA integrity_check').fetchall(),'foreign_key_check':conn.execute('PRAGMA foreign_key_check').fetchall(),'schema':conn.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name").fetchall(),'counts':{t:conn.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['incidents','evidence','diagnoses','recoveries']}}
print(json.dumps(result,ensure_ascii=True))

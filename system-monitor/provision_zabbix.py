"""Run on MON01 with .env.admin; additive lab objects only, never runtime credentials."""
import json
from pathlib import Path
import requests
from dotenv import dotenv_values


def provision():
    root=Path('/home/phat/do-an/diagnosis-engine')
    normal=dotenv_values(root/'.env')
    token=dotenv_values(root/'.env.admin').get('ZABBIX_ADMIN_API_TOKEN')
    if not token:raise RuntimeError('Admin token missing')
    counter=0
    def api(method,params):
        nonlocal counter
        counter+=1
        response=requests.post(normal['ZABBIX_URL'],headers={'Authorization':'Bearer '+token},
            json={'jsonrpc':'2.0','method':method,'params':params,'id':counter},timeout=8)
        response.raise_for_status();data=response.json()
        if 'error' in data:
            # None of the provisioning parameters contain credentials.
            raise ValueError(method+': '+str(data['error'].get('data','API error')))
        return data['result']
    hosts={};items={};triggers={}
    for name,address in [('CLI01-Gateway','192.168.56.30'),('SRV01-Routed','172.30.20.20')]:
        found=api('host.get',{'filter':{'host':[name]},'selectTags':'extend','selectInterfaces':'extend','output':['hostid','host']})
        if found:
            row=found[0]
            if not any(tag.get('tag')=='diag.scope' and tag.get('value')=='system-v3' for tag in row['tags']):raise ValueError('Unowned host collision')
            if row['interfaces'][0]['ip']!=address:raise ValueError('Unexpected lab interface')
            identity=row['hostid'];interface=row['interfaces'][0]['interfaceid']
        else:
            identity=api('host.create',{'host':name,'groups':[{'groupid':'2'}],
                'interfaces':[{'type':1,'main':1,'useip':1,'ip':address,'dns':'','port':'10050'}],
                'tags':[{'tag':'diag.scope','value':'system-v3'}]})['hostids'][0]
            interface=api('hostinterface.get',{'hostids':[identity],'output':['interfaceid']})[0]['interfaceid']
        hosts[name]={'hostid':identity,'interfaceid':interface,'ip':address}
    def item(host,key,name,kind=0,value=3,**extra):
        identity=hosts[host]['hostid']
        found=api('item.get',{'hostids':[identity],'filter':{'key_':[key]},'output':['itemid','key_']})
        if found:result=found[0]['itemid']
        else:
            params={'hostid':identity,'key_':key,'name':name,'type':kind,'value_type':value,'delay':'5s','history':'7d',
                    'tags':[{'tag':'diag.scope','value':'system-v3'}],**extra}
            if kind in {0,3}:params['interfaceid']=hosts[host]['interfaceid']
            if kind in {2,18}:params.pop('delay',None)
            result=api('item.create',params)['itemids'][0]
        items[host+':'+key]=result
        return result
    def trigger(host,key,name,expression,kind):
        found=api('trigger.get',{'hostids':[hosts[host]['hostid']],'filter':{'description':[name]},'output':['triggerid']})
        result=found[0]['triggerid'] if found else api('trigger.create',{'description':name,'expression':expression,'priority':3,
             'tags':[{'tag':'diag.scope','value':'system-v3'},{'tag':'diag.kind','value':kind}]})['triggerids'][0]
        triggers[host+':'+key]=result
    gateway='CLI01-Gateway';server='SRV01-Routed'
    for host in hosts:
        item(host,'icmpping','V3: routed/management ICMP availability',3)
        trigger(host,'icmp','V3 '+host+': ICMP unavailable','last(/'+host+'/icmpping)=0','reachability')
    item(gateway,'diag.router.ready','V3: actual forwarding, interface and route readiness')
    trigger(gateway,'router','V3 CLI01: gateway forwarding unavailable','last(/'+gateway+'/diag.router.ready)=0','reachability')
    master=item(gateway,'diag.dns.json','V3: DNS response and measured query time',0,4,delay='15s')
    item(gateway,'diag.dns.status','V3: DNS response status',18,1,master_itemid=master,
         preprocessing=[{'type':12,'params':'$.status','error_handler':0,'error_handler_params':''}])
    item(gateway,'diag.dns.ms','V3: DNS response time in ms',18,0,master_itemid=master,units='ms',preprocessing=[
         {'type':12,'params':'$.response_time_ms','error_handler':1,'error_handler_params':''},
         {'type':21,'params':'if(value === "null") return null; return value;','error_handler':0,'error_handler_params':''}])
    trigger(gateway,'dns','V3 CLI01: DNS lookup failed','last(/'+gateway+'/diag.dns.status)<>"success"','dns')
    item(server,'agent.ping','V3: routed Zabbix agent sample')
    item(server,'net.tcp.service[tcp,,80]','V3: routed TCP/80 availability',3)
    item(server,'diag.service.nginx','V3: local Nginx active state')
    trigger(server,'tcp80','V3 SRV01: routed TCP/80 unavailable','last(/'+server+'/net.tcp.service[tcp,,80])=0','http_connectivity')
    trigger(server,'nginx','V3 SRV01: local Nginx stopped','last(/'+server+'/diag.service.nginx)=0','http_service')
    trigger(server,'agent','V3 SRV01: routed agent samples missing','nodata(/'+server+'/agent.ping,30s)=1','agent_connectivity')
    for number in range(1,21):
        key='diag.storm['+str(number)+']'
        item(server,key,'V3 synthetic alert channel '+str(number),2,trapper_hosts='127.0.0.1,192.168.56.10')
        trigger(server,key,'V3 SYNTHETIC routed symptom '+str(number),'last(/'+server+'/'+key+')=1','http_connectivity')
    receipt={'hosts':hosts,'items':items,'triggers':triggers,'scope':'Additive two logical hosts on exactly three VMs; no native trigger dependencies hide raw events'}
    path=Path(__file__).resolve().parent/'config/provisioned.json'
    path.write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    try:print(json.dumps(provision()))
    except Exception as error:
        # Error messages contain only non-secret provisioning metadata.
        print(json.dumps({'status':'ERROR','error_type':type(error).__name__,'detail':str(error) if isinstance(error,ValueError) else None}))
        raise SystemExit(2)

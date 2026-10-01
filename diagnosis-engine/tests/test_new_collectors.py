import subprocess
from unittest.mock import Mock
import pytest
import roadmap_evidence as collectors
import evidence
NOW=1700000600

def agent(clock=NOW,status='0',state='0'):
    return {'itemid':'11','key_':'agent.ping','lastclock':str(clock),'lastvalue':'1','status':status,'state':state}

@pytest.mark.parametrize('item,expected',[(agent(),'success'),(agent(NOW-181),'no_data'),
 (agent(0),'missing'),(agent(status='1'),'disabled'),(agent(NOW+1),'invalid'),
 (agent(state='1'),'unsupported'),(agent(NOW-181,state='1'),'no_data')])
def test_agent_collection(monkeypatch,item,expected):
    monkeypatch.setattr(collectors.time,'time',lambda:NOW)
    monkeypatch.setattr(collectors,'get_items_by_keys',lambda *a:[item])
    assert collectors.collect_agent_metric('10683').result['status']==expected

def test_cpu_history_numeric_and_window(monkeypatch):
    monkeypatch.setattr(collectors.time,'time',lambda:NOW)
    item={'itemid':'12','key_':'system.cpu.util','status':'0','state':'0','units':'%','value_type':'0'}
    monkeypatch.setattr(collectors,'get_items_by_keys',lambda *a:[item])
    getter=Mock(return_value=[{'clock':str(NOW-i),'value':'95'} for i in (240,180,120,60,0)])
    monkeypatch.setattr(collectors,'get_item_history',getter)
    record=collectors.collect_cpu_history('10683')
    assert record.result['status']=='success' and len(record.result['samples'])==5
    getter.assert_called_once_with(item,NOW-300,NOW)

def test_dig_internal_timeout_exit9(monkeypatch):
    response=subprocess.CompletedProcess(['dig'],9,';; communications error: timed out\n;; no servers could be reached','')
    monkeypatch.setattr(evidence.subprocess,'run',Mock(return_value=response))
    assert evidence.collect_dns('service.test').result['status']=='timeout'

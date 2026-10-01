from unittest.mock import Mock
import requests
import pytest
import zabbix_client as api

@pytest.fixture(autouse=True)
def config(monkeypatch):
    monkeypatch.setattr(api,'ZABBIX_URL','http://example.test/api_jsonrpc.php')
    monkeypatch.setattr(api,'ZABBIX_API_TOKEN','TEST_ONLY_NOT_A_REAL_TOKEN')

@pytest.mark.parametrize('exception,match',[
    (requests.exceptions.Timeout('secret'),'timeout'),
    (requests.exceptions.ConnectionError('secret'),'connection error'),
    (requests.exceptions.HTTPError('secret'),'HTTP error')])
def test_transport_errors_clear_and_sanitized(monkeypatch,exception,match):
    def fail(*a,**kw):raise exception
    monkeypatch.setattr(api.requests,'post',fail)
    with pytest.raises(RuntimeError,match=match) as error:api.call_api('event.get',{},7)
    assert 'secret' not in str(error.value)

@pytest.mark.parametrize('payload,match',[
    ([], 'envelope'),({'jsonrpc':'2.0','id':8,'result':[]},'ID mismatch'),
    ({'jsonrpc':'2.0','id':7},'result'),
    ({'jsonrpc':'2.0','id':7,'error':{'code':-32602,'data':'secret'}},'JSON-RPC error')])
def test_bad_responses(monkeypatch,payload,match):
    response=Mock();response.json.return_value=payload
    monkeypatch.setattr(api.requests,'post',Mock(return_value=response))
    with pytest.raises(RuntimeError,match=match) as error:api.call_api('event.get',{},7)
    assert 'secret' not in str(error.value)

def test_invalid_json(monkeypatch):
    response=Mock();response.json.side_effect=ValueError('bad')
    monkeypatch.setattr(api.requests,'post',Mock(return_value=response))
    with pytest.raises(RuntimeError,match='invalid JSON'):api.call_api('event.get',{},7)

def test_success_uses_timeout_and_bearer(monkeypatch):
    response=Mock();response.json.return_value={'jsonrpc':'2.0','id':7,'result':[{'eventid':'458'}]}
    post=Mock(return_value=response);monkeypatch.setattr(api.requests,'post',post)
    assert api.call_api('event.get',{},7)==[{'eventid':'458'}]
    assert post.call_args.kwargs['timeout']==5
    assert post.call_args.kwargs['headers']['Authorization'].startswith('Bearer ')

def test_missing_token_blocks_request(monkeypatch):
    monkeypatch.setattr(api,'ZABBIX_API_TOKEN',None)
    post=Mock();monkeypatch.setattr(api.requests,'post',post)
    with pytest.raises(RuntimeError,match='Missing ZABBIX_API_TOKEN'):api.call_api('event.get',{},7)
    post.assert_not_called()

def test_event_requests_identity_fields(monkeypatch):
    call=Mock(return_value=[{'eventid':'458'}]);monkeypatch.setattr(api,'call_api',call)
    api.get_event_by_id('458')
    assert {'objectid','source','object','r_eventid'} <= set(call.call_args.kwargs['params']['output'])

def test_history_type_and_window(monkeypatch):
    call=Mock(return_value=[]);monkeypatch.setattr(api,'call_api',call)
    api.get_item_history({'itemid':'10','value_type':'0'},100,400)
    params=call.call_args.args[1]
    assert params['history']==0 and params['time_from']==100 and params['time_till']==400

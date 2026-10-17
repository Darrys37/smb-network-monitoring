"""Three real technical rehearsals with explicit classified startup notices."""
import json,time
import week5_rehearse as w
proof=json.loads((w.ROOT/'post-recovery-integrity.json').read_text());assert proof['integrity']==[['ok']] and not proof['fk']
w.save(w.ROOT/'rehearsal-protocol-amendment.json',{'at_utc':w.utc(),'before_first_fault':True,'reason':'MON01 recovered from hypervisor hang; only verified reboot uptime notifications may remain. No HTTP/agent/service failures permitted.','allowed_trigger_ids':['22388','25256','25300'],'background_events_retained_in_each_run':True,'week4_data_or_rules_modified':False,'post_rehearsal_all_background_recovery_required':True})
for n in [1,2,3]:w.demo(n,'-retry1' if n==1 else '')
print('Three technical rehearsals passed; waiting for all classified uptime notices to recover.',flush=True)
deadline=time.monotonic()+720;obs=[];clean=0
while time.monotonic()<deadline:
    p=w.problems();obs.append({'at_utc':w.utc(),'open_problems':p});w.save(w.ROOT/'final-background-recovery.json',obs)
    clean=clean+1 if not p else 0
    if clean>=3:break
    assert not w.unexpected_problems(p),'Unexpected background problem after demos'
    time.sleep(10)
assert clean>=3,'Startup notices have not recovered'
w.finalize_remote()
w.save(w.ROOT/'rehearsals-summary.json',{'result':'PASS','completed_at_utc':w.utc(),'aborted_attempts':[json.loads((w.ROOT/'DEMO-01/run.json').read_text())],'runs':[json.loads((w.ROOT/name/'run.json').read_text()) for name in ['DEMO-01-retry1','DEMO-02','DEMO-03']],'scope':'Three automated technical rehearsals after reboot, with startup notifications explicitly classified. Full spoken ten-minute presentation is not measured.'})

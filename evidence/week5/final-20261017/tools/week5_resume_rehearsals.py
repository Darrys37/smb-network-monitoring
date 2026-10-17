"""Continue after a recorded pre-fault postboot interlock; never erase attempts."""
import json,time
import week5_rehearse as w
p=w.ROOT/'DEMO-01/run.json'
attempt=json.loads(p.read_text());assert attempt['status'] in ('started','aborted_before_fault') and not (p.parent/'fault.log').exists()
attempt.update(status='aborted_before_fault',reason='A reboot-related background problem appeared after the first empty poll; preflight interlock prevented fault injection.',included_in_successful_rehearsals=False,retry_run_id='DEMO-01-retry1')
w.save(p,attempt)
observations=json.loads((w.ROOT/'postboot-stability-observations.json').read_text()) if (w.ROOT/'postboot-stability-observations.json').exists() else []
stable=0;deadline=time.monotonic()+900
while time.monotonic()<deadline:
    try:
        problems=w.problems();observations.append({'at_utc':w.utc(),'open_problems':problems});stable=stable+1 if not problems else 0
    except (OSError,w.paramiko.SSHException) as exc:
        observations.append({'at_utc':w.utc(),'transport_error_type':type(exc).__name__});stable=0
    w.save(w.ROOT/'postboot-stability-observations.json',observations)
    if stable>=7:break
    time.sleep(10)
assert stable>=7,'Lab did not stay free of open problems for 60s'
print('Postboot clean condition held for at least 60s; resuming technical rehearsals.',flush=True)
for number in [1,2,3]:w.demo(number,'-retry1' if number==1 else '')
w.finalize_remote()
w.save(w.ROOT/'rehearsals-summary.json',{'result':'PASS','completed_at_utc':w.utc(),'aborted_attempts':[attempt],'runs':[json.loads((w.ROOT/name/'run.json').read_text()) for name in ['DEMO-01-retry1','DEMO-02','DEMO-03']],'scope':'Three automated technical rehearsals after verified reboot of all VMs. Spoken ten-minute presentation is not measured.'})

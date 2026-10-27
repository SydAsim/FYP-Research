"""Disable only the owned preparation stop after actual saved-slot admission."""
from pathlib import Path
import json
from ops import HERE,recorder
def main():
    progress=HERE.parents[3]/'artifacts/phase-8-continuation-deployment/v11/progress-reads'
    found=[]
    for p in progress.glob('*/read-*.json'):
        r=json.loads(p.read_text())
        if r.get('Status')=='Success':
            v=json.loads(r['StandardOutputContent'])
            if v['sequence617']['state']=='RUNNING' and v['sequence617_admission']:found.append((p,v))
    assert found
    p,v=sorted(found,key=lambda pair:pair[0].stat().st_mtime)[-1]
    assert v['first616_unchanged'] and v['pause'] is None and 'SubState=running' in v['service_state']
    assert v['sequence617']['execution_id']=='01a11705-11f2-7276-8d5f-0277ced1a5f5'
    absolute=recorder.call('absolute-after-admission',['scheduler','get-schedule','--group-name','fyp-p85-v5','--name','retained-host-v11-absolute-stop-20261026'])
    assert absolute['State']=='ENABLED' and absolute['ScheduleExpression']=='at(2026-10-26T00:00:00)'
    old=recorder.call('preparation-before-retirement',['scheduler','get-schedule','--group-name','fyp-p85-v5','--name','retained-host-v11-preparation-stop-20261017'])
    assert old['Target']==absolute['Target'] and json.loads(old['Target']['Input'])=={'InstanceIds':['i-057344e5372faf62f']}
    template=json.loads((HERE/'preparation-schedule.json').read_text())
    request={k:old[k] for k in template};request['State']='DISABLED'
    recorder.record('retire-preparation-input.json',request)
    recorder.call('retire-preparation',['scheduler','update-schedule','--cli-input-json','file://'+str(HERE/'retire-preparation-input.json')])
    after=recorder.call('retired-preparation-readback',['scheduler','get-schedule','--group-name','fyp-p85-v5','--name',old['Name']]);assert after['State']=='DISABLED'
    host=recorder.call('actual-running-host',['ec2','describe-instances','--instance-ids','i-057344e5372faf62f','--query','Reservations[0].Instances[0].State.Name']);assert host=='running'
    recorder.record('actual-launch-confirmation.json',{'status':'ACTUALLY_ADMITTED_STANDALONE_V11','progress_evidence':str(p),'progress':v,'host':'running','preparation_guard':'DISABLED_AFTER_ACTUAL_ADMISSION','absolute_guard':'ENABLED_2026-10-26T00:00:00Z','source_package':json.loads((HERE/'candidate-package.json').read_text()),'originals_replayed':0,'originals_regraded':0})
    print('PASS_ACTUAL_SEQUENCE617_RUNNING_PREPARATION_GUARD_RETIRED_ABSOLUTE_RETAINED')
if __name__=='__main__':main()

"""Read-only standalone progress; preserves requests, never resumes or changes outcomes."""
import json,time,sys
from pathlib import Path
from datetime import UTC,datetime
from ops import r,HERE,HOST

def main():
    sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')
    out=HERE/'progress'/str(time.time_ns());out.mkdir(parents=True,exist_ok=False);r.HERE=out
    host=r.call('host',['ec2','describe-instances','--instance-ids',HOST,'--query','Reservations[0].Instances[0].{State:State.Name,InstanceId:InstanceId}'])
    if host['State']!='running':
        print(json.dumps({'host':host,'live_progress':'UNAVAILABLE_WHILE_HOST_NOT_RUNNING','record_directory':str(out)}));return
    body=r'''
import json,subprocess,sys
from datetime import UTC,datetime
from pathlib import Path
sys.path.insert(0,'/opt/fyp-phase8-continuation-v12/artifacts/phase-8-runner-amendment/v4-complete')
from closed145 import snapshot
root=Path('/var/lib/p8-continuation-v9/run');rows,notices=snapshot(root/'campaign.sqlite3')
counts={s:sum(x['state']==s for x in rows) for s in sorted({x['state'] for x in rows})}
active=[x for x in rows if x['state'] not in ('PLANNED','BACKED_UP')]
pending=next((x for x in rows if x['state']=='PLANNED'),None)
units=subprocess.run(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','--property=Id,MainPID,ActiveState,SubState,Result'],capture_output=True,text=True,check=True,timeout=10).stdout
checkpoints=[]
for row in active:
    p=root/'slots'/f"{row['sequence']:04d}"/'executions'/row['execution_id']/'checkpoint.json'
    if p.is_file():
        data=json.loads(p.read_bytes())
        small={k:data.get(k) for k in ('status','started_at','driver_finished_at','original_deadline','missing_final_anchor','checkpointed_at')}
        failure=data.get('failure') or {}
        small['failure']={'type':failure.get('type'),'detail':str(failure.get('detail',''))[:400]} if failure else None
        checkpoints.append({'execution_id':row['execution_id'],'data':small})
print(json.dumps({'at':datetime.now(UTC).isoformat(),'run_id':'p85-01a116f7-3b82-7a79-8653-3aee62dc99e9','counts':counts,'active':active,'next_planned':pending,'pause':json.loads((root/'pause.json').read_bytes()) if (root/'pause.json').exists() else None,'units':units,'last_notices':notices[-4:],'checkpoints':checkpoints,'source':json.loads((root/'run.json').read_bytes())['source'],'stop_at':'2026-10-26T12:00:00Z','records_read_only':True}))
'''
    command="export PYTHONDONTWRITEBYTECODE=1\n/opt/fyp-phase8-continuation-v12/.venv/bin/python -B - <<'PROGRESS'\n"+body+"\nPROGRESS\n"
    params={'commands':[command],'executionTimeout':['45']};r.record('parameters.json',params)
    sent=r.call('send',['ssm','send-command','--instance-ids',HOST,'--document-name','AWS-RunShellScript','--parameters','file://'+str(out/'parameters.json'),'--timeout-seconds','60','--comment','Read-only v12 progress; no campaign mutations'])
    cid=sent['Command']['CommandId']
    for n in range(1,7):
        time.sleep(5)
        reply=r.call('read'+str(n),['ssm','get-command-invocation','--instance-id',HOST,'--command-id',cid])
        if reply['Status']=='Success':
            data=json.loads(reply['StandardOutputContent'].splitlines()[-1]);r.record('summary.json',data)
            print(json.dumps(data,indent=2));print('Retained progress record: '+str(out));return
        if reply['Status'] in ('Failed','TimedOut','Cancelled'):raise RuntimeError('READ_ONLY_PROGRESS_FAILED_PRESERVED:'+cid)
    raise TimeoutError('PROGRESS_UNRESOLVED_NO_RESEND:'+cid)
if __name__=='__main__':main()

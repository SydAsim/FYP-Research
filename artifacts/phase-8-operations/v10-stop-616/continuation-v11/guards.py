"""Fresh independent preparation and absolute stops; read back before host boot."""
import json,sys,hashlib
from datetime import datetime,UTC,timedelta
from pathlib import Path
from ops import recorder,HERE,HOST

def read(name):return json.loads((HERE/name).read_text())
def main():
    pkg=read('candidate-package.json');assert pkg['status']=='PASS_VERIFIED_CONDITIONAL_FREEZE_NOT_LAUNCH'
    parent=HERE.parents[3]/'artifacts/phase-8-continuation-deployment/v10/guarded-resume'
    assert read('guard-role-result.json')['result']['Role']['AssumeRolePolicyDocument']==json.loads((parent/'guard-role-result.json').read_text())['result']['Role']['AssumeRolePolicyDocument']
    permissions=read('guard-permissions-result.json')['result']['PolicyDocument']
    assert permissions['Statement']==[{'Effect':'Allow','Action':'ec2:StopInstances','Resource':'arn:aws:ec2:ap-southeast-2:803656589923:instance/'+HOST}]
    state=recorder.call('fresh-host-before-guards',['ec2','describe-instances','--instance-ids',HOST])
    assert state['Reservations'][0]['OwnerId']=='803656589923'
    instance=state['Reservations'][0]['Instances'][0]
    assert instance['State']['Name']=='stopped' and instance['InstanceId']==HOST
    assert instance['BlockDeviceMappings'][0]['Ebs']['VolumeId']=='vol-09dbb42bbf607f5de'
    sg=read('current-security-result.json')['result']['SecurityGroups'][0]
    assert sg['GroupId']=='sg-076d87ac5db0a6f52' and sg['OwnerId']=='803656589923' and not sg['IpPermissions']
    volume=read('current-volume-result.json')['result']['Volumes'][0]
    assert volume['VolumeId']=='vol-09dbb42bbf607f5de' and volume['Size']==167 and volume['Encrypted'] and volume['Attachments'][0]['InstanceId']==HOST
    inventory=read('preboot-versions1-result.json')['result'];assert inventory['IsTruncated'] is False
    cloud=sum(v['Size'] for v in inventory.get('Versions',[]))
    now=datetime.now(UTC);start=datetime.fromisoformat('2026-10-07T15:24:23.810674+00:00');stop=datetime(2026,10,26,tzinfo=UTC)
    finish=now+timedelta(hours=884*262.31642189586114/1355+2.5);uncertain=finish+timedelta(hours=24)
    extra=.32696506334326947+(stop-datetime.fromisoformat('2026-10-25T15:24:23.810674+00:00')).total_seconds()/3600*7*.096/730
    rate=.1197+.005+160*.096/730
    reserves=48*160*.096/730+80*.025+5+1.25
    cost=lambda t:(t-start).total_seconds()/3600*rate+reserves+extra
    assert uncertain<stop-timedelta(minutes=30) and cost(uncertain+timedelta(minutes=30))<74 and cost(stop)<75,'PREBOOT_TIME_OR_COST_STOP'
    assert cloud+884*60*1024**2+1024**3+300*1024**2<80*1024**3,'PREBOOT_CLOUD_PROJECTION_STOP'
    recorder.record('preboot-feasibility.json',{'at':now.isoformat(),'finish':finish.isoformat(),'uncertain':uncertain.isoformat(),'completion_usd':cost(finish),'uncertain_usd':cost(uncertain),'uncertain_with_admission_lookahead_usd':cost(uncertain+timedelta(minutes=30)),'full_deadline_usd':cost(stop),'extra_root_reserve':extra,'cloud_bytes':cloud,'guard':74,'ceiling':75,'retention_decision':'2026-10-28T00:00:00Z','accounting':'Accepted original elapsed-clock formula, all prior history and reserves preserved; actual billing not substituted'})
    template=json.loads((HERE.parents[3]/'artifacts/phase-8-continuation-deployment/v10/capacity-resume/preparation-input.json').read_text())
    prepared={}
    for label,name,deadline in [('preparation','retained-host-v11-preparation-stop-20261017',now+timedelta(hours=2)),('absolute','retained-host-v11-absolute-stop-20261026',stop)]:
        request={**template,'Name':name,'ScheduleExpression':'at('+deadline.strftime('%Y-%m-%dT%H:%M:%S')+')'}
        recorder.record(label+'-schedule.json',request)
        recorder.call('create-'+label,['scheduler','create-schedule','--cli-input-json','file://'+str(HERE/(label+'-schedule.json')),'--client-token','closed616-v11-'+label+'-20261017'])
        result=recorder.call('readback-'+label,['scheduler','get-schedule','--group-name',request['GroupName'],'--name',name])
        assert all(result[k]==request[k] for k in ['Name','GroupName','ScheduleExpression','ScheduleExpressionTimezone','State','FlexibleTimeWindow','Target'])
        prepared[label]=result
    # Preserve the old guard's exact request, then disable only after new absolute is verified.
    old=recorder.call('old-absolute-before-retire',['scheduler','get-schedule','--group-name','fyp-p85-v5','--name','retained-host-v10-absolute-stop-20261025'])
    assert old['Target']==prepared['absolute']['Target'] and old['ScheduleExpression']=='at(2026-10-25T15:24:23)'
    request={k:old[k] for k in template if k in old};request['State']='DISABLED'
    recorder.record('old-absolute-disabled.json',request)
    recorder.call('disable-old-absolute',['scheduler','update-schedule','--cli-input-json','file://'+str(HERE/'old-absolute-disabled.json')])
    retired=recorder.call('old-absolute-disabled-readback',['scheduler','get-schedule','--group-name','fyp-p85-v5','--name',old['Name']]);assert retired['State']=='DISABLED'
    schedules=recorder.call('guards-final-inventory',['scheduler','list-schedules','--group-name','fyp-p85-v5','--max-results','100','--no-paginate'])
    assert not schedules.get('NextToken')
    assert {s['Name'] for s in schedules['Schedules'] if s['State']=='ENABLED'}=={prepared['preparation']['Name'],prepared['absolute']['Name']}
    recorder.record('independent-guards-verified.json',{'status':'PASS_BEFORE_BOOT','guards':prepared,'superseded_owned_guards':'All disabled, old absolute preserved before disable','host_was_stopped':True,'host_owned':True,'no_inbound_access':True,'instance_id':HOST,'expires_at':(now+timedelta(hours=2)).isoformat(),'retention_authorized_until':'2026-10-28T00:00:00Z','cost':read('preboot-feasibility.json'),'at':datetime.now(UTC).isoformat()})
    print('PASS_FRESH_INDEPENDENT_GUARDS_BEFORE_BOOT')
if __name__=='__main__':main()

"""One guarded boot after fresh independent stop readback; never auto-resends."""
import hashlib,json
from datetime import UTC,datetime,timedelta
from ops import r,HERE,HOST
def read(name):return json.loads((HERE/name).read_bytes())
def main():
    package=read('candidate-package.json');assert package['status']=='PASS_CONDITIONAL_FREEZE_LINUX_CHECKS_PENDING'
    wrappers=read('external-wrapper-verification.json');assert wrappers['status']=='PASS_LOCAL_COMMAND_REVIEW_BEFORE_BOOT'
    for name,h in wrappers['files'].items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h
    guards=read('independent-guards-verified.json');assert guards['status']=='PASS_BEFORE_BOOT'
    for label in ('preparation','absolute'):
        wanted=guards['guards'][label]
        got=r.call('immediate-'+label+'-guard',['scheduler','get-schedule','--group-name',wanted['GroupName'],'--name',wanted['Name']])
        for k in ('Name','GroupName','ScheduleExpression','ScheduleExpressionTimezone','State','Target','FlexibleTimeWindow'):assert got[k]==wanted[k]
        assert got['State']=='ENABLED'
    now=datetime.now(UTC);prep=datetime.fromisoformat(guards['guards']['preparation']['ScheduleExpression'][3:-1]).replace(tzinfo=UTC)
    assert prep>now+timedelta(minutes=45),'PREPARATION_GUARD_TOO_NEAR_NO_BOOT'
    original=datetime.fromisoformat('2026-10-07T15:24:23.810674+00:00');stop=datetime(2026,10,26,12,tzinfo=UTC)
    uncertain=now+timedelta(hours=203*262.31642189586114/1355+2.5+24)
    cost=lambda at:(at-original).total_seconds()/3600*(.1197+.005+160*.096/730)+48*160*.096/730+80*.025+5+1.25+guards['cost']['extra_root_reserve']
    assert uncertain<stop-timedelta(minutes=30) and cost(uncertain+timedelta(minutes=30))<76 and cost(stop)<77
    host=r.call('owned-host-immediately-before-boot',['ec2','describe-instances','--instance-ids',HOST])['Reservations'][0]
    assert host['OwnerId']=='803656589923'
    i=host['Instances'][0];assert i['State']['Name']=='stopped' and i['BlockDeviceMappings'][0]['Ebs']['VolumeId']=='vol-09dbb42bbf607f5de'
    authorization={'kind':'CONDITIONAL_DEPLOYMENT_AUTHORIZATION_NOT_ACTUAL_MAIN_LAUNCH','at':now.isoformat(),'human_authorization_sha256':hashlib.sha256((HERE/'authorization.json').read_bytes()).hexdigest(),'package_hash':package['package_hash'],'archive_sha256':package['archive_sha256'],'freeze_sha256':package['freeze_sha256'],'host':HOST,'root':'vol-09dbb42bbf607f5de','closed_boundary':{'BACKED_UP':1297,'PLANNED':203},'next':'01a11705-11f4-7c05-9897-af35348a8028','original_anchor':original.isoformat(),'stop':stop.isoformat(),'uncertain_with_margin':(uncertain+timedelta(minutes=30)).isoformat(),'admission_projection_usd':cost(uncertain+timedelta(minutes=30)),'full_deadline_usd':cost(stop),'guard':76,'ceiling':77,'preparation_stop':prep.isoformat(),'boot_safety':'Durable original pause and original boot-bound clock prevent old-code admission; owned units quiesced before parent/source/readiness checks','linux_checks_required_before_metadata_adoption':True}
    r.record('deployment-authorization.json',authorization)
    print(json.dumps(r.call('start-retained-v12',['ec2','start-instances','--instance-ids',HOST])))
if __name__=='__main__':main()

"""Finite read-only feasibility, one small source upload and independent stop guards."""
import base64,hashlib,json,time
from datetime import UTC,datetime,timedelta
from pathlib import Path
from ops import r,HERE,HOST

def read(name):return json.loads((HERE/name).read_bytes())
def main():
    pkg=read('candidate-package.json');assert pkg['status']=='PASS_CONDITIONAL_FREEZE_LINUX_CHECKS_PENDING'
    assert read('preboot-plan-result.json')['result']['accountPlanType']=='FREE'
    current=r.call('immediate-preboot-host',['ec2','describe-instances','--instance-ids',HOST])['Reservations'][0]
    assert current['OwnerId']=='803656589923'
    instance=current['Instances'][0];assert instance['State']['Name']=='stopped'
    assert {x['Key']:x['Value'] for x in instance['Tags']}['research.owner']=='p85-01a116f7-3b82-7a79-8653-3aee62dc99e9'
    assert instance['BlockDeviceMappings'][0]['Ebs']['VolumeId']=='vol-09dbb42bbf607f5de' and not instance['BlockDeviceMappings'][0]['Ebs']['DeleteOnTermination']
    v=read('preboot-volume-result.json')['result']['Volumes'][0]
    assert v['Encrypted'] and v['Size']==176 and v['Attachments'][0]['InstanceId']==HOST
    assert not read('preboot-security-result.json')['result']['SecurityGroups'][0]['IpPermissions']
    assert read('preboot-guard-policy-result.json')['result']['PolicyDocument']['Statement']==[{'Effect':'Allow','Action':'ec2:StopInstances','Resource':'arn:aws:ec2:ap-southeast-2:803656589923:instance/'+HOST}]
    # Global read-only Price List endpoint; all project resources stay in Sydney.
    for label,filters,expected in [
        ('compute',['regionCode,Value=ap-southeast-2','instanceType,Value=m7i-flex.large','operatingSystem,Value=Linux','tenancy,Value=Shared','preInstalledSw,Value=NA','capacitystatus,Value=Used'],.1197),
        ('gp3',['regionCode,Value=ap-southeast-2','volumeApiName,Value=gp3','productFamily,Value=Storage'],.096),
    ]:
        value=r.call('current-'+label+'-price',['pricing','get-products','--service-code','AmazonEC2','--filters',*['Type=TERM_MATCH,Field='+f for f in filters],'--max-results','20','--no-paginate'],region='us-east-1')
        assert not value.get('NextToken')
        rates={float(d['pricePerUnit']['USD']) for raw in value['PriceList'] for term in json.loads(raw)['terms']['OnDemand'].values() for d in term['priceDimensions'].values()}
        assert rates=={expected},(label,rates,'CURRENT_PRICE_DRIFT_STOP')
    bucket='fyp-p82-20261005-018da1d6-803656589923';prefix='exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/'
    total=0;markers=[];args=[];deadline=time.monotonic()+120
    for n in range(1,5):
        assert time.monotonic()<deadline
        page=r.call('current-storage-page'+str(n),['s3api','list-object-versions','--bucket',bucket,'--prefix',prefix,'--max-keys','1000','--no-paginate',*args])
        total+=sum(x['Size'] for x in page.get('Versions',[]))
        if not page['IsTruncated']:break
        marker=(page['NextKeyMarker'],page['NextVersionIdMarker']);assert marker not in markers
        markers.append(marker);args=['--key-marker',marker[0],'--version-id-marker',marker[1]]
    else:raise ValueError('INCOMPLETE_INVENTORY_STOP')
    now=datetime.now(UTC);start=datetime.fromisoformat('2026-10-07T15:24:23.810674+00:00');stop=datetime(2026,10,26,12,tzinfo=UTC)
    finish=now+timedelta(hours=203*262.31642189586114/1355+2.5);uncertain=finish+timedelta(hours=24)
    extra=.629884584534137+12*16*.096/730
    cost=lambda t:(t-start).total_seconds()/3600*(.1197+.005+160*.096/730)+48*160*.096/730+80*.025+5+1.25+extra
    sample=json.loads((HERE.parent/'recovery/verified-preservation-summary.json').read_bytes())['resources']
    prep=4*1024**3;source_bound=2*1024**3
    local_projection=sample['backup_bytes']+203*60*1024**2+1024**3+prep
    cloud_projection=total+203*60*1024**2+1024**3+300*1024**2
    physical=(203*60*1024**2+1024**3)+(50*1024**3-sample['working_bytes'])+20*1024**3+1024**3+prep+source_bound
    feasibility={'at':now.isoformat(),'remaining':203,'finish':finish.isoformat(),'uncertain':uncertain.isoformat(),'uncertain_with_margin':(uncertain+timedelta(minutes=30)).isoformat(),'uncertain_with_margin_usd':cost(uncertain+timedelta(minutes=30)),'full_deadline_usd':cost(stop),'extra_root_reserve':extra,'cloud_bytes':total,'cloud_projection_bytes':cloud_projection,'local_projection_bytes':local_projection,'preparation_copy_bound_bytes':prep,'source_clone_bound_bytes':source_bound,'required_free_before_clone_and_preparation':physical,'retained_free_bytes':sample['system_free_bytes'],'guard':76,'ceiling':77,'stop_at':stop.isoformat(),'retention_decision':(stop+timedelta(hours=48)).isoformat(),'accepted_accounting_unchanged':True,'available_credits':read('preboot-plan-result.json')['result']['accountPlanRemainingCredits'],'actual_billing':'NOT_QUERIED; credits balance is not billed campaign spending'}
    r.record('preboot-feasibility.json',feasibility)
    assert uncertain<stop-timedelta(minutes=30) and cost(uncertain+timedelta(minutes=30))<76 and cost(stop)<77,'PREBOOT_TIME_COST_STOP'
    assert max(local_projection,cloud_projection)<80*1024**3 and sample['system_free_bytes']>=physical,'PREBOOT_CAPACITY_STOP'
    delta=Path(pkg['delta_path']);digest=hashlib.sha256(delta.read_bytes()).hexdigest();assert digest==pkg['delta_sha256']
    key=prefix+'continuation-v12/deployment/'+digest+'-delta.tar.gz';checksum=base64.b64encode(bytes.fromhex(digest)).decode()
    put=r.call('put-v12-delta',['s3api','put-object','--bucket',bucket,'--key',key,'--body',str(delta),'--if-none-match','*','--server-side-encryption','AES256','--metadata',json.dumps({'sha256':digest}),'--checksum-sha256',checksum])
    head=r.call('verify-v12-delta',['s3api','head-object','--bucket',bucket,'--key',key,'--version-id',put['VersionId'],'--checksum-mode','ENABLED'])
    assert head['ContentLength']==delta.stat().st_size and head['ChecksumSHA256']==checksum and head['Metadata']['sha256']==digest
    r.record('delta-object.json',{'bucket':bucket,'key':key,'version_id':put['VersionId'],'sha256':digest,'bytes':delta.stat().st_size})
    template=json.loads((HERE.parents[1]/'v10-stop-616/continuation-v11/preparation-schedule.json').read_bytes())
    guards={}
    for label,name,at in [('preparation','retained-host-v12-preparation-stop-20261023',datetime.now(UTC)+timedelta(hours=2)),('absolute','retained-host-v12-absolute-stop-20261026',stop)]:
        request={**template,'Name':name,'ScheduleExpression':'at('+at.strftime('%Y-%m-%dT%H:%M:%S')+')'}
        r.record(label+'-schedule.json',request)
        r.call('create-'+label,['scheduler','create-schedule','--cli-input-json','file://'+str(HERE/(label+'-schedule.json')),'--client-token','closed1297-v12-'+label+'-20261023'])
        found=r.call('readback-'+label,['scheduler','get-schedule','--group-name',request['GroupName'],'--name',name])
        assert all(found[k]==request[k] for k in ('Name','GroupName','ScheduleExpression','ScheduleExpressionTimezone','State','FlexibleTimeWindow','Target'))
        guards[label]=found
    old=r.call('old-absolute-before-retire',['scheduler','get-schedule','--group-name','fyp-p85-v5','--name','retained-host-v11-absolute-stop-20261026'])
    assert old['Target']==guards['absolute']['Target'] and old['ScheduleExpression']=='at(2026-10-26T00:00:00)'
    request={k:old[k] for k in template if k in old};request['State']='DISABLED'
    r.record('old-absolute-disabled.json',request)
    r.call('disable-old-absolute',['scheduler','update-schedule','--cli-input-json','file://'+str(HERE/'old-absolute-disabled.json')])
    check=r.call('old-absolute-disabled-readback',['scheduler','get-schedule','--group-name','fyp-p85-v5','--name',old['Name']]);assert check['State']=='DISABLED'
    schedules=r.call('final-guards-inventory',['scheduler','list-schedules','--group-name','fyp-p85-v5','--max-results','100','--no-paginate']);assert not schedules.get('NextToken')
    assert {x['Name'] for x in schedules['Schedules'] if x['State']=='ENABLED'}=={g['Name'] for g in guards.values()}
    r.record('independent-guards-verified.json',{'status':'PASS_BEFORE_BOOT','guards':guards,'host_was_stopped':True,'instance_id':HOST,'owner':'803656589923','expires_at':(datetime.now(UTC)+timedelta(hours=2)).isoformat(),'old_owned_guards':'Prior disabled; superseded absolute preserved and disabled after replacement readback','cost':feasibility,'no_inbound_access':True})
    print('PASS_FRESH_FEASIBILITY_VERSIONED_DELTA_AND_INDEPENDENT_GUARDS_HOST_STILL_STOPPED')
if __name__=='__main__':main()

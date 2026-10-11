"""PREPARED ONLY. Existing Sydney CloudShell: one pinned GET, no EC2 writes."""
import hashlib, json, os, shutil, sqlite3, subprocess, sys, tarfile, time
from datetime import datetime, timezone
from pathlib import Path
BUCKET='fyp-p82-20261005-018da1d6-803656589923'
SHA='8abe7597a0e59154cf66e682fd08f3440fff815c458db0bdc8fe83666091ad24'
KEY='exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/'+SHA+'.tar.gz'
VERSION='RPSiYO12M2tM251ZCuLVOEK3IUn4NYHM'
SIZE=37906551
EXECUTION='01a11705-11f1-7386-a804-76b957c218d5'
ROOT=Path.home()/'p145-diagnostic'

def hash_file(path):
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()

def worker():
    import boto3
    from botocore.config import Config
    session=boto3.Session(region_name='ap-southeast-2')
    conf=Config(connect_timeout=5,read_timeout=10,retries={'total_max_attempts':1,'mode':'standard'})
    result={'started_at':datetime.now(timezone.utc).isoformat(),'bytes_retrieved':0,'remaining_bytes':SIZE,'status':'STARTED'}
    def save():(ROOT/'worker-result.json').write_text(json.dumps(result,indent=2))
    save()
    try:
        identity=session.client('sts',config=conf).get_caller_identity()
        if identity['Account']!='803656589923':raise ValueError('WRONG_PROJECT_STOP')
        ec2=session.client('ec2',config=conf).describe_instances(InstanceIds=['i-057344e5372faf62f'])
        state=ec2['Reservations'][0]['Instances'][0]['State']['Name']
        result['campaign_host_state']=state
        if state!='stopped':raise ValueError('CAMPAIGN_HOST_NOT_STOPPED_STOP')
        if shutil.disk_usage(ROOT).free<128*1024**2:raise ValueError('INSUFFICIENT_CLOUDSHELL_HEADROOM')
        archive=ROOT/'original145.partial'
        client=session.client('s3',config=conf)
        response=client.get_object(Bucket=BUCKET,Key=KEY,VersionId=VERSION)
        if response.get('VersionId')!=VERSION or response.get('ContentLength')!=SIZE:raise ValueError('OBJECT_IDENTITY_OR_SIZE_MISMATCH')
        with response['Body'] as body,archive.open('xb') as output:
            while True:
                chunk=body.read(65536)
                if not chunk:break
                output.write(chunk);output.flush();result['bytes_retrieved']+=len(chunk)
                if result['bytes_retrieved']>SIZE:raise ValueError('STORAGE_BOUND_SIZE_EXCEEDED')
                result['remaining_bytes']=SIZE-result['bytes_retrieved'];save()
        if result['bytes_retrieved']!=SIZE or hash_file(archive)!=SHA:raise ValueError('COMPLETE_ARCHIVE_HASH_OR_LENGTH_FAILED')
        archive.rename(ROOT/'original145.tar.gz')
        destination=ROOT/'required';destination.mkdir(exist_ok=False)
        members=['ledger.sqlite3',f'executions/{EXECUTION}/export.json',f'executions/{EXECUTION}/checkpoint.json']
        proof={'archive_sha256':SHA,'archive_bytes':SIZE,'bucket':BUCKET,'key':KEY,'version_id':VERSION,'members':{}}
        with tarfile.open(ROOT/'original145.tar.gz','r:gz') as tar:
            item=tar.getmember('slot/manifest.json')
            if not item.isfile() or item.size>2*1024**2:raise ValueError('MANIFEST_BOUND')
            raw=tar.extractfile(item).read();manifest=json.loads(raw)['files']
            (destination/'manifest.json').write_bytes(raw)
            total=len(raw)
            for name in members:
                item=tar.getmember('slot/'+name)
                if not item.isfile() or total+item.size>16*1024**2:raise ValueError('DIAGNOSTIC_RECORD_BOUND')
                raw=tar.extractfile(item).read();total+=len(raw)
                if hashlib.sha256(raw).hexdigest()!=manifest[name]:raise ValueError('REQUIRED_MEMBER_HASH')
                target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
                proof['members'][name]=manifest[name]
        export=json.loads((destination/f'executions/{EXECUTION}/export.json').read_text())
        if export['execution_id']!=EXECUTION:raise ValueError('EXECUTION_IDENTITY')
        with sqlite3.connect((destination/'ledger.sqlite3').resolve().as_uri()+'?mode=ro&immutable=1',uri=True) as db:
            if db.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:raise ValueError('LEDGER_INTEGRITY')
            schema=db.execute("SELECT name,sql FROM sqlite_master WHERE type='table'").fetchall()
            previous='GENESIS';notices=[]
            for number,at,body,prior,digest in db.execute('SELECT n,at,body,previous,hash FROM events ORDER BY n'):
                if prior!=previous or hashlib.sha256((at+body+prior).encode()).hexdigest()!=digest:raise ValueError('LEDGER_EVENT_CHAIN')
                previous=digest
                event=json.loads(body)
                if event.get('execution_id')==EXECUTION or event.get('kind') in ('DRIVER_FAILURE','CLASSIFICATION_PROBE_FAILURE'):
                    notices.append({'n':number,'at':at,'body':event,'previous':prior,'hash':digest})
            checkpoints=[]
            for identity,body,digest in db.execute('SELECT execution_id,body,hash FROM checkpoints WHERE execution_id=?',(EXECUTION,)):
                if hashlib.sha256(body.encode()).hexdigest()!=digest:raise ValueError('LEDGER_CHECKPOINT_HASH')
                checkpoints.append({'execution_id':identity,'hash':digest,'body':json.loads(body)})
            slot=db.execute('SELECT sequence,case_id,arm,execution_id,state,deadline,attempt,error FROM slots WHERE execution_id=?',(EXECUTION,)).fetchall()
            if len(slot)!=1 or slot[0][2]!='B3' or slot[0][6]!=1:raise ValueError('LEDGER_SLOT_IDENTITY')
        (destination/'notices.json').write_text(json.dumps(notices,indent=2))
        (destination/'ledger-checkpoints.json').write_text(json.dumps(checkpoints,indent=2))
        (destination/'slot-row.json').write_text(json.dumps(slot,indent=2))
        proof['ledger_event_chain_verified']=True
        (destination/'ledger-schema.json').write_text(json.dumps(schema,indent=2))
        (destination/'verification.json').write_text(json.dumps(proof,indent=2))
        with tarfile.open(ROOT/'required-records.tar.gz','x:gz') as tar:tar.add(destination,arcname='required')
        bundle=ROOT/'required-records.tar.gz'
        if bundle.stat().st_size>16*1024**2:raise ValueError('RETURN_BUNDLE_BOUND')
        result.update(status='VERIFIED_REQUIRED_RECORDS_READY',bundle_sha256=hash_file(bundle),bundle_bytes=bundle.stat().st_size,original_failure_type=export.get('failure',{}).get('type') if export.get('failure') else None)
        # Full failure/HTTP/checkpoints stay in original export. Never print credentials.
    except Exception as exc:
        result.update(status='STOPPED',error_type=type(exc).__name__)
        if hasattr(exc,'response'):
            result['aws_error_code']=exc.response.get('Error',{}).get('Code')
            result['http_status']=exc.response.get('ResponseMetadata',{}).get('HTTPStatusCode')
    result['finished_at']=datetime.now(timezone.utc).isoformat();save()
    return 0 if result['status']=='VERIFIED_REQUIRED_RECORDS_READY' else 1

def main():
    if '--worker' in sys.argv:return worker()
    ROOT.mkdir(exist_ok=True)
    # A recorded attempt is never automatically replaced, reset or retried.
    policy={'process_deadline_seconds':180,'sdk_total_attempts':1,'api_budget':{'sts_get_caller_identity':1,'ec2_describe_instances':1,'s3_get_object_version':1},'temporary_bound_bytes':128*1024**2,'return_bound_bytes':16*1024**2,'start':datetime.now(timezone.utc).isoformat()}
    with (ROOT/'attempt.json').open('x') as f:json.dump(policy,f,indent=2)
    with (ROOT/'worker-stdout.log').open('x') as out,(ROOT/'worker-stderr.log').open('x') as err:
        child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker'],stdout=out,stderr=err)
        (ROOT/'process.json').write_text(json.dumps({'pid':child.pid,'script':str(Path(__file__).resolve()),'interpreter':sys.executable}))
        try:code=child.wait(timeout=180)
        except subprocess.TimeoutExpired:
            child.kill();child.wait();code='PROCESS_DEADLINE_OWNED_CHILD_STOPPED'
    (ROOT/'process-result.json').write_text(json.dumps({'exit':code,'finished_at':datetime.now(timezone.utc).isoformat()}))
    print((ROOT/'worker-result.json').read_text())
    return 0 if code==0 else 1

if __name__=='__main__':sys.exit(main())

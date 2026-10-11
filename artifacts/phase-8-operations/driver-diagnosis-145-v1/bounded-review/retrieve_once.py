"""One bounded diagnostic retrieval. Never resumes an exhausted attempt."""
import json, time, hashlib, sys, shutil
from pathlib import Path
from datetime import datetime, timezone
import boto3
from botocore.config import Config

HERE=Path(__file__).parent
STAGE=Path('D:/FYP-ResearchBackups/slot145-diagnosis')

def main() -> int:
    STAGE.mkdir(exist_ok=True)
    plan=STAGE/'attempt.json'
    if plan.exists():
        raise RuntimeError('ATTEMPT_ALREADY_RECORDED_NO_AUTOMATIC_RESTART')
    receipt=json.loads((HERE.parent/'original145-receipt.json').read_text())
    start=time.time(); deadline=start+180
    policy={'start':start,'deadline':deadline,'connect_timeout_seconds':5,'read_timeout_seconds':10,'global_retries':1,'temporary_bound_bytes':48*1024**2,'receipt':receipt,'old_inspection_deadline_unchanged':1791737313.5411534}
    plan.write_text(json.dumps(policy,indent=2))
    result={'status':'IN_PROGRESS','verified_bytes':0,'remaining_bytes':receipt['bytes'],'errors':[]}
    retries=1
    client=boto3.Session(profile_name='fyp-research',region_name='ap-southeast-2').client('s3',config=Config(connect_timeout=5,read_timeout=10,retries={'total_max_attempts':1,'mode':'standard'},s3={'addressing_style':'path'}))
    def get_range(begin: int,end: int) -> bytes:
        nonlocal retries
        while True:
            if time.time()+15>deadline:raise TimeoutError('EXPLICIT_TOTAL_DEADLINE')
            try:
                response=client.get_object(Bucket=receipt['bucket'],Key=receipt['key'],VersionId=receipt['version_id'],Range=f'bytes={begin}-{end}')
                expected=f"bytes {begin}-{end}/{receipt['bytes']}"
                if response.get('VersionId')!=receipt['version_id'] or response.get('ContentRange')!=expected or response.get('ContentLength')!=end-begin+1:raise ValueError('RANGE_IDENTITY_OR_OFFSET_MISMATCH')
                with response['Body'] as body:data=body.read(end-begin+1)
                if len(data)!=end-begin+1:raise ValueError('SHORT_RANGE_BODY')
                return data
            except Exception as exc:
                # Exception class only: endpoint exception strings may expose URLs.
                result['errors'].append({'type':type(exc).__name__,'range':[begin,end],'at':datetime.now(timezone.utc).isoformat()})
                if retries<=0 or type(exc).__name__ not in ('ConnectTimeoutError','ReadTimeoutError','EndpointConnectionError','ConnectionClosedError'):raise
                retries-=1
                time.sleep(1)
    try:
        probe=get_range(0,16383)
        (STAGE/'original145.partial').write_bytes(probe)
        result['verified_bytes']=len(probe)
        with (STAGE/'original145.partial').open('ab') as target:
            while result['verified_bytes']<receipt['bytes']:
                begin=result['verified_bytes'];end=min(receipt['bytes']-1,begin+1024*1024-1)
                data=get_range(begin,end);target.write(data);target.flush()
                result['verified_bytes']+=len(data)
                result['remaining_bytes']=receipt['bytes']-result['verified_bytes']
                (STAGE/'checkpoint.json').write_text(json.dumps(result,indent=2))
        archive=STAGE/'original145.partial'
        digest=hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest!=receipt['sha256']:raise ValueError('FULL_ARCHIVE_HASH_MISMATCH')
        archive.rename(STAGE/'original145.tar.gz')
        result.update(status='COMPLETE_VERIFIED',sha256=digest,remaining_bytes=0)
    except Exception as exc:
        result.update(status='STOPPED',error_type=type(exc).__name__)
    result.update(finished_at=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.time()-start,remaining_bytes=receipt['bytes']-result['verified_bytes'],stage_bytes=sum(p.stat().st_size for p in STAGE.iterdir() if p.is_file()),disk_free_bytes=shutil.disk_usage(STAGE).free)
    (STAGE/'result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='COMPLETE_VERIFIED' else 1

if __name__=='__main__':sys.exit(main())

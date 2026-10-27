"""One pinned GET under90s process deadline; preserve partials, no retry."""
from pathlib import Path
import hashlib,json,time,os
import boto3
from botocore.config import Config

def main():
    out=Path('D:/FYP-ResearchBackups/continuation-v11');out.mkdir(exist_ok=True)
    p=out/'closed616-master.tar.gz'
    sha='f1fbd0bfdbfda588bc9ef51a45142c72acdf0ee4a7772b53a02752fa66a020ba'
    size=41481410
    if p.exists():
        assert p.stat().st_size==size and hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==sha,'PARTIAL_RETAINED_NO_AUTOMATIC_RETRY'
        print('PASS_EXISTING_VERIFIED_MASTER');return
    client=boto3.Session(profile_name='fyp-research',region_name='ap-southeast-2').client('s3',config=Config(connect_timeout=5,read_timeout=15,retries={'total_max_attempts':1}))
    deadline=time.monotonic()+75
    r=client.get_object(Bucket='fyp-p82-20261005-018da1d6-803656589923',Key='exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/'+sha+'.tar.gz',VersionId='R4nE4l2ASxFLolEQKfZpmoGmkeXv6gQ4')
    assert r['VersionId']=='R4nE4l2ASxFLolEQKfZpmoGmkeXv6gQ4' and r['ContentLength']==size
    try:
        with p.open('xb') as f:
            for b in r['Body'].iter_chunks(1024**2):
                assert time.monotonic()<deadline,'TOTAL_TRANSFER_DEADLINE'
                assert f.tell()+len(b)<=size,'SIZE_BOUND'
                f.write(b)
            f.flush();os.fsync(f.fileno())
    finally:r['Body'].close()
    assert p.stat().st_size==size and hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==sha
    with (out/'retrieval-proof.json').open('x') as f:json.dump({'sha256':sha,'bytes':size,'version_id':r['VersionId'],'one_get':True,'retry':False,'process_deadline':90},f,indent=2)
    print('PASS_VERIFIED_CLOSED616_MASTER')
if __name__=='__main__':main()

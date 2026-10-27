"""External guarded v11 deployment; zero scenario or driver calls."""
from __future__ import annotations
import base64,csv,hashlib,hmac,importlib.metadata,json,os,shutil,socket,subprocess,sys,tarfile,time,tomllib
from pathlib import Path

def main():
    dep=Path('/var/lib/p8-continuation-v11/deployment');dep.mkdir(parents=True,mode=0o700,exist_ok=True)
    payload=json.loads((dep/'external-input.json').read_text())
    old=Path('/opt/fyp-phase8-continuation-v10');source=Path('/opt/fyp-phase8-continuation-v11');root=Path('/var/lib/p8-continuation-v9/run')
    hashfile=lambda p:hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
    read=lambda p:json.loads(p.read_text())
    canon=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()
    def record(name,value):
        p=dep/name
        with p.open('x') as f:json.dump(value,f,indent=2)
    def command(args,seconds=20):return subprocess.run(args,capture_output=True,text=True,check=True,timeout=seconds).stdout
    units=['fyp-phase8-campaign.service','fyp-phase8-watchdog.service']
    states=command(['systemctl','show',*units,'--property=Id,ActiveState,SubState,MainPID,Result,ExecStart'])
    record('owned-unit-state-before-quiescence.json',{'state':states})
    for unit in units:
        p=Path('/etc/systemd/system')/unit
        text=p.read_text();assert '/opt/fyp-phase8-continuation-v10/' in text and '--root /var/lib/p8-continuation-v9/run' in text,'UNIT_OWNERSHIP_DRIFT'
    command(['systemctl','stop',*units])
    assert all(command(['systemctl','show',u,'--property=MainPID','--value']).strip()=='0' for u in units)
    assert hashfile(root/'pause.json')=='b2cddd1475c8b1dd2e471b7bc2cde283dfb4ef23a928a12a56be06086d8840fc'
    # Verify the complete installed parent and its exact accepted authority before reuse.
    runtime='artifacts/phase-8-runner-amendment/v4-complete'
    parent=read(old/runtime/'candidate-inventory.json')
    assert parent['package_hash']=='bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c'
    assert hashlib.sha256(canon(parent['files'])).hexdigest()==parent['package_hash']
    for name,digest in parent['files'].items():assert hashfile(old/name)==digest,'PARENT_SOURCE_DRIFT:'+name
    owner=Path('/var/lib/fyp-owner');key=(owner/'owner.key').read_bytes()
    assert owner.stat().st_mode&0o777==0o700 and (owner/'owner.key').stat().st_mode&0o777==0o600
    parent_freeze=owner/'continuation-v10-receipts/CONTINUATION_FREEZE.json'
    assert hashfile(parent_freeze)=='b886fff14d4e8384c406deb68a875bc21a9c53e2bac5a17787d800fc1d2d192f'
    for kind in ['CONTINUATION_ACCEPTED','CONTINUATION_FREEZE','CONTINUATION_LAUNCH']:
        r=read(owner/'continuation-v10-receipts'/(kind+'.json'));body={k:v for k,v in r.items() if k!='signature'}
        assert hmac.compare_digest(r['signature'],hmac.new(key,canon(body),'sha256').hexdigest())
    # One small version-pinned delta GET. No complete source/archive download.
    import boto3
    from botocore.config import Config
    s3=boto3.client('s3',region_name='ap-southeast-2',config=Config(connect_timeout=5,read_timeout=15,retries={'total_max_attempts':1}))
    obj=payload['delta'];p=dep/'delta.tar.gz';deadline=time.monotonic()+45
    response=s3.get_object(Bucket=obj['bucket'],Key=obj['key'],VersionId=obj['version_id'])
    assert response['VersionId']==obj['version_id'] and response['ContentLength']==obj['bytes']
    try:
        with p.open('xb') as f:
            for block in response['Body'].iter_chunks(65536):
                assert time.monotonic()<deadline and f.tell()+len(block)<=obj['bytes']
                f.write(block)
    finally:response['Body'].close()
    assert p.stat().st_size==obj['bytes'] and hashfile(p)==obj['sha256']
    assert not source.exists()
    command(['cp','-a','--reflink=auto',str(old),str(source)],120)
    with tarfile.open(p) as tf:
        members=tf.getmembers();seen=set()
        for m in members:
            q=Path(m.name)
            assert m.isfile() and not q.is_absolute() and '..' not in q.parts and m.name not in seen and m.name.startswith(runtime+'/')
            assert m.size<2*1024**2
            seen.add(m.name)
            data=tf.extractfile(m).read()
            with (source/q).open('wb') as f:f.write(data)
    inventory=read(source/runtime/'candidate-inventory.json');package=payload['package']
    assert inventory['package_hash']==package['package_hash'] and hashlib.sha256(canon(inventory['files'])).hexdigest()==package['package_hash']
    for name,digest in inventory['files'].items():assert hashfile(source/name)==digest,'NEW_SOURCE_DRIFT:'+name
    assert {p.relative_to(source).as_posix() for p in (source/runtime).glob('*.py')}=={n for n in inventory['files'] if n.startswith(runtime+'/') and n.endswith('.py')}
    manifest=json.loads(base64.b64decode(payload['authority']['freeze-manifest.json']))
    att=json.loads(base64.b64decode(payload['authority']['freeze-attestation.json']))
    assert hmac.compare_digest(att['signature'],hmac.new(key,canon(manifest),'sha256').hexdigest())
    assert manifest['package_hash']==package['package_hash'] and manifest['archive_sha256']==package['archive_sha256']
    receipts=owner/'continuation-v11-receipts';receipts.mkdir(mode=0o700,exist_ok=False)
    public=dep/'public-authority';public.mkdir(mode=0o700,exist_ok=False)
    for name,encoded in payload['authority'].items():
        data=base64.b64decode(encoded)
        with (public/name).open('xb') as f:f.write(data)
        if name in ['CONTINUATION_ACCEPTED.json','CONTINUATION_FREEZE.json']:
            assert hashlib.sha256(data).hexdigest()==manifest['files'][name]
            with (receipts/name).open('xb') as f:f.write(data)
            (receipts/name).chmod(0o600)
    # Confirm preserved host build and installed dependency RECORDs, with no installation.
    baseline=read(Path('/var/lib/p8-combined-v4/deployment/host-health-readiness.json'))
    assert sys.version==baseline['python'] and sys.version_info[:3]==(3,12,13)
    environments={}
    for label,name in [('application','.venv'),('analysis','.venv-analysis'),('transport','.venv-transport')]:
        site=source/name/'lib/python3.12/site-packages';packages={};records=0
        for dist in importlib.metadata.distributions(path=[str(site)]):
            packages[dist.metadata['Name'].lower().replace('_','-')]=dist.version
            for row in csv.reader((dist.read_text('RECORD') or '').splitlines()):
                if not row or not row[1]:continue
                algorithm,digest=row[1].split('=',1);target=Path(dist.locate_file(row[0]));assert algorithm=='sha256' and target.is_file()
                assert base64.urlsafe_b64encode(bytes.fromhex(hashfile(target))).decode().rstrip('=')==digest
                records+=1
        assert packages==baseline['dependency_environments'][label]['packages']
        environments[label]={'packages':packages,'record_files':records}
    record('source-and-runtime-verified.json',{'status':'PASS','package':package,'python':sys.version,'python_sha256':hashfile(Path(sys.executable).resolve()),'environments':environments,'parent_files':len(parent['files']),'new_files':len(inventory['files']),'source_transfer':'Verified parent plus version-pinned delta; complete new source inventory checked','full_archive_downloaded':False})
    print('PASS_SOURCE_AND_RUNTIME_NO_ADMISSION',flush=True)
    record('prepare-source-complete.json',{'status':'PASS','root_pause_unchanged':True,'source':str(source),'metadata_unchanged':True})
if __name__=='__main__':main()

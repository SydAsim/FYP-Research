"""Verify exact source closure and conditionally authorized parent-bound freeze."""
import hashlib,hmac,json,tarfile,gzip,shutil,sys
from pathlib import Path
from datetime import datetime,UTC
H=Path(__file__).resolve().parent;S=Path('E:/p8v11/source');P=Path('E:/p8v10/source');R='artifacts/phase-8-runner-amendment/v4-complete/'
canon=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()
hashfile=lambda p:hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2)
class Reader:
    def __init__(self,f):self.f=f;self.h=hashlib.sha256()
    def read(self,n):
        b=self.f.read(n);self.h.update(b);return b
def main():
    runtime=S/R;parent=json.loads((P/R/'candidate-inventory.json').read_text())
    for n in parent['files']:
        if n.startswith('.ruff_cache/'):
            shutil.copyfile(P/n,S/n)
    files=dict(parent['files'])
    extras=['closed616.py','closed616-reference.json','conditional-human-authorization-v11.json','check_policy_boundary_v11.py']
    changed=['refusal.py','controls.py','handover.py','operational_limits.py','operational-limit-proposal.json']
    for n in extras+changed:files[R+n]=hashfile(runtime/n)
    package=hashlib.sha256(canon(files)).hexdigest()
    inventory={'kind':'CONTINUATION_REVIEW_CANDIDATE_NOT_FREEZE','version':'phase85-continuation-v11','files':files,'package_hash':package,'parent_frozen_package_hash':parent['package_hash'],'operational_limits_sha256':hashfile(runtime/'operational-limit-proposal.json'),'originals_retained':616,'pending':884,'no_application_change':True,'historical_sidecar_applied':False}
    (runtime/'candidate-inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8',newline='\n')
    archive=Path('D:/FYP-ResearchBackups/continuation-v11/v11-complete-continuation.tar.gz')
    members=sorted([*files,R+'candidate-inventory.json'])
    with archive.open('xb') as output,gzip.GzipFile(fileobj=output,mode='wb',mtime=0,filename='') as gz,tarfile.open(fileobj=gz,mode='w|',format=tarfile.GNU_FORMAT) as tar:
        for name in members:
            p=S/name;info=tarfile.TarInfo(name);info.size=p.stat().st_size;info.mode=0o644;info.uid=info.gid=0;info.mtime=0
            with p.open('rb') as raw:
                reader=Reader(raw);tar.addfile(info,reader)
                assert reader.h.hexdigest()==(files[name] if name in files else hashfile(p)),name
    archive_hash=hashfile(archive)
    owner=Path('C:/Users/syeda/.fyp-research/phase8-owner');key=(owner/'phase84-final-v2/owner.key').read_bytes()
    previous=owner/'phase85-continuation-v10/receipts'
    for kind in ['CONTINUATION_ACCEPTED','CONTINUATION_FREEZE','CONTINUATION_LAUNCH']:
        v=json.loads((previous/(kind+'.json')).read_text());body={k:x for k,x in v.items() if k!='signature'}
        assert hmac.compare_digest(v['signature'],hmac.new(key,canon(body),'sha256').hexdigest()),kind
    parent_receipt=json.loads((previous/'CONTINUATION_FREEZE.json').read_text())
    assert hashfile(Path(H.parents[3]/'artifacts/phase-8-continuation-freeze/v10/CONTINUATION_FREEZE.json'))=='b886fff14d4e8384c406deb68a875bc21a9c53e2bac5a17787d800fc1d2d192f'
    sys.path.insert(0,str(runtime));sys.path.insert(1,str(S))
    from controls import read
    from operational_limits import effective_policy
    from handover import verify_chain
    policy=effective_policy(read(owner/'phase84-final-v2/launch-policy.json'))
    policyhash=hashlib.sha256(canon(policy.model_dump(mode='json'))).hexdigest()
    receipts=owner/'phase85-continuation-v11/receipts';receipts.mkdir(parents=True,exist_ok=False)
    original_launch=read(owner/'phase84-final-v2/receipts/LAUNCH.json')
    predecessor=hashlib.sha256(canon(original_launch)).hexdigest()
    for kind in ['CONTINUATION_ACCEPTED','CONTINUATION_FREEZE']:
        body={k:v for k,v in parent_receipt.items() if k!='signature'}
        body.update(kind=kind,package_hash=package,operational_limits_sha256=inventory['operational_limits_sha256'],predecessor_hash=predecessor,policy_sha256=policyhash,immediate_parent_freeze_sha256='b886fff14d4e8384c406deb68a875bc21a9c53e2bac5a17787d800fc1d2d192f',expires_at=policy.stop_at.isoformat(),signer='fyp-owner-conditional-authorization-20261017',readiness_sha256=None,instance_id=None)
        value={**body,'signature':hmac.new(key,canon(body),'sha256').hexdigest()}
        save(receipts/(kind+'.json'),value);save(H/(kind+'.json'),value)
        predecessor=hashlib.sha256(canon(value)).hexdigest()
    verify_chain(receipts,key,package,policy,parent_receipt['identities_sha256'],hashlib.sha256(canon(original_launch)).hexdigest(),datetime.now(UTC),prelaunch=True)
    manifest={'kind':'CONDITIONAL_CONTINUATION_FREEZE','version':'phase85-continuation-v11','package_hash':package,'archive_sha256':archive_hash,'archive_bytes':archive.stat().st_size,'archive_path':str(archive),'source_inventory_sha256':hashfile(runtime/'candidate-inventory.json'),'parent_freeze_file_sha256':'b886fff14d4e8384c406deb68a875bc21a9c53e2bac5a17787d800fc1d2d192f','parent_package_hash':parent['package_hash'],'authorization_sha256':hashfile(H/'authorization.json'),'policy_sha256':policyhash,'limits_sha256':inventory['operational_limits_sha256'],'files':{p.name:hashfile(p) for p in receipts.glob('*.json')},'conditional_linux_checks_outstanding_before_admission':True,'application_unchanged':True}
    save(H/'freeze-manifest.json',manifest);save(H/'freeze-attestation.json',{'signature':hmac.new(key,canon(manifest),'sha256').hexdigest()})
    assert hmac.compare_digest(read(H/'freeze-attestation.json')['signature'],hmac.new(key,canon(read(H/'freeze-manifest.json')),'sha256').hexdigest())
    delta=H/'v11-parent-verified-delta.tar.gz'
    with tarfile.open(delta,'x:gz') as tf:
        for name in [*(R+n for n in changed+extras),R+'candidate-inventory.json']:tf.add(S/name,arcname=name,recursive=False)
    save(H/'candidate-package.json',{'status':'PASS_VERIFIED_CONDITIONAL_FREEZE_NOT_LAUNCH','package_hash':package,'archive_sha256':archive_hash,'archive_path':str(archive),'delta_path':str(delta),'delta_sha256':hashfile(delta),'delta_bytes':delta.stat().st_size,'freeze_sha256':hashfile(receipts/'CONTINUATION_FREEZE.json'),'freeze_manifest_sha256':hashfile(H/'freeze-manifest.json'),'parent':'bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c','source_members':len(files),'linux_checks_before_admission':True})
    print(json.dumps(read(H/'candidate-package.json')))
if __name__=='__main__':main()

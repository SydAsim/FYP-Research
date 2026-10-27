"""Exact verified child archive and conditional parent-bound authority, no launch."""
from __future__ import annotations
import gzip,hashlib,hmac,json,sys,tarfile
from datetime import UTC,datetime
from pathlib import Path

H=Path(__file__).resolve().parent
S=Path('E:/p8v12/source');P=Path('E:/p8v11/source');R='artifacts/phase-8-runner-amendment/v4-complete/'
canon=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()
def digest(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def save(p,value):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2)

def main():
    parent=read(P/R/'candidate-inventory.json');inventory=read(S/R/'candidate-inventory.json')
    assert parent['package_hash']=='e89ca0fbb9c9e7333a18af23014d0d00d4ffbc6dbe1298f0546620523626e348'
    assert hashlib.sha256(canon(parent['files'])).hexdigest()==parent['package_hash']
    for name,d in parent['files'].items():assert digest(P/name)==d,name
    parent_archive=Path('D:/FYP-ResearchBackups/continuation-v11/v11-complete-continuation.tar.gz')
    assert digest(parent_archive)=='3dc00ac7b60018c7fa0357d54d5fac96f22c6e84deba39e9037575b8a93b0579'
    files=inventory['files'];package=hashlib.sha256(canon(files)).hexdigest();assert package==inventory['package_hash']
    for name,d in files.items():assert digest(S/name)==d,name
    assert {x.relative_to(S).as_posix() for x in (S/R).glob('*.py')}=={n for n in files if n.startswith(R) and n.endswith('.py')}
    changed={n for n in parent['files'] if digest(S/n)!=parent['files'][n]}
    assert changed=={R+n for n in ('controls.py','operational_limits.py','operational-limit-proposal.json','handover.py')}
    assert read(H/'local-qualification-pass.json')['checks']==12
    archive=Path('D:/FYP-ResearchBackups/continuation-v12/v12-complete-continuation.tar.gz');archive.parent.mkdir(parents=True,exist_ok=True)
    members=sorted([*files,R+'candidate-inventory.json'])
    with archive.open('xb') as output,gzip.GzipFile(fileobj=output,mode='wb',mtime=0,filename='') as gz,tarfile.open(fileobj=gz,mode='w|',format=tarfile.GNU_FORMAT) as tf:
        for name in members:
            p=S/name;t=tarfile.TarInfo(name);t.size=p.stat().st_size;t.mode=0o644;t.mtime=0;t.uid=t.gid=0
            with p.open('rb') as f:tf.addfile(t,f)
    with tarfile.open(archive,'r|gz') as tf:
        seen=[]
        for item in tf:
            assert item.isfile() and item.name not in seen
            seen.append(item.name)
            assert hashlib.file_digest(tf.extractfile(item),'sha256').hexdigest()==(files[item.name] if item.name in files else digest(S/item.name)),item.name
        assert seen==members
    owner=Path('C:/Users/syeda/.fyp-research/phase8-owner');key=(owner/'phase84-final-v2/owner.key').read_bytes();assert len(key)>=32
    prev=owner/'phase85-continuation-v11/receipts'
    for kind in ('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE','CONTINUATION_LAUNCH'):
        value=read(prev/(kind+'.json'));body={k:v for k,v in value.items() if k!='signature'}
        assert hmac.compare_digest(value['signature'],hmac.new(key,canon(body),'sha256').hexdigest())
    assert digest(prev/'CONTINUATION_FREEZE.json')=='1de01eb9ce2a8ebfa9b8a2591bbf84f62abf031d7dadf32bfaffa3254164095a'
    old=H.parents[1]/'v10-stop-616/continuation-v11'
    # The on-disk authoritative parent manifest and attestation remain unchanged.
    old=H.parents[1]/'v10-stop-616/continuation-v11'
    pm=read(old/'freeze-manifest.json');pa=read(old/'freeze-attestation.json')
    assert pm['package_hash']==parent['package_hash'] and pm['archive_sha256']==digest(parent_archive)
    assert hmac.compare_digest(pa['signature'],hmac.new(key,canon(pm),'sha256').hexdigest())
    sys.path.insert(0,str(S/R));sys.path.insert(1,str(S))
    from operational_limits import effective_policy
    from handover import verify_chain
    policy=effective_policy(read(owner/'phase84-final-v2/launch-policy.json'))
    policyhash=hashlib.sha256(canon(policy.model_dump(mode='json'))).hexdigest()
    receipts=owner/'phase85-continuation-v12/receipts';receipts.mkdir(parents=True,exist_ok=False)
    original=read(owner/'phase84-final-v2/receipts/LAUNCH.json');initial=hashlib.sha256(canon(original)).hexdigest();predecessor=initial
    parent_receipt=read(prev/'CONTINUATION_FREEZE.json')
    for kind in ('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'):
        body={k:v for k,v in parent_receipt.items() if k!='signature'}
        body.update(kind=kind,package_hash=package,operational_limits_sha256=inventory['operational_limits_sha256'],predecessor_hash=predecessor,policy_sha256=policyhash,immediate_parent_freeze_sha256=digest(prev/'CONTINUATION_FREEZE.json'),expires_at=policy.stop_at.isoformat(),signer='fyp-owner-explicit-conditional-authorization-20261023',readiness_sha256=None,instance_id=None)
        value={**body,'signature':hmac.new(key,canon(body),'sha256').hexdigest()}
        save(receipts/(kind+'.json'),value);save(H/(kind+'.json'),value);predecessor=hashlib.sha256(canon(value)).hexdigest()
    verify_chain(receipts,key,package,policy,parent_receipt['identities_sha256'],initial,datetime.now(UTC),prelaunch=True)
    delta=H/'v12-parent-verified-delta.tar.gz'
    names=sorted({n for n in files if n not in parent['files'] or files[n]!=parent['files'][n]}|{R+'candidate-inventory.json'})
    with tarfile.open(delta,'x:gz') as tf:
        for name in names:tf.add(S/name,arcname=name,recursive=False)
    manifest={'kind':'CONDITIONAL_CONTINUATION_FREEZE','version':'phase85-continuation-v12','package_hash':package,'archive_sha256':digest(archive),'archive_bytes':archive.stat().st_size,'archive_path':str(archive),'source_inventory_sha256':digest(S/R/'candidate-inventory.json'),'parent_freeze_file_sha256':digest(prev/'CONTINUATION_FREEZE.json'),'parent_package_hash':parent['package_hash'],'authorization_sha256':digest(H/'authorization.json'),'policy_sha256':policyhash,'limits_sha256':inventory['operational_limits_sha256'],'files':{p.name:digest(p) for p in receipts.glob('*.json')},'conditional_linux_checks_outstanding_before_metadata_adoption':True,'application_unchanged':True,'all1297_retained':True}
    save(H/'freeze-manifest.json',manifest);save(H/'freeze-attestation.json',{'signature':hmac.new(key,canon(manifest),'sha256').hexdigest()})
    save(H/'candidate-package.json',{'status':'PASS_CONDITIONAL_FREEZE_LINUX_CHECKS_PENDING','package_hash':package,'archive_sha256':manifest['archive_sha256'],'archive_path':str(archive),'delta_path':str(delta),'delta_sha256':digest(delta),'delta_bytes':delta.stat().st_size,'freeze_sha256':digest(receipts/'CONTINUATION_FREEZE.json'),'freeze_manifest_sha256':digest(H/'freeze-manifest.json'),'parent':parent['package_hash'],'source_members':len(files),'linux_checks_required_before_adoption':True})
    save(H/'final-verification.json',{'status':'PASS_CONDITIONAL_FREEZE_NOT_LAUNCH','source_closure':True,'parent_source_archive_authority':True,'new_archive_members_and_hashes':True,'new_receipts_chain':True,'local_controls':12,'linux_controls':'PENDING_REQUIRED_BEFORE_METADATA_ADOPTION','application_changes':0,'main_admissions':0})
    print(json.dumps(read(H/'candidate-package.json')))

if __name__=='__main__':main()

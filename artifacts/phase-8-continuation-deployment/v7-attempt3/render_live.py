from pathlib import Path
here=Path(__file__).resolve().parent
header='''set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v7
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v7:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
'''
integrity='''.venv/bin/python -B - <<'INTEGRITY'
import hashlib,hmac,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,write_new,hash_file,canonical,utc
import boto3
assert boto3.__version__=='1.43.108'
dep=Path('/var/lib/p8-continuation-v7/deployment')
assert hash_file(dep/'package.tar.gz')=='c5a90f1830b1b53a5cdafbe88daf909cb028382a281a10ecbac299016355d152'
inv=read(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json')
assert inv['package_hash']=='9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817'
assert hashlib.sha256(canonical(inv['files'])).hexdigest()==inv['package_hash']
for name,digest in inv['files'].items():
    if hash_file(Path.cwd()/name)!=digest:raise ValueError('V7_SOURCE_MEMBER_DRIFT:'+name)
owner=Path('/var/lib/fyp-owner');key=(owner/'owner.key').read_bytes()
public=dep/'authority.tar.gz.extract'
manifest=read(public/'freeze-manifest.json');att=read(public/'freeze-attestation.json')
assert hash_file(public/'freeze-manifest.json')=='3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46'
assert hmac.compare_digest(att['signature'],hmac.new(key,canonical(manifest),'sha256').hexdigest())
for kind in ('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'):
    name=kind+'.json';raw=read(owner/'continuation-v7-receipts'/name)
    assert hash_file(owner/'continuation-v7-receipts'/name)==hash_file(public/name)
    assert hmac.compare_digest(raw['signature'],hmac.new(key,canonical({k:v for k,v in raw.items() if k!='signature'}),'sha256').hexdigest())
assert read(dep/'old-unit-quiescence-attempt3.json')['status']=='PASS'
write_new(dep/'current-source-integrity-attempt3.json',{'status':'PASS','at_utc':utc().isoformat(),'source_files':len(inv['files']),'package_hash':inv['package_hash'],'archive_sha256':hash_file(dep/'package.tar.gz'),'freeze_manifest_sha256':hash_file(public/'freeze-manifest.json'),'completed_transfer_reused':True,'dependency_install':False,'driver_calls':0})
INTEGRITY
'''
with (here/'live-checks-attempt3.sh').open('x',encoding='utf-8',newline='\n') as out:
    out.write(header+integrity+"cat >/var/lib/p8-continuation-v7/deployment/host_checks-attempt3.py <<'CHECKS'\n"+(here/'host_checks.py').read_text()+"\nCHECKS\ntimeout --signal=TERM --kill-after=5s 600s .venv/bin/python -B /var/lib/p8-continuation-v7/deployment/host_checks-attempt3.py\n")

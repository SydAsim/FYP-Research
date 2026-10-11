set -euo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
test ! -e /var/lib/p8-continuation-v7/deployment/package.tar.gz
test ! -e /opt/fyp-phase8-continuation-v7
/opt/fyp-phase8-combined-v4/.venv/bin/python -B - <<'TRANSPORT_CHECK'
import importlib.metadata,json,sys
from pathlib import Path
import boto3,botocore
assert sys.version_info[:3]==(3,12,13)
assert sys.executable=='/opt/fyp-phase8-combined-v4/.venv/bin/python'
assert Path(boto3.__file__).resolve().is_relative_to(Path('/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages').resolve())
record={'status':'PASS','interpreter':sys.executable,'python':sys.version,'boto3':boto3.__version__,'botocore':botocore.__version__,'boto3_path':boto3.__file__,'qualified_v5_transport_environment':True,'dependency_install':False}
with Path('/var/lib/p8-continuation-v7/deployment/transport-import-attempt2.json').open('x') as output:json.dump(record,output,indent=2)
print(json.dumps(record))
TRANSPORT_CHECK
timeout --signal=TERM --kill-after=5s 600s /opt/fyp-phase8-combined-v4/.venv/bin/python -B /var/lib/p8-continuation-v7/deployment/bootstrap-transfer.py
cd /opt/fyp-phase8-continuation-v7
for env in .venv .venv-analysis .venv-transport; do ln -s "/opt/fyp-phase8-combined-v4/$env" "$env"; done
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B -m research.execution_linux_v1.portable
.venv/bin/python -B - <<'PY'
import hmac,hashlib,json,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import canonical,read,hash_file,write_new
dep=Path('/var/lib/p8-continuation-v7/deployment');public=dep/'authority.tar.gz.extract';owner=Path('/var/lib/fyp-owner');key=(owner/'owner.key').read_bytes()
m=read(public/'freeze-manifest.json');att=read(public/'freeze-attestation.json')
if hash_file(public/'freeze-manifest.json')!='3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46' or not hmac.compare_digest(att['signature'],hmac.new(key,canonical(m),'sha256').hexdigest()):raise ValueError('V7_FREEZE_SIGNATURE_DRIFT')
inv=read(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json')
if inv['package_hash']!='9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817' or hashlib.sha256(canonical(inv['files'])).hexdigest()!=inv['package_hash']:raise ValueError('EXACT_V7_PACKAGE_DRIFT')
for n,d in inv['files'].items():
 if hash_file(Path.cwd()/n)!=d:raise ValueError('V7_SOURCE_MEMBER_DRIFT: '+n)
receipt_dir=owner/'continuation-v7-receipts';receipt_dir.mkdir(mode=0o700,exist_ok=False)
for kind in ('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'):
 p=public/(kind+'.json');raw=read(p);body={k:v for k,v in raw.items() if k!='signature'}
 if not hmac.compare_digest(raw['signature'],hmac.new(key,canonical(body),'sha256').hexdigest()):raise ValueError('V7_RECEIPT_SIGNATURE_DRIFT')
 shutil.copyfile(p,receipt_dir/p.name);(receipt_dir/p.name).chmod(0o600)
write_new(dep/'source-and-authority-ready.json',{'status':'PASS','source_files':len(inv['files']),'freeze_manifest_sha256':hash_file(public/'freeze-manifest.json'),'package_hash':inv['package_hash'],'dependency_install_or_upgrade':False,'driver_calls':0})
print(json.dumps(read(dep/'source-and-authority-ready.json')))
PY

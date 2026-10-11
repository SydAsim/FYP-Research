set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v5
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v5:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'PY'
import hmac,hashlib,json,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import canonical,read,hash_file,write_new
dep=Path('/var/lib/p8-continuation-v5/deployment');public=dep/'authority.tar.gz.extract';owner=Path('/var/lib/fyp-owner');key=(owner/'owner.key').read_bytes()
m=read(public/'freeze-manifest.json');att=read(public/'freeze-attestation.json')
if hash_file(public/'freeze-manifest.json')!='95d48df4494ad022808c172238596f7761582781108b3f9f982088f8a50dfe26' or not hmac.compare_digest(att['signature'],hmac.new(key,canonical(m),'sha256').hexdigest()):raise ValueError('V5_FREEZE_SIGNATURE_DRIFT')
inv=read(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json')
if inv['package_hash']!='805d905760ff2565ef4f3813c0062b073d210de4e10b1fee35d3dfd2377c3627' or hashlib.sha256(canonical(inv['files'])).hexdigest()!=inv['package_hash']:raise ValueError('EXACT_V5_PACKAGE_DRIFT')
for n,d in inv['files'].items():
 if hash_file(Path.cwd()/n)!=d:raise ValueError('V5_SOURCE_MEMBER_DRIFT: '+n)
receipt_dir=owner/'continuation-v5-receipts';assert receipt_dir.is_dir()
for kind in ('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'):
 p=public/(kind+'.json');raw=read(p);body={k:v for k,v in raw.items() if k!='signature'}
 if not hmac.compare_digest(raw['signature'],hmac.new(key,canonical(body),'sha256').hexdigest()):raise ValueError('V5_RECEIPT_SIGNATURE_DRIFT')
 assert hash_file(p)==hash_file(receipt_dir/p.name)
write_new(dep/'source-and-authority-ready.json',{'status':'PASS','source_files':len(inv['files']),'freeze_manifest_sha256':hash_file(public/'freeze-manifest.json'),'package_hash':inv['package_hash'],'dependency_install_or_upgrade':False,'driver_calls':0})
print(json.dumps(read(dep/'source-and-authority-ready.json')))
PY

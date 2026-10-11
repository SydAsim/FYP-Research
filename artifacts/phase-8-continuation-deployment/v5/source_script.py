"""Render version-pinned preparation commands from verified object receipts."""
from pathlib import Path
import json
import tarfile
from ops import HERE
from controls import read

def main():
    objects=[read(HERE/'source-expanded-proof.json'),read(HERE/'authority-proof.json')]
    objects[1]['label']='authority.tar.gz'
    with tarfile.open(HERE/'public-authority.tar.gz') as incoming:
        objects[1]['expanded_bytes']=sum(m.size for m in incoming.getmembers())
    script='''set -euo pipefail
umask 077
systemctl stop fyp-phase8-campaign.service fyp-phase8-watchdog.service
systemctl is-active docker fyp-p85-continuation-bootstrap-stop.timer
install -d -m 700 /var/lib/p8-continuation-v5/deployment
cat >/var/lib/p8-continuation-v5/deployment/bootstrap-objects.json <<'OBJECTS'
'''+json.dumps(objects)+'''
OBJECTS
cat >/var/lib/p8-continuation-v5/deployment/bootstrap-transfer.py <<'TRANSFER'
'''+(HERE/'bootstrap-transfer.py').read_text()+'''
TRANSFER
timeout --signal=TERM --kill-after=5s 600s /opt/fyp-phase8-combined-v4/.venv/bin/python -B /var/lib/p8-continuation-v5/deployment/bootstrap-transfer.py
cd /opt/fyp-phase8-continuation-v5
for env in .venv .venv-analysis .venv-transport; do ln -s "/opt/fyp-phase8-combined-v4/$env" "$env"; done
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B -m research.execution_linux_v1.portable
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
receipt_dir=owner/'continuation-v5-receipts';receipt_dir.mkdir(mode=0o700,exist_ok=False)
for kind in ('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'):
 p=public/(kind+'.json');raw=read(p);body={k:v for k,v in raw.items() if k!='signature'}
 if not hmac.compare_digest(raw['signature'],hmac.new(key,canonical(body),'sha256').hexdigest()):raise ValueError('V5_RECEIPT_SIGNATURE_DRIFT')
 shutil.copyfile(p,receipt_dir/p.name);(receipt_dir/p.name).chmod(0o600)
write_new(dep/'source-ready.json',{'status':'PASS','source_files':len(inv['files']),'freeze_manifest_sha256':hash_file(public/'freeze-manifest.json'),'package_hash':inv['package_hash'],'dependency_install_or_upgrade':False,'driver_calls':0})
print(json.dumps(read(dep/'source-ready.json')))
PY
'''
    (HERE/'prepare-source.sh').write_text(script,encoding='utf-8',newline='\n')

if __name__=='__main__':
    main()

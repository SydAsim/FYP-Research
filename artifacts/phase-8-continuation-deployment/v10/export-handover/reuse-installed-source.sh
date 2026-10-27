set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v10
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v10:/opt/fyp-phase8-continuation-v10/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v10/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'REUSE'
import sys,json,hashlib,hmac
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,hash_file,canonical
source=Path.cwd();dep=Path('/var/lib/p8-continuation-v10/deployment')
baseline=read(Path('/var/lib/p8-combined-v4/deployment/host-health-readiness.json'));assert sys.version==baseline['python'] and sys.version_info[:3]==(3,12,13)
inventory=read(source/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json')
assert hashlib.sha256(canonical(inventory['files'])).hexdigest()==inventory['package_hash']=='bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c'
for name,digest in inventory['files'].items():assert hash_file(source/name)==digest,'INSTALLED_SOURCE_DRIFT:'+name
manifest=read(dep/'public-authority/freeze-manifest.json');attestation=read(dep/'public-authority/freeze-attestation.json');owner=Path('/var/lib/fyp-owner')
assert hmac.compare_digest(attestation['signature'],hmac.new((owner/'owner.key').read_bytes(),canonical(manifest),'sha256').hexdigest())
assert manifest['package_hash']==inventory['package_hash'] and manifest['archive_sha256']=='212269264d45ac8bd6637c2ca0ca5e09c951d354cb445c9bf7a16c6ba2d0ba37'
for name,digest in manifest['files'].items():assert hash_file(owner/'continuation-v10-receipts'/name)==digest
assert not (owner/'continuation-v10-receipts/CONTINUATION_LAUNCH.json').exists()
print(json.dumps({'status':'PASS_REUSED_INSTALLED_SOURCE_AND_FROZEN_AUTHORITY','source_files':len(inventory['files']),'archive_downloads':0,'archive_uploads':0,'refreeze':False,'python':sys.version}))
REUSE

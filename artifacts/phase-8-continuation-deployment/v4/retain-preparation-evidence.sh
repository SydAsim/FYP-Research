set -euo pipefail
umask 077
cd /opt/fyp-phase8-combined-v4
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B - <<'PY'
import json,sys,tarfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,write_new,hash_file
from storage import ObjectProof,S3Cloud
root=Path('/var/lib/p8-combined-v4/run');dep=root.parent/'deployment'
config=read(root/'run.json');cloud=S3Cloud(config['policy']['cloud_bucket'],'exports/phase8/'+config['policy']['run_id']+'/')
failed=Path(read(dep/'import-and-backup-readiness.json')['failed_initial_preparation_directory'])
if failed.parent!=root.parent/'backup' or not failed.is_dir():raise ValueError('EXACT_FAILED_PREPARATION_DIRECTORY_REQUIRED')
archive=dep/'retained-preparation-evidence.tar.gz'
with tarfile.open(archive,'x:gz') as t:
 t.add(failed,arcname='failed-initial-prelaunch-snapshot')
 t.add(dep/'diag-complete-v4-host-readiness-01',arcname='empty-host-readiness-diagnostic')
 for p in sorted(dep.iterdir()):
  if p.is_file() and p.suffix in ('.json','.sh','.py'):t.add(p,arcname='deployment/'+p.name)
if cloud.inventory()+archive.stat().st_size>=config['policy']['cloud_limit_bytes']:raise ValueError('CLOUD_CAP_RETAIN_LOCAL_NO_UPLOAD')
p=cloud.put(archive,cloud.prefix+'combined-v4/deployment/'+hash_file(archive)+'-preparation-evidence.tar.gz');cloud.verify(p)
reply=cloud.client.get_object(Bucket=p.bucket,Key=p.key,VersionId=p.version_id)
import hashlib
try:
 digest=hashlib.sha256()
 for chunk in reply['Body'].iter_chunks(1024**2):digest.update(chunk)
 if digest.hexdigest()!=p.sha256:raise ValueError('PREPARATION_EVIDENCE_READBACK_DRIFT')
finally:reply['Body'].close()
write_new(dep/'retained-preparation-evidence-proof.json',p.model_dump())
print(json.dumps({'status':'PASS','proof':p.model_dump(),'failed_directory_retained':True,'main_driver_replayed':False,'private_owner_key_included':False}))
PY

set -eu
cd /opt/fyp-phase8-continuation-v1
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B - <<'PY'
import json,sys,tarfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-continuation/v1'))
from controls import Journal,read,write_new,utc,hash_file
from storage import ObjectProof
from postflight import recover
from handover import verify_members
root=Path('/var/lib/p8-continuation/run');dep=root.parent/'deployment';record=read(dep/'defect-stop-backup-verification.json');j=Journal(root)
with j.connect() as db:
 proofs=[json.loads(x[0])['proof'] for x in db.execute('SELECT body FROM notices ORDER BY n') if json.loads(x[0]).get('kind')=='CLOUD_VERSION_VERIFIED']
proof=ObjectProof.model_validate(proofs[-1])
archive=root.parent/'operations-stop-readback/t/e.tar.gz'
if hash_file(archive)!=proof.sha256:raise ValueError('PINNED_OPERATIONAL_ARCHIVE_DRIFT')
with tarfile.open(archive,'r:gz') as t:
 lengths=sorted(((len(str(Path('/var/lib/p8c/o/x')/m.name)),m.name) for m in t.getmembers()),reverse=True)[:3]
print(json.dumps({'retained_failed_root':'/var/lib/p8-continuation/operations-stop-readback','same_archive_sha256':proof.sha256,'short_path_lengths':lengths}))
x=recover(proof,Path('/var/lib/p8c/o'),local_archive=archive);verify_members(x/'slot')
write_new(dep/'operational-evidence-backup.json',proof.model_dump())
write_new(dep/'shutdown-readiness-after-shortpath-recovery.json',{'status':'PASS','at_utc':utc().isoformat(),'same_archive':proof.model_dump(),'short_extraction':str(x),'original_failure_retained':True,'no_replay':True,'slot_and_master_backups':record,'retention_review_due_utc':record['retention_review_due_utc']})
print(json.dumps({'stop':record,'operations_backup':proof.model_dump(),'shortpath_readback':'PASS'}),flush=True)
PY
systemctl stop fyp-phase8-watchdog.service
/sbin/shutdown -h +1 "Authorized compute stop after full observation and all independently verified evidence backups"


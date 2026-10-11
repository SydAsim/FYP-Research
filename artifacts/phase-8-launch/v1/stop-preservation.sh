#!/bin/bash
set -euo pipefail
umask 077
cd /opt/fyp-phase8-linux-v1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
export PYTHONDONTWRITEBYTECODE=1
.venv/bin/python -B - <<'PY'
import json,shutil,sqlite3,subprocess,tarfile
from pathlib import Path
import sys
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-review-freeze/v2'))
from controls import Journal,hash_file,read,utc,write_new
from runner import cloud_for,verify_run
from storage import final_backup,upload,verify_local
root=Path('/var/lib/p8/run');journal=Journal(root);authority=verify_run(root,readonly=True);cloud=cloud_for(root)
rows=journal.rows(); started=[r for r in rows if r['state']!='PLANNED']
if len(started)!=1 or started[0]['state']!='BACKED_UP':raise ValueError('STOP_PRESERVATION_REQUIRES_FIRST_ORIGINAL_BACKED_UP')
if not (root/'pause.json').exists():raise ValueError('FAILURE_PAUSE_MISSING')
if subprocess.run(['systemctl','is-active','--quiet','fyp-phase8-campaign.service']).returncode==0:raise ValueError('CAMPAIGN_STILL_ACTIVE')
proofs=[read(p) for p in (root/'backups').glob('*.json')]
for proof in proofs:
    from storage import ObjectProof
    verify_local(Path(proof['local']),proof['sha256']);cloud.verify(ObjectProof.model_validate(proof['cloud']))
ops=Path('/var/lib/p8/backup/stop-evidence-attempt1');ops.mkdir(exist_ok=False)
for src in [root/'pause.json',root/'host-clock.json',root/'cloud-reservations.json']:
    if src.exists():shutil.copyfile(src,ops/src.name)
slot=root/'slots/0001'
for src in list(slot.glob('*.log'))+[slot/'pause.json',slot/'retired.json',slot/'retirement-intent.json']:
    if src.exists():shutil.copyfile(src,ops/('slot-'+src.name))
for src in Path('/var/lib/p8-deployment').glob('*.json'):
    shutil.copyfile(src,ops/('deployment-'+src.name))
log=subprocess.run(['journalctl','-u','fyp-phase8-campaign.service','--no-pager'],capture_output=True,check=True,text=True)
(ops/'campaign-journal.txt').write_text(log.stdout)
with journal.connect() as db:
    integrity=db.execute('PRAGMA integrity_check').fetchone()[0]
    if integrity!='ok':raise ValueError('CAMPAIGN_SQLITE_INTEGRITY')
    events=[json.loads(r[0]) for r in db.execute('SELECT body FROM notices ORDER BY n')]
write_new(ops/'stop-state.json',{'kind':'FAILURE_STOP_NOT_QUEUE_COMPLETION','at':utc().isoformat(),'pause':read(root/'pause.json'),'counts':{s:sum(r['state']==s for r in rows) for s in sorted({r['state'] for r in rows})},'events':events,'first_original':started[0]})
write_new(ops/'manifest.json',{'kind':'STOP_OPERATIONAL_EVIDENCE','postgres_dumps':False,'files':{p.name:hash_file(p) for p in ops.iterdir() if p.is_file()}})
archive=ops.with_suffix('.tar.gz')
with tarfile.open(archive,'x:gz') as out:out.add(ops,arcname='slot')
verify_local(archive,hash_file(archive));op=upload(journal,cloud,authority.policy,archive);cloud.verify(op)
master=final_backup(journal,Path('/var/lib/p8/backup'));mp=upload(journal,cloud,authority.policy,master);cloud.verify(mp)
result={'status':'PRESERVED_FAILURE_PAUSE_NO_NEW_ADMISSIONS','at':utc().isoformat(),'first_original':started[0],'original_proofs':proofs,'stop_evidence':op.model_dump(),'master_metadata':mp.model_dump(),'pause':read(root/'pause.json'),'cloud_bytes':cloud.inventory(),'source_freeze_launch_chain':'PASS','main_driver_replays':0,'queue_complete':False}
write_new(Path('/var/lib/p8-deployment/stop-preservation.json'),result)
print(json.dumps(result))
PY

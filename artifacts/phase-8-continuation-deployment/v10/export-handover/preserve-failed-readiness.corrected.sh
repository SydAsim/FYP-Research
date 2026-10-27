set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v10
export PYTHONDONTWRITEBYTECODE=1
.venv/bin/python -B - <<'PRESERVE'
import hashlib,json,os,sqlite3,subprocess,shutil
from pathlib import Path
from datetime import datetime,UTC
root=Path('/var/lib/p8-continuation-v9/run'); dep=Path('/var/lib/p8-continuation-v10/deployment'); stage=dep/'export-layout-v1'
with sqlite3.connect('file:'+str(root/'campaign.sqlite3')+'?mode=ro',uri=True) as db:
 db.row_factory=sqlite3.Row;db.execute('BEGIN')
 rows=[dict(r) for r in db.execute('SELECT * FROM slots ORDER BY sequence')]
 notices=[dict(r) for r in db.execute('SELECT * FROM notices ORDER BY n')]
 db.rollback()
units={u:subprocess.run(['systemctl','show',u,'--property=MainPID,ActiveState,SubState'],capture_output=True,text=True,check=True,timeout=10).stdout for u in ('fyp-phase8-campaign.service','fyp-phase8-watchdog.service')}
measurement=json.loads((stage/'measurement.json').read_text());adoption=json.loads((stage/'adoption.json').read_text());provenance=json.loads((stage/'provenance.json').read_text())
state={'kind':'READ_ONLY_FAILED_READINESS_PRESERVATION_NO_ADMISSION','at':datetime.now(UTC).isoformat(),'trigger':'CAMPAIGN_PROJECTED_DISK_HEADROOM_STOP','required_free_bytes':145670462448,'actual_free_bytes':shutil.disk_usage('/').free,'measurement':measurement,'adoption':adoption,'all_export_records':len(provenance['records']),'cloud_gets':adoption['cloud_gets'],'rows':rows,'notices':notices,'pause':json.loads((root/'pause.json').read_text()),'pause_sha256':hashlib.sha256((root/'pause.json').read_bytes()).hexdigest(),'units':units,'root_working_logical_bytes':sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),'new_prelaunch_exists':(root/'prelaunch-backup-proof.json').exists(),'new_complete_exists':(root/'complete-backup-proof.json').exists(),'new_readiness_exists':(root/'continuation-readiness.json').exists()}
raw=json.dumps(state,sort_keys=True,indent=2).encode();assert len(raw)<4*1024**2
p=dep/'export-handover-failed-readiness-preservation.json'
with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
summary={k:v for k,v in state.items() if k not in ('rows','notices','adoption')}
summary.update(backed_up=sum(r['state']=='BACKED_UP' for r in rows),planned=sum(r['state']=='PLANNED' for r in rows),next=rows[145],preservation_path=str(p),preservation_sha256=hashlib.sha256(raw).hexdigest(),all_rows_sha256=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),notice_count=len(notices))
print(json.dumps(summary))
PRESERVE

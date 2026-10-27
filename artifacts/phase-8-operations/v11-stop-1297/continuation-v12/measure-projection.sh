set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v12:/opt/fyp-phase8-continuation-v12/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v12/.venv-transport/lib/python3.12/site-packages
cd /opt/fyp-phase8-continuation-v12
.venv/bin/python -B - <<'MEASURE_STORAGE_ONLY'
import json,sys,math
from pathlib import Path
sys.path.insert(0,'/opt/fyp-phase8-continuation-v12/artifacts/phase-8-runner-amendment/v4-complete')
from closed145 import snapshot
from runner import meter
root=Path('/var/lib/p8-continuation-v9/run');rows,_=snapshot(root/'campaign.sqlite3')
assert sum(r['state']=='BACKED_UP' for r in rows)==1297 and all(r['state']=='PLANNED' for r in rows[1297:])
sizes=[json.loads((root/'backups'/(r['execution_id']+'.json')).read_bytes())['cloud']['bytes'] for r in rows[:1297]]
pre=json.loads((root/'prelaunch-backup-proof.json').read_bytes())
delta=pre['cloud']['bytes']-52843821
growth=(52843821-41481410)/(1297-616)*203
projected_max=max(sizes[616:])+delta+growth
floor=max(60*1024**2,math.ceil(projected_max/(4*1024**2))*4*1024**2)
print(json.dumps({'status':'MEASURED_NO_ADMISSION','max_original_archive_all_bytes':max(sizes),'max_v11_original_archive_bytes':max(sizes[616:]),'last_original_archive_bytes':sizes[-1],'old_closed1297_master_bytes':52843821,'new_prelaunch_master_bytes':pre['cloud']['bytes'],'new_boundary_compressed_delta_bytes':delta,'conservative_remaining_metadata_growth_bytes':growth,'growth_basis':'Prior verified616 master41481410 bytes through1297 master52843821 bytes, including prior format changes; extrapolated203 executions without reducing original planning floor','projected_max_archive_bytes':projected_max,'proposed_future_archive_floor_bytes':floor,'proposed_future_archive_floor_MiB':floor/1024**2,'resources':meter(root),'prelaunch':pre}))
MEASURE_STORAGE_ONLY

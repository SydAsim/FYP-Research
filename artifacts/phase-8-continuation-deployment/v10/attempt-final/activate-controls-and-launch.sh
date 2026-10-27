set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v10
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v10:/opt/fyp-phase8-continuation-v10/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v10/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'VERIFY'
import json,sys,subprocess,socket
from datetime import timedelta
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import Journal,read,write_new,hash_file,utc,guard
from runner import verify_run,verify_host_timer,verify_clock,unit_text,watchdog_unit,campaign_unit
from handover import release_reviewed_boundary,closed_boundary
from prelaunch_backup import verify_proof
from storage import S3Cloud
from research.execution_linux_v1.platform import host
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v10/deployment')
a=verify_run(root);cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/')
for phase in ('prelaunch','complete'):verify_proof(root,phase,cloud)
service,timer=unit_text(root,a.policy)
expected={'fyp-phase8-hardstop.service':service,'fyp-phase8-hardstop.timer':timer,'fyp-phase8-watchdog.service':watchdog_unit(root),'fyp-phase8-campaign.service':campaign_unit(root)}
for name,text in expected.items():assert Path('/etc/systemd/system',name).read_text()==text,'CONTROL_UNIT_DRIFT'
subprocess.run(['systemctl','enable','--now','fyp-phase8-watchdog.service'],check=True,timeout=20)
verify_host_timer(root);verify_clock(root,a.policy)
j=Journal(root);rows=j.rows();closed_boundary(rows,read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows'])
assert rows[145]['execution_id']=='01a11705-11f1-772d-8190-c43552871801'
cloud_bytes=cloud.inventory();base=max(Path(read(root/(phase+'-backup-proof.json'))['archive']).stat().st_size for phase in ('prelaunch','complete'))
projected=83218519158.73685+max(0,cloud_bytes-3066593484)+max(0,base-37194083)*1500
assert projected+a.policy.slot_capacity_reserve_bytes<a.policy.cloud_limit_bytes,'FINAL_FUTURE_STORAGE_PROJECTION_STOP'
sample=host(root,root.parent/'backup');sample.update(working_bytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),backup_bytes=sum(p.stat().st_size for p in root.parent.joinpath('backup').rglob('*.tar.gz')))
assert sample['system_free_bytes']>=145670462448,'PROJECTED_DISK_HEADROOM_STOP'
guard(a.policy,sample,utc(),cloud_bytes,extra_bytes=a.policy.slot_capacity_reserve_bytes)
uncertain=utc()+timedelta(hours=262.31642189586114+2.5+24)
assert uncertain<a.policy.stop_at-timedelta(seconds=1800) and a.policy.committed_cost(uncertain)<70
for port in (16432,16433,19100,19101,19102,19110):
    with socket.socket() as s:s.bind(('127.0.0.1',port))
release_reviewed_boundary(root)
write_new(dep/'final-release-verification.json',{'status':'PASS_EXACT_BOUNDARY_RELEASED','at':utc().isoformat(),'backed_up':145,'planned':1355,'next':rows[145],'both_backup_proofs_verified':True,'future_storage_bytes':projected,'driver_calls':0})
print(json.dumps(read(dep/'final-release-verification.json')))
VERIFY
systemctl start fyp-phase8-campaign.service
systemctl is-active fyp-phase8-campaign.service fyp-phase8-watchdog.service fyp-phase8-hardstop.timer

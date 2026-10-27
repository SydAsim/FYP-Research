"""Measured conservative external forecast increase; frozen v12 stays unchanged."""
import base64,difflib,gzip,hashlib,json,math
from pathlib import Path
H=Path(__file__).resolve().parent
def main():
    reply=json.loads((H/'measure-projection-v12-read1-result.json').read_bytes())['result'];assert reply['Status']=='Success'
    measured=json.loads(reply['StandardOutputContent'].splitlines()[-1])
    floor=measured['proposed_future_archive_floor_bytes'];assert floor==68*1024**2
    source=(H/'host_deployment.py').read_text();assert source.count('203*60*1024**2')==3
    revised=source.replace('203*60*1024**2','203*68*1024**2').replace("DEP/'external-input.json'","DEP/'external-input-projection-v2.json'")
    marker="'preparation_bound_bytes':prep,'stop_at'";assert revised.count(marker)==1
    revised=revised.replace(marker,"'future_archive_allowance_bytes':71303168,'preparation_bound_bytes':prep,'stop_at'")
    compile(revised,'host_deployment_projection_v2.py','exec')
    with (H/'host_deployment_projection_v2.py').open('x',newline='\n') as f:f.write(revised)
    with (H/'external-projection-v2.diff').open('x',newline='\n') as f:f.write(''.join(difflib.unified_diff(source.splitlines(True),revised.splitlines(True),fromfile='external-controller-v1',tofile='external-controller-projection-v2')))
    live=json.loads((H/'live-verified.json').read_bytes())['last_json'];sample=measured['resources']
    growth=sample['backup_bytes']-live['resource_sample']['backup_bytes'];complete=growth+16*1024**2
    local=sample['backup_bytes']+203*floor+1024**3+complete
    physical=203*floor+1024**3+(50*1024**3-sample['working_bytes'])+20*1024**3+1024**3+complete
    checks={'old_floor_inadequate':measured['new_prelaunch_master_bytes']>60*1024**2,'raised_floor_covers_projected_observed_max_and_original_floor':floor>=measured['projected_max_archive_bytes'] and floor>=60*1024**2,'unchanged_caps_reservation_and_physical_thresholds_pass':local<80*1024**3 and sample['system_free_bytes']>=physical and growth+complete<=4*1024**3}
    assert all(checks.values())
    qualification={'status':'PASS','checks':checks,'distinct_controls':3,'measured':measured,'local_projection_with_remaining_complete_bytes':local,'required_physical_free_bytes':physical,'frozen_source_changed':False,'caps_or_reservations_reduced':False,'original_checks_repeated':False,'research_executions':0,'controller_sha256':hashlib.sha256(revised.encode()).hexdigest()}
    with (H/'projection-v2-qualification.json').open('x') as f:json.dump(qualification,f,indent=2)
    p=json.loads((H/'external-input.json').read_bytes());p['host_controller_sha256']=qualification['controller_sha256'];p['projection_revision']={'kind':'RAISE_EXTERNAL_STORAGE_FORECAST_WITHIN_ACCEPTED_CAPS','prior_external_payload_sha256':hashlib.sha256((H/'external-input.json').read_bytes()).hexdigest(),'measured_response_sha256':hashlib.sha256((H/'measure-projection-v12-read1-result.json').read_bytes()).hexdigest(),'future_archive_allowance_bytes':floor,'qualification_sha256':hashlib.sha256((H/'projection-v2-qualification.json').read_bytes()).hexdigest(),'no_frozen_or_study_changes':True}
    with (H/'external-input-projection-v2.json').open('x') as f:json.dump(p,f,indent=2)
    blobs={n:base64.b64encode(gzip.compress((H/n).read_bytes())).decode() for n in ('host_deployment_projection_v2.py','external-input-projection-v2.json')}
    env="set -euo pipefail\numask 077\ncd /opt/fyp-phase8-continuation-v12\nexport PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\nexport PYTHONPATH=/opt/fyp-phase8-continuation-v12:/opt/fyp-phase8-continuation-v12/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v12/.venv-transport/lib/python3.12/site-packages\n"
    setup="python3 -B - <<'PROJECTION_FILES'\nfrom pathlib import Path\nimport base64,gzip\np=Path('/var/lib/p8-continuation-v12/deployment')\nfor name,data in "+repr(blobs)+".items():\n    with (p/name).open('xb') as f:f.write(gzip.decompress(base64.b64decode(data)))\nPROJECTION_FILES\n"
    for action,seconds in [('readiness',150),('complete',300),('release',150)]:
        text=env+(setup if action=='readiness' else '')+"timeout --signal=TERM --kill-after=5s "+str(seconds)+"s .venv/bin/python -B /var/lib/p8-continuation-v12/deployment/host_deployment_projection_v2.py "+action+"\n"
        with (H/(action+'-projection-v2.sh')).open('x',newline='\n') as f:f.write(text)
    print(json.dumps({'status':'PASS_3_MEASURED_PROJECTION_CONTROLS','future_archive_allowance_MiB':floor/1024**2,'controller_sha256':qualification['controller_sha256'],'projected_local_bytes':local,'required_physical_free_bytes':physical,'available_physical_bytes':sample['system_free_bytes'],'no_frozen_changes':True}))
if __name__=='__main__':main()

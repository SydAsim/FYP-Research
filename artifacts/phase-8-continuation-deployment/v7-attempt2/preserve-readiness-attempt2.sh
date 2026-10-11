set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v7
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v7:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
cat >/var/lib/p8-continuation-v7/deployment/live-preparation-failure-attempt2.json <<'FAILURE'
{"CommandId": "34df8031-b7d8-4ddf-8d87-116a8d8b76b4", "InstanceId": "i-057344e5372faf62f", "Comment": "", "DocumentName": "AWS-RunShellScript", "DocumentVersion": "$DEFAULT", "PluginName": "aws:runShellScript", "ResponseCode": 1, "ExecutionStartDateTime": "2026-10-09T15:43:45.437Z", "ExecutionElapsedTime": "PT0.772S", "ExecutionEndDateTime": "2026-10-09T15:43:45.437Z", "Status": "Failed", "StatusDetails": "Failed", "StandardOutputContent": "", "StandardOutputUrl": "", "StandardErrorContent": "Traceback (most recent call last):\n  File \"/var/lib/p8-continuation-v7/deployment/host_checks-attempt2.py\", line 87, in <module>\n    main()\n  File \"/var/lib/p8-continuation-v7/deployment/host_checks-attempt2.py\", line 38, in main\n    if subprocess.run(['systemctl','show',unit,'--property=MainPID','--value'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()!='0':raise ValueError('OLD_OPERATIONAL_UNIT_RUNNING')\n                                                                                                                                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nValueError: OLD_OPERATIONAL_UNIT_RUNNING\nfailed to run commands: exit status 1", "StandardErrorUrl": "", "CloudWatchOutputConfig": {"CloudWatchLogGroupName": "", "CloudWatchOutputEnabled": false}}
FAILURE
cat >/var/lib/p8-continuation-v7/deployment/preserve_failed_readiness_attempt2.py <<'PRESERVE'
"""Preserve the closed boundary and failed preparation before idle-host stop."""
import collections
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import time
from pathlib import Path

RUNTIME=Path('/opt/fyp-phase8-continuation-v7/artifacts/phase-8-runner-amendment/v4-complete')
sys.path.insert(0,str(RUNTIME))
from controls import hash_file,read,write_new,utc
from handover import ro_rows
from storage import S3Cloud

def main():
    dep=Path('/var/lib/p8-continuation-v7/deployment');old=Path('/var/lib/p8-combined-v4/run')
    rows=ro_rows(old);counts=dict(collections.Counter(x['state'] for x in rows))
    assert counts=={'BACKED_UP':82,'PLANNED':1418}
    assert read(old/'pause.json')['reason']=='PROTOCOL_STOP' and not (old.parent.parent/'p8-continuation-v7/run').exists()
    before=subprocess.run(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','--property=Id,ActiveState,SubState,MainPID,ExecStart,Result'],check=True,capture_output=True,text=True,timeout=20).stdout
    write_new(dep/'units-before-quiesce-attempt2.json',{'at_utc':utc().isoformat(),'output':before})
    subprocess.run(['systemctl','stop','fyp-phase8-campaign.service','fyp-phase8-watchdog.service'],check=True,timeout=40)
    out=dep/('blocked-preservation-'+str(time.time_ns()));out.mkdir()
    with sqlite3.connect((old/'campaign.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as db, sqlite3.connect(out/'campaign.sqlite3') as saved:
        db.execute('BEGIN');db.backup(saved)
    for name in ('pause.json','run.json','bindings.json','binding-seal.json','cloud.json','host-clock.json','handover.json','saved-identities.json','historical-evidence.tar.gz'):
        shutil.copyfile(old/name,out/name)
    shutil.copytree(old/'backups',out/'backups')
    controls=out/'deployment-controls';controls.mkdir()
    for p in dep.iterdir():
        if p.is_file() and p.suffix in ('.json','.py','.sh','.log'):
            shutil.copyfile(p,controls/p.name)
    for p in dep.glob('cal-backup-gate-*'):
        shutil.copytree(p,out/'calibrations'/p.name)
    commands={
        'service-journal':['journalctl','-u','fyp-phase8-campaign.service','-u','fyp-phase8-watchdog.service','--since','2026-10-09 15:42:00 UTC','--no-pager','-o','short-iso-precise'],
        'units':['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','fyp-p85-continuation-bootstrap-stop.timer','fyp-phase8-hardstop.timer','--property=Id,ActiveState,SubState,MainPID'],
        'containers':['docker','ps','-a','--format','{{.Names}} {{.Status}}'],
        'processes':['ps','-eo','pid,ppid,args']}
    for name,args in commands.items():
        result=subprocess.run(args,check=True,capture_output=True,text=True,timeout=20)
        (out/(name+'.log')).write_text(result.stdout)
    for unit in ('fyp-phase8-campaign.service','fyp-phase8-watchdog.service'):
        if subprocess.run(['systemctl','show',unit,'--property=MainPID','--value'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()!='0':raise ValueError('OPERATIONAL_PROCESS_STILL_ACTIVE')
    controls_result=read(dep/'live-preparation-failure-attempt2.json')
    summary={'at_utc':utc().isoformat(),'state':'LAUNCH_BLOCKED_BEFORE_SLOT83','counts':counts,'active':0,'next_original':rows[82],
             'pause':read(old/'pause.json'),'live_readiness_failure':controls_result,'no_new_main_root':True,'original_backup_qualification':'Historical v5 PASS_ALL_82; attempt2 source PASS, live check stopped at OLD_OPERATIONAL_UNIT_RUNNING before fresh backup qualification',
             'original_deadline':'2026-10-22T15:24:23.810674Z','retained_root_decision_deadline':'2026-10-11T09:33:51.252814Z','source_not_patched':True,'no_replay':True}
    write_new(out/'summary.json',summary)
    write_new(out/'manifest.json',{'kind':'BLOCKED_DEPLOYMENT_PRESERVATION_NOT_RESEARCH_OUTCOMES','files':{p.relative_to(out).as_posix():hash_file(p) for p in out.rglob('*') if p.is_file()}})
    archive=out.with_suffix('.tar.gz')
    with tarfile.open(archive,'x:gz') as target:target.add(out,arcname='inspection')
    policy=read(old/'run.json')['policy'];cloud=S3Cloud(policy['cloud_bucket'],f"exports/phase8/{policy['run_id']}/")
    if cloud.inventory()+archive.stat().st_size>=policy['cloud_limit_bytes']:raise ValueError('CLOUD_CAP_STOP_RETAIN_LOCAL')
    proof=cloud.put(archive,cloud.prefix+'observations/'+hash_file(archive)+'.tar.gz');cloud.verify(proof)
    write_new(dep/'blocked-preservation-proof-attempt2.json',proof.model_dump())
    print(json.dumps({'status':'PRESERVED_READY_FOR_INDEPENDENT_READBACK','summary':summary,'evidence':proof.model_dump()}))

if __name__=='__main__':
    main()

PRESERVE
timeout --signal=TERM --kill-after=5s 300s .venv/bin/python -B /var/lib/p8-continuation-v7/deployment/preserve_failed_readiness_attempt2.py

"""Closed-boundary metadata/policy binding; no application restore, replay or pause release."""
from __future__ import annotations
import json,sys,subprocess,shutil,time,hashlib
from pathlib import Path
from datetime import timedelta

def main():
    source=Path('/opt/fyp-phase8-continuation-v11');runtime=source/'artifacts/phase-8-runner-amendment/v4-complete';sys.path.insert(0,str(runtime));sys.path.insert(1,str(source))
    from controls import read,write_new,hash_file,Journal,utc
    from closed616 import prepare,verify,MASTER,REL
    from closed145 import snapshot
    from handover import bind_host_segment,ContinuationAuthority
    from runner import campaign_unit,watchdog_unit,unit_text,verify_clock
    from operational_limits import LIMITS_SHA256
    root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v11/deployment')
    assert read(dep/'prepare-source-complete.json')['status']=='PASS'
    for u in ['fyp-phase8-campaign.service','fyp-phase8-watchdog.service']:
        assert subprocess.run(['systemctl','show',u,'--property=MainPID','--value'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()=='0'
    run=read(root/'run.json');assert run['source']=='/opt/fyp-phase8-continuation-v10'
    assert hash_file(root/'pause.json')=='b2cddd1475c8b1dd2e471b7bc2cde283dfb4ef23a928a12a56be06086d8840fc'
    archives=[p for p in root.parent.joinpath('backup').glob('final-*.tar.gz') if p.stat().st_size==41481410]
    archives=[p for p in archives if hash_file(p)==MASTER];assert len(archives)==1,'EXACT_RETAINED_MASTER_REQUIRED'
    baseline=prepare(root,archives[0])
    history=root/'restart-history/v11-prior-controls';history.mkdir(mode=0o700,exist_ok=False)
    for name in ['run.json','binding-seal.json','continuation-readiness.json','prelaunch-backup-proof.json','complete-backup-proof.json']:
        assert (root/name).is_file(),name
        shutil.copyfile(root/name,history/name)
    # Preserve existing true readiness/proofs before the new prelaunch stage.
    for name in ['continuation-readiness.json','prelaunch-backup-proof.json','complete-backup-proof.json']:
        (root/name).rename(history/('active-placement-'+name))
    new={**run,'source':str(source),'manifest':str(source/'artifacts/phase-8-review-freeze/v2/review-inventory.json'),'operational_limits_sha256':LIMITS_SHA256,'continuation':{'manifest':'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json','receipts':'/var/lib/fyp-owner/continuation-v11-receipts','closed616_sha256':hash_file(root/REL)}}
    write_new(root/'run.v11-new.json',new);(root/'run.v11-new.json').replace(root/'run.json')
    seal={'run':hash_file(root/'run.json'),'bindings':hash_file(root/'bindings.json')}
    write_new(root/'binding-seal.v11-new.json',seal);(root/'binding-seal.v11-new.json').replace(root/'binding-seal.json')
    journal=Journal(root);journal.event('BINDINGS_SEALED',**seal)
    journal.event('V11_CONDITIONAL_AUTHORIZED_CLOSED616_BINDING',closed616_sha256=hash_file(root/REL),parent_source=run['source'],source=str(source),no_replay=True)
    a=ContinuationAuthority(root,new);a.verify(prelaunch=True);verify(root,closed=True)
    # Paired sampling is unchanged, after metadata and authority checks.
    bind_host_segment(root);verify_clock(root,a.policy)
    service,timer=unit_text(root,a.policy)
    units={'fyp-phase8-campaign.service':campaign_unit(root),'fyp-phase8-watchdog.service':watchdog_unit(root),'fyp-phase8-hardstop.service':service,'fyp-phase8-hardstop.timer':timer}
    oldbootstrap=Path('/etc/systemd/system/fyp-p85-continuation-bootstrap-stop.timer')
    bootstrap=oldbootstrap.read_text();assert '2026-10-25 15:24:23 UTC' in bootstrap
    units[oldbootstrap.name]=bootstrap.replace('2026-10-25 15:24:23 UTC','2026-10-26 00:00:00 UTC')
    for name,text in units.items():
        p=Path('/etc/systemd/system')/name
        shutil.copyfile(p,history/name)
        p.write_text(text)
    # Replace the owned earlier extra-storage fence with the approved final cutoff.
    oldtimer=Path('/etc/systemd/system/fyp-v10-root-cost-admission-167.timer')
    assert '2026-10-24 21:25:47 UTC' in oldtimer.read_text()
    for name in ['fyp-v10-root-cost-admission-167.timer','fyp-v10-root-cost-admission-167.service']:
        shutil.copyfile(Path('/etc/systemd/system')/name,history/name)
    cutoff=a.policy.stop_at-timedelta(seconds=a.policy.admission_cutoff_seconds)
    script=dep/'admission-cutoff.py'
    script.write_text("import sys\nfrom pathlib import Path\nsys.path.insert(0,'"+str(runtime)+"')\nfrom controls import Journal,read,utc\nfrom datetime import datetime\nroot=Path('/var/lib/p8-continuation-v9/run')\nassert utc()>=datetime.fromisoformat('"+cutoff.isoformat()+"')\nassert read(root/'run.json')['source']=='/opt/fyp-phase8-continuation-v11'\nj=Journal(root);j.pause('V11_ABSOLUTE_ADMISSION_CUTOFF');j.event('V11_CUTOFF_ACTIVE_WINDOW_PRESERVED',admission_guard_usd=74)\n")
    extra_units={'fyp-v11-admission-cutoff.service':'[Unit]\nDescription=Owned v11 final admission fence\n[Service]\nType=oneshot\nEnvironment=PYTHONDONTWRITEBYTECODE=1\nExecStart='+str(source/'.venv/bin/python')+' '+str(script)+'\n', 'fyp-v11-admission-cutoff.timer':'[Unit]\nDescription=Owned v11 cutoff; active collection continues\n[Timer]\nOnCalendar='+cutoff.strftime('%Y-%m-%d %H:%M:%S UTC')+'\nPersistent=true\nAccuracySec=1s\nUnit=fyp-v11-admission-cutoff.service\n[Install]\nWantedBy=timers.target\n'}
    for name,text in extra_units.items():
        with (Path('/etc/systemd/system')/name).open('x') as f:f.write(text)
    subprocess.run(['systemctl','daemon-reload'],check=True,timeout=20)
    subprocess.run(['systemctl','enable','--now','fyp-phase8-hardstop.timer','fyp-p85-continuation-bootstrap-stop.timer','fyp-v11-admission-cutoff.timer'],check=True,timeout=20)
    subprocess.run(['systemctl','is-active','--quiet','fyp-v11-admission-cutoff.timer'],check=True,timeout=10)
    subprocess.run(['systemctl','disable','--now','fyp-v10-root-cost-admission-167.timer'],check=True,timeout=20)
    assert subprocess.run(['systemctl','is-active','fyp-v10-root-cost-admission-167.timer'],capture_output=True,text=True,timeout=10).stdout.strip()=='inactive'
    for name,text in {**units,**extra_units}.items():assert (Path('/etc/systemd/system')/name).read_text()==text
    proof={'status':'PASS_CLOSED616_NEW_METADATA_AND_TIMERS','at':utc().isoformat(),'closed616_sha256':hash_file(root/REL),'backed_up':616,'planned':884,'next_sequence':617,'next_execution_id':baseline['rows'][616]['execution_id'],'original_pause_sha256':hash_file(root/'pause.json'),'host_clock_sha256':hash_file(root/'host-clock.json'),'stop_at':a.policy.stop_at.isoformat(),'unit_hashes':{n:hash_file(Path('/etc/systemd/system')/n) for n in {**units,**extra_units}},'driver_calls':0}
    write_new(dep/'metadata-and-timers.json',proof);print(json.dumps(proof))
if __name__=='__main__':main()

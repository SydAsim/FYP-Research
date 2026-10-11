"""External deployment order only; preserve every prior attempt and frozen source."""
import hashlib
import json
from datetime import UTC,datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent
def main():
    previous=HERE.parent/'v7-attempt2'
    for name in ('ops.py','preflight.py','prestart.py','host_checks.py','source-proof.json','source-expanded-proof.json','authority-proof.json'):
        content=(previous/name).read_text(encoding='utf-8')
        if name=='preflight.py':
            content=content.replace("read(HERE.parent/'v7/feasibility-at-stop.json')['new_boot_compute_upper_bound_usd']", "read(HERE.parent/'v7/feasibility-at-stop.json')['new_boot_compute_upper_bound_usd']+read(HERE.parent/'v7-attempt2/feasibility-at-stop.json')['new_boot_compute_upper_bound_usd']")
        if name=='prestart.py':
            content=content.replace("NAME='retained-host-v7-attempt2-preparation-stop-20261009'", "NAME='retained-host-v7-attempt3-preparation-stop-20261009'")
            content=content.replace('PASS_BEFORE_BOOT_COMMAND_SELECTION','PASS_BEFORE_BOOT_DEPLOYMENT_ORDER')
            content=content.replace("HERE/'prepare-source-attempt2.sh'", "HERE/'quiesce-old-units-before-readiness.sh'")
            content=content.replace("known={'retained-host-preparation-stop','retained-host-v7-preparation-stop-20261009'}", "known={'retained-host-preparation-stop','retained-host-v7-preparation-stop-20261009','retained-host-v7-attempt2-preparation-stop-20261009'}")
        with (HERE/name).open('x',encoding='utf-8',newline='\n') as out:out.write(content)
    wrapper=(HERE/'quiesce-old-units-before-readiness.sh').read_bytes()
    archive=HERE.parents[1]/'phase-8-continuation/v7/v7-complete-continuation-review-candidate.tar.gz'
    with archive.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()=='c5a90f1830b1b53a5cdafbe88daf909cb028382a281a10ecbac299016355d152'
    with (HERE/'wrapper-selection-check.json').open('x') as out:json.dump({'status':'PASS_BEFORE_BOOT_DEPLOYMENT_ORDER','at_utc':datetime.now(UTC).isoformat(),'wrapper_sha256':hashlib.sha256(wrapper).hexdigest(),'order':['preserve_old_unit_state','verify_exact_old_frozen_unit_ownership','stop_old_campaign_and_watchdog','verify_inactive_and_same_pause','host_readiness'],'already_completed_transfer_reused':True,'frozen_archive_unchanged':True,'dependencies_installed':False},out,indent=2)
    with (HERE/'human-acceptance.json').open('x') as out:json.dump({'at_utc':datetime.now(UTC).isoformat(),'kind':'EXPLICIT_HUMAN_AUTHORIZED_V7_PREPARATION_ORDER_CORRECTION','package_hash':'9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817','instruction':'''Correct only the external deployment order: after boot, preserve the old units’ state, verify their ownership, stop the old campaign/watchdog units, and verify they are inactive before running the host readiness check. Preserve the old durable pause. Do not weaken the check or change frozen v7.
I authorize another guarded preparation attempt and continuation under the accepted v7 limits. Recheck feasibility and verify the independent preparation-stop guard before boot; safely account for superseded preparation schedules.
Reuse completed checks. Complete the remaining live readiness and backup gates, then resume at slot 83. No broad retesting, dependency installation, replay, replacement or evidence deletion.
If any gate fails, preserve evidence and follow the reviewed safe-stop procedure. Report actual admission and host status. Proceed without another confirmation for these authorized actions.''','actual_admission':False,'guard_usd':60,'total_usd':65,'original_deadline':'2026-10-22T15:24:23.810674Z'},out,indent=2)

if __name__=='__main__':main()

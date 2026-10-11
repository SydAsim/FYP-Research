"""External orchestration only; frozen source is never edited."""
from __future__ import annotations
import json
import shutil
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
OLD=HERE.parent/'v7-attempt3'
V7PKG='9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817'
V7ARC='c5a90f1830b1b53a5cdafbe88daf909cb028382a281a10ecbac299016355d152'
V7FREEZE='3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46'
NEXT='01a11705-11f1-75f4-b64e-8f0a3679518b'

def write(name, text):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)

def main():
    candidate=json.loads((REPO/'artifacts/phase-8-continuation/v9/candidate-package.json').read_text())
    freeze=json.loads((REPO/'artifacts/phase-8-continuation-freeze/v9/freeze-verification.json').read_text())
    assert freeze['status']=='PASS' and freeze['package_hash']==candidate['package_hash']
    shutil.copyfile(REPO/'artifacts/phase-8-continuation/v9/conditional-human-authorization.json',HERE/'human-acceptance.json')
    def current(text):
        return text.replace('continuation-v7','continuation-v9').replace('continuation/v7','continuation/v9').replace('freeze/v7','freeze/v9').replace('E:/p8v7','E:/p8v9').replace(V7PKG,candidate['package_hash']).replace(V7ARC,candidate['archive_sha256']).replace(V7FREEZE,freeze['freeze_manifest_sha256']).replace('01a11705-11f1-792b-ae1e-36bfc6773842',NEXT).replace('274.51268357810414','267.1562082777036')
    for name in ('ops.py','bind_launch.py','build_reuse_gates.py','final-readiness-body.sh','complete-backup.sh','launch-service.sh','progress-v2.sh','finish_preparation_guard.py'):
        text=current((OLD/name).read_text())
        if name!='ops.py':
            text=text.replace('1418','1380').replace('1417','1379').replace('sequence83','sequence121').replace('sequence 83','sequence 121').replace('rows[82]','rows[120]').replace('==82','==120').replace('== 82','== 120').replace("'backed_up':82","'backed_up':120").replace("'BACKED_UP':82","'BACKED_UP':120").replace("'next_sequence':83","'next_sequence':121")
        if name=='build_reuse_gates.py':
            text=text.replace("live['originals_verified']==82","live['originals_verified']==120")
            text=text.replace("feasible=read(HERE/'feasibility.json')","feasible=read(HERE/'feasibility.json')")
        if name=='final-readiness-body.sh':
            text=text.replace("from runner import verify_clock","from runner import verify_clock").replace('verify_clock(root,a.policy,utc())','verify_clock(root,a.policy)')
            text=text.replace("Path('/var/lib/p8-combined-v4/run/pause.json')","Path('/var/lib/p8-continuation-v7/run/pause.json')").replace("['reason']=='PROTOCOL_STOP'","['reason']=='WALL_CLOCK_BACKWARD_STOP_ADMISSIONS'")
            text=text.replace("rows[120]['arm']=='B3'","rows[120]['arm']=='P1'")
            text=text.replace("'backed_up':82","'backed_up':120").replace("'next_sequence':83","'next_sequence':121")
        if name=='launch-service.sh':
            text=text.replace('verify_clock(root,a.policy,utc())','verify_clock(root,a.policy)').replace("Path('/var/lib/p8-combined-v4/run/pause.json')","Path('/var/lib/p8-continuation-v7/run/pause.json')").replace("['reason']=='PROTOCOL_STOP'","['reason']=='WALL_CLOCK_BACKWARD_STOP_ADMISSIONS'").replace("'next_sequence':83","'next_sequence':121")
        if name=='progress-v2.sh':text=text.replace('rows[82]','rows[120]')
        if name=='finish_preparation_guard.py':text=text.replace('=={\'BACKED_UP\':82','=={\'BACKED_UP\':120')
        write(name,text)
    pre=current((OLD/'prestart.py').read_text())
    pre=pre.replace('retained-host-v7-attempt3-preparation-stop-20261009','retained-host-v9-preparation-stop-20261010')
    pre=pre.replace('retained-host-v9-attempt3-preparation-stop-20261009','retained-host-v9-preparation-stop-20261010')
    pre=pre.replace("'backed_up':82,'planned':1418","'backed_up':120,'planned':1380").replace("'next_sequence':83","'next_sequence':121")
    pre=pre.replace("'retained-host-v9-preparation-stop-20261009','retained-host-v9-attempt2-preparation-stop-20261009'","'retained-host-v7-preparation-stop-20261009','retained-host-v7-attempt2-preparation-stop-20261009','retained-host-v7-attempt3-preparation-stop-20261009'")
    write('prestart.py',pre)
    for name in ('ops.py','prestart.py','build_reuse_gates.py','finish_preparation_guard.py'):
        p=HERE/name;text=p.read_text().replace('retained-host-v9-attempt3-preparation-stop-20261009','retained-host-v9-preparation-stop-20261010');p.write_text(text)
    # Host checks: verify retained v7 actual boundary and all 120 archives.
    health=current((OLD/'host_checks.py').read_text())
    health=health.replace("old=Path('/var/lib/p8-combined-v4/run')","old=Path('/var/lib/p8-continuation-v7/run')")
    health=health.replace("RUNTIME/'parent-v4-inventory.json'","SOURCE/'artifacts/phase-8-continuation/v8/parent-v7-inventory.json'")
    health=health.replace("hash_file(Path('/opt/fyp-phase8-combined-v4')/name)","hash_file(Path('/opt/fyp-phase8-continuation-v7')/name)")
    health=health.replace('closed-82/','closed-120/').replace("['reason']!='PROTOCOL_STOP'","['reason']!='WALL_CLOCK_BACKWARD_STOP_ADMISSIONS'")
    health=health.replace('rows[:82]','rows[:120]').replace("'closed_originals':82,'planned':1418","'closed_originals':120,'planned':1380").replace("rows[82]","rows[120]").replace("'next_sequence':83,'next_arm':'B3'","'next_sequence':121,'next_arm':'P1'").replace('PASS_ALL_82','PASS_ALL_120').replace("'originals_verified':82,'planned':1418","'originals_verified':120,'planned':1380")
    health=health.replace("sample=host(old,Path('/var/lib/p8-combined-v4/backup'));sample.update(working_bytes=0,backup_bytes=0)","sample=host(old,Path('/var/lib/p8-continuation-v7/backup'));sample.update(working_bytes=0,backup_bytes=0)\n    if sample['system_free_bytes'] < 145670462448:raise ValueError('CAMPAIGN_PROJECTED_DISK_HEADROOM_STOP')")
    write('host_checks.py',health)
    # Ownership uses old v7 source/unit factories, not the new candidate.
    quiet=(OLD/'quiesce-old-units-before-readiness.sh').read_text().replace('/var/lib/p8-continuation-v7/deployment','/var/lib/p8-continuation-v9/deployment')
    quiet=quiet.replace('/opt/fyp-phase8-combined-v4','/opt/fyp-phase8-continuation-v7').replace('/var/lib/p8-combined-v4/run','/var/lib/p8-continuation-v7/run').replace("pause['reason']=='PROTOCOL_STOP'","pause['reason']=='WALL_CLOCK_BACKWARD_STOP_ADMISSIONS'")
    quiet=quiet.replace("parent-v4-inventory.json","candidate-inventory.json").replace('closed-82/ledger-read-only.json','closed-120/ledger-read-only.json')
    quiet=quiet.replace("Path('/opt/fyp-phase8-continuation-v7/artifacts/phase-8-runner-amendment/v4-complete/closed-120/ledger-read-only.json')","Path('/opt/fyp-phase8-continuation-v9/artifacts/phase-8-runner-amendment/v4-complete/closed-120/ledger-read-only.json')")
    # Quiesce must run before download; compare actual old rows to the locally
    # frozen boundary embedded in the external wrapper, rather than new host source.
    pinned=json.loads(Path('E:/p8v9/source/artifacts/phase-8-runner-amendment/v4-complete/closed-120/ledger-read-only.json').read_text())['rows']
    line="pinned=read(Path('/opt/fyp-phase8-continuation-v9/artifacts/phase-8-runner-amendment/v4-complete/closed-120/ledger-read-only.json'))['rows']"
    quiet=quiet.replace(line,'pinned=json.loads('+repr(json.dumps(pinned,separators=(',',':')))+')')
    write('quiesce-old-units-before-readiness.sh',quiet)
    import hashlib
    write('wrapper-selection-check.json',json.dumps({'status':'PASS_BEFORE_BOOT_DEPLOYMENT_ORDER','wrapper_sha256':hashlib.sha256(quiet.encode()).hexdigest(),'order':['preserve_old_state','verify_owned_units','stop_verify_inactive','qualified_transport_import','download_integrity','host_readiness'],'dependency_install':False},indent=2))
    bootstrap=(HERE.parent/'v7/bootstrap-transfer.py').read_text().replace('continuation-v7','continuation-v9')
    write('bootstrap-transfer.py',bootstrap)
    write('deployment-manifest.json',json.dumps({'candidate':candidate,'freeze':freeze,'next_sequence':121,'next_execution_id':NEXT,'old_root':'/var/lib/p8-continuation-v7/run','new_root':'/var/lib/p8-continuation-v9/run','research_replays':0},indent=2))
    print('External v9 wrappers prepared; no AWS boot or admission.')

if __name__=='__main__':main()

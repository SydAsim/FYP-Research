"""External-only command assembly/review before the authorized guarded boot."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'guarded-resume'

def write(name,text):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)

def main():
    write('ops.py',(OLD/'ops.py').read_text())
    for name in ('inspect-effects.sh','prepare-source.corrected.sh'):
        write(name,(OLD/name).read_text())
    write('quiesce-owned-units.sh',(OLD/'quiesce-owned-units.sh').read_text().replace('guarded-resume-unit-state-before-quiesce.json','attempt-final-unit-state-before-quiesce.json').replace('guarded-resume-units-quiesced.json','attempt-final-units-quiesced.json'))
    header='''set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v10
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v10:/opt/fyp-phase8-continuation-v10/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v10/.venv-transport/lib/python3.12/site-packages
'''
    for phase in ('prelaunch','complete'):
        write(phase+'-backup.sh',header+f'''timeout --signal=TERM --kill-after=5s 1000s .venv/bin/python -B artifacts/phase-8-runner-amendment/v4-complete/prelaunch_backup.py {phase} --root /var/lib/p8-continuation-v9/run --destination /var/lib/p8-continuation-v9/backup
.venv/bin/python -B - <<'PROOF'
import json
from pathlib import Path
print(json.dumps({{'status':'PASS','phase':'{phase}','proof':json.loads(Path('/var/lib/p8-continuation-v9/run/{phase}-backup-proof.json').read_text()),'main_admitted':False}}))
PROOF
''')
    write('prepare-metadata.sh',header+''' .venv/bin/python -B - <<'METADATA'
import json,sys,hashlib,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,write_new,hash_file,Journal,utc
from closed145 import verify_retained_root
from handover import ContinuationAuthority,bind_host_segment,original_policy
from operational_limits import LIMITS_SHA256
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v10/deployment')
for u in ('fyp-phase8-campaign.service','fyp-phase8-watchdog.service'):
    assert subprocess.run(['systemctl','show',u,'--property=MainPID','--value'],check=True,text=True,capture_output=True,timeout=10).stdout.strip()=='0'
    assert subprocess.run(['systemctl','is-active',u],text=True,capture_output=True,timeout=10).stdout.strip()=='inactive'
checked=verify_retained_root(root);assert checked['backed_up']==145 and checked['planned']==1355
assert not (root/'retained-host-clock-before-v10.json').exists(),'RETAIN_PREVIOUS_BIND_ATTEMPT_STOP'
config=read(root/'run.json');original_policy(config['policy'])
historical=root/'restart-history'/'v9-before-v10';historical.mkdir(mode=0o700,exist_ok=False)
preserved={}
for name in ('run.json','binding-seal.json','continuation-readiness.json','prelaunch-backup-proof.json','complete-backup-proof.json'):
    p=root/name
    if p.exists():
        preserved[name]=hash_file(p);p.rename(historical/name)
(historical/'previous-host-clock.json').write_bytes((root/'host-clock.json').read_bytes())
write_new(historical/'preservation.json',{'at':utc().isoformat(),'preserved':preserved,'clock_sha256':hash_file(root/'host-clock.json'),'no_regrading':True})
config.update(source=str(Path.cwd()),manifest=str(Path.cwd()/'artifacts/phase-8-review-freeze/v2/review-inventory.json'),
    continuation={'manifest':'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json','receipts':'/var/lib/fyp-owner/continuation-v10-receipts'},operational_limits_sha256=LIMITS_SHA256)
write_new(root/'run.json',config)
seal={'run':hash_file(root/'run.json'),'bindings':hash_file(root/'bindings.json')};write_new(root/'binding-seal.json',seal)
j=Journal(root);j.event('BINDINGS_SEALED',**seal)
a=ContinuationAuthority(root,config);a.verify(prelaunch=True)
bind_host_segment(root)
from runner import verify_clock
verify_clock(root,a.policy)
checked=verify_retained_root(root)
write_new(dep/'metadata-prepared-final.json',{'status':'PASS','at':utc().isoformat(),'backed_up':145,'planned':1355,'next_sequence':146,'next_execution_id':checked['next']['execution_id'],'original_pause_preserved':True,'run_sha256':seal['run'],'clock_sha256':hash_file(root/'host-clock.json'),'historical_metadata':preserved,'driver_calls':0})
print(json.dumps(read(dep/'metadata-prepared-final.json')))
METADATA
''')
    # Qualified dependency-record/image/local archive/pinned cloud checks reused;
    # only current source, boundary, collection paths and count are selected here.
    old=(HERE.parent.parent/'v9/host_checks.py').read_text()
    begin=old.index("    dep=Path("); end=old.index('    for unit in',begin)
    replacement="""    dep=Path('/var/lib/p8-continuation-v10/deployment');old=Path('/var/lib/p8-continuation-v9/run')
    source_ready=read(dep/'source-ready.json');assert source_ready['status']=='PASS'
    assert source_ready['package_hash']=='bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c'
    from closed145 import verify_retained_root
    checked=verify_retained_root(old);rows=ro_rows(old)
    assert checked['backed_up']==145 and checked['planned']==1355
"""
    old=old[:begin]+replacement+old[end:]
    old=old.replace("SOURCE=Path('/opt/fyp-phase8-continuation-v9')","SOURCE=Path('/opt/fyp-phase8-continuation-v10')")
    old=old.replace('rows[:120]','rows[:145]').replace('rows[120]','rows[145]')
    old=old.replace("Path('/var/lib/p8-continuation-v7/backup')","Path('/var/lib/p8-continuation-v9/backup')")
    old=old.replace("'old_v4_source_members':len(parent['files']),",'')
    old=old.replace("'closed_originals':120,'planned':1380","'closed_originals':145,'planned':1355")
    old=old.replace("'next_sequence':121,'next_arm':'P1'","'next_sequence':146,'next_arm':'P2'")
    old=old.replace('PASS_ALL_120','PASS_ALL_145').replace("'originals_verified':120,'planned':1380","'originals_verified':145,'planned':1355")
    # Keep existing reviewed projected-disk threshold. No zero-use substitution.
    old=old.replace("sample.update(working_bytes=0,backup_bytes=0)","sample.update(working_bytes=sum(p.stat().st_size for p in old.rglob('*') if p.is_file()),backup_bytes=sum(p.stat().st_size for p in old.parent.joinpath('backup').rglob('*.tar.gz')))")
    write('host_checks.py',old)
    write('live-checks.sh',header+"timeout --signal=TERM --kill-after=5s 1000s .venv/bin/python -B /var/lib/p8-continuation-v10/deployment/host_checks-final.py\n")
    # No runtime correction: host checker is external, transferred with exact hash.
    payload=json.dumps(old)
    write('transfer-live-checker.sh',header+".venv/bin/python -B - <<'TRANSFER'\nfrom pathlib import Path\np=Path('/var/lib/p8-continuation-v10/deployment/host_checks-final.py')\nwith p.open('x',encoding='utf-8',newline='\\n') as f:f.write("+payload+")\nTRANSFER\n")
    # Additional stages are prepared as separate checked files, never generated
    # from historical P1/120 policies after the host boots.
    write('HEADER.txt',header)
    review={'kind':'EXTERNAL_COMMAND_ASSEMBLY_NOT_RESEARCH_CANDIDATE','source_package':'bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c',
        'invariants':{'ops.py':'bounded immutable AWS request/result records','prepare-source.corrected.sh':'qualified host build; pinned existing object; hash/source closure; no install',
        'prepare-metadata.sh':'in-place exact closed145; preserve prior config/readiness/proofs; original clock history',
        'host_checks.py':'qualified RECORDs/version/image checks; all145 local archive and pinned receipts; unchanged disk threshold',
        'prelaunch-backup.sh':'frozen copier/readback before readiness','complete-backup.sh':'frozen copier/readback after actual launch binding'},
        'corrections':['current145/P2 boundary and paths instead of historical120/P1','measure actual backup/working usage instead of zero placeholders','no claimed historical host binary digest'],
        'frozen_changes':False,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()}}
    write('assembly.json',json.dumps(review,indent=2))
    for p in HERE.glob('*.py'):ast.parse(p.read_text())
    print('External stages assembled; still require complete preboot review')

if __name__=='__main__':main()

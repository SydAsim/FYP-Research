set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v11
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v11:/opt/fyp-phase8-continuation-v11/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v11/.venv-transport/lib/python3.12/site-packages
timeout --signal=TERM --kill-after=5s 360s .venv/bin/python -B - <<'PRESERVE_ONLY'
"""External OS correction and closed-boundary preservation; never releases pause."""
import collections
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import time
from datetime import timedelta
from pathlib import Path

source=Path('/opt/fyp-phase8-continuation-v11')
sys.path.insert(0,str(source/'artifacts/phase-8-runner-amendment/v4-complete'))
sys.path.insert(1,str(source))
from controls import Journal,read,write_new,hash_file,utc,guard
from closed145 import snapshot
from runner import verify_run,meter
from storage import S3Cloud,final_backup,upload,verify_local
from postflight import recover

root=Path('/var/lib/p8-continuation-v9/run')
rows,notices=snapshot(root/'campaign.sqlite3')
assert collections.Counter(r['state'] for r in rows)=={'BACKED_UP':1297,'PLANNED':203}
assert rows[1297]['execution_id']=='01a11705-11f4-7c05-9897-af35348a8028'
assert not (root/'slots/1298').exists()
pause=read(root/'pause.json')
assert pause=={'reason':'PROTOCOL_STOP','at':'2026-10-23T06:18:06.055774+00:00'}
def command(args,timeout=20,required=True):
    p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    if required:p.check_returncode()
    return {'exit':p.returncode,'out':p.stdout,'err':p.stderr}
units=['fyp-phase8-campaign.service','fyp-phase8-watchdog.service']
for unit in units:
    text=Path('/etc/systemd/system',unit).read_text()
    assert '/opt/fyp-phase8-continuation-v11/' in text and '--root /var/lib/p8-continuation-v9/run' in text
assert command(['systemctl','show',units[0],'--property=MainPID','--value'])['out'].strip()=='0'
out=Path('/var/lib/p8-continuation-v11/deployment')/('stop1297-'+str(time.time_ns()))
out.mkdir(mode=0o700)
for name,args in {
    'units-before':['systemctl','show',*units,'--property=Id,ActiveState,SubState,MainPID,Result,ExecStart,KillSignal'],
    'journal':['journalctl','--since','2026-10-23 06:13:45 UTC','--until','2026-10-23 06:20:00 UTC','--no-pager','-o','short-iso-precise'],
    'containers':['docker','ps','-a','--format','{{.Names}} {{.Status}}'],
}.items():write_new(out/(name+'.json'),command(args))
for path in [Path('/etc/needrestart/needrestart.conf'),Path('/var/log/unattended-upgrades/unattended-upgrades.log'),Path('/var/log/unattended-upgrades/unattended-upgrades-dpkg.log'),Path('/var/log/apt/history.log'),Path('/var/log/dpkg.log')]:
    assert path.stat().st_size<8*1024**2
    shutil.copyfile(path,out/(path.name+'.original'))
for unit in units:shutil.copyfile(Path('/etc/systemd/system',unit),out/(unit+'.original'))
command(['systemctl','stop',units[1]])
assert all(command(['systemctl','show',u,'--property=MainPID','--value'])['out'].strip()=='0' for u in units)
assert snapshot(root/'campaign.sqlite3')[0]==rows and read(root/'pause.json')==pause
write_new(out/'saved-rows.json',rows)
write_new(out/'historical-notices.json',notices)
with sqlite3.connect((root/'campaign.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as incoming:
    with sqlite3.connect(out/'consistent-master.sqlite3') as target:incoming.backup(target)
for name in ['pause.json','host-clock.json']:shutil.copyfile(root/name,out/name)

# First qualify a staged snippet with the installed Perl configuration, then
# install collision-safely and repeat selection assertions on actual config.
snippet='# Campaign interruption recovery requires evidence review and explicit admission.\n# Defer only these service restarts; security updates remain enabled.\n$nrconf{override_rc}->{qr(^fyp-phase8-(?:campaign|watchdog)\\.service$)} = 0;\n1;\n'
staged=out/'99-fyp-phase8-defer-restarts.conf'
with staged.open('x') as f:f.write(snippet)
syntax=command(['perl','-c',str(staged)])
probe=r'''
our %nrconf=(verbosity=>0);
do '/etc/needrestart/needrestart.conf'; die $@ if $@;
if (@ARGV) { do $ARGV[0]; die $@ if $@; }
my @tests=(['fyp-phase8-campaign.service',0],['fyp-phase8-watchdog.service',0],['fyp-phase8-campaign.service.extra',1],['other-fyp-phase8-watchdog.service',1],['unrelated-example.service',1],['dbus.service',0]);
for my $t (@tests) {
    my ($service,$expected)=@$t; my $selection=1;
    for my $re (keys %{$nrconf{override_rc}}) { if($service =~ /$re/) { $selection=$nrconf{override_rc}->{$re}; last; } }
    die "SELECTION_MISMATCH:$service" if $selection != $expected;
    print "$service=$selection\n";
}
'''
staged_check=command(['perl','-e',probe,str(staged)])
target=Path('/etc/needrestart/conf.d/99-fyp-phase8-defer-restarts.conf')
assert not target.exists(),'CONFIG_ALREADY_EXISTS_RECONCILE_NO_OVERWRITE'
with target.open('x') as f:
    f.write(snippet);f.flush();os.fsync(f.fileno())
target.chmod(0o644)
assert hash_file(target)==hash_file(staged)
installed_check=command(['perl','-e',probe])
write_new(out/'correction-checks.json',{'status':'PASS','syntax':syntax,'staged_six_assertions':staged_check,'installed_six_assertions':installed_check,'config':str(target),'sha256':hash_file(target),'application_source_changed':False,'security_updates_disabled':False,'research_scenarios':0})
a=verify_run(root)
cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/')
sample=meter(root);cloud_bytes=cloud.inventory();at=utc()
guard(a.policy,sample,at,cloud_bytes)
completion=at+timedelta(hours=203*262.31642189586114/1355+2.5)
uncertain=completion+timedelta(hours=24)
extra=read(Path('/var/lib/p8-continuation-v11/deployment/root-resize-plan.json'))['total_extra_storage_reserve_usd']
assert uncertain>=a.policy.stop_at-timedelta(minutes=30) or a.policy.committed_cost(uncertain+timedelta(minutes=30))+extra>=74,'FEASIBILITY_CHANGED_REVIEW_NO_AUTOMATIC_STOP_OR_RELEASE'
write_new(out/'resume-blocker.json',{'status':'NO_RESUME_ACCEPTED_TIME_COST_GATES_FAIL','at':at.isoformat(),'completion':completion.isoformat(),'uncertainty':uncertain.isoformat(),'minimum_stop':(uncertain+timedelta(minutes=30)).isoformat(),'minimum_admission_guard_exclusive_usd':a.policy.committed_cost(uncertain+timedelta(minutes=30))+extra,'stop_unchanged':a.policy.stop_at.isoformat(),'admission_guard_unchanged':74,'total_ceiling_unchanged':75,'pause_unchanged':True})
assert snapshot(root/'campaign.sqlite3')[0]==rows and read(root/'pause.json')==pause
write_new(out/'manifest.json',{'kind':'OPERATIONAL_STOP1297_DIAGNOSTIC','files':{p.relative_to(out).as_posix():hash_file(p) for p in out.rglob('*') if p.is_file()}})
diagnostic=root.parent/'backup'/('diagnostic1297-'+str(time.time_ns())+'.tar.gz')
assert sum(p.stat().st_size for p in out.rglob('*') if p.is_file())<64*1024**2
with tarfile.open(diagnostic,'x:gz') as tf:tf.add(out,arcname='slot')
assert diagnostic.stat().st_size<64*1024**2
verify_local(diagnostic,hash_file(diagnostic))
diagnostic_proof=upload(Journal(root),cloud,a.policy,diagnostic)
print(json.dumps({'phase':'DIAGNOSTIC_BACKUP_PUT_VERIFIED','proof':diagnostic_proof.model_dump()}),flush=True)
diagnostic_rb=root.parent/'backup'/'r1297d'
recover(diagnostic_proof,diagnostic_rb)
Journal(root).event('OPERATIONAL_1297_OS_RESTART_CAUSE_VERIFIED',diagnostic=diagnostic_proof.model_dump(),correction_sha256=hash_file(target),next_sequence=1298,main_admitted=False)
archive=final_backup(Journal(root),root.parent/'backup')
assert archive.stat().st_size<512*1024**2
master=upload(Journal(root),cloud,a.policy,archive)
print(json.dumps({'phase':'MASTER_BACKUP_PUT_VERIFIED','proof':master.model_dump()}),flush=True)
master_rb=root.parent/'backup'/'r1297m'
recovered=recover(master,master_rb)
assert snapshot(recovered/'slot/campaign.sqlite3')[0]==rows
assert read(recovered/'slot/pause.json')==pause
assert snapshot(root/'campaign.sqlite3')[0]==rows and read(root/'pause.json')==pause
assert all(command(['systemctl','show',u,'--property=MainPID','--value'])['out'].strip()=='0' for u in units)
summary={'status':'PASS_CORRECTION_AND_PRESERVATION_RESUME_BLOCKED','at':utc().isoformat(),'counts':{'BACKED_UP':1297,'PLANNED':203},'next':rows[1297],'pause':pause,'pause_sha256':hash_file(root/'pause.json'),'units_quiesced':True,'source_and_authority':'PASS_UNCHANGED_FROZEN_V11','correction':read(out/'correction-checks.json'),'blocker':read(out/'resume-blocker.json'),'master_backup':master.model_dump(),'master_readback_sha256':hash_file(master_rb/'postflight-verified.json'),'diagnostic_backup':diagnostic_proof.model_dump(),'diagnostic_readback_sha256':hash_file(diagnostic_rb/'postflight-verified.json'),'diagnostic_directory':str(out),'current_resources':meter(root),'no_main_admission':True,'no_replay_regrading_or_deletion':True,'host_stop_pending':True}
write_new(out/'preservation-summary.json',summary)
print(json.dumps(summary),flush=True)

PRESERVE_ONLY

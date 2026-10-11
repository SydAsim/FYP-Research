set -euo pipefail
umask 077
cd /opt/fyp-phase8-combined-v4
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B - <<'PY'
import collections,hashlib,json,shutil,sqlite3,subprocess,sys,tarfile,time
from datetime import UTC,datetime
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import hash_file,read,write_new
from storage import ObjectProof,S3Cloud,verify_local
from research.execution_linux_v1.platform import process_identity
root=Path('/var/lib/p8-combined-v4/run');runtime=Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'
out=root.parent/'deployment/paused-preservation-20261009-1';out.mkdir(exist_ok=False);start=time.monotonic()
db=sqlite3.connect((root/'campaign.sqlite3').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('BEGIN')
rows=[dict(x) for x in db.execute('SELECT * FROM slots ORDER BY sequence')];notices=[dict(x) for x in db.execute('SELECT * FROM notices ORDER BY n')]
with sqlite3.connect(out/'campaign.sqlite3') as target:db.backup(target)
integrity=db.execute('PRAGMA integrity_check').fetchone()[0];db.close()
counts=dict(collections.Counter(r['state'] for r in rows))
if counts!={'BACKED_UP':82,'PLANNED':1418}:raise ValueError('UNEXPECTED_BOUNDARY_RETAIN_NO_SHUTDOWN')
pause=read(root/'pause.json')
if pause['reason']!='PROTOCOL_STOP':raise ValueError('UNEXPECTED_PAUSE_RETAIN_NO_SHUTDOWN')
previous='GENESIS';latest={};chain=True;parsed=[]
for n in notices:
 if n['previous']!=previous or hashlib.sha256((n['body']+previous).encode()).hexdigest()!=n['hash']:chain=False
 previous=n['hash'];event=json.loads(n['body']);parsed.append(event)
 if event.get('kind') in ('ADMITTED','TRANSITION'):latest[event['execution_id']]=event
mismatches=[]
for r in rows:
 if r['state']=='PLANNED':continue
 e=latest.get(r['execution_id']);diff={k:{'row':r[k],'notice':e.get(k) if e else None} for k in ('state','deadline','backup_hash') if not e or e.get(k)!=r[k]}
 if diff:mismatches.append({'sequence':r['sequence'],'differences':diff})
write_new(out/'ledger-read-only.json',{'integrity':integrity,'notice_chain_valid':chain,'transition_mismatches':mismatches,'rows':rows,'notices':notices})
write_new(out/'stop-notices.json',[e for e in parsed if '2026-10-09T03:25'<=e['at']<='2026-10-09T04:00' and e['kind']!='TRANSITION'])
for name in ('pause.json','run.json','bindings.json','binding-seal.json','cloud.json','host-clock.json','handover.json','saved-identities.json','continuation-readiness.json','historical-evidence.tar.gz','retained-import-pause.json'):
 if (root/name).exists():shutil.copyfile(root/name,out/name)
shutil.copytree(root/'backups',out/'backups')
cloud=S3Cloud(read(root/'run.json')['policy']['cloud_bucket'],f"exports/phase8/{read(root/'run.json')['policy']['run_id']}/")
checks=[];details=[];retained=read(runtime/'retained-slot-proofs.json');live_processes=[]
for r in rows[:82]:
 if time.monotonic()-start>300:raise TimeoutError('PRESERVATION_300_SECOND_BOUND_RETAIN_PARTIAL')
 path=root/'backups'/(r['execution_id']+'.json');proof=read(path)
 archive=runtime/retained[r['sequence']-1]['archive'] if r['sequence']<=38 else Path(proof['local'])
 verify_local(archive,proof['sha256']);cloud.verify(ObjectProof.model_validate(proof['cloud']))
 checks.append({'sequence':r['sequence'],'execution_id':r['execution_id'],'receipt_sha256':hash_file(path),'ledger_backup_hash':r['backup_hash'],'receipt_matches_row':hash_file(path)==r['backup_hash'],'local_archive':str(archive),'cloud':proof['cloud']})
 trace=runtime/'boundary/exports'/f"{r['sequence']:04d}"/'export.json' if r['sequence']<=38 else root/'slots'/f"{r['sequence']:04d}"/'executions'/r['execution_id']/'export.json'
 destination=out/'exports'/f"{r['sequence']:04d}";destination.mkdir(parents=True);shutil.copyfile(trace,destination/'export.json')
 value=read(trace);details.append({'sequence':r['sequence'],'execution_id':r['execution_id'],'arm':r['arm'],'raw_status':value.get('status'),'export_sha256':hash_file(trace),'driver_classification':value.get('driver_classification'),'driver_error':value.get('driver_error',value.get('error')),'oracle_failure':value.get('oracle_failure'),'collection_errors':value.get('collection_errors',[]),'permissive_response_errors':value.get('permissive_response_errors',[])})
 if r['sequence']>38:
  folder=root/'slots'/f"{r['sequence']:04d}";execution=folder/'executions'/r['execution_id'];services=execution/'services.json'
  if services.exists():
   for label,record in read(services)['records'].items():
    if process_identity(record['pid'])==record['identity']:live_processes.append({'sequence':r['sequence'],'service':label,**record})
  if r['sequence']>=79:shutil.copytree(folder,out/'last-slots'/f"{r['sequence']:04d}")
write_new(out/'backup-verification.json',checks);write_new(out/'completed-details.json',details)
commands={
 'service-journal':['journalctl','-u','fyp-phase8-campaign.service','-u','fyp-phase8-watchdog.service','--since','2026-10-08 19:50:00 UTC','--no-pager','-o','short-iso-precise'],
 'stop-journal':['journalctl','-u','fyp-phase8-campaign.service','-u','fyp-phase8-watchdog.service','--since','2026-10-09 03:30:00 UTC','--until','2026-10-09 04:00:00 UTC','--no-pager','-o','short-iso-precise'],
 'units':['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','fyp-phase8-hardstop.timer','--property=Id,ActiveState,SubState,MainPID,ExecMainStatus'],
 'processes':['ps','-eo','pid,ppid,lstart,args'],
 'containers':['docker','ps','-a','--format','{{.Names}} {{.Status}}']}
for name,args in commands.items():
 result=subprocess.run(args,check=True,capture_output=True,timeout=30);(out/(name+'.log')).write_bytes(result.stdout);(out/(name+'-stderr.log')).write_bytes(result.stderr)
for n in ('fyp-phase8-campaign.service','fyp-phase8-watchdog.service','fyp-phase8-hardstop.timer','fyp-p85-continuation-bootstrap-stop.timer'):
 shutil.copyfile(Path('/etc/systemd/system')/n,out/n)
summary={'observed_at_utc':datetime.now(UTC).isoformat(),'counts':counts,'originals':1500,'pause':pause,'active':0,'next_original':rows[82],'ledger_integrity':integrity,'notice_hash_chain_valid':chain,'transition_mismatches':mismatches,'backup_count_verified':len(checks),'backup_receipts_match_rows':all(c['receipt_matches_row'] for c in checks),'live_owned_application_processes':live_processes,'units':(out/'units.log').read_text(),'no_regrade':True,'no_restart':True,'no_admission':True,'source_changed':False,'elapsed_seconds':time.monotonic()-start}
write_new(out/'summary.json',summary)
write_new(out/'manifest.json',{'kind':'CONSISTENT_PAUSED_BOUNDARY_PRESERVATION_NOT_NEW_OUTCOMES','postgres_dumps':False,'files':{p.relative_to(out).as_posix():hash_file(p) for p in out.rglob('*') if p.is_file()}})
archive=out.with_suffix('.tar.gz')
with tarfile.open(archive,'x:gz') as t:t.add(out,arcname='inspection')
if cloud.inventory()+archive.stat().st_size>=read(root/'run.json')['policy']['cloud_limit_bytes']:raise ValueError('CLOUD_CAP_RETAIN_PARTIAL_AND_ROOT')
p=cloud.put(archive,cloud.prefix+'observations/'+hash_file(archive)+'.tar.gz');cloud.verify(p)
write_new(out.parent/'paused-preservation-20261009-proof.json',p.model_dump())
print(json.dumps({'summary':summary,'evidence':p.model_dump()}))
PY

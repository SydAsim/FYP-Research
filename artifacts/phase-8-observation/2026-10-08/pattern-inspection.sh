set -euo pipefail
umask 077
cd /opt/fyp-phase8-combined-v3
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B - <<'PY'
import collections,hashlib,json,shutil,sqlite3,subprocess,sys,tarfile,time
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v3'))
from controls import canonical,hash_file,read,write_new
from storage import ObjectProof,S3Cloud,verify_local
root=Path('/var/lib/p8-combined/run');out=root.parent/'deployment/pattern-inspection-20261008-1';out.mkdir(exist_ok=False)
begin=time.monotonic()
db=sqlite3.connect(f'file:{root}/campaign.sqlite3?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('BEGIN')
rows=[dict(x) for x in db.execute('SELECT * FROM slots ORDER BY sequence')]
notices=[dict(x) for x in db.execute('SELECT * FROM notices ORDER BY n')]
with sqlite3.connect(out/'campaign.sqlite3') as target:db.backup(target)
integrity=db.execute('PRAGMA integrity_check').fetchone()[0];db.close()
if any(r['state'] in ('RUNNING','EXPORTED') for r in rows):raise ValueError('ACTIVE_COLLECTION_REQUIRES_PRESERVATION_NO_SHUTDOWN')
latest={};previous='GENESIS';chain=True
for n in notices:
 if n['previous']!=previous or hashlib.sha256((n['body']+previous).encode()).hexdigest()!=n['hash']:chain=False
 previous=n['hash'];e=json.loads(n['body'])
 if e.get('kind') in ('ADMITTED','TRANSITION'):latest[e['execution_id']]=e
mismatches=[]
for r in rows:
 if r['state']=='PLANNED':continue
 e=latest.get(r['execution_id']);diff={k:{'row':r[k],'notice':e.get(k) if e else None} for k in ('state','deadline','backup_hash') if not e or e.get(k)!=r[k]}
 if diff:mismatches.append({'sequence':r['sequence'],'execution_id':r['execution_id'],'differences':diff})
write_new(out/'ledger-read-only.json',{'integrity':integrity,'chain_valid':chain,'mismatches':mismatches,'rows':rows,'notices':notices})
for n in ('pause.json','run.json','bindings.json','binding-seal.json','cloud.json','host-clock.json','handover.json','saved-identities.json','continuation-readiness.json','historical-evidence.tar.gz'):
 if (root/n).exists():shutil.copyfile(root/n,out/n)
shutil.copytree(root/'backups',out/'backups')
cloud=S3Cloud(read(root/'run.json')['policy']['cloud_bucket'],f"exports/phase8/{read(root/'run.json')['policy']['run_id']}/")
backupchecks=[];details=[];stats={};timings=[];gaps=[]
for r in rows:
 if r['state']!='BACKED_UP':continue
 if time.monotonic()-begin>300:raise TimeoutError('BOUNDED_READ_ONLY_INSPECTION_LIMIT')
 proofpath=root/'backups'/(r['execution_id']+'.json');p=read(proofpath)
 verify_local(Path(p['local']),p['sha256']);cloud.verify(ObjectProof.model_validate(p['cloud']))
 backupchecks.append({'sequence':r['sequence'],'receipt_hash':hash_file(proofpath),'ledger_backup_hash':r['backup_hash'],'receipt_matches_row':hash_file(proofpath)==r['backup_hash'],'cloud':p['cloud'],'local':p['local']})
 folder=root/'slots'/f"{r['sequence']:04d}"
 if r['sequence']<=2:folder=root.parent/'retained'/('first' if r['sequence']==1 else 'second')/'x/slot'
 tracepath=folder/'executions'/r['execution_id']/'export.json';trace=read(tracepath)
 dest=out/'exports'/f"{r['sequence']:04d}";dest.mkdir(parents=True);shutil.copyfile(tracepath,dest/'export.json')
 analysis=trace.get('analysis_row',{});values=analysis.get('values',{})
 item={'sequence':r['sequence'],'arm':r['arm'],'case_id':r['case_id'],'execution_id':r['execution_id'],'family':trace.get('input',{}).get('generator_family'),'raw_status':trace.get('status'),'driver_classification':trace.get('driver_classification'),'driver_error':trace.get('driver_error',trace.get('error')),'values':values,'analysis':analysis,'collection_errors':trace.get('collection_errors',[]),'permissive_response_errors':trace.get('permissive_response_errors',[]),'oracle_failure':trace.get('oracle_failure'),'historical_original':r['sequence']<=2,'export_sha256':hash_file(tracepath),'window_end':r['deadline'],'started_at':trace.get('started_at'),'finished_at':trace.get('finished_at'),'request_anchors':trace.get('external_requests')}
 details.append(item)
 if r['sequence']>2:
  s=stats.setdefault(r['arm'],{'n':0,'raw_status':{},'driver_classification':{},'families':{},'endpoints':{}});s['n']+=1
  for key,value in [('raw_status',item['raw_status']),('driver_classification',str(item['driver_classification'])),('families',item['family'])]:s[key][str(value)]=s[key].get(str(value),0)+1
  for k,v in values.items():s['endpoints'].setdefault(k,{})[v]=s['endpoints'].setdefault(k,{}).get(v,0)+1
 if item['collection_errors'] or item['permissive_response_errors'] or item['oracle_failure']:gaps.append(item)
write_new(out/'completed-details.json',details);write_new(out/'backup-verification.json',backupchecks)
logs=subprocess.run(['journalctl','-u','fyp-phase8-campaign.service','-u','fyp-phase8-watchdog.service','--no-pager','-o','short-iso','--since','2026-10-08 13:35:00 UTC'],capture_output=True,timeout=30)
(out/'systemd-stop-stdout.log').write_bytes(logs.stdout);(out/'systemd-stop-stderr.log').write_bytes(logs.stderr)
units=subprocess.run(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','fyp-phase8-hardstop.timer','--property=Id,ActiveState,SubState,ExecMainStatus'],capture_output=True,text=True,timeout=15).stdout
v={'observed_at_utc':datetime.now(timezone.utc).isoformat(),'counts':dict(collections.Counter(r['state'] for r in rows)),'originals':1500,'post_continuation_stats':stats,'historical_originals_separate':[d for d in details if d['historical_original']],'pause':read(root/'pause.json'),'ledger_integrity':integrity,'notice_hash_chain_valid':chain,'transition_mismatches':mismatches,'backup_count_verified':len(backupchecks),'backup_receipts_match_rows':all(x['receipt_matches_row'] for x in backupchecks),'collection_or_response_or_oracle_issue_sequences':[d['sequence'] for d in gaps],'next_original':next((r for r in rows if r['state']=='PLANNED'),None),'units':units,'descriptive_only':True,'no_regrade_or_outcome_replacement':True,'inspection_elapsed_seconds':time.monotonic()-begin}
write_new(out/'summary.json',v)
files={p.relative_to(out).as_posix():hash_file(p) for p in out.rglob('*') if p.is_file()}
write_new(out/'manifest.json',{'kind':'READ_ONLY_STOP_AND_PATTERN_EVIDENCE_NOT_REVISED_OUTCOMES','files':files,'postgres_dumps':False})
archive=out.with_suffix('.tar.gz')
with tarfile.open(archive,'x:gz') as tar:tar.add(out,arcname='inspection')
proof=cloud.put(archive,cloud.prefix+'observations/'+hash_file(archive)+'.tar.gz');cloud.verify(proof)
write_new(out.parent/'pattern-inspection-proof.json',proof.model_dump())
print(json.dumps({'summary':v,'evidence':proof.model_dump()}))
PY

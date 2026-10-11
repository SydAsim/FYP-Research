"""Read saved grades only; no oracle execution, regrading or outcome selection."""
import json, hashlib, collections, tarfile, shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
HERE=Path(__file__).parent
SOURCE=Path('E:/p8v9/source')
INSPECT=Path('E:/p8driver145v1/provisional2/inspection')
CLOSED=SOURCE/'artifacts/phase-8-runner-amendment/v4-complete/closed-120'

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    manifest=json.loads((INSPECT/'manifest.json').read_text())['files']
    member_results={n:sha(INSPECT/n)==h for n,h in manifest.items() if n!='verified-master.tar.gz'}
    assert all(member_results.values())
    rows=json.loads((INSPECT/'read-only-ledger.json').read_text())['rows']
    bindings=json.loads((CLOSED/'bindings.json').read_text())
    assert [{k:r[k] for k in bindings[0]} for r in rows]==bindings
    done=[r for r in rows if r['state']=='BACKED_UP']
    assert len(done)==145 and len(rows)==1500 and rows[145]['execution_id']=='01a11705-11f1-772d-8190-c43552871801'
    candidates=[]
    for p in Path('E:/p8v4/retained').glob('*/t/e.tar.gz'):
        name=p.parents[1].name
        if name[:4].isdigit() and int(name[:4])<=38:candidates.append((int(name[:4]),p))
    candidates.append((120,Path('artifacts/phase-8-operations/clock-diagnosis-120-v1/original120.tar.gz')))
    outcomes=[];failures=[];seen=set()
    for seq,p in sorted(candidates):
        if seq in seen:continue
        row=rows[seq-1];receipt=json.loads((CLOSED/'backups'/f"{row['execution_id']}.json").read_text())
        proof=receipt['cloud']
        if p.stat().st_size!=proof['bytes'] or sha(p)!=proof['sha256']:
            failures.append({'sequence':seq,'path':str(p),'reason':'ARCHIVE_DOES_NOT_MATCH_PINNED_RECEIPT'});continue
        with tarfile.open(p,'r:gz') as archive:
            # Reading members is in memory; no second extracted tree.
            m=json.load(archive.extractfile('slot/manifest.json'))['files']
            member=f"executions/{row['execution_id']}/export.json"
            raw=archive.extractfile('slot/'+member).read()
            assert hashlib.sha256(raw).hexdigest()==m[member]
            export=json.loads(raw)
        assert export['execution_id']==row['execution_id'] and export['arm']==row['arm']
        outcomes.append({'sequence':seq,'execution_id':row['execution_id'],'case_id':row['case_id'],'arm':row['arm'],'archive':str(p),'archive_sha256':proof['sha256'],'version_id':proof['version_id'],'export_sha256':m[member],'raw_status':export['status'],'failure_type':export.get('failure',{}).get('type') if export.get('failure') else None,'values':export['revised_grade']['values'],'voice_evidence':export['revised_grade']['observable']['voice_evidence'],'original_censor_reason':export['analysis_row'].get('censor_reason')})
        seen.add(seq)
    case_arms=collections.defaultdict(set)
    for r in done:case_arms[r['case_id']].add(r['arm'])
    available=collections.defaultdict(set)
    for r in outcomes:available[r['case_id']].add(r['arm'])
    now=datetime.now(timezone.utc);deadline=datetime.fromisoformat('2026-10-22T15:24:23.810674+00:00')
    hours=290*1355/1498;prep=2.5;rate=.1197+.005+160*.096/730
    start=datetime.fromisoformat('2026-10-07T15:24:23.810674+00:00')
    reserve=48*160*.096/730+80*.025+5+1.25
    projected=((now-start).total_seconds()/3600+hours+prep)*rate+reserve
    data={'at':now.isoformat(),'integrity_scope':'12 inspection members match included manifest; complete inspection hash not locally verified. Master pinned readback PASS on host from preservation proof; frozen bindings independently match all identities.','inspection_member_checks':member_results,'slots':dict(collections.Counter(r['state'] for r in rows)),'completed_arms':dict(collections.Counter(r['arm'] for r in done)),'unique_cases':len(case_arms),'complete_sets':sum(v=={'B3','P1','P2'} for v in case_arms.values()),'incomplete_sets':{k:sorted(v) for k,v in case_arms.items() if v!={'B3','P1','P2'}},'locally_full_archive_verified_outcomes':outcomes,'unavailable_outcome_slots':[r['sequence'] for r in done if r['sequence'] not in seen],'available_grade_arms':dict(collections.Counter(r['arm'] for r in outcomes)),'available_complete_sets':sum(v=={'B3','P1','P2'} for v in available.values()),'verification_failures':failures,'pooled_raw_status':dict(collections.Counter(r['raw_status'] for r in outcomes)),'pooled_values':{k:dict(collections.Counter(r['values'][k] for r in outcomes)) for k in outcomes[0]['values']} if outcomes else {},'sidecars_preserved':[str(p) for p in (CLOSED/'historical/timing-sidecars').glob('*.json')],'remaining_time':{'available_hours':(deadline-now).total_seconds()/3600,'unchanged_allowance_hours':hours,'preparation_shutdown_hours':prep,'required_hours':hours+prep,'shortfall_hours':hours+prep-(deadline-now).total_seconds()/3600,'window_floor_hours':1355/6,'fits':now+timedelta(hours=hours+prep)<=deadline},'cost':{'last_verified_rates_date':'2026-10-10; no current billing/pricing refresh or cost PASS','reviewed_elapsed_clock_conservative_projection_usd':projected,'guard_usd':60,'ceiling_usd':65,'reserve_usd':reserve,'includes_elapsed_paused_hours_conservatively':True},'disk_free_bytes':{d:shutil.disk_usage(d).free for d in ('C:/','D:/','E:/')},'next':rows[145]}
    (HERE/'provisional-summary.json').write_text(json.dumps(data,indent=2))
    print(json.dumps({k:v for k,v in data.items() if k not in ('locally_full_archive_verified_outcomes','unavailable_outcome_slots','inspection_member_checks','sidecars_preserved')},indent=2))

if __name__=='__main__':main()

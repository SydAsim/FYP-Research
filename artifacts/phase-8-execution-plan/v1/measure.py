"""Offline execution-plan measurements. Never imports or launches an experiment driver."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
import csv, hashlib, json, re, statistics

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
V4=ROOT/'artifacts/phase-8-study-design/v4'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
def instant(x):return datetime.fromisoformat(x.replace('Z','+00:00'))
def summary(xs):
    xs=sorted(xs)
    def q(p):
        k=(len(xs)-1)*p;i=int(k)
        return xs[i]+(xs[min(i+1,len(xs)-1)]-xs[i])*(k-i)
    return {'n':len(xs),'min':xs[0],'median':statistics.median(xs),'mean':statistics.mean(xs),'p95':q(.95),'max':xs[-1],'sum':sum(xs)}

before_file=OUT/'preserved-files-before.json'
if not before_file.exists():
    inventory={}
    for name in ('historical-hashes-before.json','candidate-source-final-hashes.json'):
        for name_,expected in load(V4/name).items():
            p=ROOT/name_;assert sha(p)==expected,name_
            inventory[p.relative_to(ROOT).as_posix()]=expected
    for p in V4.rglob('*'):
        if p.is_file():inventory[p.relative_to(ROOT).as_posix()]=sha(p)
    for p in (ROOT/'research/fixtures/phase8_design_v4').glob('*.json'):
        inventory[p.relative_to(ROOT).as_posix()]=sha(p)
    before_file.write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
inventory=load(before_file)
assert all((ROOT/p).exists() and sha(ROOT/p)==h for p,h in inventory.items())
bank=load(ROOT/'research/fixtures/phase8_design_v4/inputs.json')
slots=load(V4/'main-slots.json');review=load(V4/'review-decisions.json')
assert len(bank['main_inputs'])==500 and len(slots)==1500
assert all(s['status']=='NOT_STARTED' and s['execution_id'] is None for s in slots)
assert review['review_receipt'] is None and review['freeze_hash'] is None
qualification=load(V4/'calibration-qualification.json')
rows=[];by_slot=defaultdict(list);boot_by_directory={}
for r in qualification['all_attempts']:
    p=ROOT/r['path'];t=load(p)
    start,end=instant(t['started_at']),instant(t['finished_at'])
    anchor=max((instant(a['scripted_at']) for a in t.get('targets',[])),default=None)
    e={'case_id':r['case_id'],'arm':r['arm'],'family':t['input']['generator_family'],
       'stratum':t['input']['stratum'],'status':t['status'],'qualification':r['qualification']['status'],
       'elapsed_seconds':(end-start).total_seconds(),
       'pre_last_issued_request_seconds':(anchor-start).total_seconds() if anchor else None,
       'trace_bytes':p.stat().st_size,'path':p.relative_to(ROOT).as_posix(),'started_at':t['started_at']}
    rows.append(e);by_slot[(r['case_id'],r['arm'])].append(e)
    process=[v for v in t.get('processes',[]) if v['event']=='PROCESS_STARTED']
    if process:
        ns=int(re.search(r'-(\d+)\.log$',process[0]['log'])[1])
        boot=(start.timestamp()-ns/1e9)
        directory=p.parent.relative_to(ROOT).as_posix()
        boot_by_directory[directory]=min(boot_by_directory.get(directory,boot),boot)
assert len(rows)==178
selected=[]
for key,rs in by_slot.items():
    qualified=[r for r in rs if r['qualification']=='QUALIFIED_BOUNDARY']
    assert qualified,key
    selected.append(max(qualified,key=lambda r:r['started_at']))
assert len(selected)==150
mapping={(r['case_id'],r['arm']):r for r in selected}
cal_to_main={c['generator_family']+':'+c['cluster_id']:c['case_id'] for c in bank['calibration_inputs']}
prefix=0;active=0;trace_bytes=0;projection_rows=[]
order=load(V4/'execution-order.json')['rows']
inputs={c['case_id']:c for c in bank['main_inputs']}
for item in order:
    c=inputs[item['case_id']]
    family_key=c['generator_family']+':'+c['cluster_id']
    cal_id=cal_to_main[family_key]
    global_fault=c['generator_family'] in ('restart-before-repair','redis-loss')
    for index,arm in enumerate(item['arm_order'],1):
        r=mapping[(cal_id,arm)]
        pre=r['pre_last_issued_request_seconds'] or 0
        prefix+=pre;active+=r['elapsed_seconds'];trace_bytes+=r['trace_bytes']
        projection_rows.append({'input_order':item['order'],'batch_id':item['batch_id'],
             'case_id':c['case_id'],'arm_order':index,'arm':arm,'stratum':c['stratum'],
             'family':c['generator_family'],'calibration_case_id':cal_id,
             'calibration_trace':r['path'],'live_concurrency':1,
             'isolation':'EXCLUSIVE_PROCESS_OR_CACHE' if global_fault else 'FRESH_SCENARIO_RESOURCE',
             'parallel_live_qualified':False,'pre_request_seconds_reference':round(pre,6),
             'driver_seconds_reference':round(r['elapsed_seconds'],6),'observation_seconds':600,
             'status':'PLAN_ONLY_NOT_STARTED'})
with (OUT/'slot-plan.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(projection_rows[0]));w.writeheader();w.writerows(projection_rows)
with (OUT/'calibration-measurements.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
family_counts=Counter(c['generator_family'] for c in bank['main_inputs'])
with (OUT/'case-isolation.csv').open('w',newline='',encoding='utf-8') as f:
    fields=['case_id','stratum','family','isolation','live_parallel_qualified','reason']
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for c in bank['main_inputs']:
        name=c['generator_family']
        w.writerow({'case_id':c['case_id'],'stratum':c['stratum'],'family':name,
         'isolation':'EXCLUSIVE_PROCESS' if name=='restart-before-repair' else 'EXCLUSIVE_CACHE' if name=='redis-loss' else 'SCENARIO_SCOPED',
         'live_parallel_qualified':False,
         'reason':'Shared worker PID/configuration is replaced' if name=='restart-before-repair' else 'FLUSHDB affects entire reserved Redis database' if name=='redis-loss' else 'Unique scenario/workflow/resource and operation-scoped calls; concurrent full-window collection unqualified'})
budgets=load(V4/'budget-qualification.json')
probe=next(r for r in budgets['budgets'] if r['budget']=='observation')
probe_path=ROOT/probe['path'];probe_trace=load(probe_path)
window=next(w for w in probe_trace['observation_windows'] if w['name']=='MISSING_COMPLETION_WINDOW')
boot=summary(list(boot_by_directory.values()))
post=max(0,probe['elapsed_seconds']-600)
forecast=(1500*600+prefix+1500*boot['median']+1500*post)/3600
metrics={
 'classification':'OFFLINE_EXECUTION_PLANNING_NOT_CAMPAIGN',
 'measured_at':datetime.now(timezone.utc).isoformat(),'main_started':False,
 'calibration_all_attempts_seconds':summary([r['elapsed_seconds'] for r in rows]),
 'calibration_status_counts':dict(Counter(r['status'] for r in rows)),
 'latest_qualified_per_slot':{'n':len(selected),'selection_rule':'Latest qualified retained attempt for timing/size reference only; every original attempt remains in the CSV; never replaces an outcome'},
 'calibration_by_stratum':{s:{'duration_seconds':summary([r['elapsed_seconds'] for r in rows if r['stratum']==s]),'trace_bytes':summary([r['trace_bytes'] for r in rows if r['stratum']==s])} for s in ('CLEAN','HIDDEN_COMMIT','PLAYOUT','OTHER_BOUNDARY')},
 'runtime_startup_seconds':{**boot,'method':'First trial start minus simulator launch log filename timestamp, per calibration directory; includes readiness/driver preparation; not an isolated boot benchmark'},
 'main_projection':{'slots':1500,'observation_hours':250,'weighted_driver_only_hours':active/3600,
 'weighted_pre_request_hours':prefix/3600,'boot_per_slot_reference_seconds':boot['median'],
 'collector_overrun_reference_seconds':post,'base_serial_hours':forecast,'with_15_percent_operational_reserve_hours':forecast*1.15,
 'with_20_percent_operational_reserve_hours':forecast*1.2,'hours_per_75_slot_block':forecast/20,
 'method':'Match exact fixed recipe and arm to latest qualified calibration, weight by realized main bank. Add 600s after final issued request, startup proxy per slot and measured collector overrun. Do not add whole driver time twice.'},
 'storage':{'weighted_short_trace_projection_bytes':trace_bytes,'long_probe_path':probe_path.relative_to(ROOT).as_posix(),
 'long_probe_bytes':probe_path.stat().st_size,'long_probe_polls':len(window['polls']),
 'all_slots_at_long_probe_size_bytes':1500*probe_path.stat().st_size,
 'v4_entire_artifact_directory_bytes':sum(p.stat().st_size for p in V4.rglob('*') if p.is_file()),
 'database_footprint':'UNAVAILABLE: read-only connections timed out; no service started',
 'working_reservation_GiB':25,'separate_backup_reservation_GiB':25,
 'limitation':'One full-window probe is not a p95 size or a database/WAL benchmark; compressed savings are not assumed.'},
 'isolation':{'worker_restart_inputs':family_counts['restart-before-repair'],'cache_flush_inputs':family_counts['redis-loss'],
 'exclusive_inputs':family_counts['restart-before-repair']+family_counts['redis-loss'],
 'scenario_scoped_inputs':500-family_counts['restart-before-repair']-family_counts['redis-loss'],
 'live_parallel_qualified_cases':0,'live_concurrency_recommended':1},
 'qualified_budget_measurements':budgets['budgets'],
 'source_hashes':{p.relative_to(ROOT).as_posix():sha(p) for p in [V4/'calibration-qualification.json',V4/'budget-qualification.json',V4/'execution-order.json',ROOT/'research/fixtures/phase8_design_v4/inputs.json']}}
(OUT/'measurements.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8')
changes=[p for p,h in inventory.items() if not (ROOT/p).exists() or sha(ROOT/p)!=h]
report={'checked_at':datetime.now(timezone.utc).isoformat(),'preserved_files':len(inventory),'changed_files':changes,
 'historical_inventory_files':len(load(V4/'historical-hashes-before.json')),'candidate_source_inventory_files':len(load(V4/'candidate-source-final-hashes.json')),
 'main_slots':1500,'main_statuses':dict(Counter(s['status'] for s in load(V4/'main-slots.json'))),
 'review_receipt':review['review_receipt'],'freeze_hash':review['freeze_hash'],'main_started':False,
 'application_behaviour_changed':False,'new_outputs_only':str(OUT.relative_to(ROOT))}
assert not changes
(OUT/'preservation-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:metrics[k] for k in ('main_projection','runtime_startup_seconds','storage','isolation')},indent=2))

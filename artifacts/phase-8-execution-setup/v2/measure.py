"""Read retained qualifications and produce planning measurements; never admits inputs."""
import csv
import hashlib
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from research.execution_setup.core import Ledger, check_inventory, digest, load, now  # noqa: E402
from research.execution_setup.resources import GIB, host, tree_bytes  # noqa: E402

RUN = Path('E:/FYP-Research/phase8-setup-v1-attempt2')
BACKUP = Path('D:/FYP-ResearchBackups/phase8-setup-v1')


def instant(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def lsn(value):
    a, b = value.split('/')
    return (int(a, 16) << 32) + int(b, 16)


def summarize(values):
    return {'n': len(values), 'min': min(values), 'median': statistics.median(values),
            'mean': statistics.mean(values), 'max': max(values)} if values else None


ledger = Ledger(RUN)
ledger.verify()
rows = ledger.rows()
assert len(rows) == 2 and all(r['state'] == 'EXPORTED' for r in rows)
before = load(RUN / 'historical-hashes-before.json')
check_inventory(before)
check_inventory(load(RUN / 'source-seal.json'))
main = load(ROOT / 'artifacts/phase-8-study-design/v4/main-slots.json')
assert len(main) == 1500 and all(r['status'] == 'NOT_STARTED' and not r['execution_id'] for r in main)
executions = []
samples = []
for slot in rows:
    path = RUN / 'executions' / slot['execution_id'] / 'export.json'
    trace = load(path)
    assert digest(path) == slot['export_hash']
    polls = [load(Path(p['path'])) for p in trace['polls']]
    observed = [p['host'] for p in polls]
    samples += observed
    gap = [(instant(b['at']) - instant(a['ended_at'])).total_seconds()
           for a, b in zip(polls, polls[1:])]
    startup = (instant(trace['http'][0]['sent_at']) - instant(trace['started_at'])).total_seconds()
    delta = {role: {
        'database_bytes_delta': trace['resource_end'][role]['database_bytes'] - trace['resource_start'][role]['database_bytes'],
        'wal_bytes_generated': lsn(trace['resource_end'][role]['wal_lsn']) - lsn(trace['resource_start'][role]['wal_lsn']),
        'wal_directory_bytes_end': trace['resource_end'][role]['wal_directory_bytes'],
    } for role in ('app','truth')}
    executions.append({
        **slot, 'trace': str(path), 'driver_status': trace['status'],
        'failure': trace.get('failure'), 'oracle_failure': trace.get('oracle_failure'),
        'grade': trace.get('revised_grade',{}).get('values'),
        'started_at': trace['started_at'], 'finished_at': trace['finished_at'],
        'driver_finished_at': trace['driver_finished_at'],
        'elapsed_seconds': (instant(trace['finished_at']) - instant(trace['started_at'])).total_seconds(),
        'startup_before_first_request_seconds': startup,
        'original_anchor': trace['external_requests'][-1]['issued_at'],
        'collector_overshoot_seconds': (instant(trace['finished_at']) - instant(slot['deadline'])).total_seconds(),
        'post_return_collected_seconds': (instant(trace['finished_at']) - instant(trace['driver_finished_at'])).total_seconds(),
        'poll_count': len(polls), 'maximum_between_poll_gap_seconds': max(gap),
        'collection_errors': trace.get('collection_errors',[]),
        'collector_resumes': trace.get('collector_resumes',[]),
        'refusals': [{'path': r['path'], 'status': r['status'], 'at': r['received_at']}
                     for r in trace['http'] if r.get('status') and r['status'] >= 400],
        'growth': delta, 'export_bytes': path.stat().st_size,
        'logs_bytes': trace['resource_end']['logs_bytes'], 'audio_bytes': trace['resource_end']['audio_bytes'],
        'poll_bytes': trace['resource_end']['poll_bytes'],
        'execution_tree_bytes_now': tree_bytes(path.parent),
    })
plan = load(RUN / 'controls/late-ack-v1-plan.json')
response = load(RUN / 'controls/late-ack-v1-response.json')
event = plan['request']['event_id']
first_trace = load(Path(executions[0]['trace']))
captured = [(value['ended_at'], p['path'], a['server_received_at'])
            for p in first_trace['polls'] for value in [load(Path(p['path']))]
            for a in value['snapshot']['playback_rows'] if str(a['id']) == event]
assert response['status'] == 202 and captured
native = json.loads((OUT / 'native-memory-during-second.json').read_text(encoding='utf-8-sig'))
historical = load(ROOT / 'artifacts/phase-8-execution-plan/v1/measurements.json')
reference = historical['main_projection']
startup = statistics.median(e['startup_before_first_request_seconds'] for e in executions)
overshoot = max(e['collector_overshoot_seconds'] for e in executions)
with ledger.connect() as conn:
    events = [dict(r) for r in conn.execute('SELECT * FROM events')]
archive_events = [r for r in events if json.loads(r['body'])['kind'] in ('BACKUP_VERIFIED','INCREMENTAL_BACKUP_VERIFIED')]
tail = []
for execution in executions:
    end = instant(execution['deadline'])
    applicable = [r for r in archive_events if instant(r['at']) >= end]
    if applicable:
        tail.append((instant(applicable[0]['at'])-end).total_seconds())
finalization = max(tail) if tail else overshoot
base = 250 + reference['weighted_pre_request_hours'] + 1500 * (startup + finalization) / 3600
archive = list(BACKUP.glob('incremental-v2-*/backup-manifest.json'))
assert archive
objects = BACKUP / 'objects-v2'
full_window_bytes = max(e['execution_tree_bytes_now'] for e in executions)
metrics = {
    'classification': 'SEPARATE_SETUP_QUALIFICATION_NOT_CAMPAIGN', 'measured_at': now(),
    'scope': {'inputs':500,'arms':['B3','P1','P2'],'planned_slots':1500,'main_executions':0},
    'qualification': executions,
    'host': {
        'initial': load(RUN/'initial-resources.json'), 'current': host(RUN,BACKUP),
        'sampled_peak_used_memory_bytes': max(s['used_memory_bytes'] for s in samples),
        'minimum_available_memory_bytes': min(s['available_memory_bytes'] for s in samples),
        'available_memory_bytes': summarize([s['available_memory_bytes'] for s in samples]),
        'cpu_load_fraction': summarize([s['cpu_load_fraction'] for s in samples if s['cpu_load_fraction'] is not None]),
        'native_service_working_set_sum_bytes': sum(p['WorkingSetBytes'] for p in native),
        'sum_of_native_process_peak_working_sets_bytes': sum(p['PeakWorkingSetBytes'] for p in native),
        'peak_limit': 'Host peak sampled at poll cadence; summed process peaks need not be simultaneous; VM/container memory separate',
        'docker_engine_memory_limit_bytes': 4106457088,
    },
    'late_ack_control': {'event_id':event,'response':response,'first_capture':captured[0],
                         'detection_delay_seconds':(instant(captured[0][0])-instant(captured[0][2])).total_seconds()},
    'parallel': {'tested':False,'reason':'Available memory below the predeclared 4GiB threshold',
                 'recommended_concurrency':1,'parallel_schedule':'UNQUALIFIED; no speedup claimed'},
    'runtime': {'observation_hours':250, 'measured_startup_reference_seconds':startup,
                'measured_finalization_reference_seconds':finalization,
                'weighted_pre_request_reference_hours':reference['weighted_pre_request_hours'],
                'base_serial_hours':base,'reserve_15pct_hours':base*1.15,'reserve_20pct_hours':base*1.2,
                '75_slot_block_base_hours':base/20,
                'limitations':'Two full windows plus v4 recipe/arm references; no p95 or 1500-slot ledger benchmark; throughput and background load may differ'},
    'storage': {'qualification_live_bytes':tree_bytes(RUN),'retained_preparation_attempt_bytes':tree_bytes(Path('E:/FYP-Research/phase8-setup-v1')),
                'all_backups_bytes':tree_bytes(BACKUP),'new_objects_compressed_bytes':tree_bytes(objects),
                'new_object_count':len(list(objects.glob('*.gz'))), 'largest_measured_execution_bytes':full_window_bytes,
                '1500_at_largest_measured_execution_bytes':full_window_bytes*1500,
                'working_reservation_bytes':50*GIB,'backup_reservation_bytes':50*GIB,
                'system_drive_reservation_bytes':25*GIB,
                'backup_policy':'Each immutable file once; slot/event deltas; full ledger/database checkpoint each 75 slots, controlled checkpoint and completion',
                'physical_drives':'C,D,E all disk 0; not independent physical backup',
                'database_disaster_recovery':'No continuous PITR WAL backup; current original volumes needed to preserve active late effects'},
    'preservation': {'verified_files':len(before),'all_hashes_unchanged':True,
                     'original_collector_source_hashes_unchanged':True,'review_receipt':None,'freeze_hash':None},
}
(OUT/'measurements.json').write_text(json.dumps(metrics,indent=2,default=str)+'\n',encoding='utf-8')
(OUT/'historical-hashes-after.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
with (OUT/'resources.csv').open('w',newline='',encoding='utf-8') as handle:
    fields = list(samples[0])
    writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader();writer.writerows(samples)
manifest = {str(p):digest(p) for p in RUN.rglob('*') if p.is_file() and p.name!='runner.lock'}
(OUT/'qualification-file-hashes.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'serial_hours':base,'days_with_reserve':[base*1.15/24,base*1.2/24],
                  'minimum_available_GiB':metrics['host']['minimum_available_memory_bytes']/GIB,
                  'sampled_peak_used_GiB':metrics['host']['sampled_peak_used_memory_bytes']/GIB,
                  'largest_execution_MiB':full_window_bytes/1024**2,
                  'cpu':metrics['host']['cpu_load_fraction'],'traces':[(e['arm'],e['driver_status'],e['oracle_failure']) for e in executions]},indent=2))

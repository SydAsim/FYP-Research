"""Read existing retained evidence; write separate review appendices only."""
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, median

ROOT = Path.cwd()
OUT = ROOT / 'artifacts/independent-review-handoff/2026-10-08'
SNAP = Path('E:/FYP Project/p8-observation-20261008-1/x/inspection')

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, default=str)
        f.write('\n')

def csv_out(name, rows):
    with (OUT / name).open('x', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

manifest = read(SNAP / 'manifest.json')['files']
assert len(manifest) == 93
for name, digest in manifest.items():
    assert sha(SNAP / name) == digest, name
fixture_path = ROOT / 'research/fixtures/phase8_design_v4/inputs.json'
fixture = read(fixture_path)
cases = fixture['main_inputs']
assert len(cases) == 500
details = read(SNAP / 'completed-details.json')
proofs = {x['sequence']: x for x in read(SNAP / 'backup-verification.json')}
ledger = read(SNAP / 'ledger-read-only.json')
assert Counter(x['state'] for x in ledger['rows']) == {'BACKED_UP': 38, 'PLANNED': 1462}
exports = {}
rows = []
for d in details:
    seq = d['sequence']
    path = SNAP / f'exports/{seq:04d}/export.json'
    assert sha(path) == d['export_sha256']
    e = exports[seq] = read(path)
    proof = proofs[seq]
    assert proof['receipt_matches_row']
    deadline = datetime.fromisoformat(d['window_end'])
    finished = datetime.fromisoformat(d['finished_at'])
    anchor = datetime.fromisoformat(d['request_anchors'][-1]['issued_at'])
    assert abs((deadline-anchor).total_seconds()-600) < .001
    assert finished >= deadline
    rows.append({
        'sequence': seq, 'case_id': d['case_id'], 'arm': d['arm'],
        'scenario': d['family'], 'stratum': d['analysis']['stratum'],
        'attempt': 1, 'execution_id': d['execution_id'],
        'runner_version_recorded': e.get('combined_runner_version', e.get('setup_version', 'not recorded')),
        'driver_source_hash': e.get('driver_source_hash', 'not recorded'),
        'raw_status_preserved': d['raw_status'],
        'original_censor_reason': d['analysis']['censor_reason'],
        'classification_sidecar': 'accepted separate timing sidecar; original unchanged' if seq < 3 else e.get('driver_classification', {}).get('classification', 'normal recorded outcome'),
        **d['values'], 'final_request_utc': anchor.isoformat(),
        'window_deadline_utc': deadline.isoformat(), 'finished_utc': finished.isoformat(),
        'seconds_from_final_request': (finished-anchor).total_seconds(),
        'full_window_completed': True, 'trace_file': path.as_posix(),
        'export_sha256': d['export_sha256'], 'backup_receipt_sha256': proof['receipt_hash'],
        'backup_bucket': proof['cloud']['bucket'], 'backup_key': proof['cloud']['key'],
        'backup_version_id': proof['cloud']['version_id'],
        'backup_archive_sha256': proof['cloud']['sha256'], 'backup_bytes': proof['cloud']['bytes'],
    })
csv_out('38-executions.csv', rows)
csv_out('500-input-catalogue.csv', [{
    'case_id': c['case_id'], 'stratum': c['stratum'], 'recipe': c['generator_family'],
    'legacy_cluster_id_not_sampling_unit': c['cluster_id'], 'seed': c['seed'],
    'phase': c['correction_barrier'], 'fault_hooks': '|'.join(c['fault_schedule']),
    'provider_faults': json.dumps(c['provider']['faults'], sort_keys=True),
    'speech_exposure': c['speech_exposure'], 'arm_order': '|'.join(c['arm_order']),
    'intents': json.dumps(c['intents'], sort_keys=True), 'media': c['media'],
    'observation_seconds': c['observation_budget_seconds'],
} for c in cases])
recover = {'partial-time','full-before-correction','late-decisive-ack','restart-before-repair','reconnect-third-revision'}
summary = {
    'fixture_sha256': sha(fixture_path), 'frame_recipes': len(fixture['frame']),
    'strata': dict(Counter(c['stratum'] for c in cases)),
    'recipes': dict(Counter(c['generator_family'] for c in cases)),
    'phases': dict(Counter(c['correction_barrier'] for c in cases)),
    'speech_exposure': dict(Counter(c['speech_exposure'] for c in cases)),
    'fault_hook_memberships_nonexclusive': dict(Counter(h for c in cases for h in c['fault_schedule'])),
    'provider_fault_memberships_nonexclusive': dict(Counter(f["kind"]+':'+f['stage'] for c in cases for f in c['provider']['faults'])),
    'recovery_challenge_inputs': sum(c['generator_family'] in recover for c in cases),
    'recovery_recipes': {k: sum(c['generator_family']==k for c in cases) for k in sorted(recover)},
    'scope': 'Frozen input content; no main input executed by this report',
}
write('catalogue-summary.json', summary)
triple = []
for seq in (1,2,3):
    e = exports[seq]
    triple.append({
        'sequence': seq, 'arm': e['arm'], 'execution_id': e['execution_id'],
        'external_requests': e['external_requests'], 'targets': e['targets'],
        'provider_truth': e['snapshot']['truth'],
        'provider_observations': e['snapshot']['observations'],
        'verification_and_refusal_http': [h for h in e['http'] if h['status'] >= 400 or 'verifications' in h['path']],
        'driver_failure': e.get('failure'), 'driver_classification': e.get('driver_classification'),
        'segments_count': len(e['snapshot']['segments']), 'client_playback_count': len(e['client_playback']),
        'original_analysis_row': next(d['analysis'] for d in details if d['sequence']==seq),
        'raw_export_sha256': sha(SNAP / f'exports/{seq:04d}/export.json'),
    })
write('matched-triple-0484.json', triple)
unexecuted = next(c for c in cases if c['generator_family']=='restart-before-repair')
assert unexecuted['case_id'] not in {d['case_id'] for d in details}
write('planned-repair-fixture-UNEXECUTED.json', {'status':'UNEXECUTED_MAIN_INPUT', 'case':unexecuted})
continued = [exports[i] for i in range(3,39)]
cadence = [(datetime.fromisoformat(continued[i+1]['started_at'])-datetime.fromisoformat(continued[i]['started_at'])).total_seconds() for i in range(len(continued)-1)]
now = datetime.now(timezone.utc)
start = datetime.fromisoformat('2026-10-07T15:24:23.810674+00:00')
stop = start+timedelta(hours=360)
hour_rate = .1197+.005+160*.096/730
remaining_hours = 1462*mean(cadence)/3600
finish = now+timedelta(hours=remaining_hours)
previous = read(ROOT/'artifacts/phase-8-continuation-deployment/v3/preprovision-feasibility.json')
extra = previous['previous_compute_ipv4_usd']+previous['previous_and_retained_disk_usd_upper']+1.25
def guard(at):
    hours=(at-start).total_seconds()/3600
    return hours*hour_rate + 48*160*.096/730 + 30*.025 + 5 + extra
cost = {
    'classification':'OFFLINE_PROJECTION_EXISTING_MEASUREMENTS_NOT_CURRENT_BILLING',
    'at_utc':now.isoformat(), 'deadline_utc':stop.isoformat(), 'remaining_slots':1462,
    'minimum_observation_hours':1462*600/3600,
    '35_continued_start_to_start_intervals_seconds':cadence,
    'mean_slot_seconds':mean(cadence), 'median_slot_seconds':median(cadence),
    'projected_remaining_hours_at_observed_mean':remaining_hours,
    'projected_finish_if_immediate_utc':finish.isoformat(),
    'deadline_margin_hours':(stop-finish).total_seconds()/3600,
    'conservative_projected_committed_cost_usd':guard(finish+timedelta(minutes=30)),
    'estimated_latest_start_at_this_cadence_utc':(start+timedelta(hours=(55-48*160*.096/730-30*.025-5-extra)/hour_rate-remaining_hours-.5)).isoformat(),
    'current_actual_billed_campaign_spending':'not verified',
    'last_recorded_credits_usd':previous['credits']['accountPlanRemainingCredits']['amount'],
    'rates_as_of':'2026-10-08 deployment evidence; not refreshed by this report',
    'root_usd_per_day_730_hour_convention':24*160*.096/730,
    'per_slot_backup_compressed_bytes':{'min':min(r['backup_bytes'] for r in rows),'max':max(r['backup_bytes'] for r in rows),'mean':mean(r['backup_bytes'] for r in rows)},
    'remaining_backup_bytes_at_mean':1462*mean(r['backup_bytes'] for r in rows),
    'limitations':['35 intervals are a clean-heavy prefix, not worst-case recovery throughput','No AWS query or resource change','Billing lag, transfers, versioned duplicates, interrupted attempts and retention are uncertain','Cost guard counts original elapsed clock, including downtime'],
}
write('offline-feasibility.json',cost)
inventory = {
    'read_only_sources_verified':{'snapshot_members':93,'original_exports':38,'backup_receipts':38},
    'source_hashes': {str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [fixture_path,ROOT/'docs/12_PHASE8_CANDIDATE_V4.md',ROOT/'research/study_v4/analysis.py',ROOT/'research/study_v4/oracle.py',ROOT/'research/oracle/readiness_v2.py',ROOT/'research/arms.py',ROOT/'artifacts/phase-8-runner-amendment/v4/controls.py',ROOT/'artifacts/phase-8-runner-amendment/v4/final-verification.json']},
    'snapshot_manifest_sha256':sha(SNAP/'manifest.json'),
    'no_regrade':True,'research_executions':0,'aws_actions':0,'freeze_actions':0,
}
for name,digest in manifest.items():
    assert sha(SNAP/name)==digest
write('read-only-verification.json',inventory)
print(json.dumps({'written_appendices':6,'verified_exports':38,'catalogue':summary,'feasibility':cost},default=str))

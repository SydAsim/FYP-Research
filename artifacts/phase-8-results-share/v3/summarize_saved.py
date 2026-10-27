"""Pooled descriptive summary of already recorded grades; no inferential analysis."""
import collections
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    data = json.loads((HERE / 'saved-results.json').read_bytes())
    verification = json.loads((HERE / 'verification.json').read_bytes())
    assert verification['download_hashes_match']
    rows = [r for r in data['rows'] if r['available']]
    n = len(rows)
    values = data['pooled_values']
    corrections = sum(r['stratum'] != 'CLEAN' for r in rows)
    clean = n - corrections
    table = [
        ('Correct final business state', values['final_business_state_correct'].get('TRUE', 0), n),
        ('Correction success (correction executions only)', values['correction_success'].get('TRUE', 0), corrections),
        ('Clean useful-task success (clean executions only)', values['clean_task_success'].get('TRUE', 0), clean),
        ('Correct final supported update', values['correct_final_update'].get('TRUE', 0), n),
    ]
    bad = collections.Counter((r['stratum'], r['generator_family']) for r in rows if r['values']['final_business_state_correct'] == 'FALSE')
    groups = {
        'recorded_business_false_by_family_pooled': [{'stratum': k[0], 'family': k[1], 'executions': v} for k, v in sorted(bad.items())],
        'raw_failed_sequences': [r['sequence'] for r in rows if r['raw_status'] == 'FAILED'],
        'unsupported_exposure_true_sequences': [r['sequence'] for r in rows if r['values']['unsupported_exposed_claim'] == 'TRUE'],
        'source_oracle_versions': dict(collections.Counter(str(r['oracle_version']) for r in rows)),
        'collection_error_execution_count': sum(r['collection_errors'] > 0 for r in rows),
        'recorded_oracle_failure_execution_count': sum(bool(r['oracle_failure']) for r in rows),
        'separate_historical_timing_sidecars_applied': False,
    }
    with (HERE / 'descriptive-diagnostics.json').open('x', encoding='utf-8') as f:
        json.dump(groups, f, indent=2)
    pakistan = datetime.fromisoformat(data['snapshot_at']) + timedelta(hours=5)
    lines = [
        '# Phase 8 interim pooled results — incomplete study', '',
        f"Snapshot: {data['snapshot_at']} ({pakistan:%d October %Y, %H:%M} Pakistan time).",
        f"{data['completed_originals']}/1500 originals BACKED_UP; {data['unique_completed_inputs']} distinct inputs; {data['complete_three_arm_sets']} complete B3/P1/P2 sets.",
        f"All {data['available_grades']} saved grades were available in this snapshot; verification failures: {len(data['verification_failures'])}.", '',
        'These are original execution counts, not independent callers. Each input has three paired arm executions. This review reads stored grades only; it does not rerun an oracle, modify an outcome, apply a historical timing sidecar, fit a model, resample, rank arms or change scheduling.', '',
        '## Observed pooled outcomes', '',
        '| Recorded endpoint | TRUE / eligible executions | Descriptive percentage |',
        '|---|---:|---:|',
        *[f'| {label} | {true}/{denominator} | {100*true/denominator:.1f}% |' for label, true, denominator in table], '',
        'Other stored categories remain explicit:', '',
        *[f"- **{key}**: " + ', '.join(f'{k}={v}' for k, v in sorted(values[key].items())) + '.' for key in ['forbidden_effect', 'unsupported_exposed_claim', 'incompatible_stale_exposure', 'correct_final_update', 'corrective_delivery_after_challenge', 'complete_corrective_communication', 'explicit_retraction']], '',
        'Raw status (separate from business/speech grades): ' + json.dumps(data['pooled_raw_status'], sort_keys=True) + '.',
        'Stored timing censor reasons, unchanged: ' + json.dumps(data['pooled_censor_reasons'], sort_keys=True) + '.', '',
        '## What this supports', '',
        'Clean operation looks encouraging in the observed subset, and no forbidden effect was recorded. Faulted runs show substantial limits: incorrect final business states, missing supported final updates, two recorded unsupported decisive exposures and unresolved exposure grades. A backed-up execution is evidence retained, not a passed research outcome.', '',
        'The corrective-delivery challenge distinguishes an ordinary final update from full corrective communication: receiving a corrected statement does not establish explicit withdrawal of previously invalid content. TRUE/FALSE/UNKNOWN are retained separately. Internal repair records alone do not earn external delivery credit.', '',
        'The data are useful for a research report because failures and limits are visible. They do not yet demonstrate that P1/P2 outperform the competent baseline, that the study will meet its confirmatory gates, or that a paper is publishable. No adverse result is excluded, and no favorable stopping rule is introduced. The complete frozen comparison and missingness analyses remain for the final study.', '',
        '## Integrity and scope', '',
        f"Downloaded compressed results SHA-256: `{verification['gzip_sha256']}` ({verification['gzip_bytes']} bytes).",
        f"Uncompressed JSON SHA-256: `{verification['json_sha256']}`.",
        'Every included export matched its sealed slot-ledger hash or the retained exact-145 manifest commitment. Every backup receipt matched the consistent master snapshot and its pinned version reference. This task reused prior archive qualification; it did **not** download or freshly verify every full archive or S3 object. The result is a verified compact derivative, not a replacement evidence archive.',
        f"Saved voice-evidence labels: {json.dumps(data['voice_evidence'], sort_keys=True)}. These are scripted tone/ACK semantic protocol proxies; they do not establish intelligible real speech, human hearing or comprehension.",
        f"{groups['collection_error_execution_count']} executions recorded collection errors; {groups['recorded_oracle_failure_execution_count']} recorded oracle failures. Missing stored evidence would remain unavailable, never be filled with success or silence.", '',
        'The earlier v2 diagnostic extractor failed its transfer-size bound before publishing a result. That script, request, response and failure are preserved. The narrower v3 transfer completed with finite bounded requests. No application, frozen code, campaign ledger, pause, timing, grade or research scenario was changed.', '',
        '## Files', '',
        '- `execution-results.csv`: one row per backed-up original, identities, saved endpoint values and export SHA-256.',
        '- `saved-results.json.gz` / `saved-results.json`: compact derivative with pinned references, pooled counts, original timing categories and snapshot commitments.',
        '- `verification.json`, `download-manifest.json` and request/response files: retained transfer and verification evidence.',
        '- `descriptive-diagnostics.json`: pooled family counts and adverse/failure record locators for later review; no rankings.', '',
        'Recommendation: retain the unchanged campaign and finish its planned observation/backup sequence while guards pass. Interpret final paired effects, clean tolerance and unknown bounds only under the frozen analysis; do not repair a studied arm or tune the experiment based on this interim view.',
    ]
    with (HERE / 'REPORT.md').open('x', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    inventory = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()}
    with (HERE / 'result-inventory.json').open('x', encoding='utf-8') as f:
        json.dump(inventory, f, indent=2)
    print(json.dumps({'counts': data['counts'], 'unique_inputs': data['unique_completed_inputs'], 'complete_sets': data['complete_three_arm_sets'], 'values': values, 'groups': groups, 'strata': data['unique_inputs_by_stratum'], 'raw_status': data['pooled_raw_status'], 'censor_reasons': data['pooled_censor_reasons'], 'verification_failures': data['verification_failures'], 'seconds': verification['controller_seconds']}, indent=2))


if __name__ == '__main__':
    main()

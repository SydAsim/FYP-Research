"""Render measured review evidence, retaining previous feasibility records."""
from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from prepare_candidate import HERE

previous = json.loads((HERE / 'feasibility-final.json').read_text())
shutil.copyfile(HERE / 'feasibility-final.json', HERE / 'feasibility-before-packaging.json')
now = datetime.now(UTC)
elapsed = (now - datetime.fromisoformat(previous['at_utc'])).total_seconds()/3600
rate = .1197 + .005 + 160 * .096/730
previous['conservative_original_elapsed_clock_cost_usd'] += elapsed * rate
previous['explicit_resources_cost_usd'] += elapsed * 160 * .096/730
previous['at_utc'] = now.isoformat()
finish = now + timedelta(hours=previous['reviewed_allowance_remaining_hours'] + 2)
previous['allowance_finish_utc_if_started_now'] = finish.isoformat()
previous['review_and_deployment_slack_hours'] = (datetime.fromisoformat(previous['conservative_guard_time_utc']) - finish - timedelta(minutes=30)).total_seconds()/3600
previous['status'] = 'FAIL_DO_NOT_DEPLOY'
(HERE / 'feasibility-final.json').write_text(json.dumps(previous, indent=2))
focused = json.loads((HERE / 'focused/results.json').read_text())
size = max(p['bytes'] for p in focused['three_final_code_readbacks'].values())
floor = previous['all_version_evidence_bytes'] + (1418 + 2) * size
storage = {'existing_all_version_bytes': previous['all_version_evidence_bytes'], 'measured_metadata_archive_bytes': size, 'illustrative_remaining_metadata_and_two_prelaunch_backups_bytes': floor, 'cloud_cap_bytes': previous['cloud_cap_bytes'], 'remaining_bytes_before_slot_payload_and_growth': previous['cloud_cap_bytes'] - floor, 'not_a_guarantee': 'Calibration has no live slot payload, PostgreSQL dumps, audio or ongoing ledger growth. These add bytes. Existing cap must stop admissions when reservations do not fit.'}
(HERE / 'storage-projection.json').write_text(json.dumps(storage, indent=2))
(HERE / 'unsuccessful-preparation-notices.json').write_text(json.dumps({'retained': ['attempt1 run.json exit124, first roundtrip PASS then timeout', 'attempt2 run.json exit124, five controls PASS then timeout', 'both preservation copy timeouts and bounded local stop request timeouts; actual containers later verified exited', 'initial mypy 3 errors from expected dictionary shadowing str argument; corrected by local rename; final checker PASS', 'PowerShell brace-list parsing and inline Python quoting errors occurred before any calibration or AWS change'], 'outcomes_replaced': False}, indent=2))
text = f'''# v6 continuation review candidate — backup closure/order only

**Review package locally qualified; deployment is blocked by unchanged cost feasibility.**
No AWS start, freeze, acceptance, launch, research scenario, live application stack,
pilot or observation window was performed. Candidate/archive exact hashes are in
`candidate-package.json`; `final-verification.json` covers archive/source closure.

## Cause and narrow changes

Frozen v5 demanded readiness and CONTINUATION_LAUNCH before the prelaunch backup
could prove readiness. Its copier omitted restart-boundary.json/restart-history
and the per-slot master lacked the retained receipt closure. Existing reproduction
is retained in parent-v5-provenance/backup-gate-result.json, not rerun.

| File | Runtime difference and invariant |
|---|---|
| storage.py | Explicit PRELAUNCH/COMPLETE metadata. Carry complete restart history, retained backup receipts, cloud controls and real pause/preparation evidence. Mandatory metadata cannot silently disappear. Archive hashes now use one forward read, needed to verify expanded closure within bounded controls. Upload/inventory retry behavior unchanged. |
| postflight.py | After original bounded version-specific transfer/extraction, invoke the actual metadata/readback verifier. Missing or corrupt restart/history/readiness/receipt metadata rejects. Partial output is retained. |
| prelaunch_backup.py (new) | Existing authority verification before backup; versioned upload + independent readback before proof. Complete phase requires genuine launch/readiness and earlier backup proof. No signing or pause release. |
| handover.py | Version/parent provenance binds frozen v5. Boundary release requires both backup proofs before existing clock/timer/pause checks. Existing full authority requirements remain. |
| closed_restart.py | New v6 source/receipt/version paths only. Its v4 stopped-snapshot parent still correctly identifies the actual 82-original source. No row/order/sidecar/import changes. |
| test_backup_closure.py (new) | Fixed metadata-only controls; historical signed/public records are copied as inert test inputs, not applicable v6 authority. |

Exact unified diff: `runtime.diff`. Added public calibration records and parent
provenance are explicitly inventoried. No private signing key is packaged.
Application, migrations, fixtures, refusal/permissive-response guards, ledger
snapshot fix, arms, endpoint/oracle/analysis rules and 600s windows are byte-identical
to v5. No earlier frozen package or report is rewritten.

## Honest prelaunch sequence

Reviewed acceptance/freeze and separate deployment authority → external live gates
and closed metadata import → PRELAUNCH backup/readback without new readiness or
launch receipt → genuine evidence-backed readiness and signed launch receipt →
COMPLETE backup/readback → active reviewed watchdog/timer and final resource/cost
checks → verify both proofs and release only the import pause → standalone service.

The copier's phase is an archive distinction, never admission authorization.
Readback tests establish metadata integrity; historical receipts cannot authorize
a new candidate/host. No new main readiness/launch record was manufactured.
Exact future commands and failure rules: `REUSE_RUNBOOK.md`.

## Bounded local evidence

Pinned Linux image `sha256:5faee27d3793882b26aa166de48fc26d7939710ac9435b0fe7f988c8765497d8`:
Python 3.12.13 / SQLite 3.46.1 / botocore 1.43.108. Network disabled; no AWS client
writes. Planned 12 controls, two 300s full-suite attempts. Both exceeded that
limit and are retained as **TIMEOUT**, not PASS. Attempt1 completed one control;
attempt2 completed five, including all three actual backup/upload/readback
roundtrips and both missing restart member rejections. Copy/stop-client timeouts
are retained; all local control containers later verified exited and retained.

A declared fixed completion used those independent stored objects, without
rebuilding large archives or rerunning scenarios: seven remaining checks and
three final-code readbacks passed in **{focused['wall_seconds']:.3f}s** under a 180s cap.
Two final missing-handover copier guards passed under a separately declared 60s
cap. **14 distinct focused controls demonstrated**; the full pytest suite itself
did not finish. The only subsequent verifier typing rename is bound by strict
AST equivalence; the final missing-handover predicate was explicitly tested on
pinned Linux. Every runtime difference is documented, not hidden by a PASS label.
Final ruff and targeted configured mypy: PASS (five runtime modules).

| Actual roundtrip | Archive SHA-256 | Bytes |
|---|---|---:|
| PRELAUNCH | {focused['three_final_code_readbacks']['prelaunch']['sha256']} | {focused['three_final_code_readbacks']['prelaunch']['bytes']} |
| COMPLETE master | {focused['three_final_code_readbacks']['complete']['sha256']} | {focused['three_final_code_readbacks']['complete']['bytes']} |
| COMPLETE per-slot (metadata only) | {focused['three_final_code_readbacks']['slot']['sha256']} | {focused['three_final_code_readbacks']['slot']['bytes']} |

All three readbacks passed both existing continuation verifiers with exactly
1,500 identities, 82 backed-up and 1,418 planned, unchanged notices/receipts and
first/second sidecars. PRELAUNCH contains no new readiness/launch. Normal output
contains genuine historical late records solely for closure testing. Corrupted
history/archive, missing boundary/history/readiness/launch/handover and improper
prelaunch late records reject. The failing-authority stub proves ordering only;
no test stub grants authority or proves a live host is ready.

Evidence: `focused/results.json`, both attempt run logs, qualification plans,
`final-two-check-results.json`, `static-final.json`, `qualified-source-closure.json`.
Compressed independent test objects are retained under `E:/p8v6/retained-controls`;
qualification source archives and partial outputs/containers remain independently
retained. These are calibration evidence, never main outcomes.

## Preservation

Frozen v5 package `805d905760ff2565ef4f3813c0062b073d210de4e10b1fee35d3dfd2377c3627`;
freeze `95d48df4494ad022808c172238596f7761582781108b3f9f982088f8a50dfe26`.
All 2,343 parent source files and 2,351 signed frozen members checked before and
after. Current stopped snapshot equals all 1,500 pinned rows and its complete
notice chain verifies. Supplemental 596-member archive SHA remains
`57fa8f85c017bee13fd1325f685b928d96ba129db1b6175a4962895791ba9392`.
Its S3/local/root copies and every original archive/grade remain retained; no
grade/status/outcome replacement. First two raw FAILED statuses remain original.
Next is sequence 83 B3 attempt1 ID `01a11705-11f1-792b-ae1e-36bfc6773842`.
Final read-only AWS check: `i-057344e5372faf62f` stopped, encrypted retained root
`vol-09dbb42bbf607f5de` intact. No S3/root evidence or resource was deleted.

## Feasibility — {previous['at_utc']}

Remaining allowance **{previous['reviewed_allowance_remaining_hours']:.6f}h**, preparation
2h and shutdown 0.5h unchanged. Continuous historical cadence projects 244.978h,
but is not substituted for the reviewed allowance; original-clock costs include
paused time, previous spending, retained storage and the $1.25 reserve.
Current Sydney prices and FREE/ACTIVE credits were read at
{previous['AWS_measurements_at_utc']}; no plan upgrade or paid speech/model service.

Conservative projected committed cost **US${previous['conservative_original_elapsed_clock_cost_usd']:.6f}**
exceeds the unchanged **US$55 admission guard**. Explicit resource estimate is
US${previous['explicit_resources_cost_usd']:.6f}, but it does not override the accepted
conservative guard. US$65 total remains unchanged. Latest fitting preparation
start was **9 Oct 12:48:54.676567 UTC**, now passed. Original **22 Oct 2026,
15:24:23.810674 UTC** remains; time alone fits, cost policy does not.
**Do not propose deployment under current unchanged limits.** No clock/allowance
reduction or automatic increase is used to manufacture a passing estimate.

Expanded metadata-only backup is about {size / 1024**2:.3f}MiB. Illustrative remaining
metadata plus two preparation backups and existing evidence require
{floor / 1024**3:.3f}GiB of the unchanged 30GiB cap, before real slot payloads,
database dumps, audio, ledger growth and other retained versions. This is a lower
bound, not storage qualification for finishing all slots; capacity failures must
pause admissions. Local metadata tests do not measure full campaign overhead.

## Review verdict and concrete remaining requirements

- PASS: narrow closure/order implementation, actual local roundtrips, negative
  controls, source closure and immutable parent preservation.
- PASS: AWS kept stopped; 82 originals / 1,418 pending unchanged; no freeze/launch.
- LIMITATION: two retained whole-suite timeouts; final coverage was completed by
  bounded focused checks. Metadata-only surrogate does not qualify live AWS
  permissions, a new boot or real S3 delivery performance.
- BLOCKED: unchanged $55 feasibility guard no longer fits the reviewed allowance.
  No deployment recommendation or launch action while this remains failed.
- NOT DONE: exact-package acceptance/freeze; separate launch authorization and
  all actual readiness/resource/backup/watchdog/timer gates, if feasible later.
- Existing retained-root decision remains **11 Oct 2026, 09:33:51.252814 UTC**;
  no retention clock reset or deletion authorization is inferred.

No research extension or study change is proposed. No migrations added.
Passing local controls does not guarantee an error-free campaign.
'''
(HERE / 'REPORT.md').write_text(text, encoding='utf-8')
print(json.dumps({'status': previous['status'], 'cost_usd': previous['conservative_original_elapsed_clock_cost_usd'], 'storage': storage}, indent=2))

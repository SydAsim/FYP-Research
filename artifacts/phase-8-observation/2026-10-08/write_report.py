from pathlib import Path
from datetime import datetime,timedelta,timezone
import json,hashlib
HERE=Path(__file__).resolve().parent;ops=HERE.parents[1]/'phase-8-continuation-deployment/v3'
def read(p):return json.loads(p.read_text())
stop=read(HERE/'stopped-state.json')
anchor=read(ops/'observation-stop-host-request.json')['at_utc']
due=datetime.fromisoformat(anchor)+timedelta(hours=48)
pk=timezone(timedelta(hours=5))
with (HERE/'retention-clock.json').open('x') as f:json.dump({'basis':'CONSERVATIVE_STOP_REQUEST_BEFORE_VERIFIED_STOP','stop_requested_at_utc':anchor,'decision_due_utc':due.isoformat(),'decision_due_pakistan':due.astimezone(pk).isoformat(),'supersedes_verified-time-derived_due_in_stopped_state':True,'new_disk_deletion_authorized':False},f,indent=2)
text=f'''# Phase 8 descriptive observation — 8 October 2026

## Operational finding and resource state

The campaign paused at **8 October 2026, 18:46 Pakistan time** (13:46 UTC), following the watchdog's `LEDGER_TRANSITION_DRIFT` report during slot 38's backup transition. The runner completed that original's backup/retirement and then exited with `PAUSED_ADMISSIONS`. No slot 39 was admitted. Progress inspection found 38 BACKED_UP, 1,462 PLANNED, zero RUNNING/EXPORTED. This includes the two historical originals, rather than 38 new inputs.

After read-only inspection and independent snapshot preservation, fresh host `i-002b63326e1566005` was **verified stopped at {datetime.fromisoformat(stop['verified_at_utc']).astimezone(pk).strftime('%d %B %Y, %H:%M:%S')} Pakistan time**. Root `vol-04fa91b4840804295` remains intact; no instance, root disk, cloud evidence or local evidence was deleted. No service was restarted, no original replayed, no pause bypassed, and no source, fixture, grade or analysis rule changed. This shutdown follows the existing campaign defect/shutdown authorization and limits idle compute expense.

The retained root still incurs storage cost. A retention decision is required **by {due.astimezone(pk).strftime('%d %B %Y, %H:%M:%S')} Pakistan time**, using the conservative stop-request anchor. The earlier `stopped-state.json` records an initial due time calculated from verified stop; `retention-clock.json` explicitly preserves and corrects that derivation. The root has no deletion authorization.

## Descriptive outcomes only

There are **13 distinct inputs with any retained execution**, of which **12 have all B3/P1/P2 executions backed up**. One additional clean input has P1/P2 observations while its B3 original (sequence 39) is untouched. This is **38/1,500 original executions (2.53%)**, not 38/500 independent inputs. Full paired-input coverage is 12/500 (2.4%). No significance tests, confidence intervals, arm ranking or early-stopping efficacy analysis was performed.

For the 12 complete matched inputs, all recorded endpoint values agree across arms:

| Recorded endpoint | B3 | P1 | P2 |
|---|---:|---:|---:|
| Correct final business state | 12/12 | 12/12 | 12/12 |
| Correct final update | 11/12 | 11/12 | 11/12 |
| Unsupported exposed claim recorded | 0/12 | 0/12 | 0/12 |
| Incompatible stale exposure recorded | 0/12 | 0/12 | 0/12 |
| Clean task success, applicable clean inputs | 9/9 | 9/9 | 9/9 |

The shared missing update is input `p8v4-0484`, resource-only evidence unavailability. All arms reach correct business state but withhold final confirmation when supporting evidence is unavailable. The B3/P1 raw FAILED exports and accepted timing sidecars remain separate and unchanged. P2 sequence 3 also retains raw FAILED while its qualified classification is EXPECTED_EVIDENCE_REFUSAL, predicate UNKNOWN, retryable false and retry_performed false. This is a research outcome, not proof of infrastructure failure or business failure.

Across all 38 retained executions, business state is TRUE in 38/38, correct final update TRUE in 35/38, unsupported exposure FALSE in 38/38, and stale exposure FALSE in 38/38. Arm counts differ (B3 12, P1 13, P2 13); these aggregate denominators must not be used to rank arms. Explicit retraction and the three corrective-delivery endpoints are NOT_APPLICABLE throughout this observed prefix. Thus this prefix does **not** yet test durable corrective delivery after exposure/restart, and provides no evidence of proposed-arm superiority. It is mostly clean cases plus resource-only, hidden-commit/reordered-response, and pre-commit-delay fixtures.

The 36 continued originals retained full-window completion: finished 600.207–600.455 seconds after the final external-request anchor. No recorded collection errors, unexpected permissive-response errors or oracle failures appeared in these exports. This reports recorded evidence, rather than assuming all possible gaps were impossible. The evidence remains scripted protocol/playback testimony; it does not establish intelligible speech exposure or human understanding.

## Stop evidence and unresolved cause

The last original, sequence 38 P1 `01a11705-11f0-77aa-ac63-65d2459723f4`, completed ordinary research collection and verified backup. Stop notices place the watchdog drift report just after its BACKED_UP transition. The current independent read transaction reports SQLite integrity `ok`, a valid complete notice hash chain, zero row-versus-latest-transition mismatches, and all 38 backup receipt hashes matching their rows. All 38 local archives passed hash/gzip validation and pinned cloud version checks.

This does not disprove the earlier stop or authorize resumption. The exact transient reader state was not retained by the watchdog. Frozen `controls.py:460` checks notices and slot rows in separate SELECTs without an explicit enclosing read transaction. A reader observing different committed snapshots across those queries is a **candidate explanation**, consistent with the timing and currently consistent ledger; it is not yet a reproduced root cause. No correction was implemented. A bounded local investigation of that transition-read boundary is required before a reviewed continuation decision. The process also remained running at the host level after admissions stopped; the frozen watchdog shuts down at its hard limit rather than immediately on every protocol pause. Manual authorized shutdown was therefore performed after preservation. These instrument/operations issues do not change the research outcome grades.

## Independently retained evidence

- S3 snapshot key: `exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/observations/257cdc762459f07c67f132ed0141021dd38430a9f5cb2040cd3479e3e7d37905.tar.gz`.
- Version: `eal8yi_Nd_ELncozskW0Si5f5ELTr.b9`; SHA-256 `257cdc762459f07c67f132ed0141021dd38430a9f5cb2040cd3479e3e7d37905`; 3,515,435 bytes.
- Local archive and verified member extraction: `E:/FYP Project/p8-observation-20261008-1/`.
- Includes consistent master metadata snapshot, 38 raw exports, 38 backup receipts, original history, pause and notices, and service-stop logs. It is a diagnostic evidence package, not a replacement master or revised outcome package.
- `descriptive-patterns.json` contains the counts and complete matched-input IDs; `evidence-readback.json` pins verification; `stopped-state.json` and `retention-clock.json` record resource/retention state.

The first inspection attempt failed when it tried an original historical receipt's obsolete local pathname on the fresh host. Its partial snapshot and SSM failure remain. A separate inspection attempt used the reviewed retained-original archive locations and unchanged pinned hashes; no original receipt was rewritten. A local command-construction error is also retained in conversation output; it performed no AWS action. No unsuccessful research outcome was replaced.

**Recommendation:** operational and descriptive observation is useful, but keep the campaign stopped until the ledger-read stop is investigated under a separate bounded local scope. Keep the existing 22 October 2026 15:24:23.810674 UTC deadline and US$55/US$65 guards. No restart, launch, new host or budget/clock reset is authorized by this observation report. These early ties cannot determine publication strength or final comparative effects.
'''
with (HERE/'REPORT.md').open('x',encoding='utf-8') as f:f.write(text)
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()}
with (HERE/'inventory.json').open('x') as f:json.dump({'kind':'READ_ONLY_DESCRIPTIVE_OBSERVATION_AND_AUTHORIZED_STOP','files':files},f,indent=2)
print({'report':str(HERE/'REPORT.md'),'retention_decision_due_pakistan':due.astimezone(pk).isoformat()})

# Research readiness remedies v2 — pre-execution plan

This is a revision of the instrument, not Phase 8. Historical Phase 7 v1 source,
manifests, grades, traces and reports remain unchanged and independently hashed.
New source changes intentionally cause the old working-tree drift guard to fail;
the old archive remains the executable authority for reproducing v1.

## Files and invariants

- `packages/speech_policy/phase4.py`: semantic decisive exposure and explicit repair capability.
- `apps/api_controller/phase4_playback_service.py`: uniform capability checks, delayed/duplicate ACK safety.
- `apps/api_controller/phase1_service.py`: compare exposure against the new accepted target.
- `apps/api_controller/phase3_verification_service.py`: durable raw ordinary reads available to every arm, bounded repeated-reschedule evidence.
- `apps/api_controller/phase4_audio_service.py`: enforce repair synthesis capability.
- `research/provider_simulator/main.py`: optional oracle-only truth credential; no controller access credential.
- `apps/durable_worker/repair.py` and a new migration: durable leased repair discovery, idempotent scheduling, no completion without ACK.
- `apps/durable_worker/main.py`: documented recovery consumer entry point and startup loop.
- `research/oracle/readiness_v2.py`: externally observable arm-neutral outcomes; independent truth and available observations.
- `research/remedies/`: preservation, pre-fix reproduction, predeclared plan, runner, verifier and reports.
- `research/fixtures/readiness_v2/`: new fixture version; no pilot fixture alteration.
- `tests/unit/test_readiness_v2.py`, PostgreSQL remedy tests: construct properties and actual transaction/recovery evidence.
- Revised readiness artifacts under `artifacts/research-remedies/v2/`; no Phase 7 report overwrite.
- `compose.yaml`: enable the documented repair consumer at application startup.

Recovery entry point: `REPAIR_DELIVERY_ENABLED=true` starts the durable worker's
PostgreSQL consumer. `python -m apps.durable_worker.repair` is its bounded one-pass
equivalent; it discovers obligations itself. Outstanding repair requires a current
PRESENT operation with applicable evidence. It resumes a generated/queued segment
with stable command IDs, publishes the deliverable, and waits for actual client
ACKs. Deadline/exhausted delivery errors create durable human handoff instead of
marking speech complete. No automatic ACKs, WebRTC reconnection or provider writes
are fabricated by this consumer. A failed consumer makes worker readiness fail.

## Outcomes

Separate final business correctness (external target including end/zone/resource),
truth support at recorded publication and decisive exposure, applicable ordinary
evidence available by those moments (baseline receipts are unnecessary), stale
incompatible exposure after durable acceptance, completed correct final update,
explicit retraction of previously exposed incompatible content, and internal
obligation persistence/completion. Internal rows and arm labels never determine
observable outcome credit. Missing observations, timestamps or ACKs are UNKNOWN.
No acknowledgement implies hearing or comprehension.

Record both external correction-script anchor and PostgreSQL accepted-at anchor;
use accepted-at for stale exposure. Claim support and staleness are different
endpoints. Earlier supported exposure later requiring update is not retroactively
unsupported. A late ACK uses its recorded client exposure time, not arrival time.
Event receipt order remains separately recorded. Semantic compatibility is judged
against the external revision schedule, not merely revision numbers.

## Voice limits

All 18 planned executions use scripted clients, typed intents and deterministic
tone WAVs. Word positions are equal-duration template metadata, not acoustic forced
alignment. Introductory two-word exposure is a separate control. The decisive case
acknowledges eight words through the AM/PM time token (not just the introductory
"Your maintenance" or the confirmation verb). A changed date or zone has a later
predicate boundary. These measure protocol semantic proxies and
must never be reported as actual spoken-content exposure. Actual local voice from
v1 remains historical and is not reused as new voice evidence.

## Planned exploratory set (freeze before first execution)

Six independent *specified fixture families*, each once under B3/P1/P2: 18 slots.
No repeats increase independent n. Identifiers/date changes do not establish
population independence. No winner is predicted. Preserve B3 normal safeguards.

1. E1: issue verification; accept correction; attempt old outcome through normal arm interface; recover and update.
2. E2: publish current audio; named hold before STARTED; external version-only change with identical appointment time; attempt STARTED; accept updated target and recover. This isolates evidence-version applicability from factual truth. Retain any provider-version conflict/handoff instead of forcing completion.
3. E3: start old audio; decisive progress generated before correction, withheld until after acceptance; duplicate/delayed ACK checks; recover and update.
4. E4: full old exposure; correction accepted; obligation persists; worker process stops before delivery; new worker discovers and schedules from PostgreSQL.
5. E5: old full exposure; corrected start; missing COMPLETED; logical client disconnect/reconnect; pending-state observation; deduplicated completion.
6. E6: old full exposure; correction r2; repair begins; accepted r3; delayed r2 completion must not close latest repair; recover and update r3.

The E4 process restart must use the application recovery consumer; replay does not
pass an obligation ID to that consumer. B3/P1 have no repair consumer capability;
their ordinary final-update path still runs after restart. Disconnect E5 is an
explicit scripted client outage, not a measured WebRTC network disconnect.

## Comparable effective budgets

- Provider adapter HTTP: 30 s; runner HTTP: 40 s; scheduler-controller HTTP: 15 s.
- Reconciliation attempts: 8; operation lease: 180 s.
- Drain: at most 30 passes, each processing existing operations; record actual steps.
- Verification TTL: 30 s; repair lease: 30 s; recovery process bound: 40 s.
- Recovery: one scheduling attempt per invocation, with deterministic command IDs;
  retry reuses IDs and existing segment. No automatic client ACK or claim completion.
- Every fixture names each barrier explicitly; no timing sleep creates a race.
- Every planned slot is retained on failure/timeout; diagnostics are separate UUID
  attempts, not replacements for outcomes. No confirmatory tests/power claims.

## Exploratory analysis rules (predeclared)

Use a fixture-family row paired across B3/P1/P2, not 18 independent samples.
Record generator family, no speaker identity (tone), and all UNKNOWN/MISSING
outcomes separately. Report TRUE/FALSE/UNKNOWN/NOT_APPLICABLE counts and the first
recorded blocking mechanism. Do not impute missing ACKs as safe silence, collapse
UNKNOWN into failure/success, exclude provider conflicts, or calculate a winner,
population effect, p-value or noninferiority conclusion from these six families.
Debugging attempts are retained with separate classifications and never replace
planned executions. The source and audio bytes are archived and hash checked.

Legacy `research/oracle/grade.py` is retained for offline v1 verification only;
its arm-dependent repair endpoint is invalid for new measurements. New results
must use `research.oracle.readiness_v2`. Legacy live P8/P9 generators describe the
old intro-only fixture and are not admissible revised-instrument tests. Their
source remains in the v1 archive; no old grades are reinterpreted as v2 outcomes.

## Admission to Phase 8

Require arm-neutral grading properties; real PG repair isolation, ACK and restart
checks; honest retained exploratory results; explicit remaining media/recovery
limits; new source/metric/fixture hashes; predeclared inference, cluster provenance,
missingness and eligibility. The 100/200/100/100 allocation remains provisional.
Materializing and freezing 500 genuinely specified inputs and any missing analysis
implementation must precede the main campaign. This remedy work does not execute it.

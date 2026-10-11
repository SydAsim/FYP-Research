# Phase 8 study-design candidate v4

**Verdict: reviewable candidate; not frozen and not authorized to start the main campaign.**

The new bank contains 500 distinct inputs and 1,500 unstarted B3/P1/P2 slots.
All 450 preserved historical files have unchanged SHA-256 hashes; no files were
added inside the preserved artifact directories. No Phase 8 outcome was measured.
No application behavior or migration was changed. Local PostgreSQL, scripted
intent/tone playback and independent simulator truth supplied the calibration.

## Decisions and design-blocker disposition

| Finding | Candidate decision | Evidence / limitation |
| --- | --- | --- |
| Purposive recipe representatives did not define a caller sampling frame | Draw independent contexts and recipes within a declared fixed protocol frame; estimate its standardized risk difference | `candidate.json`, 500 inputs; no inference to unseen recipes or callers |
| Ten clean representatives were insufficient | Allocate 300 clean, 100 hidden commit, 60 playout, 40 other boundary inputs | Exact paired clean calculation below; assumptions require review |
| Full factor model was aliased | Saturated arm × eligible-stratum marginal model; paired input covariance and exact component bounds | Correction rank 9/9; hidden and clean each 3/3 |
| Final update did not establish corrective delivery or withdrawal | Separate supported delivery after challenge, complete corrective communication, conditional explicit withdrawal and internal obligation telemetry | Ordinary baseline updates get identical credit; 33 recovery inputs |
| Hook names alone were treated as sufficient | Separate real PG calibration and causal evidence ledger | All 150 recipe/arm boundary slots now have qualifying evidence; original incomplete attempts remain |
| Fault labels could describe an inert injector | Replace unsupported duplicate-after-response with actual duplicate request delivery; qualify reordered ACK relative to revision acceptance | Two-provider-response permutation remains untested; reserved cache flush is a negative control |
| Missing/late completion could be misinterpreted | Preserve UNKNOWN and cap analysis at final external script +600s, using both client and server arrival times | Actual long-window probe remains unresolved without a completion ACK |
| Recovery could be manually fabricated | Exercise P2 native consumer discovery after worker PID replacement, without supplying an obligation ID | Baseline receives its ordinary response opportunity; comparative unattended superiority is unproven |

Detailed design: [docs/12_PHASE8_CANDIDATE_V4.md](../../../docs/12_PHASE8_CANDIDATE_V4.md).
Machine-readable decisions: [review-decisions.json](review-decisions.json).

## Sampling and precision

The target is conditional performance over the 50 fixed recipes and declared
context generator. Recipe selection is uniform within stratum; dates, issues,
times and correction offsets are independently generated subject to recipe
constraints. The actual bank represents all 50 recipes and has 500 distinct
semantic hashes. Pairing arms does not increase n. Recipe labels are fixed support
labels, not randomly sampled families. No repeated speaker or recording units
exist in this instrument.

Inputs are shuffled using seed 8042043. Twenty fixed temporal blocks of 25 support
descriptive block-omission sensitivity; they do not establish independent host
batches. Primary inference needs the declared conditional-input and stationarity
assumptions. Per-stratum pairing, known/missing denominators and worst/best bounds
are retained. Structural N/A is excluded before model construction. Missing pairs
block the candidate's clean noninferiority decision; a successful rerun cannot
replace an unsuccessful primary attempt.

At n=300 and the unchanged absolute 5pp clean margin, conservative exact paired
win/loss bounds have these calculated powers:

| Discordance | True P2−B3 difference | Power |
| ---: | ---: | ---: |
| 3% | 0pp | 96.01% |
| 5% | 0pp | 80.39% |
| 5% | −1pp | 55.99% |
| 10% | 0pp | 44.80% |

These are design assumptions, not estimated nuisance rates. This is **not** an
80%-powered design for all plausible rates. At 5% discordance, the normal
precision illustration is ±2.53pp; the all-ties exact lower bound is still finite
(approximately −1.22pp). The 33 recovery inputs have limited rare-event sensitivity:
at 10% discordance a normal illustration is approximately ±10.8pp. Review must
accept these limits or commission another candidate allocation/extension before
freeze. No tolerance or sample size may be changed in response to main outcomes.

Co-primary P2−B3 claims use Bonferroni across correction and hidden-commit exposure.
Correction is standardized with weights .5/.3/.2 across its three eligible strata;
it does not use a pooled exact McNemar test for the weak average-effect null.
Single-stratum paired tests are diagnostic. The ten declared secondary comparisons
use Holm; withdrawal-only and repair telemetry remain descriptive. Exact bounds
remain nondegenerate when all observed outcomes tie.

See [analysis-design.json](analysis-design.json), [execution-order.json](execution-order.json)
and [inputs.json](../../../research/fixtures/phase8_design_v4/inputs.json).

## Calibration ledger and failures

There were **150 planned recipe/arm executions**, **3 smoke executions** and
**25 amendment executions**: 178 total, none counted toward the 500-input study.
Their raw driver statuses are 139 COMPLETED and 39 FAILED. The latter comprise
36 normal-path HTTP 409 refusals and three original timezone validation failures.
They were retained, not recoded as successful business corrections. Every one of
the 178 final trace exports passes the revised oracle adapter's evidence validation.

Qualification assesses the boundary separately from outcome success. Safe refusal
can demonstrate a fault/check while leaving correction false or unknown. Across
the original and amended calibration evidence, all 50 recipes × three arms have
qualifying boundary evidence. Historical attempts retain their original grading,
status and driver hash; amended runs qualify hooks rather than replace primary data.

The amendments fixed timezone offsets in version injection; placed resource-only,
cache-loss, 5xx, partial-effect and duplicate checkpoints before correction/reconciliation;
added the missing logical reconnect and genuinely withheld R2 completion; and
integrated the observed recovery deadline into the native restart path.
Publication timestamps are checked against that deadline; collector delay cannot
turn publication after the deadline into a timely recovery. A targeted boundary
test and fresh native P2 recovery trace verify this rule.

Raw provider event exports accompany independent truth, accepted/scripted UTC
anchors, HTTP send/receive times, playback records, audio hashes and checkpoints.
[calibration-qualification.json](calibration-qualification.json) links every attempt;
[calibration-grades.json](calibration-grades.json) contains revised measurements.
Native application Redis outage and two-response network permutation are **not**
qualified by the companion-cache and held-ACK controls. The proposed frame and
claims explicitly limit those recipes to their exercised mechanisms.

## Budget qualification

| Budget | Boundary evidence | Scope |
| --- | --- | --- |
| Provider HTTP 30s | Actual socket timeout | Adapter timeout, not business completion |
| Scheduler HTTP 15s | Actual socket timeout | Controller port boundary |
| Driver HTTP 40s | Actual socket timeout, retained transport error | Calibration driver |
| Provider barrier 120s | 120.297s, HTTP 500, independent truth empty | Actual unreleased BEFORE_COMMIT barrier |
| Core lease 180s | Competitor excluded; natural expiry permits reclaim | Real PG; no timestamp edit |
| Repair lease 30s | Competitor excluded; natural expiry permits discovery | Real PG; separate from process-crash proof |
| Reconcile 8 attempts | PG job exhausts to HANDOFF | No completion inferred |
| Drain 30 passes | Nonprogressing adapter raises at the bound | Artificial adapter test; not a transaction test |
| Recovery 40s | 40.390s with consumer intentionally paused | Real PG observation guard; restart happy path also uses guard |
| Observation 600s | 601.641s collector completion, deadline retained | Late collection is capped at external request +600s in grading |
| Permit TTL 30s | Naturally expired permit rejected with HTTP 409 | Real PG publication guard |

[budget-qualification.json](budget-qualification.json) links measurements and limits.
The first combined window probe's parallel barrier branch failed because it read
a summarized history record as a full operation. Its 40s/600s observation components
finished and were retained. A separate corrected full-PG-operation barrier probe
passed. The source was fixed; the unsuccessful attempt and original source archive
remain available. This failure is not hidden by the successful amendment.

## What the comparisons establish

| Boundary | First mechanism / result |
| --- | --- |
| Verified stale claim attempt | B3's current-revision check already refuses; P1/P2 also refuse through applicability checks. No additional outcome benefit follows from the tie. |
| Resource version changes after publication | B3's revision-only start check permits the scripted start; P1/P2 apply evidence freshness and reject it. This is protocol protection, not proof that a human heard nothing. |
| Delayed decisive ACK | Duplicate and reordered acknowledgements remain safe; P1/B3 create no forbidden repair obligation. P2 persists repair as its explicit capability. |
| Worker restart | P2's native consumer discovers PG repair and publishes; ordinary baseline response opportunities also produce updates. Obligation existence alone earns no observable credit. |
| Another accepted revision | The revised client withholds R2 completion before R3 acceptance and delivers it afterward; only applicable supported final correction can satisfy the delivery endpoint. |
| Missing completion | Publication/STARTED does not establish completed delivery. The long-window result remains UNKNOWN and the durable obligation is not declared played. |

Supported conclusions concern protocol applicability, transaction/reconciliation
behavior, typed intent corrections, ACK handling and durable mechanism operation.
The instrument can detect additional recorded protection when an unsafe action
passes baseline checks and a proposed mechanism blocks it. It cannot establish
novelty or superiority from these calibration tests, nor comparative unattended
delivery advantage over a fully deployed competent baseline responder.

Every media artifact here is scripted tone/word-timeline evidence. No actual
spoken-content exposure, intelligibility, microphone processing, hearing,
comprehension or caller-belief conclusion is supported. Those need a separate
speech protocol, intelligible recordings, independent alignment and actual
playback evidence with speaker/recording sampling.

## Files and invariants

| Files | Invariant supported |
| --- | --- |
| `docs/12_PHASE8_CANDIDATE_V4.md` | Prespecified frame, estimand, outcomes, scope and limits |
| `research/study_v4/design.py`, v4 fixture JSON | Distinct main inputs; separate calibration; deterministic hashes |
| `runtime.py`, `calibration.py` | Isolated real PG, fresh resources, named barriers, normal arm paths |
| `oracle.py`, `pipeline.py` | Label-invariant observable outcomes, applicable evidence, UNKNOWN and deadline rules; campaign lock |
| `analysis.py`, `scientific_checks.py` | Identifiable eligible models, paired estimands, clean power and missingness |
| `qualification.py`, `review_package.py` | Every attempt and raw export retained; historical hashes verified |
| `budget_calibration.py`, `window.py`, `window_calibration.py`, `barrier_timeout_calibration.py` | Actual timer/lease boundaries; component failures retained |
| New unit and PG test files | Pipeline lock, label equivalence, late ACK, stale checks and timing boundaries |
| Separate v4 artifacts and source snapshots | Historical/revised distinction; reproducibility without freeze |

Migrations added: **none**. Existing head 0013 was applied to isolated calibration
databases. User application databases, application source, prior fixtures and
frozen manifests were not reset or rewritten. No paid API keys were needed.
Isolated calibration processes were closed and the separately created test Redis
container was stopped. Reproduction of its negative control requires starting
`phase8-calibration-v4-redis`; the user's application Redis was untouched.
The final source snapshot is `candidate-source-final.zip`, with its hash inventory
and snapshot metadata saved separately; it is not a freeze receipt.

## Validation and commands

- Unit/contract regression: **118 passed**; four existing FastAPI lifecycle warnings.
- Separate scientific checks: **7 passed**.
- New PostgreSQL integration regressions: **6 passed**.
- Ruff: passed. Strict mypy: **144 source files passed**.
- Historical hash and directory checks: **450 unchanged; zero changed or added**.
- Main ledger: **1,500 NOT_STARTED, all execution IDs null**.

Commands included:

```text
.venv/Scripts/python.exe -m research.study_v4.calibration
.venv/Scripts/python.exe -m research.study_v4.calibration --cell <amended cell>
.venv/Scripts/python.exe -m research.study_v4.budget_calibration
.venv/Scripts/python.exe -m research.study_v4.window_calibration
.venv/Scripts/python.exe -m research.study_v4.barrier_timeout_calibration
.venv/Scripts/python.exe -m research.study_v4.qualification
.venv/Scripts/python.exe -m research.study_v4.review_package
.venv/Scripts/python.exe -m pytest tests/unit tests/contract -q
.venv/Scripts/python.exe -m pytest tests/integration/test_phase8_candidate_v4_postgres.py -q
.venv-study-design/Scripts/python.exe -m research.study_v4.analysis
.venv-study-design/Scripts/python.exe -m pytest research/study/scientific_checks.py research/study_v4/scientific_checks.py -q
.venv/Scripts/python.exe -m mypy apps packages research
.venv/Scripts/python.exe -m ruff check research/study_v4 tests/unit/test_phase8_candidate_v4.py tests/integration/test_phase8_candidate_v4_postgres.py --no-cache
```

Logs are retained alongside the candidate. `trace-examples.json` identifies a
successful native-recovery trace and an expected stale-claim refusal. The full
ledger includes unsuccessful attempts and unresolved outcomes.

## Remaining decisions and readiness

Review must accept the conditional protocol frame; three-arm scope rather than
the full six-arm extension; 5pp margin and power sensitivity; multiplicity;
baseline response opportunities; limited recovery sample; and observation/batch
scheduling and storage. Full sequential caps could require **250 observation
hours**, so operational scheduling and any safe early-terminal rule must be
reviewed before launch. Early exports cannot be treated as complete horizon data.

Real speech and comparative unattended-delivery conclusions remain outside this
candidate's qualified scope. No claim of a real Redis outage or two-response
permutation is included. The source snapshot and review package are candidates,
not a freeze receipt. Root historical Phase 8 reports remain unchanged.

**Phase 8 readiness: ready for design review within the stated protocol scope;
not ready to freeze or start the main campaign until those decisions are accepted
and the reviewed execution plan is frozen. The 500-input campaign is unstarted.**

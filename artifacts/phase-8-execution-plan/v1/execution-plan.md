# Phase 8 execution plan from candidate v4

**Status: final plan proposed for acceptance; not a review receipt, freeze or launch.**

Prepared 4 October 2026. Documentation and offline measurement only. Application behaviour, fixtures, candidate ledgers and historical evidence remain unchanged. The current calibration entry points reject main IDs, and the v4 analysis pipeline rejects CAMPAIGN evidence. This document does not enable either.

## 1. Confirmed proposed scope

| Inputs | Number | Arms per input | Planned executions |
| --- | ---: | --- | ---: |
| Clean requests | 300 | B3 / P1 / P2 | 900 |
| Hidden commit | 100 | B3 / P1 / P2 | 300 |
| Playback boundaries | 60 | B3 / P1 / P2 | 180 |
| Other boundaries | 40 | B3 / P1 / P2 | 120 |
| **Total** | **500** | **Three paired arms** | **1,500** |

An input is one independent draw from the declared fixed simulator recipe/context generator. Its three executions are a comparison on the same input, not three independent samples. Use the existing bank and saved random order, including each input's arm order. There are 20 fixed reporting blocks of 25 inputs, or 75 executions each. Blocks support order checks; they are not independently sampled populations.

All 1,500 candidate slots are still NOT_STARTED, with no execution IDs. Review receipt and freeze hash are null. No smaller campaign is substituted. No new research extension is added.

## 2. Only the remaining decisions

These are recommendations, not recorded acceptances. Already qualified fault boundaries and budgets are not reopened.

| Decision needing acceptance | Recommended choice | Consequence |
| --- | --- | --- |
| **D1. What population and evidence do we claim to study?** | Accept exactly the 500-input, three-arm fixed protocol frame. Treat tone audio and scripted playback reports as protocol evidence. | Results apply to this simulator/client/version and recipe mixture. They do not establish real caller understanding, speech recognition quality or performance on unseen recipes. |
| **D2. How much clean-request loss is acceptable?** | Keep the proposed absolute 5 percentage point margin and 300 clean inputs. Accept the published power sensitivity. | Calculated clean-gate power is 80.39% at equal risks and 5% paired disagreement; 44.80% at 10% disagreement. These assumptions are not pilot estimates. An inconclusive or missing-data result must stay inconclusive; no margin/sample-size change after outcomes. |
| **D3. Which comparisons and reports are mandatory?** | Accept the existing v4 binary analysis: two primary P2/B3 comparisons, the separate clean gate, and ten adjusted secondary diagnostics. Preserve the existing fixed-frame weights and identifiable arm-by-stratum analysis. Report recorded timing descriptively; make no inferential speed claim. | Primary correction uses 200 inputs and weights 0.5/0.3/0.2; hidden unsupported exposure uses 100. Bonferroni applies to the two primary claims; Holm to the ten secondary diagnostics. Missingness bounds and all planned denominators remain. This avoids promising an unintegrated latency model; it does not remove raw timing evidence. |
| **D4. What does corrective delivery mean?** | Keep the 33 predeclared recovery challenges. Give an ordinary supported B3 update the same credit as a P2 repair segment. Grade supported completion, necessary withdrawal, and internal obligation state separately. | The study can compare observed corrective communication under matched opportunities. A repair row/publication is not completed delivery. Native P2 discovery is mechanism evidence, not proof of comparative unattended superiority. |
| **D5. What schedule and observation window do we accept?** | One live input-arm execution at a time; a fresh service process set for each slot, using dedicated campaign databases and fresh bindings. Observe for the full 600 seconds after the final externally issued request. Keep the saved order. | About 256 hours before reserve; plan 295–308 hours. No concurrency qualification or early-stop rule is required for this chosen serial plan. A faster schedule is not assumed. |
| **D6. How do we preserve incomplete and interrupted results?** | Accept the observation, timeout, storage and recovery rules below, including 25 GiB working capacity and 25 GiB for a separate backup. Keep attempt 1 primary. | Failures, missing reports and late evidence remain visible. A successful rerun cannot erase a failed or incomplete original. Storage is an operating allowance, not a measured database-size guarantee. |
| **D7. What may authorize freezing and launch?** | Accept this plan, then qualify the campaign collector/ledger on separate calibration IDs, freeze the resulting research harness and source/configuration hashes, and obtain separate launch authorization. | Current calibration-only code is not a campaign launcher. The required collector/ledger preparation changes research tooling, not application behaviour. This work remains unperformed here; no guard is bypassed and no main input is executed. |

The collector qualification in D7 is an operational gate already implied by the full-window, scheduling and interrupted-run requirements. It is not another research arm, sampling extension or optional product feature.

## 3. Runtime estimate from retained measurements

Measurements were read from all 178 retained calibration traces: 150 planned executions, three smoke runs and 25 amendments. Their 139 COMPLETED and 39 FAILED driver statuses all remain in [the measurement CSV](calibration-measurements.csv). Neither a failure nor a safe HTTP 409 refusal is turned into business success for this forecast.

| Measurement | Observed value | Interpretation |
| --- | ---: | --- |
| All calibration driver durations | Median **7.68 s**, mean **8.16 s**, maximum **30.33 s** | Short scripted execution and export, usually without a full 600-second watch |
| Clean driver durations | Median **4.21 s** | Does not certify absence of later events |
| Hidden-commit driver durations | Median **8.08 s** | Includes exercised fault/recovery steps, not the full main observation horizon |
| Playback driver durations | Median **11.00 s** | Includes selected repair/restart paths |
| Other-boundary driver durations | Median **7.23 s** | Same qualification limit |
| Startup proxy across 11 calibration runtime directories | Median **12.54 s**, range **5.24–16.29 s** | First trial start minus simulator launch timestamp; includes readiness/preparation, not a controlled boot benchmark |
| Full 600-second collector probe | **601.641 s** | Measured collector finished 1.641 seconds after its deadline; late collection did not extend the grade window |
| Separate recovery guard probe | **40.390 s** | Missing consumer/completion stayed unresolved |

For timing reference only, each exact main recipe/arm is matched to its latest qualified retained calibration attempt and weighted by the actual main bank. Every other attempt is retained. This selection forecasts workload; it never selects primary outcomes.

The weighted **driver-only** forecast is 2.47 hours. It is not a campaign estimate. Much of that activity fits inside the 600-second window, so adding the whole driver duration to every window would double count it.

**Serial estimate:** 250 hours of observation + 0.38 hours before final requests + 5.22 hours of startup proxies + 0.68 hours of collector-overrun allowance = **256.29 hours**.

Allow **15–20% operating reserve** for exports, database backups, service shutdown, host slowdowns, bounded in-flight settlement and maintenance: **294.73–307.54 hours**, approximately **12–13 days continuously**. This reserve is a planning choice, not a statistical confidence interval or a measured failure rate. A 75-slot block is about **12.81 hours before reserve**. If only one block is run per day, plan about **20 run days**, with the machine kept awake for the whole active block. Long outages add calendar time and may leave affected outcomes incomplete.

The 250 hours is the observation component of the chosen full-window serial schedule. It was previously a capped sequential calculation; accepting full observation for every slot makes it planned time rather than a prediction that business commands take ten minutes each. No calibrated early-terminal rule is adopted.

Exact values, methods, source hashes and limitations are in [measurements.json](measurements.json). They are engineering forecasts based on one local machine and short calibration runs; full-campaign load has not been measured.

## 4. Parallelism and isolation

**Approved by this proposed plan: live concurrency = 1.** Full-window concurrent collection has not been qualified for any main case. Logical separation alone is not proof that shared-process faults or host load are harmless.

| Work or cases | What can safely overlap now? | Isolation rule |
| --- | --- | --- |
| Offline validation/grading of completed immutable exports | Independent file reads and grading can run in parallel; give each task its own output file, then join by input/arm/attempt | No application requests, fixture mutation or shared output writer; the paired analysis waits for its input ledger |
| **300 clean inputs / 900 slots** | Scenario-local and plausible candidates for future concurrency; **not qualified for live overlap** | Fresh workflow/property/resource, scenario, IDs and keys; execute serially in this plan |
| **195 other scenario-scoped inputs / 585 slots** | Named provider barriers, visibility/drop/reorder faults, partial/duplicate effects, resource changes, playback/late-ACK/reconnect cases are object-scoped; **not qualified for live overlap** | Scope every command, provider barrier and collection query to the execution. Reconnect here is scripted, not a browser outage. No shared worker configuration changes during another slot |
| **3 restart-before-repair inputs / 9 slots** | Cannot share the worker process being replaced | Exclusive API/voice/worker/simulator process set; preserve its databases through the window and restart. Native P2 discovery uses its existing workflow scope; keep ordinary B3/P1 response opportunities |
| **2 redis-loss inputs / 6 slots** | Cannot share the Redis database being flushed | Exclusive reserved research Redis instance/database. FLUSHDB is global to that database; never target application Redis. This remains the qualified companion-cache control |

Thus **495 inputs are scenario-scoped candidates** and **five inputs require explicit process/cache exclusivity**. This is a scope classification, not a concurrency certificate. Every slot gets serial runtime isolation under D5, including the 600-second observation period. Do not start another arm while the previous arm is still being observed. The exact 500-case classification is in [case-isolation.csv](case-isolation.csv); [slot-plan.csv](slot-plan.csv) contains the unchanged randomized order for all 1,500 proposed slots.

## 5. Observation and timeout rules

1. **Persist identity before action.** Record the frozen input/hash, arm, attempt 1, execution ID, workflow/scenario/resource IDs, command IDs, process configuration and planned script steps before sending. Record each request's actual scripted UTC time before its HTTP call, and retain its distinct accepted-revision time. A rejected or lost acceptance is not a fabricated accepted revision.
2. **Use one fixed grading deadline.** Let T be the actual externally issued final request time. Grade through T + 600 seconds. Acceptance time controls revision applicability; it does not reset this deadline. Preserve UTC offsets and original appointment IANA zones. The observer uses a monotonic timer as well as recorded UTC clocks; clock discontinuities are evidence issues, not permission to move T.
3. **Observe after the script finishes or fails.** Leave the recipe's processes/configuration alive through the window, with the same existing worker steps, attempts and response opportunities. An HTTP refusal, useful update or driver exit does not finish observation. Do not invent extra drain passes or turn on a different consumer to improve an outcome.
4. **Use read-only collection, nominally every five seconds and at the deadline.** Read application journals and independent simulator truth; retain publication, receipt, raw provider and playback records. Polling is for collection, never fault placement. Do not use extra provider status/verification calls that consume visibility counters or create supporting evidence. Keep named barriers for causality. Record actual poll times and gaps; five seconds is not a guaranteed interval.
5. **Keep the uncapped export.** Collect the final persisted prefix and any observed later events even if the final snapshot finishes after T + 600. Apply the existing v4 cap separately to grades. Playback eligibility requires both the reported client time and server receipt time inside the cap. A late ACK describing earlier content is retained but is not automatically eligible. Later repair cannot retrospectively turn an incomplete in-window result into success.
6. **Missing anchor is missing evidence.** If failure prevents issuing the final request, do not invent T or call the window complete. Keep the unissued script step and cause. Collect for 600 seconds after the last issued request, or slot start if none was issued, as a recovery/export fallback only. It does not substitute for the missing final-request anchor in v4 inference.
7. **Do not equate a limit with business failure.** Missing completion/support stays UNKNOWN. Distinguish a recorded unsafe event from an incomplete safe outcome. A known unsafe event is not erased by missing other records. Publication is not completion; client testimony is not hearing.
8. **Keep unresolved work durable.** At the cap, retain pending operation/repair rows, outstanding dispatch identities and all failures. Allow already-issued requests to settle within their existing limits before process shutdown, recording any late effects outside the primary grade. Do not send a new write solely to make the journal look finished. If bounded shutdown/transport failure leaves an effect uncertain, preserve UNKNOWN and its durable recovery state. Never delete a database or obligation because a slot ended.

The cap defines what the study measures, not a promise that no effect can ever occur later. Uncapped evidence and durable records preserve observed late effects and unresolved responsibilities; an arbitrary finite window cannot certify their permanent absence.

| Existing limit retained | Rule |
| --- | --- |
| Provider / speech scheduler / driver HTTP | **30 / 15 / 40 seconds**; record timeout and trace identity, reconcile any possible send before safe retry |
| Provider barrier | **120 seconds**; named scenario/operation binding; retain unreleased-barrier error and independent truth |
| Core / repair lease | **180 / 30 seconds**; natural lease handling, no editing timestamps to accelerate recovery |
| Reconciliation / drain | **8 attempts / 30 passes**; exhaustion remains unresolved/handoff, not fabricated completion |
| Permit validity | **30 seconds**; expiry/refusal is retained, not extended for convenience |
| Recovery watch | **40 seconds** for its defined recovery test; it does **not** replace or stop the 600-second main collector |
| Main observation | **600 seconds after final external request**, even when business commands finish sooner |

These limits already have scope-specific calibration evidence in [budget-qualification.json](../../phase-8-study-design/v4/budget-qualification.json). A collector HTTP call may return after the grading deadline. Preserve its raw timing and exclude evidence that became available after the cap; never credit a late result by shifting the deadline.

## 6. Storage and interrupted-run recovery

### Storage

- Reserve **25 GiB of working space plus 25 GiB for a separate backup**, in addition to installed images/models and existing historical evidence. Do not assume compression savings.
- Short-trace extrapolation is **180.0 MB** for 1,500 slots, but omits long collection. The retained full-window probe is **3.264 MB with 102 polls**. Giving every slot that size projects **4.896 GB** of JSON alone. This is a sizing illustration from one probe, not an upper bound; audio, logs, database/WAL, backups and abnormal growth need the allowance above.
- Database footprint could not be measured: both read-only calibration-database connections timed out. No Docker/service was started to obtain it. Measure actual growth during collector qualification and verify capacity before launch. The allowance is not evidence that PostgreSQL/WAL fits a known size.
- Write each raw execution and collector journal under a new campaign directory outside v1/v2/v3/v4. Use atomic replacement for the live checkpoint file and append-only/versioned event/export files; keep the original final exports immutable. Hash raw JSON, audio, fixtures, configuration, source and derived grades. Deduplicate identical audio by hash without removing segment references.
- Sync the slot export and ledger checkpoint to the backup before releasing that slot. Make coordinated application/truth database recovery backups at block boundaries; record their independent sequence positions and shared UTC collection cutoff. Retain enough persisted journals to reconstruct a common cutoff rather than assume two database dumps were simultaneous.
- Check free space before every slot. If it is below **10 GiB**, or measured growth shows remaining allocation will not fit with a 5 GiB operating reserve, stop admission between slots and resolve storage. Finish/retain the active slot; never prune failed attempts or historical evidence for space. Stop on a backup/hash error rather than declaring the slot safely archived.

### If execution is interrupted

1. **Interruption between slots:** resume the next unstarted slot in the saved order after hash, health, capacity and backup checks. Do not shuffle again or reset finished slots.
2. **Observer interruption while application persists:** resume collection for the **same execution ID**, bindings and original T + 600 deadline. Recover durable records and sequence positions. A collection gap can be resolved only by complete authoritative persisted journals; otherwise affected endpoints stay UNKNOWN.
3. **Unplanned worker/provider/host interruption:** preserve the original attempt and fault details. Resume its observation safely if possible, but do not replay script commands or restart the ten-minute clock. Reconcile possibly dispatched effects using stable identity before any authorised ordinary retry. An unplanned crash remains an infrastructure deviation even if business recovery later succeeds.
4. **Deadline passed while offline:** export recoverable records, cap using recorded times and explicitly record missing coverage. Durable pre-cap facts may still support specific endpoints if their journal prefix is complete. Post-cap recovery or a missing journal cannot certify earlier safe completion/absence.
5. **A diagnostic rerun is needed:** use attempt 2 or higher, a new execution ID and fresh resources, link it to attempt 1, and label it diagnostic. Attempt 1 retains its primary denominator and outcome/missingness. Do not add an independent input or substitute the rerun.
6. **Source/configuration drift or a protocol defect:** stop new admissions, preserve current evidence and issue an explicit deviation. A changed protocol requires review, a new version/freeze and a prespecified disposition of affected comparisons; do not quietly patch and continue the original campaign.

Before freeze, the campaign ledger/collector must demonstrate these behaviours on **separate calibration IDs**: full-window collection after a normal return/refusal, interruption and resumption of the same execution, missing-anchor handling, original-attempt retention, safe shutdown/export and hash drift rejection. This is research-runner preparation; it does not alter the application or add new input types. No such new calibration was run in this documentation task.

## 7. Short acceptance and launch checklist

### Accept before freezing

- [ ] **D1:** exactly 500 fixed-frame inputs across B3/P1/P2; typed/tone protocol evidence and its stated limits.
- [ ] **D2–D3:** unchanged 5pp clean margin, power assumptions, primary/secondary comparisons, missingness rules and descriptive-only timing claims.
- [ ] **D4:** matched ordinary baseline opportunities; supported delivery and required withdrawal separate from internal repair telemetry.
- [ ] **D5:** saved order, one live slot at a time, fresh process set, complete 600-second windows and the approximately 295–308-hour operating budget.
- [ ] **D6:** fixed timeouts, storage/backup allowance, original-attempt retention and interruption rules above.
- [ ] **D7:** qualified collector/ledger on separate IDs, scoped environment/budgets and complete reporting/ingestion; freeze that actual harness rather than the prose alone.
- [ ] Record the reviewer acceptance, approved plan version, source/configuration/fixture/oracle/analysis hashes and a **new** freeze receipt. Verify historical evidence unchanged. Do not mark old candidate files as a reviewed freeze.

### Verify before launching

- [ ] Dedicated campaign services/databases/Redis namespace are healthy; no application or historical database is a reset target; adequate disk and backup are available; host will remain awake through an active window.
- [ ] All 1,500 first-attempt slots are accounted for; collector/export/recovery checks passed; freeze hashes match; launch guard requires the new receipt.
- [ ] Obtain explicit launch authorization after reviewing the frozen package. **Acceptance of this plan is not itself a campaign launch.**

## Evidence and preservation

Sources: [v4 decisions](../../phase-8-study-design/v4/review-decisions.json), [v4 report](../../phase-8-study-design/v4/phase-8-report.md), [all calibration attempts](../../phase-8-study-design/v4/calibration-qualification.json), [saved order](../../phase-8-study-design/v4/execution-order.json), [candidate design](../../../docs/12_PHASE8_CANDIDATE_V4.md), [fixture bank](../../../research/fixtures/phase8_design_v4/inputs.json), [runtime](../../../research/study_v4/runtime.py), [collector](../../../research/study_v4/window.py), [capped oracle](../../../research/study_v4/oracle.py) and [blocked pipeline](../../../research/study_v4/pipeline.py).

[Preservation verification](preservation-verification.json) checks historical evidence, final candidate sources, every existing v4 artifact and the fixture bank. [measure.py](measure.py) performs only offline reads and writes inside this new plan directory; it neither imports nor runs an experiment driver. [measurements.json](measurements.json) and the two case/slot CSVs make the operational recommendations reviewable.

**Verdict:** the scope and operational choices are concrete and ready for acceptance. Campaign collection/ledger qualification and the new review/freeze/launch receipts are still required. **The main campaign remains unstarted.**

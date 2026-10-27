# Slot 616 diagnosis and safe preservation — continuation blocked by existing limits

At 2026-10-17T14:12Z, host `i-057344e5372faf62f` was independently verified **STOPPED**. Owned root `vol-09dbb42bbf607f5de` remains attached with DeleteOnTermination=false. No deletion, replay, regrading, pause clearing, freeze, deployment or new admission occurred. The user authorized investigation and recovery in this turn; no increase of the previously explicit operational limits was inferred.

## Exact boundary and demonstrated cause

The consistent ledger and notice chain verify **616 BACKED_UP / 884 PLANNED**, zero active. Next is sequence **617 / P2 / attempt 1**, execution `01a11705-11f2-7276-8d5f-0277ced1a5f5`, case `p8v4-0353`. Both the saved identity and pending state are unchanged.

Slot616 B3 execution `01a11705-11f2-7c66-8710-43c921046e1b` received HTTP409 from `/internal/phase6/b3/schedule` at 2026-10-16T13:39:12.025224Z. Its nested non-retryable `b3-evidence` problem says `Current provider facts do not support speech`. The traceback is `collector.execute -> calibration.run -> finish_update(2) -> remedies.recover -> schedule -> request`.

This is the same frozen revision-only claim-selection limitation documented for slot145, with a further declared provider capability combination. The provider lacks native rescheduling; correction commits CREATE(old), CANCEL(old), CREATE(new). Both revision2 operations are CURRENT/PRESENT. The selected RESCHEDULED_APPOINTMENT claim cannot be established from this replacement chain. In this recipe, resource_lookup=false, so resource observation is the intentional501 `Resource lookup is absent`; the three authoritative operation observations are200 and bind to the retained effects. Both frozen RESCHEDULED and COMPENSATED predicate evaluations are UNKNOWN when the resource observation is unavailable. No evidence requirements should be relaxed to announce confirmation.

The frozen refusal classifier identifies the three-operation topology, validates the declared501 response, then returns None at refusal.py:315 because its replacement exception additionally requires every observation to be200. The accepted exception covered the all200 variant only. This is a narrow experiment-control coverage gap combined with the disclosed studied claim-selection limitation. It does not demonstrate a provider outage, disk exhaustion or a business-correction failure.

The exception occurred during616, before its observation window ended. DRIVER_FAILURE was promoted to the campaign at 2026-10-16T13:49:16.475780Z. The deadline was13:49:10.289129Z; the full window and final collection completed. Backup616 was verified13:49:49.917172Z, retirement completed13:50:02Z, and the subsequent attempt to obtain another slot stopped on PAUSED_ADMISSIONS at13:50:14Z. Slot617 never started. The watchdog was not the original trigger.

## Original evidence preserved

Original archive SHA-256 `4002ff9a474c3afaae216ab8a14260801910ca82043419a3e0afd5a70dd95c89`, bytes42156874, pinned S3 version `l_.od3ASgl8Q0KJvKRyOjXCntWMc5oUu`. Original export SHA-256 `e70007cf43de2d0ad37a40f65dbbe7a23cf8dc6ba3a86d17b00a4e59c41c6c70` matches its committed manifest member. The archive, export, slot ledger and both PostgreSQL dump hashes passed checks using the existing retained archive; no diagnostic archive download was needed.

Its raw status remains FAILED. Stored grades remain: correct final business state TRUE, correction success TRUE, correct final update FALSE, unsupported exposed claim FALSE. These are the existing grades, not new grading. Timing remains originally marked INFRASTRUCTURE_FAILURE; no retrospective timing sidecar was applied. Tone/audio evidence remains a scripted protocol proxy and proves no human comprehension.

All616 backup receipt bindings passed. Original616's pinned cloud object passed verification. A consistent master snapshot, journals, notices, durable pause and clock anchor were retained under `/var/lib/p8-continuation-v10/deployment/stop-616-1792246080704133658`.

New closed-boundary master archive: SHA-256 `f1fbd0bfdbfda588bc9ef51a45142c72acdf0ee4a7772b53a02752fa66a020ba`, bytes41481410; bucket `fyp-p82-20261005-018da1d6-803656589923`, key `exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/f1fbd0bfdbfda588bc9ef51a45142c72acdf0ee4a7772b53a02752fa66a020ba.tar.gz`, version `R4nE4l2ASxFLolEQKfZpmoGmkeXv6gQ4`. Independent readback verified633 evidence pieces and the exact616/884 ledger. Readback record SHA-256 `9c61e51d54dc6070114dd8348ae6d9e2f904a72ed920aa0e2dabceafc0f9014a`.

## Small separate correction and focused checks

`candidate/refusal.py` adds only the declared missing-resource variant of the existing replacement-chain exception. It retains exact problem/request/recipe validation, all three200 authoritative status observations bound to their effects and identities, and requires both frozen predicate evaluations to be UNKNOWN for that variant. It records UNKNOWN evidence, does not infer business success from refusal and never retries the refusal. All200 replacement and legacy B3/P1/P2 proofs are preserved. No arm, application, claim selection, endpoint, fixture, oracle, analysis method or600-second window was changed.

Candidate refusal SHA-256 `37077a3d05377400df5a9ffeb2a15fed95a753b8eafa9f6af01f1fb25c2e2c86`. Exact diff: `candidate/refusal.diff`. This is an **unfrozen, undeployed classifier candidate**, not a complete authorized continuation archive.

18 fixed offline controls passed in the existing deployed Linux Python3.12.13 runtime: original rejection, narrow UNKNOWN recognition without original mutation, full-window eligibility, three unchanged legacy arm proofs, synthetic UNKNOWN P1/P2 receipts and ten negative controls. Unrelated409, outer500, provider500, corrupt hashes, missing evidence, wrong actions/effect binding, retryable responses, undeclared capability and incorrect501 body remain unrecognized. No scenario, live stack, pilot, dependency installation or full-window calibration ran. The installed frozen refusal file was checked unchanged before/after.

The first offline invocation failed before the first control because the test loader omitted registering dynamically loaded modules in sys.modules, preventing Pydantic from resolving Literal. Its script/output are retained; only that harness registration was corrected for the second invocation. An earlier external local command had a quoting syntax failure; diagnostic attempt1 also exceeded SSM output capacity by printing the entire historical manifest. Those failed external attempts remain recorded and do not represent research executions. The corrected diagnostic output returned only the required manifest binding.

## Capacity correction and refreshed feasibility

The progress script's145670462448-byte requirement is a **hard-coded prelaunch projection**, not the executable current admission threshold. Previous status answers incorrectly characterized its comparison as a current disk-gate failure. The actual frozen guard passed: live admission requires20GiB free, active collection10GiB, plus the relevant reservations; working and backup caps are checked separately. Free disk was124100911104bytes and available RAM7232819200bytes. No disk resizing or evidence deletion is indicated by this failure.

Accepted planning rate remains262.31642189586114hours/1355 slots. For884 slots:171.13484646194925 execution hours, plus2.5hours preparation/shutdown and24hours uncertainty. No allowance was reduced. At14:08:06Z, completion forecast was2026-10-24T19:46:12Z, and completion plus uncertainty2026-10-25T19:46:12Z: **4.3634hours beyond the accepted absolute stop**. A14:12:34Z refresh gives19:50:40Z and4.4378hours shortfall; any further wait increases it.

Accepted conservative elapsed-clock accounting includes all stopped/idle history, full80GiB S3 monthly reservation, request reserve, handover reserve and the167GiB root extension reserve. Forecast at14:08:06Z: completionUS$69.6852, completion plus uncertaintyUS$73.1830, full-deadlineUS$72.5471. At14:12:34Z the uncertainty forecast isUS$73.1939, plusUS$0.0729 for the admission half-hour lookahead. **The70USD admission projection fails; the75USD total ceiling still fits the evaluated completion estimate.** These are accepted formula forecasts, not actual billed spending. No actual billing claim is made and the accounting method was not substituted.

All-version cloud inventory was22269265493bytes. Conservatively reserving60MiB per remaining slot plus1GiB yields78959478357bytes cloud and81838591063bytes local backup, each below85899345920bytes. These projections precede the additional41.5MB preservation master/readback and require a fresh complete inventory before any future launch. Existing evidence was retained. Storage is not the demonstrated launch blocker.

## Minimum next procedure and explicit decision

Safe shutdown has completed; both campaign/watchdog were quiesced first and durable pause SHA-256 remains `b2cddd1475c8b1dd2e471b7bc2cde283dfb4ef23a928a12a56be06086d8840fc`. Root and S3 evidence are retained. Existing absolute stop is2026-10-25T15:24:23.810674Z and retention decision remains due2026-10-27T15:24:23.810674Z. Root167GiB retention uses the accepted recorded rate, aboutUS$0.527/day ([AWS EBS pricing](https://aws.amazon.com/ebs/pricing/)); actual total charges remain unqueried. No deletion is authorized.

Clearing the pause on frozen v10 would repeat the uncovered classifier case. A future resumption requires a complete separately inventoried classifier continuation with exact616/884 handover, verified authority/backup closure and source/runtime checks, a fresh independently read-back preparation guard and the normal genuine readiness/launch/backup sequence. Start only617/P2/attempt1. No original may be replayed or retrospectively regraded.

The existing policy cannot safely support immediate resumption. A concrete **proposal only**, calculated in `minimum-amendment-proposal.json`, is an absolute stop of2026-10-26T00:00:00Z, admission guard74USD, total ceiling75USD unchanged, caps80GiB unchanged and root retention decision by2026-10-28T00:00:00Z. This provides about4hours additional time margin beyond the current accepted uncertainty estimate; it does not guarantee completion. The root reserve and earlier external admission fence/timers must be recalculated and explicitly bound to any accepted amendment. This proposal was not applied. Explicit authorization to change limits is needed; this turn's general recovery instruction did not silently override the previously explicit no-increase conditions.

The final candidate comment was clarified after controls; its executable AST is unchanged. The tested pre-comment SHA-256 was 37077a3d05377400df5a9ffeb2a15fed95a753b8eafa9f6af01f1fb25c2e2c86. This is recorded separately in candidate/comment-only-provenance.json.

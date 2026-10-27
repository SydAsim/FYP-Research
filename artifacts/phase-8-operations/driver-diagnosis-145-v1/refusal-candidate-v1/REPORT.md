# Slot 145 — verified diagnosis and narrow classifier candidate

**Review candidate only. Continuation is blocked.** No AWS calls, boot, pause
clearing, research executions, oracle runs, regrading, freeze or launch occurred.
No application, arm, main fixture, endpoint, observation window or analysis-method
code changed. The sole proposed runtime difference is `refusal.py`; see
`refusal.diff`. The report assembler and controls are local diagnostic tools.

## Evidence and demonstrated cause

The returned bundle SHA-256 is
`f9d639added6872c5679e931b4f07e1027643d00a28f9bb4cbbc0e5601c4cb48`.
Local verification checked all returned member hashes against their proof and
original manifest, SQLite integrity, event/checkpoint hashes and execution
identity. The CloudShell proof records the complete pinned original archive
hash `8abe7597a0e59154cf66e682fd08f3440fff815c458db0bdc8fe83666091ad24`.
An independent CloudShell bundle digest was not supplied separately; the user's
description of a verified bundle and the internal provenance checks are retained
as distinct evidence. No archive was downloaded again. The supplied Downloads
file remains intact; the small returned bundle and bounded extraction are kept
under `D:/FYP-ResearchBackups/slot145-diagnosis/`.

Slot 145 is B3, `p8v4-0361`, attempt 1, execution
`01a11705-11f1-7386-a804-76b957c218d5`. Its frozen recipe is
`hidden-False-IMMEDIATE-DROP_RESPONSE`: a committed initial booking loses its
response, correction arrives, and this provider **does not support rescheduling**.

1. The provider committed the first CREATE at 17:56:47.682245 UTC. Its response
   was withheld/dropped as configured; reconciliation recovered the committed
   effect rather than blindly retrying.
2. Revision 2 was accepted at 17:56:47.779882 UTC. Recovery cancelled the old
   appointment at 17:56:48.104004 and created the corrected one at 17:56:48.424077.
   The new appointment is confirmed at 14:00–14:45 Europe/London, which is
   13:00–13:45 UTC. The old one is CANCELLED.
3. At 17:56:48.956496 the driver POSTed `/internal/phase6/b3/schedule`, with
   workflow `c9911721-7a98-433c-a53f-4d7c55dda65b` and revision 2.
4. Frozen B3 `_b3_text` selects the latest current PRESENT operation by
   `created_at DESC`. The actual resource query binds to the replacement CREATE,
   `e3f14153-5496-4784-bee8-7fa81b4cb599`; it did not select the cancellation.
   However, it chooses `RESCHEDULED_APPOINTMENT` solely because revision > 1.
5. Four fresh observations inside that request's time interval all returned
   HTTP 200: current resource facts, then replacement CREATE, compensation
   CANCEL, initial CREATE. Their authoritative operation outcomes are PRESENT.
   Both compensation and replacement are current PRESENT effects, which is
   valid for orthogonal operation dimensions.
6. Frozen `_evaluate` accepts the corrected resource state, then compares the
   recorded `CREATE → CANCEL → CREATE` evidence with the reschedule predicate's
   required `RESCHEDULE → RESCHEDULE → CREATE` actions for three statuses. The
   first action mismatches, producing **VIOLATED**, not UNKNOWN and not a
   transport error. The same recorded chain satisfies the existing
   `COMPENSATED_APPOINTMENT` predicate in the offline control. That comparison
   diagnoses the semantic mismatch; it does not authorize speech or change B3.
7. `_b3_text` raises `b3-evidence`; the voice endpoint wraps it as
   `voice-command-rejected`, HTTP 409, at 17:56:49.061807. The nested problem has
   `retryable: false`. Synthesis was rejected before TTS/audio creation. No
   decisive speech text was rendered; the attempted claim was the corrected
   appointment confirmation, not a recorded spoken sentence.
8. `finish_update → recover → schedule → request` propagated that response as
   RuntimeError. The slot ledger records DRIVER_FAILURE at 17:56:49.187462.
   The collector still observed through the original 18:06:47.750198 deadline;
   its last poll is 18:06:47.750355. Master STOP_NEW_ADMISSIONS followed at
   18:06:53.900124 (durable master pause at 18:06:53.908883). Verified cloud backup
   preceded BACKED_UP at 18:07:21.811352. This was slot 145's failure, before
   its backup, not preparation or admission of slot 146.

Exact response, full original traceback, observations, effects and notice are
copied into `evidence.json`. Existing saved grades say business correction TRUE,
correct final update FALSE, with no exposed claim. No grades were recomputed.

## Precise frozen source locations

- `E:/p8v9/source/apps/api_controller/phase6_b3_audio.py:47–67`: operation
  selection, revision-based claim type, and `b3-evidence` refusal.
- `E:/p8v9/source/apps/api_controller/phase3_verification_service.py:50–113`:
  fresh resource and bounded parent-operation reads;
  `:297–323`: action-chain expectations and VIOLATED result.
- `E:/p8v9/source/apps/voice_worker/scheduler.py:121–137`: synthesis GET before TTS.
- `E:/p8v9/source/research/study_v4/calibration.py:159,301,464` and
  `research/remedies/runner.py:245,410,463`: raised response and recovery path.
- `E:/p8v9/source/artifacts/phase-8-runner-amendment/v4-complete/refusal.py:112–114`:
  `len(current) != 1` rejects this valid two-operation topology before response
  or evidence classification. `collector.py:452–484` records/persists failure;
  collection proceeds afterward.
- `E:/p8v9/source/research/remedies/runner.py:235–242`: P1/P2 ordinary updates
  request the same reschedule claim for all later revisions.
  `apps/durable_worker/repair.py:154–162` also uses that revision-only choice.
  These are code-path findings, not observed executions of pending P1/P2 slots.

## Classification and smallest proposed correction

This is a **combination**: a demonstrated semantic claim-selection defect in the
frozen B3 application path, a corresponding choice in the common research driver,
and an instrument coverage defect. The evidence gate correctly enforces the
claim actually requested. A provider outage, authentication failure, RAM issue
or corrupt ledger is not the demonstrated original cause.

The refusal is a recordable unsuccessful research outcome caused by that
existing implementation mismatch. It was not the intentionally injected fault
itself, and “safe refusal” does not imply a healthy baseline or successful task.
Changing B3 or the common driver's claim selection would change studied behavior;
**neither is changed here**.

The candidate extends only semantic refusal recognition to the strictly bound
first-correction replacement topology: hidden-commit recipe with reschedule
unsupported; exactly three evidenced operations/effects; exactly two current
effects; matching appointment/resource identities; complete ordered HTTP-200
CREATE/CANCEL/CREATE reads matching effect facts; the frozen requested predicate
VIOLATED and the existing compensated predicate SATISFIED. P1/P2 also require
their existing negative receipt, validity, event hash and observation bindings.
Unknown status codes, unrelated 409s, provider failures and unproven chains fail
closed. No non-retryable refusal is retried. Existing permissive-response guards,
pause, collection and backup code remain unchanged.

The new proof has its own version and mechanism field. Existing single-operation
proofs retain their exact version and contents. “COMPLETED” in the proposed
instrument proof means an observed protocol outcome; it does not overwrite raw
FAILED or mean the business/speech task succeeded.

If reviewed and accepted later, a **separate timing sidecar** could change only
this instrument censor reason from INFRASTRUCTURE_FAILURE to
NO_SUPPORTED_COMPLETION, keeping event=false and the 600-second censor duration.
No accepted sidecar or retrospective analysis row was written here. Original
grades, raw statuses, archives and all original timestamps remain authoritative
historical records.

## Focused checks and preservation

The fixed plan declared 24 offline controls, zero research executions and a
120-second maximum. **24 passed in 1.96 seconds** on existing Windows Python
3.12.10. Coverage: exact retained predicate mismatch; candidate recognition
without mutation; unchanged prior B3/P1/P2 proofs; synthetic P1/P2 negative
receipt paths; 12 unrelated/corrupt-response rejection controls; complete versus
missing anchor/polls/gap/drift collection conditions. Synthetic receipt controls
are not live PostgreSQL trials or pending originals. No oracle was invoked.

Strict mypy passed for the classifier and controls. Ruff passed after test-only
line wrapping. Failed lint outputs and one report-assembly import-registration
error are retained; the latter changed only the local assembler, not runtime.
The runtime controls passed on their first attempt. Deployment's pinned Linux
runtime was not started or qualified in this task. Tests do not guarantee that
all campaign paths are error-free.

Frozen v9's **3,425 files** passed their recorded hashes. The frozen manifest,
relevant frozen source and slot-145 export match before/after hashes. Retained
master metadata matches all 1,500 saved bindings: **145 BACKED_UP / 1,355 PLANNED**.
Next remains sequence 146/P2/attempt 1,
`01a11705-11f1-772d-8190-c43552871801`. No import, replay or outcome replacement
was performed. Backup references are retained; no new live backup readback was
claimed.

## Scientific implications

The slot demonstrates successful business reconciliation and replacement,
followed by refusal of an inappropriate confirmation predicate and failure to
deliver a final update. It does not demonstrate mechanism superiority. The
shared revision-only claim choice can cause comparable communication failures
in all arms and confounds attributing such differences solely to permits or
repair mechanisms. Pending P1/P2 behavior is not inferred as an observed result.

Keeping arm behavior frozen supports a comparison of these exact implementations
with that limitation disclosed. Repairing the semantic choice would require a
separate reviewed study amendment; it cannot be smuggled into a runner fix.
No restart of comparisons or exclusion of this outcome is performed or justified
by the classifier correction alone. Tone/ACK evidence cannot establish actual
human understanding, and no synthesis/audio was produced in this slot.

## Separate operational blockers and minimum next step

At the saved calculation in `feasibility.json`, unchanged remaining allowance is
262.316 hours plus 2.5 preparation/shutdown hours. Only about 241.891 hours remain:
**22.926 hours short** of the original 22 October 2026 15:24:23.810674 UTC deadline.
The 225.833-hour window-only floor excludes measured overhead and is not used
to manufacture a PASS.

The unchanged conservative accounting forecast is **US$65.068**, above both the
US$60 admission guard and US$65 total ceiling. This is a forecast using rates
last verified 10 October, elapsed-clock accounting (including stopped hours)
and accepted reserves; it is **not actual billed spending**. No live billing,
credits, prices or storage-capacity readback was requested. Both reviewed
feasibility gates fail without changing limits or assumptions.

AWS received no mutation and remains under the stopped-host instruction. The
last retained root-retention decision deadline is 13 October 2026
16:04:13.525847 UTC; it has not been extended, and this task deletes nothing.

**Next action: review this classifier-only candidate and its scientific
disposition. Continuation cannot be proposed as ready under the current
time/cost policy.** Do not boot, clear the pause, freeze or launch this candidate.

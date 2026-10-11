# Bounded Phase 8.5 preflight — v2 candidate

**Draft: live qualification remains in progress. Not accepted, frozen, or deployable.**

## Root cause and proposed disposition

Both retained campaign attempts hit an application safeguard, then the research driver raised an exception. In resource-only scenarios, the provider commits the corrected appointment but deliberately offers no operation-status lookup. The independent truth log proves the final correction; the application's ordinary observations cannot prove the operation chain required for confirmation. These are distinct facts.

Original B3 refuses confirmation at `apps/api_controller/phase6_b3_audio.py:63` (`b3-evidence`, nested in the voice worker's 409). Original P1 obtains receipt `a19611ff-3567-4b8f-9bd0-12e7e3770da8`: result **UNKNOWN**, revision 2, resource version `1`, valid 2026-10-07 20:55:25.447513–20:55:55.447513 UTC, with no invalidation. Its attempted claim at 20:55:25.476364 UTC is inside that interval. It is rejected because UNKNOWN is not SATISFIED, not because it is stale or expired. The check is `apps/api_controller/phase3_claim_service.py:135`, calling `packages/domain/phase3_verification.py:94`. Provider status reads return 501 with “Operation status lookup is absent”; a resource read returns the corrected appointment. No claim or permit was persisted for that workflow.

P2 with no open repair obligation follows the same receipt/claim path. The frozen driver does not branch on a negative receipt before attempting authorization (`research/remedies/runner.py:255`); its HTTP wrapper raises (`research/study_v4/calibration.py:159`). The previous collector recognized only the first B3 exception. The second exception therefore paused admissions after observation and backup. Application behaviour is unchanged.

Keep both raw FAILED exports and original grades. Proposed separate sidecars classify their evidenced refusal as an unsuccessful research outcome: business correction TRUE, correct final spoken update FALSE. Neither refusal is retried. The full-window timing censor reason becomes `NO_SUPPORTED_COMPLETION`; duration remains 600 seconds and event-observed remains false. Existing latency model membership and numeric contributions therefore do not change for these two originals. Missing anchors, acknowledgements, collection gaps and unknown effects remain unknown.

## Scope and safeguards

The new `refusal.py` requires the declared recipe/fault, exact non-retryable problem, current operation/revision, applicable receipt timing, bound provider observations and hash-consistent evidence. It recomputes the existing pure verification predicate and requires a non-SATISFIED result. It does not whitelist HTTP 409 generally. Persisted proof is rederived before grading. Unexpected refusals, transport failures, source drift, corrupted captured evidence and failed backup verification retain the durable pause.

`collector.py`, `instrument.py` and `runner.py` integrate the classification with full-window collection, independent grading and backup-before-admission. Other operational components are copied from the combined continuation runner; exact provenance is recorded in `component-provenance.json`. No application code, migration, main input, saved order, endpoint, analysis method or observation window changes. Main admission is explicitly blocked in this candidate.

## Recipe review

`recipe-disposition.json` maps all 50 recipes across B3/P1/P2, with conditional outcome handling and trace links. `recipe-review.json` records 178 retained calibration attempts, including unsuccessful ones. Expected stale conflicts already use the driver's recorded `allow_failure` path. Ambiguous provider sends reconcile before retry; provider 5xx/drop faults are not automatically infrastructure failures. Exhausted visibility can return an unresolved update for independent grading. An unproved raised timeout still pauses; recipe membership alone cannot excuse it.

Compensating CREATE–CANCEL–CREATE paths may have correct final state yet fail the frozen RESCHEDULED_APPOINTMENT predicate. This semantic limitation is preserved, not repaired by changing the claim or grading success. Older failures without sufficient timestamps/evidence are not retrospectively reclassified. Existing boundary qualification is reused; this is not a new full-bank runtime pilot.

## Fixed validation

Declared before execution: nine separate serial local PostgreSQL calibrations, three refusals, three injected uncaught technical defects, three collector checkpoint/resumes; 600 seconds each, 110-minute admission budget, zero cloud spending. No admitted collector's deadline is shortened. Two local verified backup roots substitute for cloud storage in these checks; previous S3 qualification is retained, not repeated.

Offline checks: 68 candidate/control tests and 61 instrument/application regressions pass. Candidate lint passes. Configured Windows typing passes 156 files; strict native candidate typing passes 20 files with only the dynamic AWS SDK imports isolated. Linux-wide configured typing reports 11 errors in frozen Windows-specific helper paths; it is not claimed to pass. Retained failed setup/type/test attempts are listed in the final validation record. One test expectation was corrected to allow a paused exported slot to finish its own backup while still denying new admission.

Live results and final preservation verification will be added only after completion.

## Deployment and feasibility

AWS remains stopped; no new main executions, freeze or launch. Two original executions are backed up and 1,498 identities remain planned. The accepted v1 handover expects one completed original and cannot be assumed to import the now two-completed ledger. A reviewed combined handover binding both originals, accepted sidecars and the unchanged remaining identities is required before fresh-host deployment. Restarting the stopped host is not qualified.

The unchanged absolute deadline is **22 October 2026, 15:24:23.810674 UTC**. The budget remains $65 total and $55 estimated committed-cost admission guard. At the initial preflight calculation, a 12-day allowance plus two hours setup fits conditionally; a 13-day allowance already fails the $55 guard. Final calculations must use the actual completion time and retain the original clock. There is no promise of completion or automatic limit extension.

The stopped host's root disk remains retained and costs approximately $0.512/day. Its retention decision is due **9 October 2026, 21:05:37.547530 UTC**. S3 and local evidence remain preserved. Credits are not a substitute for the accepted campaign limit.

All voice evidence here is scripted tone/client protocol acknowledgement. It does not demonstrate intelligible spoken confirmation or human understanding. The three arms can tie; a passing test does not establish superiority or guarantee an error-free campaign.

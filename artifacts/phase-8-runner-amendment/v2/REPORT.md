# Phase 8.5 bounded preflight — v2 review candidate

**Verdict: reviewable, but NOT ready for deployment.** The two known refusal stops are explained and a narrow amendment is qualified. A separate permissive-response control failed six checks and remains a deployment blocker. No acceptance, freeze, launch, AWS provisioning or main execution was performed.

## 1. Both original stops

The resource-only recipe commits the corrected appointment but deliberately disables operation-status lookup. Resource observation returns the corrected appointment; current/prior operation lookups return **501, “Operation status lookup is absent.”** Independent simulator truth proves the business correction. The ordinary evidence available to the application does not support confirmation of the operation chain.

- **B3 original** `01a11705-11f0-79f1-9293-78f7f8207f70`: the confirmation request is rejected with `b3-evidence`, nested in the voice worker's 409. The first blocking check is [fresh evidence evaluation](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/api_controller/phase6_b3_audio.py:63>).
- **P1 original** `01a11705-11f0-7826-bd9d-9066d82c4452`: verification creates receipt `a19611ff-3567-4b8f-9bd0-12e7e3770da8`, result **UNKNOWN**, revision **2**, resource version **1**, valid **7 October 20:55:25.447513–20:55:55.447513 UTC**, with no invalidation. The attempted claim at **20:55:25.476364 UTC** is within that interval. [Claim authorization](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/api_controller/phase3_claim_service.py:135>) rejects it with `receipt-not-applicable`: “A current SATISFIED receipt is required.” [Receipt applicability](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/packages/domain/phase3_verification.py:94>) requires SATISFIED. This is a negative receipt, not an expired or stale one. No claim or permit was persisted for this workflow.
- **P2 corresponding path:** without an open repair obligation, it uses the same verification/claim path. Separate real PostgreSQL calibration confirms the UNKNOWN receipt and refusal. The original P2 slot remains unstarted.

The frozen [recovery driver](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/remedies/runner.py:255>) attempts authorization after receiving the negative receipt. Its [HTTP wrapper](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/study_v4/calibration.py:157>) raises. The previous collector recognized the B3 refusal only, so P1 triggered a campaign pause after its full observation and backup.

Exact requests, response bodies, ordinary observations and independent truth remain in [B3 original](retained-first-original.json), [P1 original](retained-second-original.json), and [persisted P1 receipt evidence](original-p1-receipt-evidence.json).

## 2. Narrow amendment and disposition

`refusal.py` recognizes only a matching declared fault, exact non-retryable problem, bound current operation/revision, valid claim-time receipt, hash-consistent observations and the existing recomputed non-SATISFIED predicate. It never retries the refusal or infers business success from it. `collector.py` integrates classification; `runner.py` explicitly blocks main admission. The instrument and operational components are reused from the combined continuation runner. [Exact file provenance](component-provenance.json) records copied and changed files. Application behaviour, migrations, main fixtures/order, endpoints and analysis methods are unchanged.

Both originals retain raw **FAILED**, original grades and hashes. Proposed separate [B3](first-original-proposed-sidecar.json) and [P1](second-original-proposed-sidecar.json) sidecars record business correction **TRUE**, final spoken update **FALSE**, and timing censor reason `NO_SUPPORTED_COMPLETION`. Duration remains **600 seconds** and event-observed remains **false**. Thus their numerical latency contributions and model membership do not change. `COMPLETED` in the proposed instrument denotes completed collection, not successful speech. Missing anchors, acknowledgements and capture gaps remain unknown.

**No replay/restart of the affected comparison is recommended for this classification-only change.** Host/time discontinuities remain limitations. Both originals and all **1,498** planned identities are preserved; next remains sequence 3, P2, `01a11705-11f0-7a68-8c68-4da5c8126c84`.

## 3. All-recipe review

[Disposition matrix](recipe-disposition.json) covers **50 recipes × three arms**: 10 clean, 20 hidden-commit, 10 playback and 10 other boundary recipes. [Trace review](recipe-review.json) retains **178 historical attempts**, including 39 FAILED records. Nine retained traces support the new semantic proof: six UNKNOWN and three VIOLATED, including VIOLATED examples for every arm. Older records lacking sufficient timestamps/journals are not retrospectively reclassified.

Ambiguous provider sends reconcile before retry. Planned provider write faults are distinct from driver/service defects. Visibility exhaustion may return an unresolved update for grading; unproved raised timeouts still pause. Reconciliation is **eight attempts**; drain is **30 passes**. Compensating CREATE–CANCEL–CREATE can produce correct business state yet fail the frozen RESCHEDULED_APPOINTMENT predicate; that limitation is preserved. The matrix's misleading “latest” field was corrected to use recorded aware timestamps; the draft remains retained and no reported status changed.

## 4. Finite validation and retained failures

The declared nine serial local PostgreSQL executions finished in **6,054.91 seconds**, within the **6,600-second admission budget**. Every execution retained the original 600-second window, independent grades and two hash-verified backup copies. All raw statuses remain FAILED: six evidenced refusals and three deliberately injected uncaught technical exceptions after successful clean behaviour.

| Arm | Evidenced refusal → backup → permitted continuation | Injected defect → durable pause/no next admission | Collector process checkpoint/restart → no replay |
| --- | --- | --- | --- |
| B3 | [PASS](qualification/cal-v4-preflight-v2-refusal-b3.json) | [PASS](qualification/cal-v4-preflight-v2-defect-b3.json) | [PASS](qualification/cal-v4-preflight-v2-recovery-b3.json), 16 POSTs before/after |
| P1 | [PASS](qualification/cal-v4-preflight-v2-refusal-p1.json) | [PASS](qualification/cal-v4-preflight-v2-defect-p1.json) | [PASS](qualification/cal-v4-preflight-v2-recovery-p1.json), 17 POSTs before/after |
| P2 | [PASS](qualification/cal-v4-preflight-v2-refusal-p2.json) | [PASS](qualification/cal-v4-preflight-v2-defect-p2.json) | [PASS](qualification/cal-v4-preflight-v2-recovery-p2.json), 17 POSTs before/after |

Recovery preserves identity/deadline on the same boot. Backup precedes next admission. Test backup roots share one physical local disk; this verifies protocol handling, not independent hardware durability or fresh S3 permissions. [Qualification summary](qualification-summary.json) links proofs and retained source paths. Existing [8.2](../../phase-8.2-report.md), [completed 8.3](../../phase-8.3-recovered-outcomes.md) and 8.4 evidence is reused; historical stop headings are preserved.

Candidate/control tests: **68 pass** on Windows and Linux. Relevant regressions: **61 pass**. Lint passes; configured Windows typing passes **156 files**; strict native runner typing passes **20 files** with the dynamic SDK boundary isolated. Linux-wide typing has **11 errors in frozen Windows-specific helpers**, retained as a platform limitation. Setup/type/lint failures and one corrected test expectation remain in [diagnostic records](retained-diagnostic-attempts.json). That expectation now permits completing a paused exported slot's own backup while denying new admission.

**Additional concrete blocker:** [six declared local control checks](allow-failure-gap-result.json), under a 60-second budget, demonstrate that `allow_failure=True` returns an unrelated 409 or 500 at the stale-playback path for B3/P1/P2 without raising. The collector's catch-only pause cannot catch that call if later driver steps succeed. No such outcome is alleged for the two originals. This is not covered by the narrowly proved receipt refusal. The source was not silently changed during qualification. A semantic guard for deliberately permissive calls must be implemented and qualified before deployment, retaining expected stale refusals and barrier polling. Nine passing executions do not establish an error-free campaign.

The new refusal calibrations tie: all arms correct business state and withhold confirmation. First blocker is B3's fresh predicate or P1/P2's SATISFIED-receipt gate. No superiority follows. Evidence is scripted tone/client acknowledgement, not intelligible speech or human comprehension.

## 5. Preservation, feasibility and recommendation

[After-work verification](preservation-after.json): **4,212 protected files unchanged**. Frozen continuation members and accepted parent inventory match their recorded hashes. Original exports, grades, accepted first sidecar, historical receipts and saved identities remain unchanged. AWS instance **i-034252c3e9b083abf is STOPPED**; root disk **vol-0f667d76019af7a47** and S3/local evidence remain retained. Only read-only AWS checks occurred. The local qualification capsule was stopped after completion; its evidence remains retained.

[Calculation at 8 October 02:54:43 UTC](feasibility-final.json), using unchanged Sydney rates and the conservative elapsed-clock policy:

| Remaining serial allowance, plus two hours setup | Estimated finish UTC | Committed estimate including reserves | Fits $55 guard / $65 total / original deadline |
| --- | --- | --- | --- |
| 12 days | 20 October 04:54 | **$52.02** | YES, conditional |
| 13 days | 21 October 04:54 | **$55.52** | NO / YES / YES |

Observation alone requires **249.67 hours**. The historical pilot median gives approximately **255.24 execution hours** before setup; it is a reference, not a whole-bank guarantee. The 12-day plan's latest setup start under the conservative guard is **8 October 23:19:40 UTC**. Deadline remains **22 October 2026, 15:24:23.810674 UTC**. No clock or limit resets. Stopped-disk retention costs approximately **$0.512/day**; its decision is due **9 October 21:05:37.547530 UTC**. Billing/credit reporting can lag.

**Do not deploy this candidate.** Concrete remaining requirements are: (1) qualify the permissive-call semantic pause guard; (2) qualify handover of two closed originals and the unchanged 1,498 identities—the accepted v1 route expects one closed original; (3) review the candidate/sidecars, then separately freeze/authorize a deployable combined package; (4) recalculate feasibility and verify fresh-host/backup/timer readiness without resetting limits. Restarting the stopped host is not qualified. No broad pilot or optional research extension is proposed.

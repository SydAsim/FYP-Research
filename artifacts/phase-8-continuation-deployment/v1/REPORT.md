# Continuation v1 deployment — admissions stopped for a new refusal

## Freeze and authorization

The exact accepted package is `c308222096cf3c9026aa275e73fd7d75bce386e641824330f385dab02d4b609f`.
Acceptance and immutable freeze were recorded before deployment. Freeze manifest SHA-256:
`4b921d416b9111594531ca33f26b1b307e04b22241ef995b6e571ce96a21f3e7`.
The parent chain, continuation chain, 1,913 frozen members, 6,134 protected historical paths, three original archives and 158 original archive members passed verification.
The later preservation check passed again. Historical preview counts deliberately remain unchanged.

Separate deployment/launch authorization binds the actual fresh host and readiness hash.
Readiness SHA-256: `14fd53d2ec16b7b121c20b386fbbd85699424439338d9e4a507894f40011cbf7`.
Signed authorization is evidence of permission; actual service/admission records establish what ran.

## Actual deployment and admission

- Run: `p85-01a116f7-3b82-7a79-8653-3aee62dc99e9`.
- Region: ap-southeast-2; profile fyp-research; FREE plan verified. No paid speech/model services or plan upgrade.
- Fresh host: `i-034252c3e9b083abf`; root disk `vol-0f667d76019af7a47`.
- Standalone service started 2026-10-07 20:55:12 UTC.
- Slot 2 admitted **2026-10-07T20:55:15.021480Z**, 8 October 01:55:15 Pakistan time.
- Input p8v4-0484; P1; original attempt 1; execution `01a11705-11f0-7826-bd9d-9066d82c4452`.
- Its full observation deadline remains **2026-10-07T21:05:24.632653Z**.
- At admission verification: first original BACKED_UP, slot 2 RUNNING, 1,498 PLANNED. No slot 3 admission.
- Operational deadline remains **2026-10-22T15:24:23.810674Z**, 22 October 20:24:23.810674 Pakistan time.

## Concrete blocker

The P1 driver received a non-retryable HTTP 409 from POST `/internal/phase3/claims`:

```json
{"type":"https://example.invalid/problems/receipt-not-applicable","title":"Receipt not applicable","status":409,"detail":"A current SATISFIED receipt is required","instance":"/internal/phase3/claims","trace_id":"f0d10924-4790-4668-828f-d96ad23e3fc4","retryable":false}
```

The submitted receipt was `a19611ff-3567-4b8f-9bd0-12e7e3770da8`, expected revision 2.
The backend applicability check is in `apps/api_controller/phase3_claim_service.py:134`, with rejection at line 143.
The recorded stack proceeds through the ordinary correction/confirmation path:
study_v4 calibration finish_update → remedies recover → schedule → claims.
The provider truth log records CREATE followed by RESCHEDULE, with corrected resource version 1.
Business correction therefore has supporting provider facts; this does not establish a delivered confirmation.

This is **outside** the accepted narrow B3 `b3-evidence` refusal recognizer.
The frozen instrument retains raw FAILED and DRIVER_FAILURE, rather than relabelling every 409.
No retry, receipt relaxation, frozen-code change, new sidecar, replay, replacement or next admission is authorized by this stop.
This establishes a new unrecognized-refusal/classification blocker; it does not prove the backend safety check is faulty.

A durable master admissions pause was added while the current collector continued.
Its first pause was `UNRECOGNIZED_DRIVER_FAILURE_SLOT_2_NO_NEXT_ADMISSION`; subsequent frozen failure-handling notices remain retained.
The operational stop helper waits for the original window, verified slot backup and owned resource retirement, verifies version-pinned readbacks, saves master/operational evidence and requests compute stop.
Actual completion and stopped-host proof will be recorded separately; a scheduled stop is not a confirmed stop.

## Readiness and feasibility evidence

All 16 reviewed readiness gates passed before admission:
1,903 actual source hashes; pinned CPython 3.12.13 and three locked dependency environments;
13,629 installed RECORD hashes; immutable image digests;
one empty dedicated service-readiness diagnostic (not a research execution);
all four services HTTP 200; no main replay; exact ledger import and saved identities;
versioned S3 permissions and pinned archive readbacks; protected key permissions;
no inbound security-group access; cloud capacity and actual headroom.

Before admission: available RAM 7,362,691,072 bytes; free disk 160,538,947,584 bytes;
all cloud object versions 32,968,585 bytes; zero outstanding upload reservations.
These are point measurements, not peak-memory claims.

Conservative remaining 314-hour plan fit: projected finish 20 October 22:55:10 UTC,
estimated committed cost plus 30-minute tail US$54.64899357015955.
The US$65 total policy, US$55 admission guard and US$1.25 handover reserve inside those limits are unchanged.
The estimate is not a final bill or a guarantee; paused time still counts and continuation must be recalculated after resolving this blocker.
Observed FREE-plan credit balance before deployment was US$119.37; billing may lag.
This failure stop does not reset the clock or allow automatic limit increases.

Two independent absolute campaign stop timers and the watchdog were active before admission.
A service reload re-armed the relative preparation timer; a separate absolute preparation guard preserved its original 7 October 22:26:52 expiry.
Only after actual slot 2 admission were both preparation timers stopped, leaving both campaign absolute stops and watchdog active.
The accepted timer implementation has second-level calendar resolution; the policy retains its exact fractional deadline.

## Verified prelaunch backup

Bucket: `fyp-p82-20261005-018da1d6-803656589923`.

- Key: `exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/822e6875ee0f2599de6c59604def6ad1ba7820a0e5fa813fc5d3c7828737e66d.tar.gz`.
- Version: `.nxKrNbydlyw6LpPIZOSC1UxxE6Mg.LM`.
- SHA-256: `822e6875ee0f2599de6c59604def6ad1ba7820a0e5fa813fc5d3c7828737e66d`.
- 244,029 bytes; local archive, S3 version and complete downloaded member hashes verified.
- Original first execution raw FAILED, original grades and separate accepted sidecar remain unchanged.
- Slot 2 / stop backups require their actual completion proofs; prelaunch backup does not contain slot 2 outcomes.

## Authorized old cleanup

Old host `i-0a6196aff6f8098ac` was verified stopped and owned, then terminated without restarting.
Its owned, detached root `vol-07baf9132bce08e77` was deleted after independent retained evidence verification.
A later volume inventory returned no matching old root. S3 and local evidence were preserved.
The fresh disk is retained; no authority to delete it is inferred from the old-resource cleanup instruction.
Fresh stopped-disk retention is funded for 48 hours; retention beyond that requires a decision, not automatic deletion.

## Retained preparation attempts

All failed preparation/transport/readiness attempts remain separate from main outcomes.
These include Windows long-path freeze copying, upload-signature attempts, private-directory permission rejection,
SSM comment/line-ending problems, port TIME_WAIT inspection and the cancelled operational stop helper.
That helper was cancelled while waiting, with no output/backup operations; its v2 passes typed ObjectProof values into the unchanged qualified postflight function.
No application or frozen research source was patched.

## Check progress

From the project directory in a normal terminal with AWS CLI and profile fyp-research configured:

```powershell
powershell -NoProfile -File ".\artifacts\phase-8-continuation-deployment\v1\Check-Progress.ps1"
```

The helper is read-only, never starts a stopped host and never clears a pause.
The service, collector, backup wait and shutdown run on AWS without an active Codex chat.
A closed-window defect stop requires review; do not restart the stopped host or clear failure pauses.
The original 22 October deadline remains the outer limit even while paused.

## Disposition

Freeze and authorized deployment succeeded. Actual next admission occurred.
Uninterrupted continuation is **blocked by the new P1 refusal**. Preserve slot 2 as its original attempted outcome and leave the remaining 1,498 identities untouched.
No broader amendment or launch is performed in this work.

## Confirmed final disposition

The full 600-second slot 2 window finished. The frozen runner exported raw FAILED, graded it, verified its backup and retired only its isolated resources. The main service exited with status 1 on the durable pause; slot 3 was never admitted.

The outcome export SHA-256 is `bd4d32f4968eaff243d65d9cfe8fad36c603cd709c09ee7fdebd29746e90da42`.
Final ledger: **2 BACKED_UP, 1,498 PLANNED, zero active executions**. BACKED_UP denotes retained evidence, not research success.

| Evidence | SHA-256 / version | Verified status |
|---|---|---|
| Slot 2, 526,263 bytes | `8fb4547bd0eee33743997f9ad602fb4c03d0243ce117cbd5c11f1fb765daf739` / `B0toEx.sKtZy5q.HBTNWDk4j1W75NKmT` | Version-pinned download, full archive and member hashes PASS |
| Stopped-boundary master, 253,654 bytes | `f39e75cac63d077137ff6bd5e09ef6c2e66f7ddf3caa869ccd0fefa77fdf1661` / `Dvltv.4YHlHKxeB3N7goE.vTaaTCuf5l` | Version-pinned download, full archive and member hashes PASS |
| Operational evidence, 14,541,760 bytes | `1b9118f582ca8f999b768f3ccb2fc2d8241be75055caa1d47d2d14a37cb7f094` / `XpBm7FhdnvndXMM2vL6JjGtCMTHC3irW` | Same archive recovered to reviewed shorter path; full member hashes PASS |

All keys use `exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/<sha256>.tar.gz` in the existing bucket.
The operational archive's initial extraction failure is retained. Its identical downloaded archive was recovered under `/var/lib/p8c/o`; longest final member path was 224 characters. Neither failure handling nor short-path recovery changed research code or outcomes.

After these checks, watchdog was stopped and shutdown was scheduled for **2026-10-07 21:10:21 UTC**. A subsequent EC2 DescribeInstances independently confirmed the fresh host **STOPPED**. See `confirmed-host-stopped.json`; this is actual state, not an authorization or scheduled-stop claim.

The fresh root disk and all S3 versions remain retained. Disk retention review is due no later than **2026-10-09T21:05:37.547530Z** (10 October 02:05:37 Pakistan time), a conservative 48-hour bound. At the verified gp3 rate, this 160-GiB disk costs approximately US$0.512/day while retained; S3 retention also continues. No automatic fresh-disk deletion or host restart is authorized by the old cleanup instruction.

Continuation remains blocked. Required next work is review of this specific P1 refusal and its runner/analysis disposition, with versioned qualification if changed, plus a retention decision before the stated bound. The original deadline and funding limits have not been extended.

Additional local copies passed full archive/member checks under `C:/p8c1/s/x/slot`, `C:/p8c1/m/x/slot` and `C:/p8c1/o/x/slot`. Their pinned object receipts are recorded in `poststop-local-evidence.json`. Original first-attempt local evidence under `C:/fyp-p85` remains unchanged.
Slot 2 retained analysis: final_business_state_correct TRUE; correction_success TRUE; correct_final_update FALSE; unsupported_exposed_claim FALSE; incompatible_stale_exposure FALSE. Its 600-second timing record retains INFRASTRUCTURE_FAILURE and event_observed false. No accepted B3 timing sidecar was applied to P1.
The separate final verification checks all 1,500 saved identities/order against the downloaded master, confirms exactly two BACKED_UP and 1,498 PLANNED, rechecks frozen members and protected history, and binds the actual EC2 stopped-state evidence. PASS describes evidence/operational verification; it does not describe a successful campaign outcome or authorize continuation.


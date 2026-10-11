# Continuation v8 — clock correction and exact 120-original boundary

**Clock/handover qualification PASS; deployment BLOCKED by storage feasibility.**
Review candidate only. No acceptance, freeze, AWS start, application-stack start,
research execution, replay, new observation window or regrading occurred. AWS
instance `i-057344e5372faf62f` remains stopped; its encrypted 160-GiB owned root
`vol-09dbb42bbf607f5de`, S3 versions and all local evidence remain retained.

## Exact narrow runtime changes

`runtime.diff` records every edited/new runtime code line against frozen v7.

| File | Change and preserved invariant |
| --- | --- |
| `clock_sampling.py` (new) | Monotonic-before → UTC wall → monotonic-after; midpoint operand, bracket width and half-width uncertainty. Reject nonfinite/naive, decreasing or >0.050-second brackets explicitly; do not call sampling delay a rollback. |
| `runner.py` | Read/seal-check clock metadata and boot identity first, then obtain the fresh pair. Remove the caller's stale wall operand. Print actual operands, anchor, boot, bracket, elapsed differences, uncertainty range, comparison RHS and result to the service journal. A rejection also records the operands in the durable notice chain before the existing pause. |
| `handover.py` | Same sampler for future boot anchors after metadata/authority checks; store complete paired anchor. New v8 provenance includes sampling hash; continuation authority binds frozen v7 as immediate parent. Original authority/limits remain unchanged. |
| `closed_restart.py` | New pinned 120-original boundary, next sequence 121 P1; retain old clock pause, metadata, raw export hashes, notices, sidecars and receipts in restart history. New v8 source/root/receipt paths. Import no live application databases. |
| `reuse_prepare.py` | Retained-host import reads actual old v7 root and its clock pause; verifies 120/1380 and records next 121. Existing external authority, quiescence and resource gates remain. |
| `test_clock_continuation_v8.py` (new) | Twelve clock and six exact-boundary/actual-backup controls; only temporary calibration metadata, no main admission capability. |

`controls.py`, including the original five-second comparator, boot mismatch,
decreasing-counter and 360-hour/absolute-deadline checks, is byte-identical to v7.
Both near-threshold (exact five seconds vs one microsecond beyond) and genuine
six-second rollback controls retain rejection behavior. Combined sampling
uncertainty is **reported**, never added to the five-second allowance. The point
estimate still uses the unchanged comparator. A bracket up to 50 ms limits local
sampling error; it does not certify absolute UTC accuracy or human understanding.
An uncertain sample pauses admissions instead of widening the guard.

Successful samples are structured operational journal entries, avoiding repeated
ledger growth on every five-second watchdog check. Rejected samples are durable
ledger notices included in ordinary metadata backups; anchor operands are sealed
in `host-clock.json`. Operational journal preservation remains the reviewed stop
procedure. Journal rotation/absolute UTC accuracy are not newly qualified here.
This fixes the demonstrated measurement defect; it does not reconstruct the
unrecorded operands of the historical rejection or claim an NTP step occurred.

No changes to application code, migrations, contracts, research fixtures, arms,
driver behavior, refusal/response guards, oracle, analyses or 600-second windows.
The existing executable snapshot fix, S3 bounded inventory retries, v6 backup
copier/readback and v7 operational overlay are reused unchanged. Historical
`continuation-backup.json` version headings remain `v6`, a documented inherited
copier label; v8 authority/provenance identifies the current package separately.

## Qualification and unsuccessful attempts

Predeclared `PLAN.md`: 18 distinct focused controls, 240-second attempt bound,
pinned Linux image
`sha256:5faee27d3793882b26aa166de48fc26d7939710ac9435b0fe7f988c8765497d8`,
Python 3.12.13, network disabled, 1 GiB memory/one CPU. No installs or broad suites.

- First attempt: **11 clock controls passed**, one test failed on exact IEEE-754
  equality, metadata fixture unfinished when the 240-second bound stopped it.
  Corrected only the failed assertion to approximate float comparison. Its result,
  stopped container and partial metadata remain. Initial lint failures remain in
  `static-initial.txt`; final Ruff passes six code files.
- Second finite plan: run only that corrected assertion and six unfinished
  boundary controls on container-local files. **Six passed**, including exact
  import, altered identity/active slot/incomplete receipt rejection and actual
  prelaunch backup/readback. The complete backup was produced, but its check was
  interrupted at the same bound. Stopped container/partial readback are retained.
- Final finite plan: **one unfinished check only**, complete the existing normal
  archive's independent stored-copy readback and corrupt-metadata rejection.
  **PASS in 45.078 seconds**, no copier rerun and no passed controls repeated.

Aggregate: **18 distinct required controls qualified**. Interrupted attempts
remain TIMEOUT, not retroactively PASS. The initial floating-point failure remains
recorded. Qualification took two bounded unsuccessful attempts and one targeted
completion; this is not an error-free-campaign claim.

The first review-builder attempt also stopped on ordinary Windows path access
to a 270-character frozen file. The file was present through its extended-length
path; the builder now uses that same read-only path method as the original freezer.
`build-attempt1.json` retains the failure. No frozen file was repaired or replaced.
The second builder attempt passed preservation checks but failed a descriptive
dependency inventory lookup for a pnpm lock absent from the qualified research
deployment source. The inventory now names the actual unchanged deployed files;
no dependency was added or installed. `build-attempt2.json` and its builder source
retain that failure. Neither failed builder produced a candidate archive.

Final runner-only noqa comment is proven byte-reconstructable to the first tested
source and AST-identical. All other runtime hashes match those exercised; only
the failed test assertion changed. Mypy passed five runtime files; the final
runner was also checked. Existing PostgreSQL/refusal/permissive-response/snapshot,
operational-limit and backup qualifications are reused with hashes, not repeated.

Actual prelaunch archive: **35,806,214 bytes**, SHA-256
`592acfe8fe8f8d5616426483033cd0b5f60e171436daec9d3cf1442400cc0e10`.
Actual complete archive: **35,807,410 bytes**, SHA-256
`0faf68ce986469cbb0033a0e77011acb1fdb6868f17a9cbaf16d88a37b45d706`.
Actual copier and independent stored-copy readback verify complete restart history,
120 receipts, ledger/notices, original identities and public records. Missing
restart boundary and corrupted historical pause are rejected. The tests use
genuine historical public readiness/receipts as copying fixtures only; no v8
acceptance/readiness/launch record is fabricated or authorized by those tests.

## Evidence and next identity

Exactly **120 BACKED_UP / 1,380 PLANNED**, no active slot, 1,500 original identities
in saved serial order. Both original raw FAILED statuses, original grades and
separate accepted timing sidecars remain unchanged inside preserved history.
Every raw export's identity and receipt hash is verified. Reuse the previously
verified 120 pinned S3-version checks and full stopped-master readback; fetch only
the absent 83–119 archives by pinned version, verify whole SHA-256/trailer and
select their exact existing execution exports. All 37 transfers succeeded on
attempt 1; transfer partials/copies are retained. Slot 120 was already verified.
No oracle or driver was rerun.

Next: **sequence 121 / p8v4-0108 / P1 / attempt 1**,
execution `01a11705-11f1-75f4-b64e-8f0a3679518b`, fixture hash
`631eaf33600be4ae6bd97338f75481265282e45d44a6463d05bc030661279f7d`.

Authoritative stopped-master hash:
`5892e3b90b577537c99720debd87726ed424c06b319f404edd60169a449ca7e7`;
S3 version `87kdc4YhTj9U3OqnEya6RwaNdADynjkC`. Frozen-v7 parent package:
`9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817`;
parent freeze `3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46`.
Member hashes, all preserved historical files, source closure and parent bytes
are verified before/after; exact final inventory/archive hashes are in
`candidate-package.json`. The inventory identifies source, fixtures, executable
code, oracle/analysis, runtime seals and evidence separately without altering them.

## Refreshed feasibility — unchanged limits

Read-only 10 October AWS measurements: FREE/ACTIVE plan, **US$113.55 credits**,
host stopped, owned encrypted root retained, all-version cloud usage
**1,694,494,293 bytes**. Current Sydney pricing matches accepted rates:
compute $0.1197/hour; IPv4 $0.005/hour; gp3 $0.096/GiB-month;
conservative first-tier S3 $0.025/GiB-month. No paid Cost Explorer query was added.

At **10 October 12:07:54 UTC**, the unchanged 290-hour/1,498-slot allowance scaled
to actually pending 1,380 gives **267.1562 hours**, plus two hours preparation and
30 minutes shutdown. Projected shutdown **21 October 17:47:16 UTC** precedes the
original **22 October 15:24:23.810674 UTC** deadline. Original elapsed-clock cost
accounting, including paused time, retained storage, $5 operational reserve and
$1.25 handover reserve, projects **US$58.08**. No allowance reduction or limit
increase. Latest preparation start under the same conservative cost calculation:
**11 October 01:19:58 UTC**; recalculate before any future authorized boot.
Billing/credits can lag; estimates are not invoice caps or completion guarantees.

**Storage fails:** measured 35.807-MB metadata base, unchanged extra 8.336-MB/slot
payload allowance, twice the larger retained compressed-ledger slope
(8,443.68 bytes/slot), 256 KiB/slot index allowance and current all-version usage
project **73.70 GiB**, or **74.70 GiB with the next-slot reserve**. The unchanged
cloud and dedicated local-backup caps are **60 GiB**. This conservative planning
projection is not an assertion that actual future growth is known; it nevertheless
fails the reviewed feasibility rule. Do not lower assumptions solely to pass it.
Even omitting the extra payload allowance would not satisfy the same cap/reserve.
No backup-size optimization or new retention-policy change was silently added.

## One combined decision — currently HOLD

**Recommendation: review this exact clock/boundary candidate; do not authorize
deployment as ready.** Its code/closure checks are qualified, but a combined
acceptance → freeze → deployment decision cannot safely advance to boot while
the 60-GiB feasibility check fails. The concrete outstanding requirement is a
reviewed, measured storage-feasible evidence/metadata route under the existing
limits; this task does not implement an additional backup-policy amendment.
No optional research extension is proposed.

If that requirement is separately resolved in a subsequent exact candidate,
one explicit combined decision may accept its package/archive hashes, authorize
freeze against v7 and separately authorize retained-host deployment only after
all gates pass. `DEPLOYMENT_ORDER.md` specifies the guarded route, real prelaunch
backup → genuine readiness/launch → complete backup order, fresh paired boot
anchor, ownership/quiescence, independent preparation timer and original stop.

| Gate | Status |
| --- | --- |
| Clock correction / genuine rollback, boot mismatch and deadline | PASS |
| Exact 120/1380 boundary, identities, notices and original receipt/export hashes | PASS |
| Actual prelaunch and complete backup/readback closure | PASS |
| Source/application/fixture/oracle/analysis preservation | PASS (inventory verified) |
| Time and US$60/US$65 estimate | Conditional PASS at stated timestamp |
| 60-GiB cloud/local capacity projection | **FAIL — deployment blocked** |
| New live readiness/permissions/resources/timers/backups | NOT EXECUTED; requires later authorization |
| Acceptance/freeze/deployment/launch | NOT RECORDED |

Pause alone still does not stop compute. Keep the existing preservation/shutdown
procedure and independently verified two-hour preparation-stop guard on any
future preparation; after its reviewed retirement only existing watchdog/operator
shutdown and original absolute stop remain. Snapshot/clock fixes do not add an
automatic post-pause shutdown. Retained-root decision is still due **11 October
09:33:51.252814 UTC**. No evidence/root deletion is authorized here. Reconciliation
remains eight **attempts**, drain thirty **passes**.

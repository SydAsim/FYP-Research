# Slot-145 bounded diagnosis — original cause still blocked

## Verdict and preserved boundary

**No demonstrated code defect and no qualified continuation procedure yet.** The
original slot-145 exception, traceback and HTTP evidence are missing locally.
Current S3 connection failures do not establish what caused the original driver
failure. No correction candidate or runtime diff is justified.

No AWS boot, service restart, pause clearing, freeze, launch, research execution,
replay, replacement, regrading, dependency installation or evidence deletion was
performed. AWS was last independently confirmed STOPPED at
2026-10-11T16:05:07.617447Z. A fresh read-only EC2 request failed with
ConnectTimeout; it is **not** a fresh state confirmation. Root
`vol-09dbb42bbf607f5de` and pinned S3/local historical evidence remain retained.
The existing retained-root decision deadline is **2026-10-13T16:04:13.525847Z**.

Boundary remains **145 BACKED_UP / 1,355 PLANNED / zero active**. All 1,500 saved
identity/order fields match frozen bindings. Next is sequence **146, P2, attempt
1**, execution **01a11705-11f1-772d-8190-c43552871801**, case p8v4-0361.
Its deadline remains null; nothing has been admitted. The twelve retrieved
inspection members match their included manifest, but the complete inspection
hash/master SQLite were not independently verified locally. The prior stopped
boundary preservation proof records pinned-master full readback PASS on the host
and verification of all 145 pinned backups; this is reused evidence, not a new
local full-archive verification.

## Inventory before retrieval

`local-inventory.json` records recursive file sizes, locations and errors at
16:59:27Z, before the new transfer. `downloads-inventory.json` subsequently
checks the user's Downloads folder; it contains no target candidate.

| Checked location | Logical file bytes |
|---|---:|
| D:/FYP-ResearchBackups (before new staging) | 44,442,047 |
| D:/P82 | 28,930,136 |
| D:/P83 | 95,449,610 |
| D:/P83R7 | 95,449,610 |
| Entire accessible E: inventory | 11,070,578,676 |
| Repository on C: | 7,966,999,304 |
| C:/Users/syeda/Downloads | 1,693,419,004 |

D: research directories total **264,271,403 bytes / 252 MiB**. The inventoried
locations total about **19.55 GiB** of logical files; this includes historical
duplicates and is not the same as physically allocated disk usage. Known old
slot-145 diagnostic staging totals **107,939,285 bytes / 102.94 MiB** across C:/E:.
The scan excludes .git, node_modules, .venv, cache and system directories. Its
43 access errors are old pytest `*current` symlink aliases, retained in the
inventory; this is not a claim to have inspected every byte on all disks.
No file of target size 37,906,551 bytes and no target execution export was found
in the inventoried locations. No Python/AWS/curl transfer process was present
before or after the bounded attempt. One diagnostic Python process ran during it.

Before transfer: free C: **18,460,467,200**, D: **107,700,801,536**, E:
**185,520,205,824 bytes**. Final measured free space is in `final-feasibility.json`
(C: 18,952,085,504; D:/E: unchanged). No evidence was deleted to obtain headroom.

`range-audit.json` rechecks range offsets, lengths, hashes and pinned version:
176 transport2 pieces / **11,534,336 bytes**, and 147 transport3 pieces /
**9,633,792 bytes**, all valid against their proofs. These are inspection-archive
ranges, **not slot-145 original ranges**; they cannot be merged into the requested
original. Shared old deadline **16:48:33.541153Z** remains exhausted and unchanged.
The old lock/checkpoints, failed CLI pieces and provisional extractions remain.
No large inspection transfer was restarted or copied again.

## One finite retrieval, then stop

The new user-requested diagnostic attempt is separately recorded, not a reset of
an exhausted transport checkpoint. Canonical staging:
**D:/FYP-ResearchBackups/slot145-diagnosis**. One process, one SDK route, one
16-KiB pinned probe before larger reads; no alternate transport or wrapper restart.

Declared controls: connect 5s, response read 10s, 180s overall, one global retry,
48-MiB temporary bound; no hidden SDK retries (`total_max_attempts=1`). The
script refuses automatic reuse of its already recorded attempt. Receipts resolve:

- Bucket: `fyp-p82-20261005-018da1d6-803656589923`
- Key: `exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/8abe7597a0e59154cf66e682fd08f3440fff815c458db0bdc8fe83666091ad24.tar.gz`
- Version: `RPSiYO12M2tM251ZCuLVOEK3IUn4NYHM`
- Size: **37,906,551 bytes**; SHA-256: **8abe7597a0e59154cf66e682fd08f3440fff815c458db0bdc8fe83666091ad24**.

Both probe attempts failed with **botocore ConnectTimeoutError** while executing
version-pinned GetObject for bytes 0–16383, at **17:01:21.912353Z** and
**17:02:04.273122Z**. No HTTP body/version/range was obtained. Total elapsed
**83.549763s**, **0 bytes retrieved**, **37,906,551 bytes remaining**. Staging is
**1,248 bytes**, only attempt/result records. Per-request elapsed time exceeded
the nominal connect timeout, which is not a total DNS/address-resolution deadline;
the overall attempt nevertheless stopped within its declared 180-second bound.
This does not qualify a generally strict process-level deadline implementation.
No credentials or signed URLs were logged. `result.json` is retained in staging;
there are no active transfers and no automatic retry scheduled.

## What the original evidence currently establishes

The preserved journal/notice sequence agrees:

1. 10 October **17:56:31.611033Z**: B3 original slot 145 admitted.
2. Observation deadline **18:06:47.750198Z**.
3. **18:06:53.900124Z**: master STOP_NEW_ADMISSIONS with DRIVER_FAILURE;
   durable pause **18:06:53.908883Z**.
4. **18:06:53.939767Z**: original exported; services quiesced immediately after.
5. **18:07:21.797955Z**: pinned backup verified; **18:07:21.811352Z** BACKED_UP.
6. **18:07:31.210142Z**: campaign prints VERIFIED BACKUP 145/1500.
7. **18:07:39.739009Z**: next admission rejected with PAUSED_ADMISSIONS.

The original driver exception occurred within slot 145; its master pause was
propagated **before** that backup. Slot 146 did not execute. The secondary
PAUSED_ADMISSIONS is not the original exception, and no retrieved evidence shows
the watchdog caused DRIVER_FAILURE.

Frozen source explains propagation, not cause: `collector.py:452–481` saves
failure type/detail/full traceback, classifies a narrowly recognized refusal or
writes slot DRIVER_FAILURE/pause; `runner.py:395–402` propagates the slot pause
after export. The runner then backs up the closed slot and rejects another
admission. Without the original export and slot ledger it is impossible to name
the actual failing function/operation/time or distinguish transient failure,
application/runner defect, resource issue or evidence corruption.

Precisely missing: verified `slot/executions/01a11705-11f1-7386-a804-76b957c218d5/export.json`
(failure.type/detail/traceback, HTTP observations/checkpoints),
`slot/ledger.sqlite3`, checkpoint.json and their original member-manifest hashes.
These are retained in the specified original archive and retained AWS root.

## Provisional evidence, no comparative analysis

Saved completion counts: **B3 49, P1 48, P2 48**; **49 unique task IDs**, **48
complete B3/P1/P2 sets**, one incomplete set **p8v4-0361 (B3 only)**. Recipe/stratum
coverage is recorded separately in `cluster-coverage.json`. Task counts are not
independent callers, speakers or recordings, and repeated cell members do not
create independent scenario families.

The 49 task IDs span **21 recipe clusters**: CLEAN 36, PLAYOUT 7,
OTHER_BOUNDARY 3, HIDDEN_COMMIT 3 unique tasks. This imbalance further limits
any preliminary outcome interpretation.

In-place verification reuses local originals **1–38 and 120**: **39 complete
archive hashes/bytes match pinned historical receipts**, and all 39 export member
hashes/identities match their manifests. No failed verification was excluded:
`verification_failures=[]`. Available grades span B3 12 / P1 13 / P2 14 and only
**12 locally complete grade comparison sets**. The other **106 completed slots'
grades are unavailable locally**, not success, failure or oracle UNKNOWN by
assumption. Other local inspection exports are retained but not admitted into
this summary without the same full original-archive verification.

Read existing frozen grades only, pooled for safety/integrity monitoring; no
inferential tests, arm ranking, adaptive scheduling or retrospective regrading:

- Raw status: **36 COMPLETED, 3 FAILED** (originals 1, 2, 3).
- Final business state: **39 TRUE**; forbidden effect **39 FALSE**.
- Correct final update: **36 TRUE, 3 FALSE**.
- Correction success: **9 TRUE, 30 NOT_APPLICABLE**; clean success **30 TRUE,
  9 NOT_APPLICABLE**.
- Unsupported exposed claim / incompatible stale exposure: **39 FALSE** each.
- Explicit retraction and corrective-delivery challenge endpoints: **39
  NOT_APPLICABLE** each. This subset provides no durability-challenge result.
- Saved values contain zero endpoint UNKNOWN and zero raw TIMEOUT **in these 39
  available records only**. Missing 106 grades prevent full-campaign counts of
  refusals, failures, timeouts or UNKNOWN. Three retained raw failures are
  documented refusal outcomes; the first two historical infrastructure timing
  classifications and separately accepted refusal timing sidecars remain
  traceable, unchanged. Third original already stores NO_SUPPORTED_COMPLETION.

All evidence is **SCRIPTED_TONE_SEMANTIC_PROXY**. Acknowledgements do not establish
human exposure/comprehension, actual speech recognition, intelligibility or
end-to-end native audio performance. Correct business state with missing final
update demonstrates why these endpoints must remain separate. The accessible
subset is availability-limited, dominated by clean cases, not a representative
study estimate. No superiority, novelty, equivalence or completed-study conclusion
is supported.

## Time/cost and minimum next step

At **2026-10-11T17:10:09.287065Z**: unchanged allowance
`290 * 1355 / 1498 = 262.316422h`, plus **2h preparation + .5h shutdown** gives
**264.816422h**, against **262.237368h** remaining. **Fails by 2.579054h**.
The 600s-window-only floor is **225.833333h**, excluding drivers, setup, backup,
collection, shutdown and recovery. Earlier calibrated serial median 613.386s is
not whole-bank qualification; no new throughput measurement or lowered planning
assumption was substituted. Additional diagnosis/maintenance consumes more time.

The unchanged conservative elapsed-clock method, previous rates and reserves
projects **US$62.10264**, above the **US$60 admission guard**, below US$65. It
charges elapsed paused hours conservatively and includes prior elapsed spending,
retained-storage/operational reserve; it is not an invoice or a fresh price/credit
verification. Live billing/pricing cannot currently be validated. **No time or
cost-feasibility PASS.** The US$60/65, 80-GiB caps, original deadline and 600s
windows remain unchanged.

First obtain the **specified pinned original archive** through a working read-only
channel and verify its full hash; reuse it in place. Do not start another transfer
automatically. The smallest extraction is prepared as `extract_required.py`:
only original manifest/export/checkpoint/slot ledger, full archive/member checks,
no live app. If network retrieval stays blocked, `RETAINED_ROOT_FALLBACK.md`
prepares an offline-root-on-clean-helper route, with exact parameterized commands,
autostart prevention, independent 15-minute stop guard, bounded extraction,
pause preservation and root reattachment. **Unexecuted and not yet qualified**:
clean helper/permissions, current connectivity, cost and shutdown readback remain
concrete prerequisites. It does not assume an old preparation reserve is feasible.

Even after diagnostic retrieval, continuation requires a demonstrated cause,
justified version/recovery, preserved 145-closed boundary and passing unchanged
feasibility/readiness gates. Present evidence does not authorize unchanged-code
resume or justify a speculative fix. Stop here for review; no freeze/launch.

## Focused work/checks retained

Only this new diagnostic directory was added: inventory/retrieval/range audit,
read-only saved-grade summary, prepared extractor, fallback and reports. The new
48-MiB-bounded D: folder contains metadata only. Frozen v9/application/fixtures,
grades, ledger identities and migrations have **no diff**. Reuse the earlier
3425-file frozen-v9 PASS in `../attempt2/frozen-v9-preservation.json`; do not
describe it as a new qualification run.

Checks: 323 saved range proofs passed (inspection only); 39 archive/export
verifications passed; all 1,500 saved bindings matched; 12 inspection member
hashes passed. One new retrieval attempt failed after its one permitted retry;
one read-only EC2 lookup failed. Diagnostic Python AST syntax checks passed;
prepared fallback/extractor were **not executed or runtime-qualified**. No code
defect reproduction, research scenario, broad regression or 600s test was run.
Every prior unsuccessful attempt is retained. Machine-readable evidence and
commands are alongside this report; the D: attempt/result files remain in place.

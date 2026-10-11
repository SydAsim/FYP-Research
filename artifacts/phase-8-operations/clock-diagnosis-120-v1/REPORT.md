# Clock-stop diagnosis — preserved 120-original boundary

## Verdict

**Confirmed measurement defect; exact historical operands unavailable.** Frozen v7
can report `WALL_CLOCK_BACKWARD_STOP_ADMISSIONS` with perfectly aligned clocks.
Its watchdog captures wall time, performs resource measurement and a bounded S3
inventory, then samples monotonic time. Delay between those reads is counted as
clock divergence. Ten deterministic controls reproduced this and retained real
rollback, wrong-boot and decreasing-monotonic detection.

The retained history strongly supports this mechanism for the stop: one rejected
watchdog sample, no subsequent fresh-clock rejection, continuous collector times,
and no NTP step logged near the event. **The actual duration of the stale sample
and a unique cause for that particular rejection are not demonstrable**, because
the runtime persisted neither operand. No discrete backward clock step has been
established. The report does not relabel the retained pause or change grades.

## Exact check and recoverable numbers

| Value | Recorded evidence |
| --- | --- |
| Anchor wall | `2026-10-09T16:08:42.718627+00:00` |
| Anchor monotonic | `310.287448543` seconds |
| Anchor boot | `7abb4fdc-0087-4877-bfdd-31c2b7ec37f3` |
| Anchor SHA-256 | `d1a10553b87af960d5c9befc3dffa86fffc6d039794546444f586e54fd9d8a38` |
| First rejection notice | n=15603, `2026-10-09T23:14:41.752107+00:00` |
| Durable pause written | `2026-10-09T23:14:41.760070+00:00` |
| Notice wall minus anchor | `25559.033480` seconds |
| Pause wall minus anchor | `25559.041443` seconds |

For the actual (unrecorded) wall argument `T` and monotonic reading `M`, the exact
frozen calculation was:

```text
wall_elapsed = (T - 2026-10-09T16:08:42.718627Z).total_seconds()
mono_elapsed = M - 310.287448543
reject if wall_elapsed < mono_elapsed - 5
```

The notice and pause timestamps are new wall reads after this comparison. Neither
is `T`, and the archive contains no triggering `M`. The two numeric differences
above describe recorded timestamps, not a reconstructed guard result.
`calculation.json` explicitly leaves missing operands null.

The offline control uses exact frozen watchdog argument order with synchronized
clocks: wall elapsed **100**, then two seconds of resource work and six seconds
of inventory work, then monotonic elapsed **108**. The check becomes
**100 < 108 - 5 = 103**, hence rejection. A fresh paired sample after the same
work gives **108 < 103**, which is false. These are synthetic diagnostic values,
not historical AWS readings.

## Source trace and anchor assessment

- `runner.py:794`: `watchdog_tick(root, utc(), meter(root), cloud.inventory(), ...)`
  evaluates its arguments before entering the function. S3 work is allowed up to
  120 seconds by `inventory_read.py`; a successful slow inventory need not log a
  retry/error.
- `runner.py:582–612`: passes that earlier `at` to `verify_clock`; after catching
  its ValueError, continues into `verify_run`, which takes a fresh wall reading.
- `runner.py:195–207`: reads/seal-checks clock metadata before sampling monotonic
  time. Even this local work separates the caller's wall and monotonic readings.
- `controls.py:290–302`: boot mismatch and decreasing monotonic checks precede
  the five-second divergence comparison. Threshold and deadline were unchanged.
- `handover.py:307–322`: captures `at = utc()` before the anchor monotonic read.
  This also lacks a sampling bracket. A large anchoring offset can trigger the
  same message; the controls demonstrate that possibility. The retained anchor
  is hash-sealed, matches readiness and slot 120's boot, and passed fresh checks
  before and after the event. No persistent >5-second anchor offset is shown.

These four inspected runtime files match the accepted v7 candidate inventory,
and their before/after hashes match. No runtime correction was applied.

## Clock journals and boot identity

Chrony selected `169.254.169.123` at 16:03:44.608982 UTC and logged a
**1.301109-second step** at 16:03:45.910139 UTC on 9 October. This recorded boot
adjustment precedes the sealed anchor by **296.808488 seconds**. It is not
the 23:14:41 rejection and cannot directly explain post-anchor divergence.

There is no chrony step logged near the rejection. Falseticker/source-selection
messages begin at 01:29 UTC on 10 October, after the campaign had stopped. They
do not establish an adjustment at the trigger. `NTPSynchronized=yes` at
preservation time is a later status, not proof of clock accuracy at the trigger.
The retained journal is a unit journal in wall-time format, not a complete kernel
clock audit or a journal export with monotonic timestamps. Unlogged adjustments
and smaller clock drift therefore cannot be categorically excluded.

Slot 120 records the same boot ID as the anchor. The exact guard reaches its
divergence check only after the boot comparison passes. No boot mismatch notice
was found. Boot identity is verified from retained evidence, not a new boot.

## Event sequence and timing implications

1. Sequence 120, P2, was admitted at 23:10:20.512695 UTC. Its original
   observation deadline remained **2026-10-09T23:20:31.190524+00:00**.
2. At 23:14:41.752107 UTC the watchdog wrote one divergence notice; the durable
   pause followed at 23:14:41.760070. No wall/monotonic operands were included.
3. The current collector continued through its original full window. Slot 120
   contains **115 polls**, no negative gaps, and no recorded
   collection errors. Poll gaps range from **1.309127**
   to **6.519575 seconds**. Its final poll starts at
   **2026-10-09T23:20:31.190685+00:00**, **0.000161 seconds**
   after the unchanged deadline. No shortened window is shown.
4. Verified backup 120 was logged at 23:21:00.970648 UTC. At 23:21:35.859004 the
   parent refused its next admission with `PAUSED_ADMISSIONS` and exited. The
   watchdog continued until evidence-preservation quiescence on 10 October.

The stale watchdog operand is an admission-safety measurement. It is not a
recorded appointment, playback or outcome timestamp. This defect alone provides
no basis for shifting original timestamps, regrading outcomes or replacing any
original. Collector deadlines and research event timing rely on recorded UTC;
if a genuine adjustment is later established, affected latency/window claims
would need a separately traceable timing review. Current evidence cannot certify
absolute UTC accuracy or retrospectively provide paired monotonic event times.
Slot 120's continuity does not establish identical timing quality for every
earlier original. Their grades and existing timing sidecars remain unchanged.

## Smallest justified next correction and procedure — proposed only

1. In a new research-runner version, capture a fresh paired clock sample inside
   `verify_clock` **after** metadata/seal/boot reads. Do not use the earlier caller
   wall argument to compare with a later counter. Bracket the wall read with
   monotonic reads and reject an excessively delayed/uncertain sampling bracket
   explicitly, rather than calling it clock rollback. Preserve the existing
   five-second divergence limit, absolute stop time and all admission gates.
2. Persist the actual wall/monotonic operands, bracket width, anchor hash, boot
   IDs, computed differences and caller in the durable diagnostic notice. Use
   the same paired-sampling approach for a new boot segment's anchor. Never
   overwrite the old anchor, notices or pause.
3. Update only the closed-boundary continuation metadata needed for **120 closed /
   1,380 planned**, next **121, P1, attempt 1**. Existing v7 `closed_restart.py`
   and `reuse_prepare.py` are pinned to 82 closed/next 83 and cannot be reused
   unchanged for this boundary. Preserve all 1,500 identities, receipts, raw
   grades, historical notices and sidecars; restore metadata only, not old live
   databases or drivers.
4. Qualify the narrow correction and boundary offline in the deployment-matching
   pinned runtime, then present the version for review/freeze and separate
   deployment authorization. Current controls are Windows Python 3.12.14 pure
   arithmetic/source-expression tests, **not Linux deployment qualification**.
5. A future authorized retained-host boot must use the reviewed preparation-stop
   guard, owned-unit quiescence, source/dependency checks, exact closed-boundary
   import, genuine readiness records, verified backup sequence and absolute
   shutdown timers. A new per-boot counter anchor must retain the original
   operational start and **22 October 2026, 15:24:23.810674 UTC** deadline.
   Recalculate feasibility under **US$60 admission guard / US$65 total ceiling**;
   any failed gate stops continuation. No new instance is justified by this
   clock-reader defect alone.

Directly restarting v7 or clearing its failure pause is not justified. No clocks,
thresholds, deadline, application behaviour, study inputs, analyses or observation
windows were changed here. No acceptance, freeze, deployment or launch occurred.

## Validation and preservation

- Ten predeclared controls: **10 PASS, 0 FAIL**, 0.088120
  seconds. No scenarios, pilot, services or observation windows executed.
- Pinned inspection archive SHA-256:
  `7dbfc44f3df08717acd802cd6fda7b79c9e6e281cd87a7e4fbb423747ac59859`.
- Complete master SHA-256:
  `5892e3b90b577537c99720debd87726ed424c06b319f404edd60169a449ca7e7`.
  Inspection/member/master hashes verified after bounded short-path extraction.
- Master integrity, full notice hash chain, saved order and all 1,500 identity
  bindings passed; all 120 local backup-receipt hashes match the ledger. The
  preserved master/member hashes match before and after read-only inspection.
  The prior preservation verified all 120 pinned S3 versions; this diagnosis
  reuses that evidence without repeating its cloud checks.
- Slot 120 pinned archive SHA-256 `f061057a2dec11196dd82231e37e6ae8502416e5402cba2d9b7524c3df59e2b2`:
  complete archive and all **836** manifest
  members verified. Original export SHA-256 `a1f5f025bf6fd6118102293ed03447e3a57b1fffd7b4a59c5694b0d8f9e1113c`.
  No oracle rerun or grade edits. Four bounded version-specific range reads
  reconstructed that archive; pieces and transfer records were retained.
- AWS host `i-057344e5372faf62f` read back **stopped**; owned root
  `vol-09dbb42bbf607f5de` remains attached with deletion-on-termination disabled.
  Existing retained-root decision deadline remains **11 October 2026,
  09:33:51.252814 UTC**. Evidence and root were not deleted.

Files created here: diagnostic extraction/read scripts, fixed control plan and
results, pinned local evidence copies/transfer records, calculation, this report
and a final hash manifest. No application or frozen package file was modified.
Read-only S3/EC2 calls retrieved existing evidence/state; AWS compute stayed off.
No failed control or transfer attempt occurred. One unsuccessful diagnostic
timing summary included nested historical polls; its script and result remain
retained and explicitly invalidated by `retained-diagnostic-issue.json`. The v2
reader bound the exact slot-120 execution prefix/ID/arm/attempt and verified its
exported poll hashes. No raw record or grade changed. The diagnosis remains
bounded by the historical instrumentation gap stated above.

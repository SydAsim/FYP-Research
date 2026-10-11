# Phase 8 progress and guarded stop — 10 October 2026

## Verified state

- **120 BACKED_UP / 1,380 PLANNED / zero active** — 8% of 1,500 original executions
  retained, not a claim that every business or speech outcome passed.
- Paused at 2026-10-09 23:14:41.760070 UTC (10 October 04:14:41 Pakistan time).
- Reason: `WALL_CLOCK_BACKWARD_STOP_ADMISSIONS`.
- Campaign service failed; watchdog was still running when inspected. Neither
  was restarted. Watchdog was quiesced solely for consistent preservation.
- Host `i-057344e5372faf62f` is **verified stopped** at 2026-10-10T10:56:07.899050+00:00.
  Encrypted 160-GiB owned root `vol-09dbb42bbf607f5de` retained, no deletion.
- Next unchanged identity: sequence 121, P1, attempt 1,
  `01a11705-11f1-75f4-b64e-8f0a3679518b`. No admission/replay/replacement occurred.

## Trigger and limits of diagnosis

The frozen guard compares wall-clock elapsed time with monotonic elapsed time
from the sealed host anchor and refuses admissions if wall elapsed is more than
five seconds behind monotonic elapsed (`controls.py:290–302`). The exact durable
pause is retained. This message does not prove a discrete wall-clock jump or its
cause. Campaign/watchdog journals, clock-service journals, time status and anchor
were preserved for later review. No code, clock setting, policy or guard changed.

## Preservation before stop

Every completed slot's backup receipt hash and all **120 pinned S3 archive versions**
were verified. A consistent complete master archive was uploaded using frozen
code and independently downloaded/read back from its pinned S3 version into a
separate directory on the host; archive/member/continuation checks and all 1,500
rows passed. A second inspection archive retains that master, complete read-only
ledger, raw pause/anchor, service state and diagnostics. Both external version
heads, exact sizes, metadata and S3 SHA-256 checksums were independently verified
from the local terminal before requesting idle-host stop. No full local archive
download is claimed; external pinned evidence and retained root remain available.

Master SHA-256: `5892e3b90b577537c99720debd87726ed424c06b319f404edd60169a449ca7e7`.
Pinned version: `87kdc4YhTj9U3OqnEya6RwaNdADynjkC`.
Inspection SHA-256: `7dbfc44f3df08717acd802cd6fda7b79c9e6e281cd87a7e4fbb423747ac59859`.
Pinned version: `T2KU5rqPjLfWGWKFx5Rh121j.VdIKDIm`.

Original/raw grades, identities, order, earlier failed attempts, source/freeze and
all S3/local evidence remain unchanged. AWS compute was stopped through the
standing authorized preservation/shutdown procedure. The original US$60 guard,
US$65 ceiling and 22 October 2026 15:24:23.810674 UTC deadline remain unchanged;
this task did not authorize or attempt continuation or a feasibility reset.

Retained-root decision bound remains **11 October 2026, 09:33:51.252814 UTC**
(14:33:51 Pakistan time). Root removal has not been authorized here. Clock-cause
review and a qualified continuation decision remain outstanding.

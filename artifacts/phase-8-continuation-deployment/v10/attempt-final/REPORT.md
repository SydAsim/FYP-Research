# v10 guarded deployment: corrected invocation passed; metadata layout blocked

## Result and retained state

**BLOCKED_CLOSED145_EXPORT_LAYOUT_SAFE_STOP_VERIFIED.** No original execution was
admitted. The host `i-057344e5372faf62f` was independently verified **STOPPED** at
**2026-10-12T19:20:19.664989Z** (**13 October, 00:20:19 Pakistan time**). The owned
root `vol-09dbb42bbf607f5de`, source, failed attempt records and all evidence are
retained. The preparation guard was disabled and independently read back only
after verified shutdown. The absolute AWS guard was verified enabled before boot
and was not modified during retirement.

Boundary remains **145 BACKED_UP / 1,355 PLANNED / zero active**. Next remains
**146/P2/attempt 1**, `01a11705-11f1-772d-8190-c43552871801`. All 1,500 rows exactly
matched the frozen closed-145 snapshot during root inspection. No grades, raw
statuses, timestamps, identities, order or historical timing sidecars changed.

## Completed correction and preboot review

The prepared external invocation correction was reused. It compares the retained
host's actual full Python build with its recorded host qualification, preserves
the 3.12.13/import gates, and records the current binary SHA-256 without claiming
that a historical host binary hash exists. Source/dependency requirements remain.

All remaining external command stages were assembled before boot and reviewed
together. Twelve Bash scripts passed `bash -n` on the already available pinned
Linux image, with no network or installation; 14 embedded Python blocks parsed.
The review checked LF, Bash invocation, heredoc quoting, version-pinned CLI/S3
arguments, environment paths, current closed-145/P2 selections, source/authority
binding, amended timer values and the backup/readiness ordering. Completed
research qualification was reused; no pilot, scenarios or broad test suite ran.

External-only corrections recorded separately:

- Current source/ledger paths and **145/P2/1,355** expectations replaced stale
  historical **120/P1/1,380** selections in the reused live checker/stages.
- The bootstrap-timer ownership check uses the actual retained v4 template's
  description, instead of an invented description.
- Working/backup usage is measured rather than filled with zero.
- A unique preparation idempotency token was selected before its AWS write.
- A local nested PowerShell quoting failure occurred before any AWS start call;
  it is retained. Rendering/start was moved to a separately parsed Python file.

These are controller/stage changes outside the frozen research source. The
command review and file hashes are in `preboot-command-review-final.json`.

## Fresh preboot controls and source deployment

Bounded fresh AWS reads verified the stopped owned instance/root, no inbound
access, FREE/ACTIVE plan and credits, complete all-version inventory and Scheduler
role trust/exact-host stop permission. Inventory remained **3,358,711,686 bytes /
204 versions**, no truncation. No listing absence was treated as nonexecution.
The earlier ambiguous command's historical execution remains **UNKNOWN**.

Fresh planning at 19:10 UTC passed using unchanged allowances: **262.3164 hours**
remaining, **2.5 hours** preparation/shutdown, and **24 hours** operational reserve.
Forecast was **US$65.89**, or **US$69.39** with the reserve. Future storage retained
the whole previous 1,500-slot slope/base extrapolation, positive inventory growth,
600-MiB staging and 1-GiB reservation: **78.7753 GiB**. Actual host capacity and
fresh metadata size still required later checks; this was not admission readiness.

The owned independent preparation guard
`retained-host-v10-final-prep-20261013` was created and independently read back for
**2026-10-12T21:10:30 UTC**. The amended absolute guard and complete owned schedule
inventory also passed; only these two guards were enabled. Superseded preparation
schedules were disabled. The instance boot was acknowledged and EC2/SSM verified
running/Online.

The reviewed expiry fence and actual read-only root inspection preceded further
writes. Inspection retained the original pause SHA-256
`28ea1aec440408f1d9e467ece07e54c39485d14c29434dc79b35b9460919d519`; no old command
process was active. A separately named, ownership-checked quiescence succeeded
at **19:15:27.797761 UTC**, with both units inactive/PID zero and every row/pause
unchanged. The original exclusive wrapper was not blindly resent.

The corrected source invocation then **succeeded**. It reused S3 version
`QmAcYmVhFW5GHo08qBB01sD.laBJlcyo`; one source download, no reupload. The complete
archive hash, all **3,441** inventoried files and public authority/HMAC bindings
verified. The current host executable hash was
`021044895e95be79dc2f110367607e684119afbc8ce75f6f0eec94844e0acec7`, with its full
qualified Python build unchanged. No dependency or private signing key was
installed/transferred. Verified source is retained at
`/opt/fyp-phase8-continuation-v10`; do not rerun the exclusive fresh-source bootstrap.

Frozen package remains
`bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c`.
Archive remains
`212269264d45ac8bd6637c2ca0ca5e09c951d354cb445c9bf7a16c6ba2d0ba37`.
No new freeze or candidate was created.

## Precise failed gate

SSM command `2907ce35-0931-450f-99d2-876a80fc8aa9` failed at
**2026-10-12T19:17:37.804Z**, ResponseCode **1**:

```text
prepare-metadata.sh -> closed145.verify_retained_root(root)
/opt/fyp-phase8-continuation-v10/artifacts/phase-8-runner-amendment/v4-complete/closed145.py:95
  raw = read(path)
FileNotFoundError:
  /var/lib/p8-continuation-v9/run/exports/0001/export.json
```

The entire top-level `run/exports` directory is absent. This frozen continuation
validator assumes a materialized per-sequence export layout. The retained host's
actual layout differs. The bounded read-only inspection demonstrated:

- `run/historical/first-slot/executions/01a11705-11f0-79f1-9293-78f7f8207f70/export.json`
  exists, **1,485,724 bytes**, SHA-256
  `283001dc1a5904f3e8b4de893ef658d2e7fe8053b8e98ed7baad6f242d318d8b`, exactly the
  frozen first-original commitment.
- The retained first archive exists at
  `/opt/fyp-phase8-combined-v4/artifacts/phase-8-runner-amendment/v4-complete/retained-archives/0001.tar.gz`,
  **444,490 bytes**. Its original receipt and pinned cloud reference remain present.
- `run/restart-history/exports` exists. No assumption was made that it contains
  all 145 required records; those were not individually verified in this attempt.
- The run configuration still selects **v9**. No metadata history subdirectory
  was written and no clock rename/rebinding occurred. The failure was before
  those operations. Both owned units remained inactive and the original pause
  stayed unchanged.

This demonstrates a **continuation metadata-layout blocker**, not loss of the
first original, not a new research DRIVER_FAILURE, and not an application or
grading correction. Evidence for every one of the 145 exports still needs exact
verification; the first matching record alone does not qualify the whole handover.
The frozen validator was not weakened or patched, and no alternative path was
silently accepted.

One bounded diagnostic read was retained, followed by safe stop and independent
EC2 stopped readback. No automatic boot/retry loop occurred. Full source/dependency/
archive live checks, capacity, timer installation, PRELAUNCH readback, genuine
readiness/launch binding, COMPLETE readback and pause release were not reached.

## Backups, policy and minimum recovery

**No new PRELAUNCH or COMPLETE backup receipt exists from this attempt.** Existing
independent references remain preserved:

- Original 145: SHA-256
  `8abe7597a0e59154cf66e682fd08f3440fff815c458db0bdc8fe83666091ad24`, pinned S3 version
  `RPSiYO12M2tM251ZCuLVOEK3IUn4NYHM`.
- Closed-145 master: SHA-256
  `b40bc792c0e7c9d94edc513a24bfae1abe8536475947be13a1ee35949b6ced08`, pinned version
  `3pLbzfgLl6SW0nbeiXBi3QZiCEvGt4pt`.

At **19:22:56.344725 UTC**, unchanged accounting forecasts **US$65.92** completion,
**US$69.42** with reserve, and **US$72.22** at the full deadline. These retain all
elapsed stopped/running history and fixed reserves; they are not actual billed
spending. Actual compressed metadata growth/capacity remains unqualified. Limits
remain **US$70 / US$75**, **80 GiB**, and the original clock anchor with **432 hours**.

Minimum next procedure: qualify an **external, exact-record metadata handover**
that locates each original export in its retained verified history/archive,
checks archive/member hash and identity, and materializes the frozen validator's
required layout without altering bytes/grades or replacing the original copy.
Do not modify frozen `closed145.py`, infer missing grades, replay drivers or bulk
download archives unnecessarily. Reuse installed verified v10 source; do not
resend the fresh-source bootstrap. New feasibility/guard and all outstanding live
readiness/readback gates remain required before admission. This procedure was
not implemented or executed after the failed gate.

Absolute stop remains **2026-10-25T15:24:23.810674Z**. Root-retention decision remains
due no later than **2026-10-27T15:24:23.810674Z**; no deletion is authorized.

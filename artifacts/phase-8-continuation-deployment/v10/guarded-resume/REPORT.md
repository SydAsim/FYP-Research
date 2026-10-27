# Guarded v10 deployment after returned CloudShell control evidence

## Actual result

**BLOCKED_EXTERNAL_INTERPRETER_SELECTION_SAFE_STOP_VERIFIED.** The retained host
was booted under independently verified stop protection, inspected, and its old
owned units quiesced. Source preparation then failed **before downloading the
source archive**. Safe stop completed. EC2 verified **STOPPED** at
**2026-10-12T18:47:22.154265Z**. The preparation schedule was subsequently disabled
and independently read back. The absolute AWS guard remains enabled as verified
before boot; retirement targeted only this attempt's preparation schedule.

No sequence-146 admission, driver call, pause release, new readiness/launch
receipt, PRELAUNCH or COMPLETE backup occurred. No evidence/root deletion,
application changes, tests/pilot, regrading, replay or refreeze occurred.

## Returned evidence and reconciliation

The supplied file matches the user's independently supplied SHA-256
`3a4744dbbffd90d7c233a2f7117e5743bfe3dd891309f7ff62771b844e3bbd70` and exact
**207,205 bytes**. All 22 regular JSON members were safely read, parsed and
hashed; expanded content is **502,058 bytes**, within the handoff bound. The
original file remains unchanged. Records were retained once at
`D:/FYP-ResearchBackups/v10-control/returned-attempt2`.

The successful CloudShell reads were reused, not rerun:

- Project `803656589923`; retained instance stopped and exact root attached.
- Both SSM history pages completed: 50 + 15 commands, final token absent.
- Wider-window invocations and CloudTrail lookup completed with no match.
- Existing source version HEAD verified size, checksum, metadata and version.
- Complete campaign-prefix all-version inventory: **3,358,711,686 bytes**,
  **204 versions**, no truncation.
- FREE/ACTIVE plan, **US$108.01** reported credits.
- Exact amended absolute shutdown schedule enabled.

Previously completed local identity/SSM responsiveness reads also succeeded and
were reused. The local control route worked throughout this preparation; an
additional manual CloudShell deployment handoff was not needed.

Historical execution of the ambiguous 16:27:20 request remains **UNKNOWN**.
Listings do not prove nonexecution. The reviewed conservative expiry fence
**17:14:50.228195 UTC** had passed. Stopped-host evidence and protection justified
the first new **read-only** root inspection, not blind resubmission of the old
exclusive transfer wrapper.

The read-only inspection returned success at **18:43:33.476697 UTC**. It found no
original transferred script, pre-quiescence record or completed quiescence proof,
and no active process for the original script. This describes observed retained
effects, not a retrospective claim that the old request never ran.

All **1,500** actual rows exactly matched frozen closed-145 metadata, including
states and original identities. The original DRIVER_FAILURE pause SHA-256 was
`28ea1aec440408f1d9e467ece07e54c39485d14c29434dc79b35b9460919d519`.
Campaign was static/inactive; the owned old watchdog had booted automatically.
Both unit files matched their frozen source-generated ownership checks.

A separately named conditional quiescence then succeeded at **18:44:07.352599
UTC**, preserved its own before/after records, stopped both old units, verified
PID zero/inactive, and retained the pause and every row. The original exclusive
transfer wrapper was not resent or overwritten.

## Protection and feasibility before boot

The existing Scheduler role's trust and exact-host stop permission were read
back and matched the earlier verified documents. A fresh owned schedule
`retained-host-v10-guarded-resume-stop-20261012` was created and independently
read back for **20:40:12 UTC**. Absolute protection remained
**2026-10-25T15:24:23 UTC**, before the fractional authoritative stop. Complete
owned schedule inventory showed only the new preparation and amended absolute
guards enabled; all superseded preparation schedules were disabled.

Before boot the unchanged remaining allowance was **262.3164 hours**, plus
**2.5 hours** preparation/shutdown and **24 hours** operational uncertainty.
The whole earlier 1,500-slot slope, metadata-base extrapolation, 600-MiB staging
allowance and 1-GiB reservation were preserved. Positive inventory growth,
including the successful earlier deployment upload, was added without reducing
allowances. Projected evidence including reservation was **78.7753 GiB**, below
80 GiB. Fresh compressed metadata growth and actual host resources were still
required later; those admission gates were not reached.

Updated after shutdown at **18:50:05.844481 UTC**:

- Completion forecast: **US$65.84**.
- Completion plus the existing operational uncertainty reserve: **US$69.34**.
- Full absolute-deadline forecast: **US$72.22**.

These use accepted elapsed-clock accounting from the original anchor, including
paused history and the preparation boot, full 80-GiB storage-month, root/request/
handover reserves. They are distinct from actual billed spending and do not
replace it. Limits remain **US$70 admission / US$75 total**. No clock reset,
budget increase or allowance reduction occurred. Feasibility must be recalculated
before any subsequent preparation/admission; these are not runtime guarantees.

## Exact failed gate and responsibility

The external controller's `prepare-source.sh` IMPORT_CHECK line 4 asserted the
Python binary SHA-256 from the **pinned test container**:

`0e6475dfda68a9b2d93501449fc47593ca169010e8f4881577b97463fd0c1263`.

That was an incorrect controller selection. The actual qualified host uses
uv's Python binary:

`/root/.local/share/uv/python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12`

Actual hash:
`021044895e95be79dc2f110367607e684119afbc8ce75f6f0eec94844e0acec7`.

The successful read-only diagnostic proved the host's full version/build string
exactly matches its retained host qualification:
`3.12.13 (main, Aug 7 2026, 02:25:39) [Clang 22.1.3 ]` (the raw record retains
the original whitespace). Existing boto3 and botocore imports succeeded, both
version **1.43.108**. The retained host baseline does not contain a historical
binary digest; the current hash is not relabelled as one. Full dependency RECORD
and source checks remain required before admission.

This is a demonstrated **external deployment-controller defect**, not a frozen
application/classifier defect or a demonstrated host-runtime drift. The failed
invocation, parameters, exception, SSM response and runtime diagnostic are all
preserved. The final source directory and new archive were independently observed
absent. No dependency was installed and no source transfer was retried.

`prepare-source.corrected.sh` is prepared **but not executed**. Its narrow change
uses the existing qualified host's full build-string comparison, preserves the
3.12.13 version gate/import order, and records the actual binary hash. Its import
block was parsed locally; retained diagnostic readings demonstrate the comparison.
No research test or successful qualification was repeated. The old failed file is
unchanged; `external-invocation.diff` and `external-invocation-correction.json`
retain both wrapper hashes. No frozen package bytes changed.

Other external source-rendering differences were path/version substitutions,
an exact streamed size bound and renaming verified extraction instead of making
another complete copy. None reached execution after the failed import check.

## Frozen authority, originals and backups

- Frozen v10 package:
  `bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c`.
- Archive:
  `212269264d45ac8bd6637c2ca0ca5e09c951d354cb445c9bf7a16c6ba2d0ba37`.
- Previously verified freeze/source authority was reused, not regenerated.
- Existing uploaded source version `QmAcYmVhFW5GHo08qBB01sD.laBJlcyo` is preserved.

Boundary remains **145 BACKED_UP / 1,355 PLANNED**, all original statuses/grades/
timestamps/order retained. Next remains **146/P2/attempt 1**,
`01a11705-11f1-772d-8190-c43552871801`. No historical timing sidecar was applied.

Existing backup receipts/references remain:

- Original 145 SHA-256
  `8abe7597a0e59154cf66e682fd08f3440fff815c458db0bdc8fe83666091ad24`, pinned version
  `RPSiYO12M2tM251ZCuLVOEK3IUn4NYHM`.
- Closed-145 master SHA-256
  `b40bc792c0e7c9d94edc513a24bfae1abe8536475947be13a1ee35949b6ced08`, pinned version
  `3pLbzfgLl6SW0nbeiXBi3QZiCEvGt4pt`.

There are **no new PRELAUNCH/COMPLETE backup receipts**. Verification of all pinned
original backups, source/dependency closure, actual capacity, amended local units,
fresh boot anchor, both independent backup readbacks, genuine readiness and launch
authority, and exact pause release remain outstanding. The source upload and root
inspection are not substituted for these gates.

## Minimum next procedure

Use the prepared corrected **external invocation**, without a research candidate
or refreeze. Recalculate live feasibility, establish a fresh independently verified
preparation guard, boot and inspect/quiesce owned units again, then execute the
unchanged frozen source deployment and every outstanding readiness/backup gate.
Do not reuse the disabled preparation guard, replace outcomes or reset allowances.
No further boot was attempted after this failed gate.

Root storage remains owned and retained, no deletion authorized. Absolute stop
remains **2026-10-25T15:24:23.810674Z**; retention decision remains no later than
**2026-10-27T15:24:23.810674Z**.

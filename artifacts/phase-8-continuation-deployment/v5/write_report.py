from datetime import datetime,timedelta
from ops import HERE
from controls import read,write_new

status=read(HERE/'final-status.json')
freeze=read(HERE.parents[2]/'artifacts/phase-8-continuation-freeze/v5/freeze-verification.json')
readback=read(HERE/'blocked-evidence-readback.json')
feasible=read(HERE/'feasibility.json')
latest=datetime.fromisoformat(feasible['conservative_guard_time_utc'])-timedelta(hours=status['unchanged_allowance_hours']+2+.5)
margin=(latest-datetime.fromisoformat(status['at_utc'])).total_seconds()/3600
write_new(HERE/'remaining-feasibility-at-stop.json',{'at_utc':status['at_utc'],'status':'CONDITIONAL_NO_LAUNCH','remaining_hours':status['unchanged_allowance_hours'],'cost_usd':status['current_projection_with_new_2h_preparation_usd'],'latest_new_preparation_start_utc_with_unchanged_allowance':latest.isoformat(),'hours_remaining_to_that_bound':margin,'guard_usd':55,'total_usd':65,'deadline_unchanged':status['original_deadline'],'not_a_launch_authorization':True,'planning_allowance_not_reduced':True})
report=f'''# v5 deployment — frozen, launch blocked, host stopped

## Actual result

The exact accepted v5 package was frozen and verified against v4 on 9 October 2026. Package hash: `{status['package_hash']}`. Freeze-manifest SHA-256: `{freeze['freeze_manifest_sha256']}`. All {freeze['verified_members']} frozen members and the authorization/parent chain passed. The separate human deployment authorization was recorded; no new signed runtime CONTINUATION_LAUNCH receipt was issued and no main execution was admitted.

The retained host `i-057344e5372faf62f` started for preparation at **11:17:31.181234 UTC** under an independently enabled Sydney stop schedule due **13:17:11 UTC**. It is verified **stopped at {status['at_utc']}**. Root `vol-09dbb42bbf607f5de` remains attached, encrypted and retained; nothing was deleted. The stop-only schedule remains in place for its one-time trigger, along with its scoped role/group. The old campaign/watchdog operational services were quiesced and the original PROTOCOL_STOP was preserved.

**82 BACKED_UP / 1,418 PLANNED / zero active.** Next remains sequence **83, B3, attempt 1**, ID `{status['next_execution_id']}`. No replay, replacement, new research outcome or grade change occurred. The new actual campaign metadata root was never created; separate diagnostic copies are labelled calibration-only.

## Gates demonstrated

- Exact source/archive and signed freeze verified on the host; original v4 source unchanged.
- All 82 complete local archives/member hashes and pinned S3 versions passed.
- Python build, existing environment versions and distribution RECORD hashes matched the prior host readiness evidence; pinned images matched. No dependency install/upgrade or application stack was run.
- Available RAM: **7,434,235,904 bytes**; disk free: **156,746,051,584 bytes**; all-version S3 inventory: **658,466,989 bytes** before supplemental preservation. Resource/storage gates passed.
- Original absolute timer retained **22 October 2026, 15:24:23 UTC**; independent prestart stop configuration and actual Sydney-context role permission simulation passed.

## Concrete failed gate — backup closure/order

Frozen `storage.py:370` copies ordinary continuation metadata, including mandatory `continuation-readiness.json` at line 378. `final_backup` invokes that copier at line 414. The documented prelaunch order calls it before creating the new readiness/launch records. The separate staged 82-original metadata control reproduced **FileNotFoundError for continuation-readiness.json**.

The copier also omits **restart-boundary.json** and **restart-history**, which `closed_restart.verify` requires at lines 132 and 141. A second inert copier control supplied the ordinary fields and proved both required restart records were absent from its output. This affects standard master/per-slot continuation backup closure; readback cannot pass the new verifier as documented. No synthetic receipt was placed in the real owner directory and no guard was bypassed.

Both controls completed on the pinned host Python in **1.334 seconds**, ID `cal-backup-gate-1791545565417340258`; zero scenarios, pilot executions or observation windows. Full raw result: `backup-gate-result.json`. Partial diagnostic output is retained. Frozen source was not patched.

## Unsuccessful preparation retained

The initial IAM simulation omitted aws:RequestedRegion and returned organization denial; supplying the actual Sydney request context returned allowed without changing policy. AWS documents supplying SCP context values and cautions that simulations can differ from live behavior: [IAM simulator](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_testing-policies.html).

The first transfer command omitted the installed SDK environment path and failed before download. The corrected transfer verified the archive but its completion writer collided with the transfer's existing source-ready marker. The existing marker was preserved and a separate signed-authority verification passed; the transfer was not replayed. An initial local helper Path-type error and interrupted slow random-access readback are also retained. Streaming verification reused the same downloaded version; no outcome was replaced.

## Preservation and limits

The current consistent master snapshot, pause, logs, receipts, calibration failures and deployment controls are independently retained on root/S3/local. Archive SHA-256 **{readback['proof']['sha256']}**, S3 version **{readback['proof']['version_id']}**. Local: `E:/p8v5/blocked-20261009/evidence.tar.gz`. All **{readback['members_verified']}** inventoried members passed independent streaming verification in **{readback['streaming_seconds']:.3f}s**; the preserved SQLite rows exactly match all 1,500 originals. Historical S3/local archives and both original raw FAILED records/grades remain unchanged.

At stop verification, unchanged-allowance projected committed cost was **US${status['current_projection_with_new_2h_preparation_usd']:.3f}**, with a new full 2h preparation allowance and 0.5h shutdown allowance. Original **US$55 admission guard / US$65 total / US$1.25 reserve** and **274.513h remaining planning allowance** are unchanged. On this conservative original-clock model, only **{margin:.3f}h** delay margin remained, with latest new preparation start **{latest.isoformat()}**. This is an estimate, not invoice certainty; further delay may make continuation infeasible. Do not reduce the allowance or reset any limit.

Root retention decision remains due **11 October 2026, 09:33:51.252814 UTC**. The preparation boot/stop does not reset it. Campaign deadline remains **22 October 2026, 15:24:23.810674 UTC**.

## Recommendation

**Do not launch frozen v5.** Prepare a separately versioned, narrowly qualified correction for restart-metadata backup/readback closure and the prelaunch readiness/authorization dependency order. Preserve v5 and every original. Recalculate feasibility before any next deployment; no new AWS launch or freeze is performed by this report. No additional study arm, input, endpoint, analysis or observation-window change is proposed.
'''
with (HERE/'REPORT.md').open('x',encoding='utf-8') as handle:handle.write(report)
print(str(HERE/'REPORT.md'))

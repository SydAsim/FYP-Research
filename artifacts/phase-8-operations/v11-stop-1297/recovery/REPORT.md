# Stop after1297: cause corrected; continuation remains gated

Verified23October2026,10:28UTC /15:28Pakistan. **AWS instance i-057344e5372faf62f is STOPPED.** Its owned encrypted176-GiB root vol-09dbb42bbf607f5de remains attached, DeleteOnTermination=false. No evidence was deleted.

## Exact cause and event order

This was an operating-system maintenance interruption, not a demonstrated new research-driver failure.

1. At06:14:27UTC Ubuntu unattended upgrades started. Its log names zlib1g; dpkg records the change from1:1.3.dfsg-3.1ubuntu2.2 to1:1.3.dfsg-3.1ubuntu2.3.
2. The unattended-upgrades dpkg log explicitly records `systemctl restart fwupd.service fyp-phase8-campaign.service fyp-phase8-watchdog.service polkit.service rsyslog.service udisks2.service`. Systemd independently records stopping/restarting both research services at06:14:32–33UTC.
3. The campaign unit's configured KillSignal is SIGINT. Its journal says `Parent stopped; detached collector continues. Keep host running.` The existing runner handles KeyboardInterrupt by recording a BETWEEN_SLOTS pause. The first pause notice is06:14:32.688654UTC.
4. The detached sequence1297 collector retained its original06:16:36.194811UTC deadline. Sequence1297 became BACKED_UP at06:17:27.158847UTC; archive-retention completion was recorded at06:17:44.765463UTC.
5. The restarted parent attempted next admission after that backup. The existing durable pause caused ValueError PAUSED_ADMISSIONS, then PROTOCOL_STOP at06:18:06.037537UTC. The durable PROTOCOL_STOP pause is dated06:18:06.055774UTC.

The initial interruption and the subsequent admission refusal are distinct. Empty SSM command history was not used to infer nonexecution: the positive maintenance-log and systemd records establish the cause.

Evidence: initiating-pause-summary.json and retained initiating-pause/SSM responses; prior earliest-inspection-summary.json. Raw units, operating-system logs, notices and a consistent master snapshot are also in the independently verified diagnostic backup below.

## Narrow correction and checks

One external host configuration was added, outside frozen application/research source:

`/etc/needrestart/conf.d/99-fyp-phase8-defer-restarts.conf`

```perl
$nrconf{override_rc}->{qr(^fyp-phase8-(?:campaign|watchdog)\.service$)} = 0;
1;
```

Exact installed file SHA-256, including explanatory comments: **a2fa11ad5a52dce6d32ce8731bf1bc8bea6eee6d76872a55e02bb01cda4cbe73**.

The installed needrestart implementation and configuration were inspected. override_rc=0 defers automatic restart while preserving its report; package/security updates remain enabled. This affects exactly these two service names. It does not prevent all host interruptions, change autostart, introduce automatic pause clearing, or change the accepted shutdown policy. Review removal of this deferral after the campaign.

Qualification: Perl syntax PASS; six distinct selection assertions PASS, each against staged and installed configuration: campaign/watchdog deferred; suffix/prefix lookalikes and an unrelated service retain normal selection; existing dbus deferral retained. No research scenarios, application-stack launches, pilot, replay, or600-second calibration were run. These configuration checks do not guarantee future uninterrupted execution.

Frozen v11 source/authority verification and ledger binding verification passed. Frozen package remains e89ca0fbb9c9e7333a18af23014d0d00d4ffbc6dbe1298f0546620523626e348, archive3dc00ac7b60018c7fa0357d54d5fac96f22c6e84deba39e9037575b8a93b0579. No refreeze, new launch authority, application, claim-selection, fixture, oracle, grade, analysis or observation-window change occurred. The observed OS zlib update is explicitly retained as environment provenance; this report does not claim OS binaries were unchanged.

## Preserved exact boundary

-1297 BACKED_UP,203 PLANNED, zero active; all1500 saved identities/order unchanged.
- Next sequence1298/B3/attempt1, case p8v4-0322, execution01a11705-11f4-7c05-9897-af35348a8028; no slot1298 directory/admission.
- Every completed row's receipt hash and execution binding was checked. Latest original1297 whole local archive, required member hashes and pinned cloud HEAD/checksum were verified.
- Original1297 archive4ea8a34a3fe0ca41c2c4df38978b07698b69c9b7fec1b013d0c37a69b741ee6c,53822445bytes, version cLGGcyu1txxJuGzaQ3rq9MBQxd30qP7c remains intact.
- Durable pause remains byte-identical, SHA-2567cf255c9359c9c88951eac98eade347adad2831ad1fd522ea1eab33e1c616ab8.

Only the owned watchdog was stopped after verifying the campaign parent had PID0 and no active execution. Both unit PIDs were then verified0. The paused boundary was checked before/after preservation. The owned instance/root tags and ownership were verified before one EC2 stop request; subsequent EC2 read confirmed STOPPED. No service was resumed or pause cleared.

## New version-pinned preservation backups

Bucket fyp-p82-20261005-018da1d6-803656589923; both keys have prefix `exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/` followed by the SHA-256 and `.tar.gz`.

| Record | SHA-256 | Bytes | S3 version |
|---|---|---:|---|
| Diagnostic snapshot, logs, notices and correction checks |11004a2a2556849280ab32d54d772fe4b767cc03f6d0a5966178aa3c225bc2c4|12937550|J4X4IaL13MR_VgKlQ18Xof_1BVpNu28z|
| Complete master continuation metadata and original receipts |98b581a9b3868d51f2bb8fafb1dde510c174970089bae488a1aea3677b61effe|52843821|pn_YI_TJ_E8f8w75te05AE1DELM5apFo|

Both uploads were HEAD/checksum verified and independently downloaded from pinned versions. Full archive/member verification and continuation metadata verification completed. Readback records SHA-256: diagnostic726b14481bb104df044079d9274a7b16d8fad53e75eded748e3c373480104b4b; master45663d96cc12318bd934fad04ebc528a4768347ad969457952c62a8643473d7b. Readback ledger rows and pause match the actual retained boundary.

The master and diagnostic readbacks remain under `/var/lib/p8-continuation-v9/backup/r1297m` and `r1297d`. Original inspection directory: `/var/lib/p8-continuation-v11/deployment/stop1297-1792750933234669142`.

## Retained failed operational attempts

These are external preservation/control failures, not additional research executions. None is relabelled successful.

1. Local parsing of the successful preflight output initially failed because the clock guard emitted a JSON diagnostic before the final summary. The already-retained output was parsed locally; the successful remote command was not rerun.
2. First preservation command cb1c0d5a-33d1-4495-bd64-8dd18c1417d2 stopped at an external64-MiB diagnostic-closure bound before creating/uploading an archive. The consistent SQLite snapshot plus JSON notices measured about103MiB. Successful installed configuration checks and all partial evidence were retained. A separate measured128-MiB external diagnostic allowance was documented; frozen80-GiB caps were unchanged.
3. Follow-on command df3ea86e-084e-4dec-83a5-5cb06dfd2964 completed both uploads and independent readbacks, then stopped at its external1-GiB additional-copy target. Measured backup growth was1452356833bytes /1.353GiB. This target failure remains recorded. No second backup/upload or research command was attempted. A separate read-only reconciliation verified the completed readbacks, unchanged boundary and real80-GiB cap compliance before shutdown. Future recovery should reuse these verified copies, not repeat them.

All original request/response, poll and failure records remain in this directory. Additional preservation copies have been included in the updated storage projection.

## Why resume did not pass

The user authorized diagnosis, a justified correction and continuation within existing gates. This does not authorize silently increasing limits or reducing planning allowances.

Updated at23October10:29:23UTC, preserving accepted262.31642189586114/1355hours per execution,2.5hours preparation/shutdown,24hours uncertainty and30minutes margin:

| Item | Result |
|---|---|
| Remaining execution planning time |39.299hours|
| Completion plus preparation/shutdown |25October04:17:20UTC|
| Completion plus24-hour uncertainty |26October04:17:20UTC|
| Required stop including30-minute margin |later than26October04:47:20UTC|
| Accepted absolute stop |26October00:00UTC|
| Deadline gate |FAIL; needs more than4.789additional hours as of that calculation|
| Admission forecast with minimum extended-root retention |more than US$74.81045|
| Accepted admission guard / total ceiling |US$74 / US$75, unchanged|
| Admission forecast gate |FAIL; guard shortfall more than US$0.81045|
| Accepted current full-deadline forecast |US$74.10242|

These are conservative elapsed-clock projections, including original history/reservations and stopped time, not actual billed spending. Actual billing was not queried or substituted. The numerical minimum moves with delay and is not approval of an amended policy.

Storage passes with the retained additional copies: current dedicated backup60.114GiB; full remaining local projection73.009GiB; cloud all-version projection65.832GiB; caps80GiB. Working data11.31GB and physical free80.274GiB were measured; RAM available approximately6.73GiB. Cloud projection reuses the complete preflight inventory plus the exact two newly verified objects; no other cloud writes were made in this task.

## Minimum next step and retained resources

**Correction installed and verified; campaign NOT resumed.** The required next decision is an explicit operational deadline/admission-policy amendment, with fresh time/cost feasibility and appropriate versioned authority/timer bindings. Current lower bound is roughly five extra hours and admission guard aboveUS$74.81, including the measured minimum root-retention adjustment. It is not safe to promise that this minimum will still fit the unchangedUS$75 ceiling after further delay.

After such authorization, use one guarded retained-host continuation, reuse this exact closed boundary and successful backups, refresh source/runtime/resources/storage/timers, establish the reviewed fresh boot anchor without resetting original elapsed history, preserve the historical pause, and release only through the authorized reviewed procedure. No broad pilot or new research fixture is needed for this OS correction. Current task does not issue that policy amendment or new launch authority.

Host is STOPPED; root and S3/local evidence retained. Applying the accepted48-hour stopped-root bound conservatively from the stop request gives a retention decision by25October2026,10:27:33UTC /15:27:33Pakistan, earlier than the existing absolute outer decision bound28October00:00UTC. No deletion is authorized. Storage continues to incur charges while compute is stopped; the forecast retains its accepted accounting.

Detailed records: verified-preservation-summary.json; final-feasibility.json; initiating-pause-summary.json; closed1297-preflight-summary.json; reconciled-preservation.json; stopped-read1-result.json; the fixed plan, external scripts and all retained failed invocations beside this report.

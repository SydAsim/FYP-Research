# Guarded reuse of the stopped campaign host

This is a proposed deployment procedure, not authorization. Do not start AWS
until the exact candidate is accepted, immutably frozen against v4, and the
separate deployment authority in the user's combined instruction is recorded.

## Fixed bindings

- Existing instance: `i-057344e5372faf62f`; root: `vol-09dbb42bbf607f5de`.
- Profile: `fyp-research`; Region: `ap-southeast-2`.
- New source: `/opt/fyp-phase8-continuation-v5`.
- New metadata root: `/var/lib/p8-continuation-v5/run`.
- Keep `/opt/fyp-phase8-combined-v4` and `/var/lib/p8-combined-v4` intact.
- Reuse the existing pinned application, analysis and transport environments;
  verify their package versions and distribution RECORD hashes first. New source
  environment symlinks may point to the unchanged old environments. No install,
  model download, database restore or dependency upgrade is part of this route.
- Original campaign policy, start, absolute deadline, budget and reserve remain
  unchanged. Recalculate feasibility immediately before boot and admission.

## Before boot

1. Verify candidate archive/member hashes, accepted freeze signature and its v4
   parent chain; record explicit deployment authorization bound to this version,
   run and same instance/root. Do not reuse v4 launch authorization for v5.
2. Recheck EC2 ownership, stopped state, retained encrypted root, no other running
   campaign host, FREE/ACTIVE plan, credits, prices and policy feasibility.
3. Establish an independent **two-hour preparation stop before EC2 start**. The
   old preparation timers were disabled after v4 launch; they are insufficient.
   Proposed route: one Sydney EventBridge Scheduler one-time StopInstances
   target, scoped to this instance, using a verified service execution role.
   Keep the existing original-deadline timer as the independent absolute stop.
   Verify schedule state, UTC trigger, exact instance input, target role/trust
   and StopInstances permission through live AWS reads. A scheduler API acceptance
   alone is not proof that the role can stop the instance. If this cannot be
   verified, **do not start the host**. No replacement server is needed to solve
   this requirement. Creating a dedicated stop role/schedule requires the
   combined deployment authorization; none has been created in this task.
4. Record the preparation deadline from the actual start request, not a later
   successful boot. Do not reset the original operational clock. Scheduler
   delivery is not hard real time: AWS scheduling/delivery delays must be reported;
   the operator's bounded stop-on-failure procedure remains required.

AWS universal-target format and execution-role requirements are documented in
[AWS Scheduler targets](https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-targets-universal.html)
and [execution-role setup](https://docs.aws.amazon.com/scheduler/latest/UserGuide/setting-up.html).
This proposed preparation guard is an operational addition; it does not change
campaign failure-pause or automatic campaign shutdown policy.

## After boot, before admission

1. Retain boot/SSM logs. The old watchdog is read-only and the old run is durably
   paused with zero active slots. Its enabled boot entry is not a launch gate for
   v5. Stop the old campaign/watchdog operational units, never resume their run.
   Preserve any additional old operational notices and the old root.
2. Use the already qualified bounded version-specific download, hash verification
   and short-path extraction routines. Retain failed transfers/extractions.
   Install into the new source path; verify complete source/executable closure.
   Never overwrite the frozen v4 source or old evidence root.
3. Verify the original 82/1,418 closed boundary from a consistent read of the old
   ledger, its chain, IDs, order and receipts; reverify all 82 local full archives
   and pinned S3 versions. First 38 archives are in v4's retained archive directory;
   the other 44 are at each preserved receipt's local path. Verify both original
   FAILED exports and their accepted timing sidecars remain unchanged.
4. Verify private owner permissions, dependency/binary/image hashes, no surviving
   owned application processes, no occupied research ports, resource/storage
   headroom, S3 versioning/permissions and a **complete** S3 inventory.
5. Produce an operator-HMAC-signed external gate record bound to this package,
   instance/root, preparation deadline and actual AWS evidence. Use a short expiry.
   It must contain the checks enforced by `reuse_prepare.py` and their underlying
   retained evidence; do not substitute unchecked Boolean flags.
6. With Python 3.12.13 and the unchanged environments on PYTHONPATH:

   ```sh
   cd /opt/fyp-phase8-continuation-v5
   /opt/fyp-phase8-combined-v4/.venv/bin/python -B \
     artifacts/phase-8-runner-amendment/v4-complete/reuse_prepare.py \
     --root /var/lib/p8-continuation-v5/run \
     --external-gates /var/lib/p8-continuation-v5/deployment/external-gates.json
   ```

   This imports **metadata only**, preserves the old pause and operational logs,
   creates a new review pause and binds a new boot/monotonic anchor to the
   unchanged original start/deadline. It does not replay a driver or restore SQL.
7. Create a versioned prelaunch master backup with `final_backup`/`upload`;
   independently download that exact version and verify every member, the imported
   ledger, historical notice prefix, receipts, 82 exports and timing sidecars.
   Preserve its proof. No backup failure may be ignored.
8. Install and verify new systemd unit text from the new source against this root.
   Verify the original absolute timer's trigger is still **22 October 2026,
   15:24:23 UTC**, the external preparation stop remains enabled, and no v5
   campaign service has started. Set every existing readiness check only from
   verified evidence, hash the readiness record, then record the separate signed
   CONTINUATION_LAUNCH receipt bound to it and the actual instance.
9. Recheck full inventory, reservations, RAM/disk, projected committed cost and
   exact sequence 83 immediately before release. `release_reviewed_boundary`
   may release **only the new reviewed import pause**, leaving the old PROTOCOL_STOP
   intact. Start the new standalone campaign service using `runner.py run`, not
   a rerun/resume command against the old root.
10. Confirm actual ADMITTED identity `01a11705-11f1-792b-ae1e-36bfc6773842`, sequence
    83, B3, attempt 1. Keep the external preparation stop until actual service/
    watchdog/timer and admission proof are verified; then retire that preparation
    schedule so it cannot stop a successfully running campaign later. Preserve
    all scheduler/role/cleanup evidence. Keep the absolute deadline stop active.

## Failure and retention

Any failed gate stops this procedure. Before admission, preserve evidence and
stop the host within the existing bounded procedure. After admission, honor the
active execution's original observation deadline and verified backup before a
permitted idle-host stop. Never clear a later technical pause, substitute zero
storage, retry a business write, or replace an outcome.

Reuse is **qualified for closed-boundary metadata handover**, not yet for this
host's next live boot. Concrete deployment-time requirements still to satisfy:
independent prestart stop/role verification; source/dependency/resource checks;
82 full-archive/S3 rechecks; verified new master backup; actual timers/readiness
and signed launch binding. Failure of any requirement means no slot 83 admission.

The existing retained-root decision deadline is **11 October 2026,
09:33:51.252814 UTC**. No disk or evidence deletion is authorized here. Do not
extend retention automatically or infer that host reuse resets campaign limits.

# Fresh-host readiness and terminal route

These are future steps after acceptance, freeze and separate deployment authorization.
No command below was used to start AWS or a main original during preparation.

## Review now, on the current Windows computer

```powershell
.\.venv\Scripts\python.exe artifacts/phase-8-continuation/v1/verify_package.py
.\.venv\Scripts\python.exe artifacts/phase-8-continuation/v1/handover.py verify-import --root artifacts/phase-8-continuation/v1/import-preview
```

Both are read-only. The preview has no host clock, active slot or launch receipts.

## Future deployment prerequisites

Selected Region `ap-southeast-2`; profile `fyp-research`; FREE plan remains unchanged.
One fresh m7i-flex.large/x86 host, original qualified Ubuntu AMI resolution verified,
encrypted 160-GiB gp3/3000 IOPS/125 MiB/s, instance-initiated shutdown STOP,
delete-on-termination false until evidence retention is resolved. No inbound security
group rules; SSM and scoped instance role. No embedded keys or paid model/speech calls.
Package source root `/opt/fyp-phase8-continuation-v1`, operational root
`/var/lib/p8-continuation/run`, backup `/var/lib/p8-continuation/backup`.
No overlapping research services; ports 16432/16433/19100/19101/19102/19110 free.
The original host stays stopped; its old application state is not restored.

Provisioning must use a new deployment token/instance identity linked to the original
run, not the old RunInstances token or a new study run. Record actual configuration,
prices, credit status and preparation start. Arm `bootstrap-timers.sh` before downloads.
Its two-hour preparation stop is independent of the fixed original absolute stop.

Download the original archive and delta by pinned version/hash. Use existing bounded
version-specific transport and safe short-path extraction, retaining partial pieces and
failures. A checksum failure or collision stops deployment. Never extract over changed
original paths. The delta adds new version paths and reviewed provenance files only.

Create the three original locked environments with recorded Python 3.12.13/runtime
hash resolution, uv.lock and the frozen analysis/transport requirements. Verify package
versions and exact PostgreSQL/Redis image digests. Reuse the Phase 8.1/8.2 corrections;
do not repeat the known system-Python/package-install fallback. Real host startup
readiness may provision an empty dedicated diagnostic stack to check health/schema,
then retain its logs and retire only its owned resources. It executes no study input.

## Exact metadata import and activation commands

Only after approved deployment, set the working directory and environment:

```bash
cd /opt/fyp-phase8-continuation-v1
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B artifacts/phase-8-continuation/v1/handover.py stage --root /var/lib/p8-continuation/run --master /var/lib/p8-continuation/retained/master/slot --first /var/lib/p8-continuation/retained/first/slot
.venv/bin/python -B artifacts/phase-8-continuation/v1/handover.py verify-import --root /var/lib/p8-continuation/run
.venv/bin/python -B artifacts/phase-8-continuation/v1/handover.py bind-host --root /var/lib/p8-continuation/run
```

`bind-host` requires both original authority and newly accepted/frozen continuation
receipts; it does not require or constitute main launch. It creates one fresh boot
anchor without resetting policy time. Never repeat it to replace an anchor.

Original owner key/receipts stay private under `/var/lib/fyp-owner` (0700; key 0600),
outside source. New chained receipts are under `continuation-receipts` and bind the
candidate package, unchanged full policy, saved identities, first export and parent
freeze. The LAUNCH receipt additionally binds actual instance/readiness; ordinary
old receipts alone do not authorize new code. No new receipts exist in this package.

Before issuing that receipt, write an evidence-backed `continuation-readiness.json`:
actual instance, original run, canonical policy hash, handover hash, boot-anchor hash,
and every named check below TRUE. Each check references retained raw evidence; a
boolean without its demonstrated evidence does not qualify the host. Failures remain
in separate numbered readiness attempts. Owner signing records verified readiness
under the human's separate authorization, never an invented human decision.

| Required runtime check | Exact evidence/consequence |
|---|---|
| original_host_stopped | Fresh DescribeInstances; exact original ID remains STOPPED; never start it |
| original_backups_pinned_verified | HEAD/GET exact three versions from `local-postflight.json`; checksum, bytes, gzip/member hashes, both dumps; first export unchanged |
| imported_closed_boundary | SQLite integrity/notice chain; all 1500 identities; one backed-up first and 1499 planned; no active row/driver |
| source_and_dependency_hashes | Parent archive/inventory plus delta/inventory; executable closure, Python/runtime resolution, lockfiles, SDK and image digests |
| no_original_replay | First raw FAILED and grades retained; no old DB/worker/playback restored; no slot-1 driver folder created on new host |
| exact_original_policy | Same run/start/360h/deadline, $65/$55, 600s, thresholds and retention; no new budget origin |
| deadline_and_budget_fit | Recompute remaining serial planning fit and committed cost including $1.25 reserve; fresh prices/credits; reject changed rates/late setup |
| disk_ram_capacity | Actual >=2 GiB available RAM; >=20 GiB free across paths plus 1-GiB reserve; 50-GiB working/backup limits; active 1-GiB/10-GiB stops |
| s3_versioning_and_permissions | Dedicated existing prefix, versioning ENABLED, encrypted object support; scoped PUT, version GET/HEAD/LIST proven with a small labelled prelaunch probe |
| cloud_cap_inventory | All versions plus unresolved reservations below 30 GiB; no hidden fresh-prefix allowance |
| prelaunch_master_backup_verified | Snapshot imported master with prior chain, bindings, original receipt, handover/boot/source/authorization provenance; manifest, gzip, version/hash/size verified before slot 2 |
| independent_absolute_stop | Original absolute deadline unit present and active; next trigger verified; shutdown retains disk |
| independent_bootstrap_stop | Bootstrap absolute timer and bounded preparation timer active while preparing; no conversation dependency |
| no_inbound_access | Actual security group/network/SSM role matches approved original service pattern |
| owner_key_permissions | Private key outside source; existing original signature chain validates; no secret in evidence/source/user data |
| retained_disk_disposition_within_original_limit | Verified independent copies and authorized old disk cleanup by 2026-10-09T15:57:46Z, or admissions remain stopped for an explicit retention decision |

Archive the prelaunch master/provenance independently before the first new admission.
Use the existing versioned S3 upload/verification/reservation implementation, not an
unverified success return. Pinned transport HEAD checks are not a replacement for
full archive/member verification. No only-copy deletion or unresolved upload retry.

After the readiness-bound LAUNCH receipt exists:

```bash
.venv/bin/python -B artifacts/phase-8-continuation/v1/runner.py verify --root /var/lib/p8-continuation/run
.venv/bin/python -B artifacts/phase-8-continuation/v1/runner.py install-watchdog --root /var/lib/p8-continuation/run
systemctl is-active fyp-phase8-hardstop.timer fyp-phase8-watchdog.service
.venv/bin/python -B artifacts/phase-8-continuation/v1/handover.py release-reviewed-boundary --root /var/lib/p8-continuation/run
```

This specific release retains the old pause/notice chain and records its disposition.
It cannot clear a later technical failure or replay a driver. Verify units, source,
backup and fit again. Only then start the service under separate human authorization:

```bash
systemctl start fyp-phase8-campaign.service
systemctl status fyp-phase8-campaign.service --no-pager
journalctl -u fyp-phase8-campaign.service -n 30 --no-pager
```

Deactivate the bounded preparation timer only after actual campaign service activation;
retain both absolute stop mechanisms and watchdog. If activation fails, leave the
preparation stop active. Main execution is owned by systemd, not Codex.

## Progress, stop and recovery

```bash
.venv/bin/python -B artifacts/phase-8-continuation/v1/runner.py status --root /var/lib/p8-continuation/run
.venv/bin/python -B artifacts/phase-8-continuation/v1/runner.py pause --root /var/lib/p8-continuation/run
```

Pause refuses future admissions; allow the active window/backup to finish. Do not use
host STOP to create an ordinary between-slot pause. To resume a genuine BETWEEN_SLOTS
pause on the same boot, verify readiness and use `runner.py clear-pause`, then start
the service; the saved queue and deadline persist. A failure pause requires review.
Reboots, missing checkpoint/service identity or interrupted drivers remain stops.
Read-only ambiguous-backup reconciliation does not clear a failure pause.

Postflight uses the version-pinned bounded downloader, verified archive/member hashes
and short-path extraction. Original and amendment grades remain together. Final
analysis uses this version's `analyze.py` so the first sidecar remains traceable.
Keep final master/receipts independently backed up before shutdown. No automatic
evidence deletion; storage retention has the original 48h/first-month limits and
escalation. Missing/unexecuted originals stay in the planned denominator.

# v7 guarded preparation attempt 2: readiness blocked; AWS stopped

## Result

The authorized wrapper-only transport correction succeeded. The exact interpreter
`/opt/fyp-phase8-combined-v4/.venv/bin/python` imported boto3 1.43.108 from
`/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages`
before executing the unchanged bootstrap-transfer.py. No dependencies were
installed. Source transfer, archive/member hashes and signed v7 authority passed.
The original failed transport attempt remains in the separate v7 directory.

**Continuation did not launch.** At 2026-10-09 15:43:45.437 UTC, command
`34df8031-b7d8-4ddf-8d87-116a8d8b76b4` failed the read-only gate in
`host_checks-attempt2.py:38`: **OLD_OPERATIONAL_UNIT_RUNNING**.
An old enabled operational service was running after boot. Exact captured state:

```
MainPID=0
Result=success
ExecStart={ path=/opt/fyp-phase8-combined-v4/.venv/bin/python ; argv[]=/opt/fyp-phase8-combined-v4/.venv/bin/python /opt/fyp-phase8-combined-v4/artifacts/phase-8-runner-amendment/v4-complete/runner.py run --root /var/lib/p8-combined-v4/run ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }
Id=fyp-phase8-campaign.service
ActiveState=inactive
SubState=dead

MainPID=580
Result=success
ExecStart={ path=/opt/fyp-phase8-combined-v4/.venv/bin/python ; argv[]=/opt/fyp-phase8-combined-v4/.venv/bin/python /opt/fyp-phase8-combined-v4/artifacts/phase-8-runner-amendment/v4-complete/runner.py watchdog --root /var/lib/p8-combined-v4/run ; ignore_errors=no ; start_time=[Fri 2026-10-09 15:42:52 UTC] ; stop_time=[n/a] ; pid=580 ; code=(null) ; status=0/0 }
Id=fyp-phase8-watchdog.service
ActiveState=active
SubState=running
```

The existing retained-host preparation route quiesces old units later, during
reuse_prepare.py. The earlier host check requires them already quiescent. That
deployment ordering assumption was not satisfied on this boot. I did not change
the frozen code, weaken the check or retry the failed readiness gate. The services
were stopped only for the required failure-preservation/shutdown procedure.

## Boundary and preservation

- **82 BACKED_UP; 1,418 PLANNED; zero active.** Every original row matches the
  accepted closed-82 snapshot. Original raw failures, grades, sidecars, backup
  references and saved order remain unchanged.
- Next remains sequence **83**, B3, attempt 1,
  `01a11705-11f1-792b-ae1e-36bfc6773842`.
- Old durable `PROTOCOL_STOP`, 2026-10-09 03:39:42.861710 UTC, was preserved.
- No new metadata run root, driver command, application stack, prelaunch backup,
  genuine readiness record, launch receipt or complete launch backup was created.
- The new preservation archive retains the consistent ledger, historical metadata,
  backup receipts, live gate failure, pre-quiescence state, post-quiescence state,
  service journal and deployment records. Its pinned S3 version, archive hash and
  every manifest member were independently verified locally before idle-host stop.
- Archive SHA-256: `fd8f62ff7ec53c1e7d7f38437b51b4a9b940f91b77dc3e1400770bc5fd4c459e`.
- Pinned S3 version: `BZy7nSn_uhgPCYHivugaEe5dgDI1cHgW`.
- Independent local copy: `E:\p8v7\blocked-20261009-v7-attempt2\evidence-complete.tar.gz`.

Host `i-057344e5372faf62f` is **verified stopped** at 2026-10-09T15:52:09.597563+00:00.
Encrypted 160-GiB root `vol-09dbb42bbf607f5de` remains attached and protected
from deletion. No evidence or root storage was deleted.

## Guard handling

The fresh independent preparation stop was established/read back before boot,
scoped to this host, with regional IAM simulation. It is due at
**2026-10-09 17:41:56 UTC**. Only after replacement verification were the two owned
superseded preparation schedules disabled and read back. The absolute hard
deadline guard was not changed. The fresh preparation guard remains enabled
after this failed attempt; compute has already been stopped independently.

## Exact scope and costs

Frozen v7 package `9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817` and archive
`c5a90f1830b1b53a5cdafbe88daf909cb028382a281a10ecbac299016355d152` remain unchanged. Runtime differences in this attempt
are confined to external deployment invocation/evidence capture. The wrapper
diff and preboot interpreter-selection proof are retained here. A local rendering
command failed due to quoting before any remote action; its failure record is
retained separately. The first preservation download hit its 180-second bound;
its 2-MiB partial file was preserved. The first readback-resume wrapper refused
to overwrite the existing proof file before issuing any cloud request. That
failure is also retained. A separate resume verified the existing proof and
downloaded only the remaining ranges from the exact pinned version, at most four
read-only requests with 120-second bounds. All partial/range files remain beside
the independently verified complete archive. No completed qualification was repeated and no dependencies,
study fixtures, application behaviour or analysis rules changed.

At 2026-10-09T15:52:36.978312+00:00, the unchanged remaining allowance is
274.512683578 hours plus two hours preparation and 30 minutes
shutdown. Conservative projected total **US$56.20** and explicit
resource projection **US$53.38** still fit the US$60 guard/US$65 ceiling,
including prior spending, retained storage and both v7 preparation boots. This
boot's compute/IPv4 upper bound through verified stop is **US$0.0198**.
Projected shutdown is 2026-10-21T04:53:22.639193+00:00; this is an estimate, not a guarantee
or a real-time billing cap. A new live feasibility check remains necessary before
any future boot or admission. No allowance or clock was reset.

Original hard deadline: **22 October 2026, 15:24:23.810674 UTC**.
Retained-root disposition deadline: **11 October 2026, 09:33:51.252814 UTC**.

The concrete remaining deployment requirement is to quiesce the old operational
units before the live host check through the reviewed external preparation route.
This attempt stops here; no failed gate was bypassed and no second boot was made.

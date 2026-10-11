"""Report the failed readiness gate and verified shutdown; no new AWS actions."""
import json
import sys
import tarfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

here=Path(__file__).resolve().parent
sys.path.insert(0,'E:/p8v7/source/artifacts/phase-8-runner-amendment/v4-complete')
from controls import hash_file,read,write_new
from operational_limits import effective_policy

def main():
    final=read(here/'final-status.json')
    assert final['host_state']=='stopped' and final['actual_main_admission'] is False
    saved=read(here/'blocked-evidence-readback.json')
    assert saved['status']=='PASS' and saved['all_1500_original_rows_unchanged']
    archive=Path(saved['local_archive'])
    assert hash_file(archive)==final['preservation']['sha256']
    retained={}
    with tarfile.open(archive,'r:gz') as incoming:
        for name in ('deployment-controls/units-before-quiesce-attempt2.json','service-journal.log','units.log'):
            handle=incoming.extractfile('inspection/'+name)
            assert handle is not None
            retained[name]=handle.read().decode()
    write_new(here/'retained-service-trigger-evidence.json',retained)
    before=json.loads(retained['deployment-controls/units-before-quiesce-attempt2.json'])['output']
    feasible=read(here/'feasibility.json')
    start=datetime.fromisoformat(read(here/'start-request-anchor.json')['at_utc'])
    stopped=datetime.fromisoformat(read(here/'final-stopped-host-request.json')['at_utc'])
    seconds=(stopped-start).total_seconds()
    compute=seconds/3600*(.1197+.005)
    now=datetime.now(UTC)
    policy=effective_policy(read(Path('E:/p8v7/source/artifacts/phase-8-runner-amendment/v4-complete/original-launch-policy.json')))
    finish=now+timedelta(hours=feasible['allowance_hours']+2+.5)
    conservative=policy.committed_cost(finish)
    explicit=feasible['projected_explicit_usd']+compute+(now-datetime.fromisoformat(feasible['at_utc'])).total_seconds()/3600*160*.096/730
    write_new(here/'feasibility-at-stop.json',{'status':'STILL_FITS_ESTIMATE_NO_LAUNCH' if max(conservative,explicit)<60 and finish<policy.stop_at else 'DO_NOT_RESTART','at_utc':now.isoformat(),'allowance_hours':feasible['allowance_hours'],'preparation_hours':2,'shutdown_hours':.5,'projected_shutdown_utc':finish.isoformat(),'projected_conservative_usd':conservative,'projected_explicit_usd':explicit,'new_boot_compute_upper_bound_usd':compute,'compute_seconds_to_verified_stop':seconds,'guard_usd':60,'total_usd':65,'original_deadline':policy.stop_at.isoformat(),'clock_reset':False,'previous_spending_and_retained_storage_included':True,'live_recheck_required_before_any_future_boot':True,'actual_admission':False})
    text=f'''# v7 guarded preparation attempt 2: readiness blocked; AWS stopped

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
{before.strip()}
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
- Archive SHA-256: `{final['preservation']['sha256']}`.
- Pinned S3 version: `{final['preservation']['version_id']}`.
- Independent local copy: `{saved['local_archive']}`.

Host `i-057344e5372faf62f` is **verified stopped** at {stopped.isoformat()}.
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

Frozen v7 package `{final['package_hash']}` and archive
`{final['archive_sha256']}` remain unchanged. Runtime differences in this attempt
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

At {now.isoformat()}, the unchanged remaining allowance is
{feasible['allowance_hours']:.9f} hours plus two hours preparation and 30 minutes
shutdown. Conservative projected total **US${conservative:.2f}** and explicit
resource projection **US${explicit:.2f}** still fit the US$60 guard/US$65 ceiling,
including prior spending, retained storage and both v7 preparation boots. This
boot's compute/IPv4 upper bound through verified stop is **US${compute:.4f}**.
Projected shutdown is {finish.isoformat()}; this is an estimate, not a guarantee
or a real-time billing cap. A new live feasibility check remains necessary before
any future boot or admission. No allowance or clock was reset.

Original hard deadline: **22 October 2026, 15:24:23.810674 UTC**.
Retained-root disposition deadline: **11 October 2026, 09:33:51.252814 UTC**.

The concrete remaining deployment requirement is to quiesce the old operational
units before the live host check through the reviewed external preparation route.
This attempt stops here; no failed gate was bypassed and no second boot was made.
'''
    with (here/'REPORT.md').open('x',encoding='utf-8') as out:out.write(text)
    print(json.dumps({'host':'stopped','actual_admission':False,'boundary':'82/1418','preservation_readback':'PASS','exact_gate':'OLD_OPERATIONAL_UNIT_RUNNING','report':str(here/'REPORT.md')},indent=2))

if __name__=='__main__':main()

"""Document the stopped deployment and preserved evidence; no retries or AWS actions."""
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,'E:/p8v7/source/artifacts/phase-8-runner-amendment/v4-complete')
from controls import read, write_new
from operational_limits import effective_policy


def main() -> None:
    state=read(HERE/'final-status.json')
    assert state['host_state']=='stopped' and state['actual_main_admission'] is False
    authority=read(HERE/'authority-chain-verification.json');assert authority['status']=='PASS'
    feasible=read(HERE/'feasibility.json');start=read(HERE/'start-request-anchor.json')
    stopped=read(HERE/'final-stopped-host-request.json')['at_utc']
    seconds=(datetime.fromisoformat(stopped)-datetime.fromisoformat(start['at_utc'])).total_seconds()
    compute_bound=seconds/3600*(.1197+.005)
    policy=effective_policy(read(Path('E:/p8v7/source/artifacts/phase-8-runner-amendment/v4-complete/original-launch-policy.json')))
    now=datetime.now(UTC);finish=now+timedelta(hours=feasible['allowance_hours']+2+.5)
    cost=policy.committed_cost(finish)
    explicit=feasible['projected_explicit_usd']+compute_bound+(now-datetime.fromisoformat(feasible['at_utc'])).total_seconds()/3600*160*.096/730
    write_new(HERE/'feasibility-at-stop.json',{'status':'STILL_FITS_ESTIMATE_NO_LAUNCH' if cost<60 and explicit<60 and finish<policy.stop_at else 'DO_NOT_RESTART',
              'at_utc':now.isoformat(),'allowance_hours':feasible['allowance_hours'],'preparation_hours':2,'shutdown_hours':.5,
              'projected_shutdown_utc':finish.isoformat(),'projected_conservative_usd':cost,'projected_explicit_usd':explicit,
              'new_boot_compute_upper_bound_usd':compute_bound,'compute_seconds_to_verified_stop':seconds,
              'guard_usd':60,'total_usd':65,'clock_reset':False,'rates_and_credit_evidence':'read-only-aws/',
              'live_recheck_required_before_any_future_boot':True,'actual_admission':False})
    report=f'''# v7 deployment: freeze verified; bootstrap blocked; host stopped

## Final state

- Exact accepted package: `{state['package_hash']}`.
- Archive SHA-256: `{state['archive_sha256']}`.
- Immutable v7 freeze: `{state['freeze_manifest_sha256']}`.
- Freeze verification PASS: 2,454 members, signed frozen v5 parent and original
  authority. Additional transitive signature/archive check PASS through original
  authority and v1 → v3 → v4 → v5 → v7.
- Authorized host `i-057344e5372faf62f` started 9 October **14:46:46 UTC**;
  independently verified **stopped by 14:57:53 UTC**. Root
  `vol-09dbb42bbf607f5de` remains encrypted, attached and protected from deletion.
- **82 BACKED_UP, 1,418 PLANNED, zero active. No original was admitted.**
  Next remains sequence 83, B3, attempt 1,
  `01a11705-11f1-792b-ae1e-36bfc6773842`.

## Exact blocking failure and responsibility

At 14:50:52 UTC, SSM command `750e4701-9cb8-4049-bb86-3596e7951565`
failed at `bootstrap-transfer.py:10`, `import boto3`:
`ModuleNotFoundError: No module named 'boto3'`.

The deployment wrapper invoked application `.venv/bin/python` before setting the
qualified transport `PYTHONPATH`. **My adaptation omitted the already qualified
v5 environment setting** shown in `v5/transfer-env-attempt2.sh`. This is a
deployment-orchestration error, not a missing package in the accepted runtime or
an application refusal. No package download/extraction, metadata import, research
driver, prelaunch backup, readiness record, new launch receipt or complete
authorized backup took place. I stopped at this failed gate; no retry, dependency
installation, frozen-code patch or pause bypass was performed.

The concrete correction needed before another boot is to use the existing
qualified transport environment **before** the bootstrap command, retaining this
failed attempt. No broad pilot or application change is needed. This report does
not itself authorize another boot or assume the old preparation guard qualifies
one.

## Preservation and shutdown

Before boot, live prices, FREE/ACTIVE plan, US$116.26 credits, host/root ownership,
network and current feasibility passed. The existing scoped Scheduler role and
Sydney-context permission simulation passed. A fresh independent preparation
stop was created/read back for **16:46:34 UTC**, before the start request. It is
retained after this unsuccessful preparation. No campaign service was restarted.

The old `PROTOCOL_STOP` remains at 9 October 03:39:42.861710 UTC. Existing code,
all original statuses/grades/sidecars, identities and backup references remain.
The frozen source/archive/authority packages are also independently retained
under versioned S3 objects. New preservation captured the consistent ledger,
backup receipts, old metadata, notices, deployment error, process/unit/container
state and service logs. Its version-specific cloud object was downloaded locally;
whole-archive SHA, every manifest member and all 1,500 original rows passed.

Preservation object SHA-256:
`{state['preservation']['sha256']}`

Pinned S3 version: `{state['preservation']['version_id']}`.
Local independent copy: `E:/p8v7/blocked-20261009-v7/evidence.tar.gz`.
This is a verified **blocked-state preservation backup**, not a completed v7
prelaunch/launch backup. Fresh v7 live readiness gates remain uncompleted.

The first extra historical-chain verification used the wrong historical anchor
type (manifest hash instead of signed original FREEZE receipt hash). That failed
operator check/output is retained. A separate corrected verifier passed; no
historical receipt or frozen file was changed to make it pass.

## Unchanged limits and remaining feasibility

US$60 admission guard, US$65 total, 60-GiB caps and reviewed storage retention
remain accepted. Reviewed remaining allowance remains
{feasible['allowance_hours']:.9f} hours, plus two-hour preparation and 30-minute
shutdown. At {now.isoformat()}, conservative projected total is **US${cost:.2f}**;
explicit-resource estimate **US${explicit:.2f}** includes this unsuccessful boot.
This boot's compute/IPv4 upper bound through verified stop is **US${compute_bound:.4f}**.
These are deterministic estimates, not a real-time invoice cap. Current prices,
credits, prior costs, retained storage and feasibility must be checked again
before any future boot/admission; no planning allowance was reduced.

Original hard deadline: **22 October 2026, 15:24:23.810674 UTC**.
Retained-root disposition deadline: **11 October 2026, 09:33:51.252814 UTC**.
Neither clock nor limit was reset. Root/S3/local evidence was not deleted.
No research scenarios, pilot, completed v6 tests or 600-second calibration were
run during this deployment attempt.
'''
    with (HERE/'REPORT.md').open('x',encoding='utf-8') as output:output.write(report)
    print(json.dumps({'host':'stopped','actual_admission':False,'freeze':'PASS','authority_chain':'PASS',
                      'preservation_readback':'PASS','projected_conservative_usd':cost,'report':str(HERE/'REPORT.md')},indent=2))


if __name__=='__main__':
    main()

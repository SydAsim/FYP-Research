# Phase 8.3 finite calibration operations

Candidate only; not a protocol freeze or main-study launch authority. This package
admits only its 24 `cal-v4-linux-v1-p83-v1-*` slots. It uses the preserved v3.1
combined entrypoint with v2 full-window collection and new initializer/orchestration
seals. No application code, arm safeguards, migrations or outcome definitions change.

## Before launching

- Renew `fyp-research` sign-in after the user's requested login confirmation.
- Record the actual new human approval in `approval.json`, including stage 8.3,
  decision APPROVED_BY_USER, user_message, limit_usd "2.00", planned_executions 24,
  max_powered_hours 6, main_authorized false, and cleanup
  REMOVE_AFTER_TWO_VERIFIED_LOCAL_COPIES_AND_S3. A test example is not approval.
- Local prerequisites: AWS CLI v2.36.41 or a compatible login-capable version,
  repository `.venv`, preserved source archives and this sealed package; valid
  `fyp-research` credentials for the intended project. No keys go in this package.
- The deployer checks the current free plan, Sydney image/type eligibility,
  empty ingress rules and fresh on-demand compute/IP/disk rates. Any missing,
  ambiguous or changed qualification stops deployment. No service permissions
  are expanded and no paid plan is activated.
- The proposed US$2 is a conservative finite-operation budget, not an AWS billing
  hard cap. The absolute six-hour guest shutdown bounds powered time; verify
  stopped state and remove retained disk promptly after verified copies. Guest
  failure may require an explicit EC2 stop. Disk storage keeps accruing while stopped.

## Normal Windows terminal launch after those approvals

From the project root, with the final package and actual `approval.json` present:

```powershell
.venv/Scripts/python.exe artifacts/phase-8-parallel-pilot/v1/deploy.py --approval artifacts/phase-8-parallel-pilot/v1/approval.json
```

This makes one immutable launch intent and prints the exact new server ID.
Do not run it again after any ambiguous launch: read `launch-intent.json` and
query the recorded client token with `ec2 describe-instances` first. Never generate
a replacement ID to hide a failed original.

The server bootstraps sealed dependencies and starts two systemd units. The pilot
runs the fixed serial-first order; the finisher independently waits for completion,
preserves reachable outstanding collection deadlines on a stop, verifies backups
and regrades exports, archives raw failures and measurements, verifies its S3 upload
and stops the server. It uses no Codex API, chat callback or paid model/voice API.
The infrastructure behavior is still awaiting live 8.3 qualification.

## Status without a Codex conversation

Read the ID from `launched.json`; then use normal CLI commands, always with profile
`fyp-research` and Region `ap-southeast-2`:

```powershell
aws ec2 describe-instances --instance-ids <recorded-id> --profile fyp-research --region ap-southeast-2 --query 'Reservations[].Instances[].State.Name'
aws s3api list-objects-v2 --bucket fyp-p82-20261005-018da1d6-803656589923 --prefix exports/phase83- --profile fyp-research --region ap-southeast-2
```

For detailed progress, SSM Run Command on that exact ID may read
`journalctl -u fyp-p83-pilot.service --no-pager -n 25` and
`systemctl show fyp-p83-pilot.service fyp-p83-stop.timer`. Retain each request,
command ID and output; failed or pending SSM delivery is not an execution outcome.
No inbound ports or SSH keys are needed.

## Stop and interruption rules

- Stop new admissions through SIGTERM to the pilot's main process (SSM command
  `systemctl kill --kill-whom=main --signal=SIGTERM fyp-p83-pilot.service`). Its
  handler writes a stop notice and finishes already admitted reachable windows.
  Do not power off merely to pause between slots.
- New resource pressure, source drift, worker loss or protocol/isolation defects
  stop further admission. The original ledger, traces and deadlines remain.
- The cost stop is absolute and never reset on reboot. Hard host failure may prevent
  full collection; interrupted/missing evidence stays incomplete/UNKNOWN. Readiness
  is not PASS for those slots. Collection gaps and unadmitted slots are reported.
- The finite orchestrator deliberately refuses a nonempty run directory. It has
  **no automatic rerun or whole-pilot resume**. The underlying combined collector's
  per-execution read-only resume keeps the original ID/deadline, but attach it only
  after verifying the same surviving services and no competing collector. Recovery
  across an EC2 shutdown/host loss is not qualified. Do not replay a business driver.
- Diagnostic retries require a separate reviewed version/label and new admission;
  they never replace the saved original. No extra automatic experiments are authorized.

## Export, two local copies and cleanup

Download the exact content-hash key in the server receipt to a new local filename.
`head-object --checksum-mode ENABLED` must agree on SHA256, bytes, metadata and
VersionId. Verify the downloaded file with `Get-FileHash -Algorithm SHA256`.
Copy it to a different physical backup drive and verify again. Two partitions on
the same physical disk are not two independent backups. Extract without overwriting
older evidence; independently verify each backup manifest and replay all valid
exports with the revised oracle. Retain incomplete runs and analysis failures too.

Only after those checks and the human cleanup choice, inspect the exact new ID's
owner/stage tags, root volume ID and DeleteOnTermination flag, then terminate that
server. Verify the server is terminated and the exact root disk is deleted. Keep
S3 evidence, previous 8.2 resources/evidence and the local archives. Never use a
global Docker prune, cache flush or broad cloud-resource deletion.

## Interpretation

Each arm has six original references and two predeclared schedule repeats. Repeats
do not enlarge independent N. No lost attempts, silent substitutions or inferred
silence/completion. A two-lane PASS covers the observed restart/cache pair for that
arm only; all other recipes remain serial unless separately qualified. Report ties
and UNKNOWN honestly. Tone/ACK measurements are synthetic protocol evidence;
they cannot establish intelligible speech exposure or human understanding.

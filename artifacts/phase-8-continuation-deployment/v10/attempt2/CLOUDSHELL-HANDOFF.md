# v10 attempt 2: one read-only CloudShell deployment-control handoff

This is the external controller's **read-only reconciliation/preflight stage**.
It cannot boot, resend a command, clear a pause or launch. The local route failed
required gates, so the guarded deployment stopped before boot. This handoff does
not claim that an alternate deployment transport is fully qualified. Existing
deployment authorization remains conditional on the genuine live gates.

## Upload exactly this file

`C:\Users\syeda\OneDrive\ドキュメント\ChatGPT\Final Year Project\artifacts\phase-8-continuation-deployment\v10\attempt2\cloudshell-control-preflight.py`

SHA-256:
`a679b9d8ee0e79423c51c02458dd8c28e423dab70a6fe4459722fc10d4c22500`

Use the existing **Sydney (`ap-southeast-2`) CloudShell** session in project
`803656589923`. Upload using Actions → Upload file. The uploaded script contains
no credentials or owner signing key and does not read either from disk. It uses
CloudShell's existing AWS authentication. Do not upload `owner.key` or AWS
credential files. Do not install dependencies or change security settings.

Prerequisites: existing AWS CLI, Python 3.9 or later, `timeout`, and permission
for the listed read-only APIs. STS identity and stopped host/root ownership are
checked before subsequent queries. The APIs are STS GetCallerIdentity, EC2
DescribeInstances, SSM ListCommands/ListCommandInvocations/GetCommandInvocation,
CloudTrail LookupEvents, S3 HeadObject/ListObjectVersions, FreeTier
GetAccountPlanState, and Scheduler GetSchedule. A missing prerequisite stops
the script, rather than obtaining new permissions or booting the host.

## Run once

```bash
cd "$HOME"
python3 --version
aws --version
command -v timeout
printf '%s  %s\n' 'a679b9d8ee0e79423c51c02458dd8c28e423dab70a6fe4459722fc10d4c22500' 'cloudshell-control-preflight.py' | sha256sum --check --strict && timeout --signal=TERM --kill-after=5s 610s python3 cloudshell-control-preflight.py
```

The hash check must say `cloudshell-control-preflight.py: OK`. Do not execute
after a failed hash check. The script enforces 600 seconds overall, 16 requests
maximum, 45 seconds per CLI process, connect/read timeouts of 5/25 seconds, and
zero automatic retries. It refuses an existing staging directory rather than
overwriting or resetting an attempt. Staging is bounded to 8 MiB including
records and compressed bundle, with 256 KiB reserved for failure records.
No source archive GET/upload occurs; only the existing pinned source HEAD is
checked. Pagination is bounded and incomplete pagination fails closed.

## Expected output

If all read-only prerequisites complete:

```text
{"status":"READ_ONLY_CONTROL_EVIDENCE_COMPLETE_RETURN_FOR_RECONCILIATION", ...}
{"bundle":"/home/cloudshell-user/fyp-v10-attempt2-control/control-evidence.tar.gz","sha256":"<actual bundle hash>","bytes":...}
```

No match still reports `historical_execution_unknown: true`. It is **not** proof
of nonexecution and is not authorization to boot. An active matching command is
retained for review. No response is broadly accepted based on an HTTP status.

On a failed prerequisite:

```text
{"status":"FAILED_PREREQUISITE_NO_BOOT","detail":"<exact failed gate>"}
{"bundle":".../control-evidence.tar.gz","sha256":"<actual bundle hash>","bytes":...}
```

Exit 1 denotes failure, exit 2 denotes an existing attempt directory. If an
external timeout or bundle-capacity error prevents a bundle, retain the staging
directory and return the exact error plus `failure.json` if present. Do not
rerun, delete files or change to another transport automatically.

## Download and return

CloudShell Actions → Download file:

`/home/cloudshell-user/fyp-v10-attempt2-control/control-evidence.tar.gz`

If the script prints a different home directory, use its exact printed bundle
path. It creates one small bundle, without copying the research source/archive.

After downloading in Windows PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\Users\syeda\Downloads\control-evidence.tar.gz'
```

Compare that SHA-256 with the script's printed bundle hash. Return the bundle,
its printed hash, bytes and exit status. This returns evidence; it does not ask
for another deployment authorization. Local verification/reconciliation and
the still-required live gates must pass before the authorized workflow resumes.

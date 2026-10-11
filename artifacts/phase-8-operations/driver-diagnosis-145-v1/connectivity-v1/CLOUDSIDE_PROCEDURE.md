# One prepared cloud-side extraction — not executed

## Preferred alternative and prerequisites

Use **an existing trusted AWS CloudShell session in ap-southeast-2**, signed into
project 803656589923. CloudShell is supported in Sydney and listed among the
new AWS experience's Free Tier services. Its compute/persistent shell storage
have no additional CloudShell charge; ordinary AWS request/transfer charges
remain. Sources: [CloudShell pricing](https://aws.amazon.com/cloudshell/pricing/),
[Sydney endpoint](https://docs.aws.amazon.com/general/latest/gr/cloudshell.html),
[new experience service list](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html),
[S3 transfer pricing](https://aws.amazon.com/s3/pricing/).

**An existing accessible session has not been verified.** The connected browser
inventory exposes no AWS tabs or Chrome connection, and local SDK/CLI cannot
reach the relevant AWS TCP endpoints. No hosted AWS MCP execution tool is
available in this tool session. This is a prepared route, not a ready/qualified
maintenance deployment. Do not launch a new CloudShell environment, helper,
EC2 instance, Lambda or other resource under this task's authority.

Required before future execution:

1. Existing CloudShell environment already available in Sydney; project identity
   matches, browser can return a file through CloudShell Actions → Download file.
2. Existing console principal permits STS:GetCallerIdentity, EC2:DescribeInstances,
   S3:GetObjectVersion for the **exact pinned object**, plus existing KMS decrypt
   permission if needed. No broader/new access is assumed or requested silently.
3. Python 3, boto3/botocore already present, >=128 MiB free home storage; no installs.
4. Record a US$0.01 incremental diagnostic allowance within the existing US$65
   policy/reserve and verify service availability/permissions. This estimate is
   not evidence of current spend or a waiver of the campaign admission guard.
5. Future explicit authority for this diagnostic execution; current task prepares
   it only. The campaign host/root are untouched and the durable pause persists.

## Exact finite procedure

Transfer only the prepared `cloud_extract.py` script into that existing session.
No credentials, access keys, signing keys or project archive are uploaded. Its
reviewed SHA-256 is
`b2f7815dcffdaf9a98012dcc2039754b9936e690ea5bdfc33836ae19172b3740`.
Use CloudShell Actions → Upload file for this script only, then in that session:

```bash
set -euo pipefail
export AWS_DEFAULT_REGION=ap-southeast-2
python3 -c 'import boto3, botocore, sqlite3, tarfile'
printf '%s\n' 'b2f7815dcffdaf9a98012dcc2039754b9936e690ea5bdfc33836ae19172b3740  cloud_extract.py' | sha256sum -c -
python3 cloud_extract.py
```

The script enforces **180 seconds at process level**, killing only its own Popen
child on expiry; 5s connect/10s read timeouts; SDK total attempts=1; one GET of
the exact version; no retries, transport switching, uploads or request replay.
Before GET, one STS identity check and one EC2 state check must pass. Any other
project or host state other than STOPPED aborts. All outputs/partials stay under
one canonical cloud staging root **~/p145-diagnostic**. `attempt.json` is exclusive:
existing attempts cannot be silently reset or rerun. Bound: 128 MiB temporary
storage and 16 MiB returned bundle, with explicit member/size checks. An exhausted
attempt requires review; do not relaunch the wrapper.

It retrieves only this object:

```
Bucket: fyp-p82-20261005-018da1d6-803656589923
Key: exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/8abe7597a0e59154cf66e682fd08f3440fff815c458db0bdc8fe83666091ad24.tar.gz
Version: RPSiYO12M2tM251ZCuLVOEK3IUn4NYHM
Size: 37906551
SHA-256: 8abe7597a0e59154cf66e682fd08f3440fff815c458db0bdc8fe83666091ad24
```

No inspection archive, other original archives or campaign root is accessed.
The source archive stays in CloudShell. Only the required original manifest,
export.json, checkpoint.json and slot ledger are extracted after complete archive
hash verification and member hash checks. Integrity/event-chain/checkpoint hashes
are checked on the copied immutable slot ledger; original DRIVER_FAILURE and
classification events, slot identity and checkpoint records are preserved in
derived JSON beside raw originals. No grading or live application code runs.

Success must say **VERIFIED_REQUIRED_RECORDS_READY** and supply the derived bundle's
SHA-256/bytes. Use CloudShell Actions → Download file:

```
/home/cloudshell-user/p145-diagnostic/required-records.tar.gz
```

Verify the actual home directory with `printf '%s\n' "$HOME"`; if it differs,
use that actual path, not a guessed alternative. Save this **small derived bundle**
to the existing local staging **D:/FYP-ResearchBackups/slot145-diagnosis**, preserving
its previous exhausted attempt/result files. Return `worker-result.json` and
`process-result.json` too; they contain no credentials or signed URLs.
Verify locally using the exact displayed bundle SHA-256 before opening records:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'D:\FYP-ResearchBackups\slot145-diagnosis\required-records.tar.gz'
```

The bundle member manifest and source proof must then match the pinned original
receipt. Original export/checkpoint/slot-ledger member hashes must match the
original manifest; only then correlate the original exception and event times.
Do not mistake a derived bundle hash for the original full archive hash.

If it fails, retain `attempt.json`, worker/process result/logs, any partial archive
and partial extraction. Return only those small diagnostic records, record bytes
retrieved/remaining, and stop. Never delete partial evidence or retry automatically.
No keys/tokens/signed URLs are printed. No campaign timer is reset; CloudShell
process termination does not start/stop any EC2 host. Leave existing CloudShell
evidence retained; do not terminate/delete its environment under this task.

## Cost and unresolved gates

Compute: US$0 CloudShell fee. S3→CloudShell same-region data transfer: US$0 under
published S3 rules. One S3 GET is billable; returning <=16 MiB may use remaining
free egress or incur ordinary transfer costs. Free egress availability is **not
assumed**. For planning only, US$.001 per GET plus US$.20/GiB return reserve yields
**US$0.004125**, rounded up to **US$0.01**. These deliberately conservative
assumptions are not a Sydney SKU quote, invoice measurement or paid-plan change.
Actual invoice/billing access remains unavailable; accepted campaign accounting
is unchanged. Do not infer credits equal actual spend or use this tiny diagnostic
cost to declare the campaign feasible.

The script is AST syntax-checked only, **not run or runtime-qualified**. Actual
CloudShell existence, login, access policies, browser download and available
headroom remain unresolved. If there is no existing accessible environment,
stop for a bounded maintenance decision instead of creating one here.

## Last resort

Only if the cloud-side S3 route cannot be made available, consider the separately
prepared [read-only retained-root procedure](../bounded-review/RETAINED_ROOT_FALLBACK.md).
It still requires verified helper ownership, same AZ, permissions, clean OS with
no research autostart, ro/noload mounting, pause preservation, independent shutdown
protection, original attachment restoration and stopped-state readback. None of
those live prerequisites has been demonstrated here. No volume detachment or
helper/campaign boot was performed. This route is more invasive and remains a
separately reviewed fallback, not an automatic next attempt.

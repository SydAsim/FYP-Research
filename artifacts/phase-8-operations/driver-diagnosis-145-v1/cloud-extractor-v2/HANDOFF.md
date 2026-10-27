# Slot 145 diagnostic extraction: manual handoff

Use the existing Sydney CloudShell session. Do not start EC2, create another environment, change permissions, install dependencies, delete staging, or rerun a failed attempt.

## Upload one file

CloudShell **Actions → Upload file**:

`C:\Users\syeda\OneDrive\ドキュメント\ChatGPT\Final Year Project\artifacts\phase-8-operations\driver-diagnosis-145-v1\cloud-extractor-v2\cloud_extract_v2.py`

Corrected script SHA-256:

`d56ef48676c7e30e5c23fbd5d84b1dd7ecda280dec76582f7d1b5e8ede8eadae`

This is a separate version. The original script remains unchanged at SHA-256 `b2f7815dcffdaf9a98012dcc2039754b9936e690ea5bdfc33836ae19172b3740`.

## Verify and run once

Paste into that existing CloudShell terminal:

```bash
cd "$HOME"
printf '%s\n' 'd56ef48676c7e30e5c23fbd5d84b1dd7ecda280dec76582f7d1b5e8ede8eadae  cloud_extract_v2.py' | sha256sum -c - && python3 -B cloud_extract_v2.py
```

The hash must say `cloud_extract_v2.py: OK` before execution. Do not set Region variables to make a mismatched environment pass. The script requires Linux, existing boto3/botocore, Sydney Region variables, free disk headroom, an unused attempt boundary, available staging budget, account `803656589923`, and instance `i-057344e5372faf62f` in `stopped` state. STS and EC2 are checked before the single version-pinned S3 GET. Permission errors stop the operation; no permission changes are attempted.

## Limits and evidence preservation

- 128 MiB total counted staging, including existing contents and the uploaded script. Files are conservatively rounded to 4 KiB; directory/metadata allowances and existing allocated blocks also count.
- 1 MiB within that cap is reserved for failure/final records and bounded logs. Normal writes cannot consume it.
- Capacity is checked before file/directory creation and each unbuffered streamed write. Initial worst-case capacity is checked before GET; required raw records, generated JSON and compressed output have separate bounds.
- Raw required records: 16 MiB combined. Derived JSON: 16 MiB combined. Compressed returned bundle: 16 MiB. Each captured log: 32 KiB. Each control/failure record: 16 KiB.
- Only one script process writes staging at a time. Parent startup records precede child writes; bounded parent log buffers are committed only after child exit. Do not concurrently write into this staging directory with other commands.
- Work deadline: 180 seconds from parent start. On expiry the parent kills only its child, retains partial files, and writes bounded outcome records. Up to two seconds per pipe reader and child reaping are allowed for teardown; these do not extend the child's work deadline.
- SDK total attempts: one. Before-send guards also reject a second STS, EC2 or S3 operation send, including SDK redirects/retries. No managed multipart transfer, local archive download, upload, or write API.
- The exact archive is 37,906,551 bytes, pinned version `RPSiYO12M2tM251ZCuLVOEK3IUn4NYHM`, SHA-256 `8abe7597a0e59154cf66e682fd08f3440fff815c458db0bdc8fe83666091ad24`. The bucket/key remain exactly those in `original145-receipt.json`.
- Full archive and selected original member hashes are checked before success. The immutable slot ledger's integrity, event chain and checkpoints are checked. The raw exception/traceback, HTTP observations and checkpoints remain in the original export in the small bundle.
- Existing attempts, partials and outputs are never overwritten or deleted. An existing attempt stops before another GET. If existing contents leave no failure-record reserve, no further writes occur; the terminal reports the refusal.

This is a budget for controlled diagnostic staging, not a CloudShell-wide filesystem quota. OS files, third-party concurrent writers and unrelated directories are outside its control. The corrected code and controls do not qualify or authorize campaign continuation.

## Expected output

Success prints JSON containing:

```json
{
  "status": "VERIFIED_REQUIRED_RECORDS_READY",
  "account": "803656589923",
  "region": "ap-southeast-2",
  "campaign_host_state": "stopped",
  "bytes_retrieved": 37906551,
  "remaining_bytes": 0,
  "api_sends": {
    "sts.GetCallerIdentity": 1,
    "ec2.DescribeInstances": 1,
    "s3.GetObject": 1
  },
  "bundle_sha256": "ACTUAL_64_CHARACTER_HASH",
  "bundle_bytes": 12345,
  "process_exit": 0,
  "download_path": "/home/cloudshell-user/p145-diagnostic/required-records.tar.gz"
}
```

The bundle hash and bytes above are placeholders, not predicted measurements. Use the actual printed values. Failure prints `status: STOPPED` with a reason/error code. Stop there, retain the directory and send the printed JSON; do not rerun or download a partial bundle as if verified. `worker-result.json`, `process-result.json` or `parent-failure.json` (when created) retain small failure records.

## Download and local verification

On success, CloudShell **Actions → Download file**:

`/home/cloudshell-user/p145-diagnostic/required-records.tar.gz`

If your home directory differs, use the actual absolute `download_path` printed by the script. Save the small bundle directly to:

`D:\FYP-ResearchBackups\slot145-diagnosis\required-records.tar.gz`

Do not replace an existing file. Preserve the previous local exhausted attempt/result records.

Run in Windows PowerShell:

```powershell
$diagnosticBundlePath = 'D:\FYP-ResearchBackups\slot145-diagnosis\required-records.tar.gz'
$diagnosticExpectedHash = (Read-Host 'Paste bundle_sha256 printed by CloudShell').Trim().ToLowerInvariant()
$diagnosticActualHash = (Get-FileHash -LiteralPath $diagnosticBundlePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($diagnosticActualHash -ne $diagnosticExpectedHash) { throw 'Bundle SHA-256 mismatch; stop' }
python -B 'C:\Users\syeda\OneDrive\ドキュメント\ChatGPT\Final Year Project\artifacts\phase-8-operations\driver-diagnosis-145-v1\cloud-extractor-v2\verify_bundle.py' --bundle $diagnosticBundlePath --sha256 $diagnosticExpectedHash
```

Expected local status: `VERIFIED_LOCALLY`. It verifies the returned bundle hash, pinned source proof, original and derived member hashes, SQLite integrity/event chain/checkpoints and identity. It creates a separate `verified-cloud-v2` subdirectory without changing existing evidence. Local checks rely on the verified CloudShell execution for the full original archive hash; the entire original archive is deliberately not downloaded locally.

Return the bundle and actual CloudShell JSON/hash to this chat. Diagnosis starts only after local verification. No replay, regrading, campaign boot, pause clearing, freeze or launch.

## Focused checks completed

Three synthetic offline controls passed on local Python 3.12.10 in 0.98 seconds: normal extraction/bundle creation; refusal before excessive stream/derived/bundle writes with partials retained; existing file/log/metadata accounting and old-attempt refusal. Zero AWS calls and zero research scenarios. Docker was unavailable, so these checks do not claim a pinned Linux or CloudShell runtime test. CloudShell dependencies/permissions/account/host remain live gates enforced during the single authorized run.

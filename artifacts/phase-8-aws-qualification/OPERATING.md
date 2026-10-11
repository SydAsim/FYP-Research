# Phase 8.2 AWS qualification — operating notes

**Calibration only. There is no main-launch or protocol-freeze command.**
The scope remains 500 inputs across B3/P1/P2, 1,500 unstarted main slots.
The approved spending envelope covers this finite qualification, not the campaign.

## Prerequisites and independence

Selected Region: ap-southeast-2. Local AWS CLI profile: `fyp-research`.
The temporary host is `i-0938c2aa962389253`; owner tag is
`p82-20261005-018da1d6`. Bucket:
`fyp-p82-20261005-018da1d6-803656589923`.
All host actions require checking that identity/ownership remains unchanged.

The dedicated Ubuntu 24.04 amd64 server uses ordinary Python 3.12, Docker,
locked dependencies, preserved PostgreSQL/Redis image digests and the unchanged
8.1 capsule. No Codex client, conversation, paid voice API, cloud LLM or local
Windows machine is needed by the running job. SSM dispatch returns immediately;
systemd supervises the job. The instance role handles S3 exports. Local sign-in
is needed only for management/status/download calls, not continuously for the job.

V1 is preserved as an unsuccessful original. V2 qualifies the corrected
post-cutoff collector; v3 adds checks of executing adapter files outside the
capsule. V3.1 also numbers future diagnostic attempts as 2. The raw v2 diagnostic
attempt=1 is preserved and excluded by its DIAGNOSTIC_RERUN label and original
linkage. V3/v3.1 have init/verify-only cloud checks and integrity regressions;
neither has a separate full-window execution. A reviewed later pilot must use
one explicit candidate identity incorporating these changes.

The finite units were `fyp-p82-qualification-v2.service` and
`fyp-p82-finish-v2.service`. Neither enables automatic admission on a reboot.
The absolute cost-stop timer targets 2026-10-05 21:11:53 UTC. It is not permission
to run later sessions or reset a four-hour allowance. The export finisher stops
the instance sooner after collectors finish and the S3 checksum is verified.
Root disk persists until the user's cleanup choice.

## Normal-terminal status and download (PowerShell)

These commands are read-only and do not start the server:

```powershell
$phase82Aws = 'C:/Program Files/Amazon/AWSCLIV2/aws.exe'
& $phase82Aws ec2 describe-instances --instance-ids i-0938c2aa962389253 --profile fyp-research --region ap-southeast-2 --query 'Reservations[].Instances[].{State:State.Name,Type:InstanceType,Tags:Tags}'
& $phase82Aws s3api list-objects-v2 --bucket fyp-p82-20261005-018da1d6-803656589923 --prefix exports/ --profile fyp-research --region ap-southeast-2
```

Use the content-addressed key from `v1/exports-discovery-completed.json` and download
to a **new** destination. Preserve an existing outcome/archive instead of replacing
it. Check the downloaded SHA-256 against the key, upload receipt and S3 checksum.

```powershell
$phase82Download = 'E:/fyp-phase82-evidence/review-download.tar.gz'
if (Test-Path -LiteralPath $phase82Download) { throw 'Choose a new destination; preserve the existing archive.' }
& $phase82Aws s3api get-object --bucket fyp-p82-20261005-018da1d6-803656589923 --key 'exports/phase82-final-evidence-2f1793d840be7a8c407d2fdfe8814eec1d14f9ed972a628a2329f06f4e780175.tar.gz' --checksum-mode ENABLED --profile fyp-research --region ap-southeast-2 $phase82Download
$phase82Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $phase82Download).Hash.ToLowerInvariant()
if ($phase82Hash -ne '2f1793d840be7a8c407d2fdfe8814eec1d14f9ed972a628a2329f06f4e780175') { throw 'Archive hash mismatch; preserve it and stop.' }
$phase82Hash
```

The final report supplies the actual key/hash and retained local paths. Extract
to a short path such as `E:/fyp-phase82-evidence/attempt2`: the first extraction
under the long OneDrive project path hit Windows' path-length limit. The archive
was intact; that failed extraction remains separately retained.

## Collector controls on an already reviewed, running Linux host

The commands below operate a pre-existing **calibration** ledger. They are not
an authorization to buy another server, replay an original, run the main bank,
or rerun the finite AWS qualification in its existing directories.

```bash
cd /opt/fyp-phase8-linux-v1
export P8_DOCKER_DATA_PATH=/srv/fyp-p82-v3.1-integrity
.venv/bin/python /opt/fyp-phase82-qualification-v3.1/runner_v3.py status --root /srv/fyp-p82-v3.1-integrity/zero-admission
.venv/bin/python /opt/fyp-phase82-qualification-v3.1/runner_v3.py verify --root /srv/fyp-p82-v3.1-integrity/zero-admission
```

The init-only ledger has two PLANNED calibration slots and no execution IDs:
DIAGNOSTIC_RERUN attempt=2 and ORIGINAL_PLANNED attempt=1.
Do not admit those slots under this finite check. For a later reviewed calibration
queue, use its explicit new root and unchanged order:

```bash
# Only for a separately reviewed calibration queue and spending envelope:
.venv/bin/python /opt/fyp-phase82-qualification-v3.1/runner_v3.py run --root NEW_REVIEWED_ROOT --pause-after 1
.venv/bin/python /opt/fyp-phase82-qualification-v3.1/runner_v3.py pause --root NEW_REVIEWED_ROOT
.venv/bin/python /opt/fyp-phase82-qualification-v3.1/runner_v3.py resume --root NEW_REVIEWED_ROOT --pause-after 1
```

`pause` prevents new admissions. It does not end the active observation. Ctrl+C
or SIGTERM to the **runner parent** leaves its detached collector alive. Keep
the host and Docker running. Reattach with the same ledger; retain the original
execution ID/deadline and never replay an interrupted driver. A pause caused by
source drift, resource pressure, protocol failure or service/host loss cannot be
automatically cleared as a user pause. Host reboot recovery is unqualified and
is refused for active attempts: preserve their gaps/missingness, not a fresh
attempt masquerading as the original.

## Observation, failures and storage

- Full 600 seconds after the recorded final script-issuance anchor, including
  normal returns, refusals, failures and delayed acknowledgements. Acceptance is
  a distinct durable server event. V2 requires a final snapshot to **start** at or
  after the original cutoff; acquisition overshoot does not extend the grade window.
- Poll nominally every five seconds, record start/end and actual gaps. Journals
  and independent provider truth retain event timestamps; a polling gap is not
  evidence of silence. Collection errors, missing final anchors or lost playback
  acknowledgements keep affected evidence/timing unknown. A missing anchor uses
  start+600 solely as a bounded collection cutoff, never an invented request time.
- SQL checkpoint is authoritative. Original exports and unsuccessful attempts
  are retained. Diagnostics have new IDs and labels, link to the original, and
  are excluded from original-attempt effect estimates. No debugging replacement.
- Drift or protocol defect stops new admissions, records a durable notice and
  preserves evidence. A running collector continues its fixed window where the
  infrastructure permits; abrupt host/service loss remains explicitly incomplete.
- Admission: >=1.5 GiB available RAM for one calibration, >=4 GiB for the finite
  two-lane check, >=5 GiB system/Docker disk and >=2 GiB output/backup reserve.
  Active pressure below 1 GiB RAM stops further admission. These are calibration
  limits; existing stronger campaign disk/memory gates still need review.
- Incremental compressed objects, hash manifests, SQLite checkpoints and
  PostgreSQL dumps are retained. The original failed run also has stopped physical
  PostgreSQL data supplements. Restoration/PITR is not demonstrated by checksums.
- S3 exports use unique content-hash keys, versioning, private access, encryption
  and SHA-256 verification before shutdown. Local C:/D:/E: partitions are all on
  Disk 0, so only the S3 copy adds a separate physical failure domain.
- If export/checksum verification fails, keep the disk and emit a failure notice;
  the absolute stop timer still bounds powered time. A stop during an unfinished
  window does not become a completed outcome. Do not terminate the instance until
  retained archives/backups are verified and cleanup is chosen.

## Scope of parallel qualification and analysis

Only the two declared P2 calibration recipes are tested for overlap. Separate
network/PID namespaces, application/truth PostgreSQL servers, caches, bindings,
queries and outputs are required. A restart must leave the peer worker unchanged;
cache loss must leave the peer sentinel intact. Other recipes and B3/P1 overlap
remain serial/exclusive. Do not halve the 1,500-slot forecast from this pair.

Retain the existing clustered latency analyses; descriptive-only reporting does
not replace them. The independent input is the resampling unit, keeping its three
arms paired within declared strata. Fixed recipe labels and repeated calibration
runs are not new independent clusters. Any future concurrent schedule needs
recorded lanes/overlap blocks and reviewed shared-host dependence assumptions.
These synthetic tone/ACK traces test protocol mechanisms, not intelligible speech,
ASR, human hearing/understanding or warm telephone transfer.

## Completed session and retained finalization failures

The instance is STOPPED, verified by AWS API after the independent export unit
completed. The dated stop timer is a record of this session, not a reusable
spending grant. Do not restart the instance or re-execute completed queues.

The first v2 finisher lost a temporary source archive after a reboot. Its
export-only replacement then failed on a version-specific S3 read permission.
An attempted permission expansion was rejected by automatic approval review.
No permission expansion was applied. The successful replacement used the
existing current-object read permission, required the original returned VersionId
and SHA-256, and retained the source in a persistent control directory. All
failures remain in the final evidence archive; no business driver was replayed.

Exact verified archive metadata is in v1/download-completed-verification.json;
backup checks are in postprocess-v1/completed-backup-check.json. The server/disk
cleanup choice is separate from campaign review. Keeping the 40 GiB stopped
disk costs approximately US$0.126/day at the measured rate; do not let an
unsupervised retention interval silently exceed the approved budget.

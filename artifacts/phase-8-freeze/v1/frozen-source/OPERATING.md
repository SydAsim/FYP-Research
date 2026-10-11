# Standalone operation — future accepted/frozen/authorized package only

These commands are instructions for a later authorized launch. **None were used
to launch the main campaign.** No AWS provisioning command is included here.

## Prerequisites

An authorized Sydney Linux x86_64 host, systemd, Docker, Python 3.12.13, uv 0.9.24,
the accepted source capsule, an encrypted 160 GiB evidence disk, 8 GiB RAM, private
SSM access and an instance role scoped to the dedicated versioned evidence prefix.
Do not place AWS keys in the project or services. Keep application/model paths
local and simulator/tone-only. Verify actual OS/Docker/working/backup free space;
50/50/25/35 GiB reservations are one disk, not independent disks.

Use `/opt/fyp-phase8-linux-v1` as the short source root, `/var/lib/p8/run` for the
new ledger and `/var/lib/p8/backup` for backups. The roots must be separate fresh
directories. Verify the archive SHA-256 against `bundle-receipt.json` before
extraction. Use the reviewed `transport.py` local-archive extraction on a new
short root for Windows inspection; ordinary Linux tar extraction below assumes
the hash-verified, locally assembled trusted source archive.

```sh
sudo mkdir -p /opt/fyp-phase8-linux-v1 /var/lib/p8
sudo tar -xzf campaign-source.tar.gz -C /opt/fyp-phase8-linux-v1
cd /opt/fyp-phase8-linux-v1
uv sync --locked --no-install-project
uv venv .venv-analysis
uv pip install --python .venv-analysis/bin/python -r research/study/requirements.txt
uv venv .venv-transport
uv pip install --python .venv-transport/bin/python -r artifacts/phase-8-review-freeze/v2/requirements.txt
.venv/bin/python -m research.execution_linux_v1.portable
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
```

Docker PostgreSQL/Redis images must match `IMAGE_DIGESTS` in
`research/execution_linux_v1/runner.py`. Pull the exact recorded digest, then tag
it `postgres:16.9`/`redis:7.4.5-alpine` if absent. Confirm no unrelated services
occupy loopback DB ports 16432/16433 or application ports 19100/19101/19102/19110.
If Docker data is outside `/var/lib/docker`, set `P8_DOCKER_DATA_PATH` consistently
for the terminal and systemd service; verify the corresponding disk free check.
The accepted default host uses `/var/lib/docker`.

The candidate `Dockerfile` reproduces the dependency layers for local package
verification; the autonomous main controller runs as a host systemd service.
Application child processes use the original locked environment and source-only
PYTHONPATH. Analysis/transport overlays must not alter application packages.

## Acceptance, freeze and launch are separate

No main receipts or owner signing key are supplied. After actual human acceptance,
the trusted operator records REVIEW_ACCEPTED, then FREEZE, then the separately
authorized LAUNCH. Store owner key (at least 32 bytes) and receipts outside the
source, protected by owner-only permissions. Each receipt follows `Receipt` in
`controls.py`: scope CAMPAIGN, package inventory fingerprint, schedule file SHA-256,
policy commitment, prior receipt's canonical SHA-256, signer, expiry and HMAC-SHA256
signature over the original JSON fields excluding `signature`, using sorted compact
JSON. Do not create a receipt from these instructions without the corresponding
human decision. Test capabilities have CALIBRATION scope and are unusable for main.

REVIEW_ACCEPTED and FREEZE commit to all static fields of `policy-proposal.json`.
LAUNCH also binds the fresh run ID and conservative UTC host start: use the launch
authorization timestamp **before provisioning**, not a later runner-start timestamp.
All expiries must cover the 360h deadline. The actual policy is a `Policy` object,
not the proposal's wrapper. A future start is rejected. Hashes/source closure are
verified on every admission and periodically during collection. Main ledger and
execution UUIDs are allocated only after this complete authorization chain.

Only after those decisions and the separately authorized deployment:

```sh
.venv/bin/python artifacts/phase-8-review-freeze/v2/runner.py init \
  --root /var/lib/p8/run --backup /var/lib/p8/backup \
  --source /opt/fyp-phase8-linux-v1 \
  --manifest artifacts/phase-8-review-freeze/v2/review-inventory.json \
  --schedule artifacts/phase-8-review-freeze/v2/schedule.json \
  --policy /var/lib/fyp-owner/launch-policy.json \
  --receipts /var/lib/fyp-owner/receipts --key /var/lib/fyp-owner/owner.key
.venv/bin/python artifacts/phase-8-review-freeze/v2/runner.py verify --root /var/lib/p8/run
sudo --preserve-env=PYTHONPATH .venv/bin/python artifacts/phase-8-review-freeze/v2/runner.py install-watchdog --root /var/lib/p8/run
systemctl is-active fyp-phase8-hardstop.timer fyp-phase8-watchdog.service
sudo systemctl start fyp-phase8-campaign.service
```

The installer creates the hard-stop timer, admission watchdog and campaign unit;
it does not start the campaign unit. Main run refuses admission without matching,
active independent timers. The campaign service survives terminal/chat closure;
it does not automatically restart after a protocol failure or host reboot. Keep
the exact launch receipts/configuration in the evidence record. Verify the
instance shutdown behaviour is **stop**, preserving its encrypted evidence disk;
timer and completion shutdown are not AWS termination/deletion operations.

## Progress, pause and resume

```sh
sudo journalctl -u fyp-phase8-campaign.service -u fyp-phase8-watchdog.service -f
.venv/bin/python artifacts/phase-8-review-freeze/v2/runner.py status --root /var/lib/p8/run
.venv/bin/python artifacts/phase-8-review-freeze/v2/runner.py pause --root /var/lib/p8/run
```

Pause stops new admissions. The active original keeps collecting, exporting and
backing up; wait for its BACKED_UP state. For a finite pause, the controller exits
at the next admission gate. Host time and estimated charges continue. To resume
an ordinary BETWEEN_SLOTS pause within the same boot/deadline, after the service
has exited:

```sh
.venv/bin/python artifacts/phase-8-review-freeze/v2/runner.py resume --root /var/lib/p8/run
```

That command operates in the terminal. For unattended service resume:

```sh
.venv/bin/python artifacts/phase-8-review-freeze/v2/runner.py clear-pause --root /var/lib/p8/run
sudo systemctl start fyp-phase8-campaign.service
```

Only an ordinary pause can be cleared. Do not rename/delete failure pauses by hand. They
require diagnosis and a recorded human review; source changes require a new
accepted package. No automatic failure-unpause or diagnostic rerun is provided.

For terminal operation independent of a service, `run --root ... --pause-after N`
pauses after N additional fully backed-up slots. `--checkpoint-once` is a separate
calibration control; it must not be used in the main schedule. A Ctrl+C parent
pause leaves the detached collector running. Keep the host up; resume attaches
to its pinned PID or SQL checkpoint. It must never replay the driver.

If same-boot collector recovery is needed, original services/DBs, source seals and
checkpoints must survive. Same ID and deadline are preserved. A missing checkpoint,
host reboot or lost service/database stops automatic recovery. Preserve the
interruption and unresolved original; never initialize a replacement run over it.

## Backup failure, postflight and analysis

An ambiguous cloud PUT keeps its reservation and rejects repeated/new PUTs.
Reconcile the exact pending archive without writing another object:

```sh
.venv/bin/python artifacts/phase-8-review-freeze/v2/runner.py reconcile-backup --root /var/lib/p8/run
```

A unique matching version can be verified read-only; failure pause remains.
No-match/multiple-match/hash drift require review. Backups/failures/partial dumps
are retained. SQL state cannot be changed to pretend backup success.

Use each `run/backups/<execution-id>.json` with postflight on a new short local
directory. This command reads S3 through profile `fyp-research`; it does not launch
an execution or clean up resources:

```powershell
python artifacts/phase-8-review-freeze/v2/postflight.py <proof.json> E:/P8R001
```

For offline verification, add `--local-archive <archive.tar.gz>`. Preserve every
interrupted transfer and partial extraction. Reconcile stale locks before retained
renaming. On expiry, use a separately labelled linked transport attempt, preserving
the old checkpoint/pieces; never reset its original deadline. Require two local
hash-matching archives plus the pinned cloud version and postflight/accounting
checks before any later authorized evidence-disk cleanup. No cleanup is included
in this runner. Escalate before 48h stopped-disk retention or the first cloud month
expires if verification/retention is still unresolved.

Run read-only analysis from a fresh output path after downloading/preserving all
original evidence, with the accepted source environment and receipts:

```sh
.venv/bin/python artifacts/phase-8-review-freeze/v2/analyze.py /var/lib/p8/run /var/lib/p8/analysis-original.json
```

Read-only checks verify the chain at its launch anchor, allowing postflight after
operational expiry; they do not permit new admissions or a reset host clock.
Missing originals remain UNKNOWN with the saved execution identity, attempt 1
and planned denominator. Diagnostic traces never replace originals. Do not run
the main analysis as a pre-launch substitute for actual observations.

No continuous Codex conversation, manual repair delivery or paid API is a runner
dependency. A delayed bill, hardware failure or indefinite retention still needs
operator attention; unattended execution is not a promise of lossless recovery.

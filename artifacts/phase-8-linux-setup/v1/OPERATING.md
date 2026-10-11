# Phase 8.1 Linux source capsule — terminal operation

Status: **calibration-only, not frozen, main campaign blocked**. The study stays
500 inputs × B3/P1/P2 = 1,500 first-attempt slots, with the existing 600-second
observation window, endpoints, timeouts, missingness and original-attempt rules.
This adapter reuses the preserved v4 instrument and storage v2. It does not change
application behaviour, migrations, provider semantics, arm opportunities or fixtures.

## Prerequisites and transfer

Dedicated Linux x86_64 host (Ubuntu 24.04 with Python 3.12 is the intended AWS
target), Linux kernel with pidfd support, cgroup v2, Docker Engine/CLI, stable UTC
clock, source directory writable by its research operator, output and backup
directories outside the source tree. The Linux container validation is separate
from EC2 qualification: no AMI or instance type has been certified yet.

AWS project resources belong in **ap-southeast-2**, using profile **fyp-research**
for management. Native application/simulator processes need no AWS credentials.
Do not copy local `.aws`, `.env`, browser sessions, keys or models onto the host.
The capsule contains public synthetic research evidence; it contains no credentials.
No instance is created by this package. Before 8.2 provisioning, agree a finite
AWS calibration spend ceiling and check actual Sydney pricing, plan, quotas and
storage. Do not upgrade the free plan or create a main-study server implicitly.

Transfer `linux-source.tar.gz` and its `.sha256` file through an approved host
management session. In the transfer directory:

```bash
sha256sum -c linux-source.tar.gz.sha256
mkdir -p /opt/fyp-phase8-linux-v1
tar -xzf linux-source.tar.gz -C /opt/fyp-phase8-linux-v1
cd /opt/fyp-phase8-linux-v1
bash artifacts/phase-8-linux-setup/v1/bootstrap.sh
export P8_DOCKER_DATA_PATH="$(docker info --format '{{.DockerRootDir}}')"
.venv/bin/python artifacts/phase-8-linux-setup/v1/runner.py --help
```

Prepare permissions for a dedicated operator (example `fyp`, Docker access) before
extraction; no root AWS credentials are needed. `bootstrap.sh` installs locked
runtime dependencies and a **separate** analysis environment. Source/fixture
files stay byte-identical. Bootstrap does not initialize, freeze or launch a study.
Frozen Windows path references are supported by manifest-declared Linux file
aliases. The original JSON strings, traces and grades are never rewritten.
Database image identities must be matched against the local evidence before
8.2; architecture is deliberately x86_64, not an unqualified Arm port.

## Finite qualification commands (8.2, not executed by bootstrap)

Choose NEW paths; never reuse an unsuccessful attempt directory.

```bash
cd /opt/fyp-phase8-linux-v1
export P8_DOCKER_DATA_PATH="$(docker info --format '{{.DockerRootDir}}')"
.venv/bin/python artifacts/phase-8-linux-setup/v1/runner.py init \
  --root /srv/fyp/cal-linux-v1 --backup /srv/fyp-backup/cal-linux-v1
.venv/bin/python artifacts/phase-8-linux-setup/v1/runner.py verify --root /srv/fyp/cal-linux-v1
.venv/bin/python artifacts/phase-8-linux-setup/v1/runner.py run --root /srv/fyp/cal-linux-v1
```

These admit only two new `cal-v4-linux-v1-*` IDs, one normal B3 return and one P1
stale-claim refusal. They are collector qualifications, not a paired comparison
or sufficient evidence to qualify every AWS fault. 8.2 must prespecify its finite
additional fault/resource checks in a separate version if needed. There is **no
main-launch or freeze command**. Plan acceptance does not authorize launch.

Calibration admission retains >=1.5GiB available RAM, >=5GiB system/Docker free,
>=2GiB output/backup free. The probe uses Linux `MemAvailable` capped by cgroup v2
headroom. CPU reports whole-kernel aggregate; container tests cannot attribute it
to an instance workload. Main capacity thresholds remain review decisions from
the Windows report (3GiB available, 25GiB Docker, 50GiB working, 50GiB backup).
Actual EBS allocations and filesystem sharing require new measurement; this
package does not claim those reserves or disjoint physical backups exist on EC2.

## Independent operation and progress

For supervised calibration, the foreground terminal is sufficient. For operation
after logout, install the supplied service unit after preparing its operator,
paths and NEW calibration directory:

```bash
sudo cp artifacts/phase-8-linux-setup/v1/fyp-phase8-calibration.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start fyp-phase8-calibration.service
journalctl -u fyp-phase8-calibration.service -f
```

The unit has no boot enablement and no automatic restart/replay. It uses Python,
Docker, PostgreSQL and local files; it does not import Codex or invoke an agent.
OS process independence is exercised locally; actual EC2 systemd operation and
logout resilience still require 8.2 qualification. Progress appears every 30
seconds, with execution ID, state and original deadline. Raw terminal/service
logs and ledger failure events remain durable.

## Pause, resume, failures and evidence

```bash
.venv/bin/python artifacts/phase-8-linux-setup/v1/runner.py pause --root /srv/fyp/cal-linux-v1
.venv/bin/python artifacts/phase-8-linux-setup/v1/runner.py status --root /srv/fyp/cal-linux-v1
# After the active slot exports, or to attach to a continuing detached collector:
.venv/bin/python artifacts/phase-8-linux-setup/v1/runner.py resume --root /srv/fyp/cal-linux-v1
.venv/bin/python artifacts/phase-8-linux-setup/v1/runner.py backup --root /srv/fyp/cal-linux-v1
.venv/bin/python artifacts/phase-8-linux-setup/v1/runner.py verify --root /srv/fyp/cal-linux-v1
```

`pause` stops new admissions and lets the current window finish. SIGINT/SIGTERM
to the parent records a safe stop and leaves the detached collector running.
Resume waits for a still-owned live collector; otherwise it attaches read-only
to the original checkpoint, ID, bindings and deadline. It never replays the
driver. A missing SQL checkpoint, host reboot, lost service, source drift or
backup error stops admission and preserves evidence. Only intentional pauses
can be cleared by `resume`; a defect is not silently converted into a user pause.
Keep Docker, original volumes and the host alive through active observation.
Do not reboot/stop the EC2 host as a routine pause during a slot.

Pidfd signalling plus start ticks prevent PID reuse cleanup. A boot ID guards
against cross-reboot attach. File locking is nonblocking `flock`, released by
the OS after process exit. All databases/cache resources must have this setup's
ownership label before start/stop/flush. Existing application resources are never
reset. Single concurrency remains enforced; no parallel schedule is qualified.

The inherited collector retains late durable events, missing completion as
UNKNOWN, uncapped exports, fixed grading deadlines and all first attempts.
Incremental verified compressed objects and ledger deltas are backed up after
exports; full database checkpoints retain the storage v2 cadence. There is no
continuous WAL archive or proven full-host/disaster recovery. A separately
located backup on the same disk is not independent physical protection.

## Local validation

The Dockerfile builds a Linux test environment from the exact source capsule.
Unit checks exercise actual Linux process ownership, detached-child survival,
locks and launch guards. `smoke.py` boots new PostgreSQL servers and unchanged
application processes, verifies schema/health, attaches to identical PIDs,
backs up and verifies hashes, then stops only owned resources. It sends **zero
business requests** and admits **zero calibration or main-study slots**.
Bridge-network mode `P8_VALIDATION_NETWORK` exists only for this local container
test; the network must be labelled `research.linux.validation=v1`. The AWS native
path uses loopback bindings; it must be tested independently in 8.2.

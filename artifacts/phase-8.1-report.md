# Phase 8.1 — Linux execution preparation

**Status: Phase 8.1 local Linux preparation gates passed. Phase 8.2 has not
started. Main campaign remains unstarted and guarded.**

## Scope and files

New `research/execution_linux_v1/{__init__,platform,portable,runtime,runner}.py`
implements Linux resource probing, nonblocking OS file locks, process start-time
identity, pidfd cleanup, boot-ID/service-loss guards and independent collector
launch/parent reattach. It reuses the historical collector, ledger, storage v2,
v4 oracle and instrument through research-process-only bindings. No application
module is patched and no original source file is edited.

New `artifacts/phase-8-linux-setup/v1/` contains the normal-terminal entrypoint,
deterministic source capsule builder, pinned Linux validation Dockerfile, native
bootstrap, manual systemd unit, operating instructions, Linux tests, PostgreSQL
boot-check script and retained validation records. This report is a new artifact;
the earlier Phase 8 reports and freezes remain untouched.

Migrations added: **none**. Existing schema head `0013_readiness_capability` was
applied to new owned research PostgreSQL servers. Dedicated cache/server ownership is checked before
start/stop/flush. Regional AWS resources remain restricted to ap-southeast-2.
Read-only AWS plan verification found FREE/ACTIVE with $100 credits; no AWS
server, database, storage purchase or paid API was created or invoked.

## Research invariants

- Scope remains 500 inputs × B3/P1/P2 = 1,500 main slots. All are NOT_STARTED.
- This package admits only a separate `cal-v4-linux-v1-*` queue; it cannot freeze
  or launch the main campaign. No main IDs were executed, no reviewer receipt
  was generated and no source snapshot is represented as a reviewed freeze.
- PostgreSQL owns durable correctness; Redis remains the companion-cache control.
- The application, provider behaviour, arm opportunities, fixture bank, revised
  grader, endpoints, missingness and 600-second windows remain unchanged.
- Same execution identity/deadline, SQL-authoritative checkpoints, original
  failed attempts, separately labelled diagnostics and immutable exports remain.
- Lost services/host reboot/ambiguous interrupted commands are not replayed.
- Scientific dependencies have a separate environment; an analysis import overlay
  is excluded from application-service environments. AWS/provider keys are also
  excluded from those environments.

## Validation and retained failures

| Check | Evidence | Result |
| --- | --- | --- |
| Pinned Linux image and locked runtime dependency installation | `docker-build-attempt1.txt`, `linux-validation-image.json` | PASS; Linux amd64, Python 3.12.13, separate analysis environment |
| Original Windows regressions | `windows-regression.txt` | **38 passed** |
| First Linux regression attempt | `linux-unit-attempt1.txt` | **42 passed / 8 failed**; preserved Windows backslash path references could not be opened on Linux |
| Revised Linux regressions and OS boundaries | `linux-unit-attempt2.txt` | **50 passed**, no skipped tests; retained intermediate validation |
| Initial real Docker boot attempt after resource restoration | `linux-postgres-boot-attempt1.txt` | FAIL: lowercase Docker absent-object message was rejected; zero slots admitted, original attempt retained |
| Docker message compatibility regression and original Linux checks | `linux-unit-attempt3.txt` | **54 passed** in 12.59 seconds, no skipped tests; includes absent-message case variants and refusal of other errors/wrong resource names |
| New strict typing and lint | `mypy-docker-remedy.txt`, `ruff-docker-remedy.txt` | PASS (eight implementation/entrypoint files typed) |
| Historical and prior-source preservation | `final-verification-after-boot.json` | PASS: **1,625 files unchanged**, all 1,500 main slots NOT_STARTED |
| Linux PostgreSQL/application boot, backups and service attach | `linux-postgres-boot-attempt2.txt`, linked success record below | PASS: four services healthy, separate process attached to the same PIDs, existing schema installed, zero workflows/executions |
| Backup integrity and owned cleanup | `final-verification-after-boot.json` | PASS: six checkpoint file hashes, eight compressed/raw object pairs, SQLite integrity; all three owned containers stopped with exit 0 |

The portability remedy declares 300 read-only Linux file aliases for exact frozen
Windows references. Canonical artifact bytes and JSON path strings are unchanged.
All original failed validation output is retained. This is a filesystem adapter,
not an outcome/grader change.

Linux test success includes real OS `flock` exclusion/crash release, real detached
child survival after its launcher exits, process identity mismatch refusal and
owned-process shutdown. It also includes main-ID rejection, fixed deadline/ID,
reboot/lost-service refusal, environment isolation and preserved oracle/storage
regressions. The separate boot check exercises real PostgreSQL; neither check
substitutes for full-window AWS collector qualification. The image uses the pinned dependency build plus the
exact current capsule extracted into a temporary validation container; the base
validation image alone is not represented as the final capsule source version.

Successful evidence: `linux-unit-attempt3.txt` (54 passes; standalone Linux process
and revised-instrument checks), plus the
[real PostgreSQL boot success](<E:/FYP-Research/phase8-linux-v1/boot-attempt2/boot-smoke-success.json>).
Expected refusal evidence: the main admission,
lost-PID, reboot and lock tests in that suite, plus `local-resource-stop.json`.
The [unsuccessful boot attempt](<E:/FYP-Research/phase8-linux-v1/boot-attempt1/boot-smoke-failure.json>)
is retained separately. No successful Linux business/600-second execution trace
exists yet: the boot script deliberately admitted zero calibration slots and
issued zero business requests. Passing counts are repeated validations of
overlapping suites, not additional independent study inputs.

The boot backup is recorded in its
[manifest](<D:/FYP-ResearchBackups/phase8-linux-v1/boot-attempt2/incremental-v2-edc97850-346c-4d22-8c2d-cf1dcbcb1f03/backup-manifest.json>).
It includes application and simulator PostgreSQL dumps and the research ledger.
Hash/decompression/SQLite integrity verification passed; a PostgreSQL restore to
a replacement AWS host is not claimed by this boot check. The PostgreSQL volumes,
stopped containers and owned validation network remain for evidence retention.

## Resource incident

At the local stop, available memory briefly fell below 1GiB and C: free space
briefly fell to about 0.2GiB. At the retained later check, RAM was about 1.65GiB
available and C: about 0.43GiB free. E:/D: had much more space, but Docker and the
Windows system paging file are on C:. The paging file had grown to 8,966MiB
allocated at inspection; that observation is not sole-cause attribution.

Three build-cache records created by this task were selectively removed by ID:
`0i0l75l7p7pqxjp9b0ze0ogiy`, `j0r5clpjqhjnwe3i9r78apkgo`,
`9j2ichom6c0ng6f9q5xe7s3wg`. This freed cache inside Docker but did not restore
the required Windows C: reserve. No global prune, existing-container shutdown,
historical-volume deletion, paging configuration change or host restart occurred.
No validation container or new research database stack remains running.

After the user freed disk space, host checks passed. Immediately before the
successful boot, C: had **19.20GiB** free and available RAM was **2.36GiB**
(`resource-before-boot-attempt2.json`). The validation container was limited to
2GiB RAM and two CPUs; its success snapshot reported **408MiB** used and
**1.60GiB** available inside that limit. These are admission/end snapshots, not
peak memory or campaign throughput measurements. Linux sees the Docker VHD's
logical free space; the separate Windows probe verifies the backing C: reserve.
The after-boot host snapshot retained about **19.19GiB** free C: and **1.74GiB**
available RAM. This remains insufficient to qualify two concurrent executions.

The local boot gate passed with >=5GiB free on C: and >=1.5GiB available RAM. Actual
capacity must be remeasured before admission. An AWS filesystem may have different
limits; the Docker Desktop VHD's logical free space does not prove Windows backing
disk capacity, so local validation checks the Windows host separately.

## Commands and operating evidence

Commands executed: read ordered repository sources; read AWS Compute and Billing
skills; read-only `freetier get-account-plan-state`; build the versioned capsule;
pull official Docker CLI 29.4.1; build pinned Linux dependencies; run original
Windows regressions; run Linux tests twice in one bounded container; run strict
mypy/ruff; verify historical hashes/main ledger; inspect local memory/disk/cache;
prune only three identified task-owned build-cache records; remeasure after user
cleanup; run two separately retained finite PostgreSQL boot attempts; verify the
corrected Docker boundary, backup integrity and owned service shutdown. Exact test commands
and stdout are retained in this package's validation records and terminal history.

Native Linux terminal, pause/resume, manual systemd and bootstrap commands are in
`OPERATING.md`. The runner imports no Codex tooling, conversational scheduler or
cloud voice provider. Detached process independence was tested; actual EC2
systemd/logout operation has not been tested. There is no automatic boot launch.

## Remaining gates and limitations

1. Before AWS qualification (8.2), agree its finite spend ceiling, check Sydney
   prices/plan/quotas and prepare a dedicated host. No AMI, capacity, AWS runtime,
   cost estimate or parallel isolation has been qualified by this work.
2. Qualify actual Linux full-window return/refusal, process resume and recovery
   faults in 8.2. Current OS tests establish implementation compatibility, not
   full-window throughput or unattended repair superiority.
3. Main review/freeze/separate launch authorization still remain later gates.
   Serial concurrency only; no parallel qualification was admitted.
4. No full-host disaster recovery/PITR or independent physical backup claim is
   added. No real-speech/human-comprehension claim is added.

## Candidate identity and readiness checklist

Current source capsule: **1,642 files**, 300 compatibility aliases, SHA-256
`2cbc081470257e3fa7c9c9c25ec749af1024b2d29496f99fbaf6511d1e4a1fe5`.
It is a versioned preparation candidate, not a reviewed protocol freeze.
Earlier blocked verification records and the prior package backup are retained;
`final-verification-after-boot.json` records the subsequent successful gate.

| Gate | Status | Remaining action |
| --- | --- | --- |
| Linux process, lock, drift/admission guards and preserved instrument regression | PASS | None for 8.1 |
| Real PostgreSQL boot, service attach, backup integrity and owned shutdown | PASS | None for 8.1 |
| Historical evidence and original application/migrations unchanged | PASS | Continue checking hashes in later stages |
| Normal terminal entrypoint and detached OS process boundary | PASS | EC2 service/logout and complete collector qualification belong to 8.2 |
| AWS capacity, pricing, finite calibration budget, actual full-window recovery | UNRESOLVED | Review finite 8.2 plan and qualify a dedicated Sydney host |
| Concurrent execution isolation and campaign speedup | UNRESOLVED | Serial only until separate bounded qualification passes |
| Main review, protocol freeze and launch | NOT AUTHORIZED | Keep all 1,500 slots unstarted |

**Verdict:** Phase 8.1 local preparation is complete and ready for review. AWS
qualification is the next stage; its gates remain explicit. No AWS resources,
paid API calls, protocol freeze or main-campaign executions were made.

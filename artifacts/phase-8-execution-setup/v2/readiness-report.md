# Phase 8 standalone execution setup — readiness report

**Verdict: ready for review; not ready to freeze or launch.** The campaign remains
unstarted: **500 inputs, B3/P1/P2, 1,500 NOT_STARTED slots**, no review receipt and
no protocol freeze hash. No application behaviour, executable contract or migration
was changed. All new work is research collection, ledger, orchestration, tests and
documentation. No paid API, cloud service, subscription or new research arm was used.

## Recommended schedule and cost

Run **one execution at a time**, with a fresh local service process set and new
scenario/workflow/property bindings. Keep all restart/cache-fault cases exclusive.
Ordinary cases are also serial: different IDs do not qualify overlap. Retain the
v4 shuffled input order, randomized arm order and twenty blocks of 25 inputs / 75
slots. A routine terminal run handles collection, export, backup and next admission
without an active Codex chat or continuous manual supervision. Defects stop admission.

Observation alone is 250 hours. With measured startup/finalization and existing
v4 recipe/arm timing references, the estimate is **262.65 hours** before reserve,
or **302.05–315.18 hours / 12.6–13.1 continuous days** with 15–20% operational reserve.
A 75-slot block is about 13.13 hours before reserve, or 15.1–15.8 hours with reserve.
One completed block per day implies approximately twenty calendar days. Windows
must remain awake for every active window; pausing between slots is allowed.

This is a planning estimate, not measured 1,500-slot throughput. It uses two full
windows, a 13.47-second startup reference, a 15.98-second finalization/backup
reference, and v4's 0.377 hours of weighted pre-final-request work. The 600-second
horizon was never shortened. Late-stage ledger size, antivirus, Docker activity,
host load and storage contention can change runtime; no p95 is inferred from two
cases. No qualified parallel estimate exists. A two-lane halving of 250 hours is
not presented as achievable throughput.

Local study execution has **no API fees**. Available RAM and disk, Windows uptime
and the computer's electricity are the practical constraints. No upgrade is
required by the software; adequate free space and headroom still need to be arranged.

## Live qualification evidence

The observation horizon is final externally scripted request + 600 seconds,
including time after a driver return/refusal. It is not reset at return or resume.

| Execution | What was exercised | Retained result |
| --- | --- | --- |
| [B3 normal return](E:/FYP-Research/phase8-setup-v1-attempt2/executions/588c3f20-30ce-46db-a86e-58d20e336006/export.json) | Collector checkpoint exit, services continued, same execution/deadline resume; post-return late ACK | Driver COMPLETED; final business state TRUE; speech support/update and clean outcome UNKNOWN after the separately declared late duplicate ACK control |
| [P1 buffered stale refusal](E:/FYP-Research/phase8-setup-v1-attempt2/executions/a8256c50-d495-4de6-9a34-f7f88ff1fd67/export.json) | Normal-path STARTED refusal (HTTP 409), ordinary corrective update, full window, safe-stop request while active | Driver COMPLETED; final state, accepted correction and current update TRUE; unsupported/stale exposure UNKNOWN; refusal preserved |

These are collector qualifications on different cases/arms, **not a paired arm
comparison**. Oracle validation means the evidence was accepted and graded; it
does not mean every outcome was TRUE or safety was proved. No superiority, novelty,
clean-case noninferiority or human-exposure conclusion follows from these runs.

The B3 deadline remained `2026-10-05T09:42:02.187487+00:00`; export collection ended
1.79 seconds later. The collector resumed the SAME ID after a deliberate checkpoint
gap of 66.27 seconds between polls. Durable services/journals continued; the gap is
retained, not labelled continuous polling. The separately declared duplicate ACK
was captured 3.76 seconds after its durable server timestamp, in
[poll 84](E:/FYP-Research/phase8-setup-v1-attempt2/executions/588c3f20-30ce-46db-a86e-58d20e336006/polls/00084.json).
Its later scripted client timestamp introduces support uncertainty; it is not
rewritten to improve the grade. See the retained
[control plan](E:/FYP-Research/phase8-setup-v1-attempt2/controls/late-ack-v1-plan.json)
and [response](E:/FYP-Research/phase8-setup-v1-attempt2/controls/late-ack-v1-response.json).

The P1 deadline remained `2026-10-05T10:08:52.892261+00:00`; collection ended 1.99
seconds later. A safe-stop request at 10:01:36 stopped future admissions while
the active collector continued. Its maximum between-poll gap was 6.11 seconds.
Both runs retained 93 polls; polling takes time in addition to the 5-second wait.
Neither had a recorded collection error or oracle exception. Missing playback
evidence remains unknown; a server refusal is not assumed to prove client silence.

## Resources measured on this computer

Host measurements are in [measurements.json](measurements.json) and
[resources.csv](resources.csv). The usable physical RAM was 15.81GiB, consistent
with the user's nominal 16GB. C:, D: and E: are partitions of physical disk 0.
Docker's data VHD is on C: at
`C:/Users/syeda/AppData/Local/Docker/wsl/disk/docker_data.vhdx`.

| Measurement | Observed |
| --- | --- |
| Available RAM at initialization | 2.09GiB |
| Minimum available RAM during collection | **2.08GiB** |
| Sampled peak whole-host RAM used | **13.73GiB** |
| Available RAM after qualification | 3.51GiB |
| Native research service working sets / sum of process peaks | 304.77 / 305.46MiB; includes Windows launcher children, excludes Docker VM and collector/parent |
| Whole-host CPU during collection | Mean 36.25%, median 35.60%, sampled maximum 72.92% |
| Docker engine allocation | 3.82GiB RAM, 8 logical CPUs; each new PostgreSQL capped at 256MiB / 1 CPU, companion cache at 64MiB / .25 CPU |
| Free disk after qualification | C: **8.53GiB**, E: 182.93GiB, D: 100.53GiB |

Host peaks are sampled at collection cadence; short peaks between samples may be
missed. Summed per-process peak working sets need not occur simultaneously. Host
load includes unrelated applications and eleven pre-existing containers; no claim
is made that all host CPU/RAM usage was caused by the research runner.

Available memory remained below the predeclared **4GiB** threshold for testing two
concurrent executions. The two-execution test was therefore **not admitted**.
This is a measured reason for serial execution, not evidence that parallelism is
unsafe on every machine. It does not certify overlapping restart/cache controls.

## Growth and backups

| Growth | B3 qualification | P1 qualification |
| --- | ---: | ---: |
| App database | +528KiB | +384KiB |
| Simulator truth database | +352KiB | +0KiB allocated size; new facts still persisted |
| App WAL generated | 695.5KiB | 265.3KiB |
| Truth WAL generated | 590.9KiB | 57.5KiB |
| Logs / WAV audio | 24.5 / 61.9KiB | 29.6 / 129.5KiB |
| Final export | 770KiB | 2,011KiB |
| Poll evidence | 2.16MiB | 8.11MiB |
| Complete execution directory | 3.75MiB | **12.19MiB** |

WAL generation is cumulative write volume, not retained disk use. At export, WAL
directories were 32MiB for app and 16MiB for truth. Repeated checkpoints and Docker
VHD allocation can change physical usage; two trials do not establish a growth bound.

The live qualification tree was 19.40MiB. All retained backups, including original
v1 full copies, occupied 11.0MiB. The storage-v2 object archive used **1.21MiB for
214 compressed objects**. At the largest measured execution size, 1,500 execution
directories alone would occupy about **17.86GiB**, excluding growing ledger,
database and backup overhead. This is an illustration, not a worst-case bound.

The original per-slot full-tree copying policy would grow cumulative backups
quadratically. It is preserved historically but superseded by storage v2: each
sealed file once, compressed objects verified against raw hashes, slot/event
deltas after exports, and full ledger/database checkpoints each 75 slots, controlled
checkpoint and completion. Full historical audits occur at those checkpoints and
completion; source/active evidence is checked during collection. Explicit `verify`
performs a full audit. Failed archive attempts retain their directories and do not
advance the archive cursor.

Reserve **50GiB working evidence on E:, 50GiB backup on D:, and 25GiB on the Docker
data drive** before main launch. E:/D: meet those proposed disk reserves now; C:
does not. Main RAM admission should require at least 3GiB available, higher than
the qualified calibration minimum of 1.5GiB. These are proposed launch requirements,
not permission to start. The frozen package must enforce the accepted thresholds.

During active collection, available RAM below .75GiB or system disk below 2GiB
produces a durable pressure notice and stops further admission while collection
continues. New serial calibration admission is rejected below 1.5GiB available RAM,
5GiB on C: or 2GiB on output/backup volumes. Hard exhaustion, OS termination and
clock discontinuities cannot guarantee complete evidence: preserve gaps/unknowns,
do not extend deadlines or silently replace attempts.

### Backup/recovery limits

Original PostgreSQL volumes remain the correctness authority for active late
effects. There is **no continuous PITR WAL archive**. Between full database
checkpoints, finalized evidence and ledger deltas are backed up; full database
disaster restoration and unattended full-host recovery were not qualified.
Never reconstruct missing provider effects as successes or retry ambiguous writes.
The qualified recovery is a collector-process checkpoint with services continuing.

D: backups protect against file damage but are on the same SSD as C:/E:. Physical
drive failure protection requires copying checked backups to an existing independent
device, or explicitly accepting that limitation. No cloud purchase is prescribed.

## Isolation and interference assessment

- Two new labelled app/truth PostgreSQL servers use ports 16432/16433, distinct
  roles/databases and retained named volumes. Existing application databases were
  not reset or reused. The simulator alone receives truth-write/oracle settings;
  controllers/workers do not receive simulator credentials or oracle tokens.
- API/voice/worker/simulator use 19100/19101/19102/19110. Each slot starts a fresh
  process set. Runtime cleanup checks PID creation identity; no orphan research
  service on those ports remained after either execution.
- Resource/workflow/scenario IDs and collection queries are execution-bound.
  Truth reads do not consume provider status-visibility counters or advance jobs.
- Provider barriers are scenario-bound. Research adapter globals are bound only
  inside one dedicated OS process, never shared between concurrent threads.
- Restart targets the current owned worker and, when the native P2 recovery path
  is used, its workflow scope. Native recovery is the existing application path;
  the collector does not manually deliver repair or replay commands.
- Cache flush checks the new research container's ownership label. It targets
  that entire companion cache, so it remains exclusive. It does not target the
  application or historical v4 Redis; this application does not consume the
  companion cache, so it remains a negative control rather than an app outage.

The current qualification did not execute a restart/cache overlap or a pair of
concurrent ordinary cases. Their overlapping isolation remains UNRESOLVED, and
none is scheduled concurrently. Previous v4 hook qualifications remain historical
evidence; this package does not relabel them as new parallel qualification.

After both exports and verified backups, the three owned research database/cache
containers were stopped with ownership checks, preserving their volumes. Existing
application containers remain running. Read-only status/hash verification needs
no database restart; fresh qualifications can use the released research ports.

## Analysis compatibility and evidence limits

The original Phase 8 clustered latency requirement is retained. The prior
descriptive-only timing proposal is explicitly superseded by
[analysis-compatibility.md](../v1/analysis-compatibility.md): paired input-cluster
intervals, stratified resampling, restricted protocol completion time at 600 seconds,
completed-subset descriptions, explicit missingness bounds, and the existing
identifiable arm + stratum censored lognormal AFT with input-cluster bootstrap.
Recipe labels are fixed support, not sampled family clusters. Repetitions/reruns
do not increase independent n. Shared host/time dependence remains a conditional
assumption and requires the retained order/block sensitivity reporting.

The binary endpoints, missingness rules, 300 clean inputs with 5pp tolerance,
co-primary comparisons and ten-comparison Holm family remain unchanged. Review
must accept the explicit timing amendment and nominal secondary interval scope.
Synthetic text/tone and scripted ACKs support protocol/timing/transaction and
evidence-handling conclusions, not hearing, intelligibility, ASR, turn-taking,
caller comprehension or real telephone reliability. No real speech campaign or
optional extension is added here.

## Changed files, validation and preserved failures

New collector package: `research/execution_setup/{core,resources,runtime,worker,
cli,timing,__init__}.py`; targeted tests: `tests/test_execution_setup.py`.
The separate artifact package v2 contains `runner.py`, `test_storage.py`,
`measure.py`, terminal instructions, this report and retained measurements.
Storage v2 changes only research orchestration; it reuses the original collector
and oracle. Its entrypoint is hash-registered before admission. No earlier
migration, application file or frozen fixture was edited. Existing schema head
was installed on the new dedicated research databases; migrations added: **none**.

Validation: **38 tests passed**, strict type checking passed for eight implementation
files, lint passed, two real-PostgreSQL full-window executions were exported without
collector/oracle exceptions. Tests cover deadline/ID preservation, interrupted-driver
non-replay, missing anchors, immutable collisions, export/checkpoint/event drift,
diagnostic retention, backup snapshots, resource guards, paired clustering, censoring,
AFT integration, incremental object reuse/corruption and historical full audits.
See [regression.txt](regression.txt), [mypy.txt](mypy.txt), [ruff.txt](ruff.txt),
[preservation.txt](preservation.txt) and [qualification-file-hashes.json](qualification-file-hashes.json).

Executed commands and prerequisites are in [OPERATING.md](OPERATING.md). PowerShell
started the runner independently, then exited; collector progress continued. A
separate invocation resumed the first execution. No active-chat dependency exists
in the execution path. Closing the Codex UI itself was not an additional experiment;
the evidence is OS process independence and terminal-only invocation.

All **1,358** historical/candidate/previous-plan files in the preservation inventory
passed before/after hashes. Frozen Phase 7 v1 manifests, source archive, traces,
grades/reports and v4 sources/fixtures remain unchanged. The original collector
source hashes also remain unchanged across the storage-v2 qualification.

Retained unsuccessful attempts: initial inventory preparation interrupted before
admission (generated dependency/build traversal), the subsequent guarded refusal
to run that incomplete setup (`config.json` missing), and one late-control helper
bootstrap failure before plan/transmission. Their original directory/logs remain at
`E:/FYP-Research/phase8-setup-v1`. Development validation initially had 2 failures
/ 14 passes, fixed before live qualification; its record remains in
[unsuccessful-attempts.json](../v1/unsuccessful-attempts.json). No unsuccessful
attempt was substituted for or removed from a study outcome.

## Finite readiness checklist

| Item | Status | Concrete remaining action |
| --- | --- | --- |
| 500 × B3/P1/P2 and windows/endpoints retained; main blocked | PASS | Keep guards until reviewed freeze and separate launch authorization |
| Terminal-only healthy execution and progress | PASS | Use the versioned entrypoint and keep host awake |
| Full-window normal return/refusal; late ACK retained | PASS | Retain UNKNOWN grades and the deliberate gap |
| Same-ID/deadline process resume; saved order and safe stop | PASS | Services/original volumes must continue; never replay driver |
| Missing anchors, immutable evidence, diagnostic retention, drift guards | PASS | Preserve first attempts and investigate defects in a new version |
| Incremental backups, SQLite restoration, hash rejection | PASS | Accept the full-audit/checkpoint cadence and maintain reserves |
| Whole-host/database disaster recovery and physical backup | UNRESOLVED | Accept bounded recovery scope; arrange independent backup if required; do not claim active late-effect recovery after data loss |
| Two-execution isolation, including restart/cache overlap | UNRESOLVED | Accept serial-only schedule; no parallel launch in this package |
| Proposed main disk reserve on Docker's C: drive | FAIL | Increase measured free space from 8.53GiB to at least 25GiB, or review a research Docker storage location with that reserve |
| Sustained main RAM margin / large-ledger resource behavior | UNRESOLVED | Accept/enforce 3GiB admission margin; current minimum was 2.08GiB; retain resource stops and conservative runtime reserve |
| Timing contract compatibility | PASS code / UNRESOLVED review | Accept input-cluster intervals, censored interpretation and dependence/model assumptions |
| Protocol review, freeze, launch authorization | UNRESOLVED | Review scope, schedule, thresholds, backup limitations and timing amendment; then freeze the exact package and authorize launch separately |

**Final verdict:** the finite setup and qualification evidence are ready to review.
The resource and review actions above must be resolved before freezing and launch.
The 500-input campaign is unstarted; this package neither freezes nor authorizes it.

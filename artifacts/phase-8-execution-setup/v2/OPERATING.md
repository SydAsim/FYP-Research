# Storage v2 terminal setup

Use this entrypoint for the reviewed setup. It reuses the v1 collector and v4
instrument, and adds incremental compressed archiving. It cannot freeze or launch
the main campaign. The qualification has two slots; the guarded main order still
contains 500 inputs × B3/P1/P2 = 1,500 NOT_STARTED slots.

## Prerequisites

Windows, Python 3.12 and the existing project environment, Docker Desktop with the
local `postgres:16.9` and `redis:7.4.5-alpine` images, and free research ports
16432/16433/19100/19101/19102/19110. No paid keys, LiveKit service, cloud scheduler
or subscription is needed. Keep Windows awake and Docker running during active
windows. The current environment's base Python binary is in the local Codex runtime
cache; it is an installed file dependency, not a dependency on an active chat.
Uninstalling that runtime would require rebuilding the environment with ordinary
Python 3.12. No agent or conversational connection is imported by this runner.

For finite calibration, admission requires 1.5GiB available RAM, 5GiB free on C:,
and 2GiB on output/backup volumes. Main planning proposes at least 3GiB available
RAM, 25GiB on Docker's data drive, 50GiB for working evidence and 50GiB for backups.
Those main thresholds must be accepted and enforced in the future frozen package;
this qualification runner does not admit any main ID.

## Exact PowerShell commands

```powershell
Set-Location -LiteralPath 'C:\Users\syeda\OneDrive\ドキュメント\ChatGPT\Final Year Project'
$env:PYTHONIOENCODING = 'utf-8'

# Read and fully verify the retained qualification; no new execution.
.\.venv\Scripts\python.exe artifacts/phase-8-execution-setup/v2/runner.py status --root E:/FYP-Research/phase8-setup-v1-attempt2
.\.venv\Scripts\python.exe artifacts/phase-8-execution-setup/v2/runner.py verify --root E:/FYP-Research/phase8-setup-v1-attempt2

# Only if a new finite qualification is wanted: NEW directories, never overwrite.
.\.venv\Scripts\python.exe artifacts/phase-8-execution-setup/v2/runner.py init --root E:/FYP-Research/new-qualification --backup D:/FYP-ResearchBackups/new-qualification
.\.venv\Scripts\python.exe artifacts/phase-8-execution-setup/v2/runner.py run --root E:/FYP-Research/new-qualification
```

The normal foreground terminal runs independently until the finite queue completes
or a guard stops admission. Progress is printed every 30 seconds; per-execution
logs and durable notices identify failure, deadline and execution ID. No Codex
turn is used as a scheduler. The qualified runs were started as detached Windows
processes from PowerShell, and continued after the launching command returned.

The retained qualification is complete and its owned database/cache containers
were stopped after export; their named volumes remain intact. `status` and `verify`
work without those databases running. A fresh qualification can use the now-free
research ports. Database backup of the retained run requires starting its owned
containers first; read their exact names from its `resources.json`, verify the
`research.setup` ownership label, and start only those names. Do not run `resume`
on a completed directory merely to start databases or create another outcome.

## Stop and resume

```powershell
# From a second terminal: stop NEW admissions while the current slot finishes.
.\.venv\Scripts\python.exe artifacts/phase-8-execution-setup/v2/runner.py pause --root E:/FYP-Research/new-qualification
.\.venv\Scripts\python.exe artifacts/phase-8-execution-setup/v2/runner.py status --root E:/FYP-Research/new-qualification
.\.venv\Scripts\python.exe artifacts/phase-8-execution-setup/v2/runner.py resume --root E:/FYP-Research/new-qualification

# Reproduce process checkpoint recovery in a NEW qualification.
.\.venv\Scripts\python.exe artifacts/phase-8-execution-setup/v2/runner.py run --root E:/FYP-Research/new-qualification --checkpoint-once
.\.venv\Scripts\python.exe artifacts/phase-8-execution-setup/v2/runner.py run --root E:/FYP-Research/new-qualification --pause-after 1
.\.venv\Scripts\python.exe artifacts/phase-8-execution-setup/v2/runner.py resume --root E:/FYP-Research/new-qualification
```

Resume uses the SAME execution ID and original deadline; it never reissues the
driver. Existing services and original PostgreSQL volumes must remain available.
A driver interrupted during a write stays uncertain and is not retried. An expired
deadline is not extended: export uncapped durable journals with the gap recorded;
the oracle caps grades at the original horizon and treats missing anchors/evidence
as unknown. If services/host were lost, retain the incident and do not claim the
qualified continuing-service recovery path demonstrated full-host recovery.

Ctrl+C in the parent is a safe admission stop; its child can continue collecting.
Wait for EXPORTED before stopping Docker or Windows. Never use `pause` to overwrite
a defect notice or delete a failure pause. Intentional between-slot/user pauses
are the only automatically resumable reasons. Protocol defects, source drift,
collector/oracle errors and failed backups require investigation in a separately
recorded version/diagnostic attempt. Do not edit seals, move deadlines, overwrite
outcomes, clear defects as ordinary pauses or replace an original with a rerun.

## Integrity and backups

The executing storage entrypoint is copied and registered by hash before admission.
Source and active evidence checks run during collection. Finalized evidence is
audited before it is archived; full historical ledger/export checks occur at
75-slot checkpoints and completion. Explicit `verify` always performs a full audit.
This bounded policy supersedes v1's repeatedly hashing all historical poll files
in every active minute. A drift discovery stops admission and preserves all
affected executions for review; no automatic regrading or replacement occurs.

Storage v2 copies each sealed file once into `objects-v2/<raw-hash>.gz`, verifies
the decompressed hash, and writes a new slot/event/object delta after each export.
Each 75-slot boundary, controlled checkpoint and completion also retains a full
SQLite snapshot and separately timed dumps of app/truth PostgreSQL. Original v1
full backups are preserved. Compression savings are measured, not guaranteed for
every future trace. No external service is required.

```powershell
.\.venv\Scripts\python.exe artifacts/phase-8-execution-setup/v2/runner.py backup --root E:/FYP-Research/new-qualification
.\.venv\Scripts\python.exe artifacts/phase-8-execution-setup/v2/runner.py verify --root E:/FYP-Research/new-qualification
```

Between full checkpoints, final exported outcomes and ledger deltas are backed up,
not a new full database dump on every slot. Original volumes remain the authority
for active late effects. There is no continuous PostgreSQL point-in-time WAL archive.
After database loss, stop admissions, retain all originals and restore a verified
full checkpoint/deltas into a NEW recovery directory; do not claim missing active
effects were recovered or blindly replay them. End-to-end disaster restoration of
all services/volumes remains unqualified. The tested SQLite snapshot restores
metadata, not a lost provider's unobserved effects.

C:, D: and E: are partitions of the same physical SSD. For hardware failure
protection, copy verified archives to an existing independent device. A failed
backup directory remains present and its cursor is not advanced.

## Validation commands

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv-study-design/Lib/site-packages').Path
.\.venv\Scripts\python.exe -m pytest tests/test_execution_setup.py tests/unit/test_phase8_candidate_v4.py artifacts/phase-8-execution-setup/v2/test_storage.py -q
.\.venv\Scripts\python.exe -m mypy research/execution_setup artifacts/phase-8-execution-setup/v2/runner.py
.\.venv\Scripts\python.exe -m ruff check research/execution_setup tests/test_execution_setup.py artifacts/phase-8-execution-setup/v2/runner.py artifacts/phase-8-execution-setup/v2/test_storage.py
```

See `analysis-compatibility.md` in v1 for the retained clustered latency intervals,
input sampling/dependence unit, censored AFT, missingness rules and speech limits.
The readiness report distinguishes qualified behaviour from remaining review and
resource actions. These commands do not authorize a study freeze or launch.

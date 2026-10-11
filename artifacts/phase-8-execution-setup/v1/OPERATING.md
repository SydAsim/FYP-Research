# Terminal operating instructions

This version runs the **two-slot qualification only**. It has no freeze or main
launch command. The 500-input, 1,500-slot order is retained in a guarded schedule
template. Enabling that schedule requires the reviewed protocol, a new frozen
package and separate launch authorization. Commands below do not enable it.

## Prerequisites

- Windows, Docker Desktop running in Linux-container mode; computer awake, sleep
  disabled for the entire active observation and collection period.
- Project's Python environment and unchanged application dependencies (`uv.lock`).
  Existing local `postgres:16.9` and `redis:7.4.5-alpine` images; provision uses
  `--pull=never` and cannot silently download a replacement image.
- Research ports 16432/16433 and 19100/19101/19102/19110 free. New labelled container
  names and volumes; never substitute existing application servers or caches.
- Available memory at least 1.5GiB for serial calibration. At least 5GiB free on C:
  for this finite qualification, and 2GiB each for output and backup. Main planning
  requires the larger disk reservations in the readiness report, not these smaller
  qualification limits. Two concurrent executions remain unqualified.
- No API keys. The simulator, deterministic tone output and scripted ACK client
  are local. The application UI/LLM/LiveKit stack is not required by this research
  runner. Running unrelated services affects available RAM and measured CPU load.

## Commands from a normal PowerShell terminal

```powershell
Set-Location -LiteralPath 'C:\Users\syeda\OneDrive\ドキュメント\ChatGPT\Final Year Project'
$env:PYTHONIOENCODING = 'utf-8'

# Inspect the already qualified directory; does not admit any execution.
.\.venv\Scripts\python.exe -m research.execution_setup.cli status --root E:/FYP-Research/phase8-setup-v1-attempt2
.\.venv\Scripts\python.exe -m research.execution_setup.cli verify --root E:/FYP-Research/phase8-setup-v1-attempt2

# A fresh finite qualification uses a NEW directory. Never overwrite the retained one.
.\.venv\Scripts\python.exe -m research.execution_setup.cli init --root E:/FYP-Research/another-qualification --backup D:/FYP-ResearchBackups/another-qualification
.\.venv\Scripts\python.exe -m research.execution_setup.cli run --root E:/FYP-Research/another-qualification
```

The runner prints progress every 30 seconds and preserves per-execution terminal
logs; the collector reports remaining time at least every minute. It checkpoints,
collects the full fixed window after normal returns/refusals, exports, backs up and
advances in saved order. A Codex chat, API subscription or hosted scheduler is not
involved. Closing Codex does not provide input to these processes. Do not close the
terminal itself while expecting the parent scheduler to admit later slots.

## Safe stop and resume

From a second normal terminal, request a stop after the active slot:

```powershell
.\.venv\Scripts\python.exe -m research.execution_setup.cli pause --root E:/FYP-Research/another-qualification
.\.venv\Scripts\python.exe -m research.execution_setup.cli status --root E:/FYP-Research/another-qualification
.\.venv\Scripts\python.exe -m research.execution_setup.cli resume --root E:/FYP-Research/another-qualification
```

`pause` prevents further admissions; the active slot continues to its original
deadline. `resume` clears only an intentional user/between-slot pause. Ctrl+C at
the parent also stops admissions while its independent child finishes collecting.
Wait for export before stopping Docker or shutting down Windows. Each execution
has an OS lock, preventing a second collector from silently entering it.

To reproduce the qualified collector checkpoint path in a **new qualification**:

```powershell
.\.venv\Scripts\python.exe -m research.execution_setup.cli run --root E:/FYP-Research/another-qualification --checkpoint-once
.\.venv\Scripts\python.exe -m research.execution_setup.cli run --root E:/FYP-Research/another-qualification --pause-after 1
.\.venv\Scripts\python.exe -m research.execution_setup.cli resume --root E:/FYP-Research/another-qualification
```

This deliberate checkpoint exits the collector but keeps services alive. Resume
reattaches read-only to the same execution, without extending the deadline or
replaying the driver. If the original deadline already passed, retain the gap,
collect current durable journals and keep late effects in the uncapped export;
the revised oracle excludes events after the original cap. Never relabel this as
uninterrupted collection. A missing final anchor cannot earn a complete timing or
negative exposure result.

## Failures, drift and recovery limits

Driver/collector/oracle/backup failures and source/hash drift produce durable
events, a failure notice and an admission pause. Do not edit the source seal,
delete the pause file or overwrite an export to make a run pass. Collect and retain
the original; investigate in a new versioned qualification package. A separately
labelled diagnostic slot can be appended with `diagnostic --original <execution-id>`;
it never replaces attempt 1, and defect pauses are not automatically cleared.

If Windows or Docker stops, durable data stays in the dedicated volumes and ledger.
This version qualifies process checkpoint recovery with **services continuing**;
it does not qualify unattended full-host recovery. Restore service ownership and
the original source package before collecting the same attempt. A missing/dead
service causes retained collection failures and unknown evidence. Do not retry
ambiguous writes or start a fresh execution as its replacement. Repair delivery
remains the application recovery path, not a collector command.

## Backups

```powershell
.\.venv\Scripts\python.exe -m research.execution_setup.cli backup --root E:/FYP-Research/another-qualification
.\.venv\Scripts\python.exe -m research.execution_setup.cli verify --root E:/FYP-Research/another-qualification
```

Each backup is a new directory with checked hashes, a SQLite snapshot, logs,
checkpoints, audio, poll records, final exports and separate app/truth database
dumps. Failed backups remain present. Dumps are separately timed, not a simultaneous
distributed snapshot. C:, D: and E: are partitions of physical disk 0: copy verified
backups to an existing independent drive for physical-drive failure protection.
Keep named volumes and original exports. Do not use `docker compose down -v` or
delete volumes as a recovery shortcut.

Analysis libraries remain separate from application dependencies. The existing
`.venv-study-design` supplies `research/study/requirements.txt`; tests use:

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv-study-design/Lib/site-packages').Path
.\.venv\Scripts\python.exe -m pytest tests/test_execution_setup.py tests/unit/test_phase8_candidate_v4.py -q
.\.venv\Scripts\python.exe -m mypy research/execution_setup
.\.venv\Scripts\python.exe -m ruff check research/execution_setup tests/test_execution_setup.py
```

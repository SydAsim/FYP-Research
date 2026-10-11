# Standalone setup qualification v1

Status: separate execution qualification, not a protocol freeze. Main admission is disabled.

## Scope decided before execution

Retain the v4 candidate: 500 context inputs, paired B3/P1/P2 (1,500 slots), the
300/100/60/40 strata allocation, existing outcomes, 33 delivery challenge inputs,
and 600 seconds after the final externally scripted request. No paid calls,
microphone, native audio adapter or cloud services. Tone and scripted ACKs are
protocol evidence, not evidence of hearing or human understanding.

Create two separately identified calibration cases, copied from the **calibration**
bank, with fresh workflow/scenario/property bindings. Never copy a main input into
a live calibration. Retain the original context and fault configuration and record
the new fixture hash. All extra runs are diagnostic attempts, never replacements.

1. Normal clean B3 return: collect through the original 600-second deadline.
   Exit the collector after two polls, leave services running, back up, then attach
   from a second terminal process to the same ID and deadline. Pause after export.
2. P1 buffered stale STARTED refusal: resume the saved second slot, preserve the
   refusal and ordinary corrective response, then collect the full 600 seconds.

Budgets remain the v4 budgets. Collector cadence is 5 seconds, service readiness
40 seconds, database backup 60 seconds. Record actual gaps and overshoot. A missing
final-request anchor gets a fixed fallback collection cutoff at execution start
plus 600 seconds, **not a fabricated request**: its final-window negatives and
resolution timing remain unknown. No accepted revision is inferred from a request.
Full-window collection continues after ordinary returns, refusals and driver
failures; new admissions stop on defects. An interrupted driver is never replayed.

## Resource and isolation gate

First measure one execution. Do not admit even serial calibration below 1.5GiB
available RAM, 5GiB free on the Docker/system drive, or 2GiB on output/backup drives.
Two concurrent executions require at least 4GiB available RAM and complete separate
service processes, ports, app/truth PostgreSQL servers, bindings and fault controls.
The current runner is deliberately serial; if headroom is absent, record the
parallel test as unattempted and retain exclusive execution for every case.

Two owned PostgreSQL containers (256MiB/1 CPU each), plus an owned 64MiB companion
cache, use new names/volumes. API/voice/worker/simulator have research-only ports.
The existing schema is installed unchanged, with no migration or application edit.
Global bindings in inherited research adapters are changed only in a dedicated OS
process; they are never shared between concurrent threads. Cache ownership is
verified before a flush; cache loss remains a companion-cache negative control.
Worker restart is restricted by PID creation identity and workflow scope. Neither
mechanism establishes safe overlapping executions without a live isolation test.

While active, RAM below .75GiB or system disk below 2GiB stops subsequent admissions
and produces a durable warning while collection continues. A source/export/checkpoint
hash mismatch, oracle defect or collector error stops admissions and retains the
original attempt. Hard disk exhaustion or OS termination cannot guarantee logging;
the recovery verdict must explicitly retain gaps and missingness.

## Validation and grading

Unit checks cover same-ID/deadline resume, original retention, diagnostic labels,
main-ID rejection, immutable collisions, event/checkpoint/export drift, SQLite
backup recovery, missing anchors, resource thresholds, clustered timing and AFT.
Live exports run the existing v4 revised observable grader, with durable server
ACK times where available. Polls independently read simulator truth and
workflow/call-scoped durable application journals; they do not read provider
status endpoints or advance jobs. Collector gaps remain recorded; missing ACKs
remain unknown for exposure/completion outcomes, never presumed silence.

Checkpoint state and its event hash commit together in the research SQLite ledger.
The JSON checkpoint is a convenience view. Final exports/polls/audio use exclusive
creation and registered hashes. Immutability is detectable local integrity, not WORM
or protection against deliberate rewriting of all manifests. Backups include the
ledger, traces, audio, logs, and separately timed dumps of both dedicated databases;
two database dumps are not a simultaneous distributed snapshot.

The resource estimate will use actual full-window measurements, existing v4
recipe/arm timing references and conservative reserves. Two trials cannot estimate
p95 growth, memory peaks between polls, hardware performance under all 50 recipes,
or shared-host statistical dependence. Do not shorten windows to improve estimates.

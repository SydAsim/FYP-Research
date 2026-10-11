# Phase 8.3 — fixed parallelism pilot, candidate v1

Status: PREPARED FOR REVIEW; no AWS resource or pilot execution is authorized by this file. The 500-input campaign remains unstarted and unfrozen. The earlier US$2 grant covered Phase 8.2 only.

## Remaining gaps reviewed from 8.2

- V2 completed full windows; v3.1 integrity/diagnostic numbering had component and init-only checks. A complete window must exercise their combined candidate.
- Only P2 restart/cache overlap was tested. B3/P1 overlap and representative clean, hidden-commit and playout behaviour remain unqualified.
- Earlier serial and parallel timings used different recipes; they cannot establish a speedup for matched workloads.
- Short measurements did not qualify all-recipe throughput, campaign storage, prolonged load, host disaster recovery or real speech.

## Fixed size and sequence

**24 planned executions, six protocol recipes, three arms, zero main inputs.** Use new `cal-v4-linux-v1-p83-v1-*` IDs; preserve fixture parameters from separate v4 calibration prototypes. No main bank record may supply a pilot fixture.

1. Measure one clean B3 execution first, with the combined runner and full 600-second window.
2. Complete a serial reference for all six recipes under B3/P1/P2: 18 executions total, including that first one. Fixed recipe order: clean, hidden commit with immediate visibility and dropped response, buffered stale start, decisive partial-time exposure, worker restart before repair delivery, dedicated cache loss.
3. Three two-lane blocks follow, one per arm B3/P1/P2. Each block overlaps restart-before-repair with Redis loss: six additional executions. These are labelled PLANNED_SCHEDULE_REPEAT and linked to the corresponding serial execution. They do not increase independent scenario N and never replace original outcomes.
4. Parallel slots require measured first-execution headroom and current >=4 GiB available host RAM, >=5 GiB system/Docker disk and >=2 GiB output/backup reserve. Active resource pressure stops new admissions. If headroom is insufficient, run those six saved slots serial, record SERIAL_FALLBACK before their admission, and recommend serial. No extra cases or tuning loop.

All cases keep the existing arm definitions, endpoints, named fault barriers, retry/recovery budgets, scripted tone/ACK paths and final-request +600-second observation. The partial-time recipe reaches decisive time content; it is not the distinct late-decisive-ack recipe. The selected six are representatives, not exhaustive fault coverage.

## Proposed resources, time and spending ceiling

One dedicated Sydney m7i-flex.large, 2 vCPU/8 GiB, encrypted 40 GiB gp3, no inbound access; local simulator and scripted audio only. Reuse read-only preserved source/candidate archives and the existing scoped export role. No paid voice/model calls, database service, new IAM permission expansion or paid-plan upgrade.

**Proposed ceiling: US$2 for this pilot, subject to explicit approval and fresh pricing/plan checks.** Maximum powered session: six hours from original launch, absolute stop deadline that does not reset on reboot. Stop new admissions with less than 20 minutes before that deadline. Automatic verified export and stop on completion/failure. Keep the root disk for at most two days within the estimate unless cleanup is explicitly chosen earlier; a stop timer does not delete it. Cleanup choice is required before deployment.

At 8.2's measured rates, a script must recompute the six-hour compute/IP/disk allowance, two-day disk retention and US$0.50 export contingency before deployment. A price/plan change that exceeds US$2 blocks launch. This is a spending plan, not an invoiced cost or exact AWS billing cap.

Observation-window lower bounds: bounded parallel 3 hours (18 serial windows plus three concurrent pairs); serial fallback 4 hours. Allow approximately 3.5–4.5 hours with qualified overlap, 4.5–5.5 hours serial including bootstrap/exports. These are provisional estimates, not representative quantiles. The six-hour deadline bounds the finite attempt; unadmitted slots remain recorded.

## Completion and admission criteria

Completion means all 24 slots are accounted for, not that every business grade is TRUE. Retain PASS, expected refusal, business failure, UNKNOWN, timeout, infrastructure failure, and NOT_ADMITTED outcomes. Every admitted execution must retain its original ID/deadline and final query starting at/after cutoff, or be explicitly incomplete. Independently regrade exports and validate backup hashes. Missing anchors/ACKs remain unknown.

The parallel-isolation gate requires distinct services, namespaces, networks, application/truth databases, caches, resource/fault/query bindings and outputs. For each arm, restart changes only its lane's worker; cache FLUSHDB affects only its own cache; independent truth and snapshots contain no peer workflow. Use BOTH_RESOURCES_READY barrier, not a sleep to place faults. Current CPU/memory and per-lane counters are recorded. If source drift, collector defect or interference occurs, stop new admissions and retain evidence; do not silently patch or rerun.

An isolation pass is limited to the measured restart/cache pair and arms. Do not generalize to all main recipes. Comparing serial and repeated parallel records is descriptive schedule qualification, not a treatment effect or superiority test. Report first blocking mechanism and all arm outcomes without predicting a winner.

## Outputs and final recommendation

- Sealed combined research runner, fixed plan/order, preserved source inventory and tests.
- Per-slot immutable exports, ledgers, original failures and labelled repeats; host and lane resource measurements, wall time and poll gaps.
- Measured serial versus supported limited overlap; estimate campaign time only for the explicitly eligible fraction. Other cases stay serial.
- Database/WAL, logs, tone audio, raw/compressed exports and backup growth. WAL allocation is not linear per-case growth. Project campaign disk plus backup reserve using measured data; the calibration disk is not campaign capacity proof.
- Keep input-clustered latency intervals in the main analysis. Any mixed schedule needs reviewed shared-host dependence and overlap metadata before freezing.
- Phase 8.3 report with PASS/FAIL/UNRESOLVED gates and remaining limitations. Synthetic protocol tests do not establish real spoken exposure, human understanding or transparent recovery after host loss.

No main campaign, freeze, optional extension or open-ended optimization is included.

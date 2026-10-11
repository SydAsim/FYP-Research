# Phase 8.3 — parallelism pilot preparation

Status: **RUNNING — approved 24-execution calibration pilot.** The 500-input
B3/P1/P2 study remains unstarted and unfrozen. This report records launch and the
first completed window; it is not a completed parallelism result.

## Approved launch and live status

The user approved: "approve US$2 pilot and cleanup. also u will be free right the
excution is on auto pilot ?" This covers Phase 8.3 only, not the main campaign.
[Approval](phase-8-parallel-pilot/v1/approval.json).

- One Sydney server: `i-021200fbdba05bb8e`, owner `p83-c525d267c8ec`.
- Absolute stop: **2026-10-06 19:53:31 UTC**, **7 October 00:53:31 Asia/Karachi**.
  The installed timer was verified through SSM. It does not reset on reboot.
- Source archives and dependencies passed bootstrap hash checks. The first B3
  execution, `86f44a58-9847-4723-a002-98d45a5fe820`, completed and exported its
  full original window ending **14:05:04.650857 UTC**. The serial block passed
  collection/isolation checks. P1 subsequently began, ID
  `804e7936-2358-4785-805f-671e2c2d05a5`, original cutoff **14:15:24.688444 UTC**.
- First measured host peak used memory **1.195 GiB**, minimum available **6.399
  GiB**, maximum sampled CPU **49.36%**. This meets the first headroom condition;
  current resources and the remaining absolute deadline must still permit each
  planned pair after all 18 serial references. It is not a parallelism PASS.
- Initial local direct-script launch failed before AWS creation because the
  repository import root was absent. The unsuccessful attempt is retained in
  `launch-wrapper-attempt1.json`; separate `launch.ps1` supplies that root without
  changing sealed cloud research code. The subsequent single approved launch
  used one recorded client token and succeeded. No business execution was replaced.

### Standalone postflight and storage clarification

The cloud systemd job runs the fixed pilot and saves/validates its exports without
Codex calls. A separate finite normal-terminal controller is running locally:
`control-v1/watch.py`, launch process ID **12360**. It polls for the saved receipt,
verifies the exact S3 object version/bytes/SHA256 and pilot/source identity,
downloads two copies, independently regrades retained exports, verifies backup
manifests, then terminates only the tagged approved server and its root disk.
Failures stop this controller, retain original files/IDs and leave evidence for
review. It does not admit cases, replay drivers, expand permissions or call models.
It also checks for a still-running owned server after the absolute cost deadline.

Measured C:, D: and E: are all **partitions of physical Disk 0**. The earlier
operations document's extra instruction to use different physical local disks
cannot be met on this computer. The approved cleanup guard requires two verified
local copies and S3. The implemented locations are `E:/fyp-phase83-evidence` and
`D:/P83`, explicitly labelled as **one local physical failure domain**, with the
versioned verified S3 object stored separately. No independent local-hardware
backup claim is made. This records the discrepancy rather than silently treating
partitions as independent storage.

Keep the computer awake for automatic local postflight/cleanup. The AWS pilot
continues and its stop timer remains active if the computer or Codex chat closes;
local postflight cannot run while the computer is off. A hard interruption of
postflight requires reconciliation of saved files/cleanup intent, not a driver
rerun or overwriting an unsuccessful copy.

Postflight controller checks: **3 tests passed**, strict type check passed, lint
passed. An initial missing type annotation was repaired before starting the
separately sealed controller; its failed check is retained. The full real export
and cleanup path remains pending until the pilot finishes. See
[controller source](phase-8-parallel-pilot/control-v1/watch.py) and its journals.

An independent finite local report process (ID **11300**) waits for postflight and
writes `artifacts/phase-8.3-outcomes.md`, preserving all 24 planned statuses, endpoint
grades/UNKNOWN, trace links, host/time/storage measurements and a conservative
schedule recommendation. It makes no network/model calls or case admissions.
Its type/lint checks passed; a retained rendering smoke check confirmed that all
24 unadmitted slots remain visible and cannot produce a PASS. It records mechanism
fields without claiming that a repair field alone identifies the first unsafe-action
block. Human review of supported conclusions and main-study eligibility remains
necessary before any freeze or launch. This reporting process does not change the
sealed cloud collector or replace unsuccessful observations.

## Reviewed gaps and fixed response

| Completed 8.2 evidence / remaining gap | Fixed 8.3 response |
|---|---|
| Four valid v2 windows; combined v3.1 had only integrity/init checks | Every pilot slot uses combined v3.1 collector plus the separately sealed new initializer |
| Two P2 recipes overlapped; B3/P1 overlap unqualified | A restart/cache pair for each of B3/P1/P2, after serial references |
| Earlier serial/parallel workloads differed | Match each repeated recipe/arm/context to its retained serial execution; label schedule repeats separately |
| Refusal can leave exposure evidence UNKNOWN | Retain UNKNOWN and full observation; never equate refusal with silence |
| Restart/global cache changes can affect neighbors | Private lane processes, bridges, PostgreSQL/cache containers, fault controls; peer cache sentinels, worker identities/lifecycles and collection contamination checks |
| Sustained storage, other recipes and hard host recovery unqualified | Limit any recommendation to measured pairs; keep others serial and report unresolved capacity/recovery |

## Plan declared before execution

See [fixed plan](phase-8-parallel-pilot/v1/plan.md) and
[24-slot manifest](phase-8-parallel-pilot/v1/slots.json).

- **24 planned calibration executions, zero main inputs**: six original protocol
  recipes × B3/P1/P2 = 18 serial references; three two-lane restart/cache blocks =
  six linked PLANNED_SCHEDULE_REPEAT executions. The first slot is clean B3 and
  measures single-execution host use before any concurrency.
- Six recipes: clean Asia/Karachi appointment, hidden commit/dropped response,
  buffered stale claim, decisive partial-time playback, restart before repair,
  dedicated Redis loss. Separate v4 calibration prototypes only.
- Preserve all existing endpoints, named barriers, budgets and **600-second
  original observation windows**. All planned successes, failures, timeouts,
  UNKNOWN, incomplete and NOT_ADMITTED outcomes remain in accounting.
- Proposed new **US$2 ceiling**, one Sydney 2-vCPU/8-GiB server with encrypted
  40-GiB gp3, maximum six powered hours with an absolute stop deadline. No paid
  speech/models, managed database, subscription or permission expansion.
- Current 8.3 approval was granted in the quoted user message above. The historical
  US$2 approval covered 8.2 only and was not reused.
  The temporary session was expired, but the existing codex-user IAM connection
  is valid. The fyp-research profile now reuses that existing credential provider;
  identity and ACTIVE FREE plan were verified, with US$119.85 credits reported.
  No new keys were copied. The redundant browser login was cancelled. The earlier
  failed probe is retained. Fresh pricing/instance checks must precede deployment.
  [Connection resolution](phase-8-parallel-pilot/v1/connection-resolution.json)
  supersedes the candidate operations document's instruction to renew sign-in.

Completion requires all 24 slots explicitly accounted for, cutoff-valid collection
for completed executions, identical independent regrades, verified retained
exports/backups, intact historical hashes, reported resource measurements and
an isolation verdict for each attempted pair. It does **not** require favorable
outcome grades. Infrastructure/protocol defects stop admission and block qualification.

## Schedule and estimates — historical measurements, not new results

**Recommend serial for now.** Admit a pair only if the first measured reference
has minimum available memory ≥4 GiB and peak used memory ≤3 GiB, current available
memory ≥4 GiB, system/Docker disk ≥5 GiB, output/backup reserve ≥2 GiB and ≥20 minutes
remain before the original host stop. Otherwise the six saved repeats run serial
and the decision is recorded as SERIAL_FALLBACK. Resource pressure during a window
stops new admissions while reachable active collection continues.

8.2 measured serial slots at approximately 603 seconds and one P2 pair at 10m26s;
its sampled paired host peak was 1.597 GiB used, minimum 5.997 GiB available and
maximum CPU 91.05%. The maximum recorded collection gap was 5.512 seconds. These
support testing two lanes, not declaring this pilot qualified.

- Pilot observation floor: three hours if all three pairs qualify; four hours for
  serial fallback. Provisional total: **3.5–4.5 hours paired, 4.5–5.5 hours serial**,
  including preparation/exports; six-hour stop retains unfinished/unadmitted slots.
- Prior measured rates give approximately **US$0.780** for a six-hour host,
  **US$0.252** for up to two days of stopped-disk retention, plus **US$0.50** export
  allowance = **US$1.532**. These are 8.2 rates, not fresh prices or an invoice.
  Fresh ambiguous rates or a total above US$2 block deployment.
- Historical raw execution folders were 4.58–16.11 MiB and individual exports
  0.90–2.80 MiB: 24 slots imply roughly 110–387 MiB raw and 22–67 MiB export files,
  before database volumes, WAL, images, logs, archive and backup growth. Retained
  physical PostgreSQL volumes are measured separately; WAL preallocation is not
  per-minute growth. This does not establish that a 40-GiB main host is sufficient.
- Main serial floor remains **250 hours** for 1,500 windows; retain the earlier
  12.6–13.1-day planning range until representative measurements revise it. No
  whole-bank two-lane speedup is justified. If a pair qualifies, use measured pair
  wall time only for that recipe/arm allocation; isolate the remainder.

## Files and invariants

Only `artifacts/phase-8-parallel-pilot/v1/` and this report were added/changed.
No application behavior, earlier migration, main fixture, arm profile or outcome
grader was edited. Migrations added: **none**.

| Files | Invariant supported |
|---|---|
| plan.py, slots.json, plan.md, budget-proposal.json | Fixed size/order, calibration-only IDs, unchanged windows, repeat links and predeclared budget |
| combined.py | Latest combined collector; sealed executing adapters; one private slot; original deadline/attempt identity |
| pilot.py, lane.py, monitor.py, checks.py | Serial-first headroom gate; isolated resources/faults; finite admission; safe stop; retained failed attempts |
| bootstrap.sh, finish.sh | Terminal/systemd execution with no Codex dependency; absolute cost stop; bounded preservation and content-verified export |
| postprocess.py, relocated measure_p82.py/backups_p82.py | All 24 statuses, no replacement, independent revised regrade, preserved 8.2 measurement algorithms with import-path adaptation only |
| aws.py, deploy.py | Immutable requests, ambiguity stop/reconciliation, new human approval, fresh price/free-plan/Region checks |
| test_*.py, local-candidate-attempt*, *attempt*.txt/json | Qualification boundaries and unsuccessful local attempts retained |
| preserved-before.json, preservation-after.json, seal.json | Historical preservation and candidate identity; these are not protocol-freeze receipts |
| OPERATING.md | Exact terminal launch/prerequisites, status, interruption/export/cleanup rules and limitations |

## Validation evidence

- Local candidate attempt 1: **14 checks passed**, original/repeat initialization
  and verification; **zero admissions**.
- Attempt 2: **two collection/import errors**, caused by shallow relocated Linux
  paths. Its code snapshot, logs and request/result are retained unchanged.
- Candidate attempt 3: **17 checks passed**, shell syntax, original/repeat
  initialization and source/history/main guards; **zero admissions**, all 1,500
  main ledger slots NOT_STARTED. [Linux validation log](phase-8-parallel-pilot/v1/linux-init-attempt3.txt).
- Windows research tests: **12 passed**; strict type checking passed for nine new
  source modules. Intermediate type/lint failures are retained alongside repairs.
- The relocated measurement pipeline independently replayed **all five historical
  8.2 exports** with identical grades, including the original cutoff-defective
  attempt. These are compatibility checks, not new 8.3 executions.
  [Retained replay comparison](phase-8-parallel-pilot/v1/historical-replay-compatibility.json).
- Meaningful checks reject main IDs, shortened windows, unsafe headroom/deadline,
  crossed cache faults, peer restarts/query contamination, inherited stage approval
  and absent/ambiguous prices. Missing executions remain 24 NOT_ADMITTED entries.
- Successful trace: initialization/verification in the linked candidate-3 log.
  Expected failure evidence: launch-scope and isolation rejection tests; live
  business success/failure traces are **not yet available**.
- Before/after inventory covers **1,939 protected historical/source files**, including
  completed 8.2 evidence. [Final verification](phase-8-parallel-pilot/v1/preservation-after.json)
  passed with all 1,939 hashes identical.

## Remaining decisions and limitations

### Fresh read-only preflight, 6 October 2026

The complete prepared deployment preflight passed using the existing IAM provider:
correct project, ACTIVE FREE plan (US$119.85 reported credits), empty ingress,
available x86_64 image, free-plan-eligible m7i-flex.large, and current Sydney prices.
Compute remains US$0.1197/hour, in-use IPv4 US$0.005/hour, gp3 US$0.096/GiB-month.
The six-hour host + two-day disk reserve + US$0.50 allowance remains US$1.5323,
below the proposed US$2 ceiling. This is an estimate, not an invoice or billing cap.
[Fresh preflight evidence](phase-8-parallel-pilot/v1/readiness-1791294431893980800-summary.json).
All request/response journals are retained. No AWS resource or business execution
was created; repeat preflight at the actual approved launch.

| Gate | Status / concrete next action |
|---|---|
| Fixed pilot design and separate IDs | PASS, declared before execution |
| Local combined initialization and safeguards | PASS; does not substitute for real PostgreSQL windows |
| Historical hashes and main launch guard | PASS; final inventory identical and all 1,500 main slots unstarted |
| AWS connection | PASS; existing IAM provider verified through fyp-research; no browser sign-in required now |
| New stage budget/cleanup authorization | PASS; actual stage-specific approval recorded |
| Fresh AWS plan/pricing and deploy preflight | PASS read-only; repeat at approved launch |
| 24 live windows, peer isolation and new measurements | RUNNING; first B3 full-window export verified, remainder pending |
| Standalone cloud shutdown/export path | Bootstrap/timer/first collection verified; final export and shutdown pending |
| Other-recipe overlap/sustained main capacity | UNRESOLVED; retain serial recommendation |
| Hard EC2 restart/restore | UNQUALIFIED; no transparent whole-pilot resume or driver replay |
| Actual intelligible speech / hearing | Not in scope; scripted tone/ACK only |

The approved bounded pilot is **running**, not yet a completed 8.3 qualification.
The 500-input campaign remains unstarted and no protocol freeze or main launch
authority has been granted. Report all 24 outcomes and the measured recommendation
after verified evidence arrives; do not infer whole-bank speedup from this first slot.

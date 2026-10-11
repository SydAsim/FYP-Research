# Phase 7 pilot and protocol freeze

## Scope

Execute 40 independently specified synthetic maintenance scenario instances to
debug the protocol. These are purposively chosen instances with shared templates,
not 40 independently sampled people or proof of population independence. They
are fresh executions; Phase 6 executions are not counted as pilot observations.
Phase 8 has not begun.

The plan uses 20 structural covering rows, five provider timing boundaries, five
additional fault/read cases, one concurrent resource conflict, four audio timing
boundaries and five clean instances. One clean instance has six acoustic
versions. Its primary version is recorded clean speech, chosen in advance; the
other five are exploratory versions under that same scenario. Thus 40 instances,
45 scenario versions and 267 executions are different counts. Conflict uses only
B3/P1/P2; the other versions use all six arms. The structural domain constraints
and counterfactual audio limits in the Phase 6 report continue to apply.

## Endpoints and utility condition

There are two primary endpoints, with primary comparison P2 versus B3:

1. Correction success: externally specified final intent and absence of forbidden
   provider effects, for revision scenarios.
2. Per-task unsupported decisive confirmation under post-commit ambiguity:
   exposed decisive claim lacking applicable evidence at release/play, restricted
   to hidden-commit response-loss cases.

Client playback acknowledgements are an exposure proxy. They do not establish
physical hearing or comprehension. Controller process safety and external
end-to-end task correctness remain separate. Honest unresolved handoff can count
as safe resolution, and cannot count as a completed booking or useful decisive
outcome. Actual local recognition failures remain task failures.

The clean-task non-inferiority margin is 5 percentage points, a Phase 7 design
choice. P2 must have a one-sided 95% lower bound on the paired clean success
difference above -0.05. The analysis obtains a conservative bound by subtracting
the exact upper bound for paired losses from the exact lower bound for paired
wins, allocating alpha .025 to each tail. Safety improvement alone is insufficient:
clean utility and outcome coverage must also be reported. Five clean pilot
instances cannot establish this condition conclusively.

## Analysis plan

Retain one predeclared primary observation per scenario. Acoustic variants and
model repetitions do not increase independent sample count. Report raw paired
2x2 tables, discordant counts, rates and exact binomial intervals. Pilot McNemar
p-values are descriptive, without confirmatory conclusions. Exact McNemar uses
the binomial distribution, as documented by [statsmodels](https://www.statsmodels.org/dev/generated/statsmodels.stats.contingency_tables.mcnemar.html).
Rare-event bounds use exact binomial inversion; [NIST explains the need for exact
limits when failures are rare](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).
The paired non-inferiority construction is our conservative Bonferroni
combination of those bounds.

For the main campaign, apply Holm familywise alpha .05 across the two primary
tests. P1 mechanism comparisons and earlier baselines are secondary, with their
own declared comparison families. Use scenario-cluster bootstrap intervals for
paired latency differences (2000 draws, seed 7001). Do not convert absent or
non-comparable timestamps to zero. Resolution timeouts are right-censored at
their actual recorded observation boundaries. If multiple audio/seeds are used,
fit logistic mixed effects with fixed arm/phase/fault/revision/action and random
scenario-template and audio/speaker intercepts. Those main analyses belong to
Phase 8.

The manifest template allocates 500 new instances: 100 clean, 200 hidden-commit
ambiguity, 100 playout and 100 other provider-boundary instances. This is a sample
justification and frozen stratum plan, not a power guarantee. Pilot discordance
estimates have large uncertainty and shared-template dependence. At 500 total,
zero observed failures has an exact two-sided 95% upper bound near 0.735%; the
bound in a smaller stratum is wider. No pilot instance is reused in the main
campaign. Before Phase 8 starts, materialize and hash all 500 inputs and applicable
arms against this frozen generator/fixture domain; do not adapt selection to
observed main outcomes.

## Versions and budgets

The freeze records every executable source/contract/migration/fixture hash,
lockfile, container image identity, actual model and audio hash, transcript,
prompt and raw model output hash. It includes a portable source ZIP; generated
build/cache directories are excluded explicitly. There is no Git commit yet;
source inventory hashes identify the current uncommitted code.

Frozen effective budgets:

| Setting | Value |
|---|---:|
| Reconciliation attempts | 8 |
| Durable worker lease | 180 seconds |
| Provider adapter HTTP timeout | 30 seconds |
| Runner HTTP / named barrier timeout | 40 seconds |
| Workflow drain transition limit | 30 |
| Verification validity | 30 seconds |
| Intent HTTP timeout | 90 seconds |
| Local intent temperature / token limit | 0 / 120 |
| Acoustic capture process limit | 240 seconds |

The provider adapter's actual 30-second timeout is separate from the harness's
40-second wait. Preserve both. Models remain local Vosk, Qwen2.5 0.5B and eSpeak;
native-audio comparisons and paid providers are outside this pilot.

## Failure inspection and exclusions

Each unsuccessful or unsafe endpoint gets a review containing raw independent
provider history, client exposure, mechanism evidence, workflow/execution IDs,
reason and disposition. Read the generated reviews before final freeze.
Unobservable, partial and concurrently changed effects, baseline limitations,
withheld cancellation speech and clarification are retained and differentiated.
An unexpected failure in P2 must be investigated as a possible defect, not
renamed to an expected failure. Do not mutate the original replay after a fix:
version the affected protocol/fixtures and retain prior attempts.

Infrastructure failures/timeouts have trace IDs and explicit attempt ledgers.
They remain accounted-for planned slots; reruns have recorded reasons and retain
the original. Missing primary pairs prevent a confirmatory claim until accounted
for and sensitivity bounds are reported. Recognition failures, refusals, UNKNOWN,
handoffs and wrong intents are never excluded because they reduce success.

## Reproduction and drift guard

From the repository, with locked dependencies and the existing local services:

```powershell
$env:DATABASE_SYNC_URL='postgresql://voice_agent:voice_agent_local@127.0.0.1:15432/voice_agent'
$env:SIMULATOR_DATABASE_URL='postgresql://simulator:simulator_local@127.0.0.1:5433/simulator_truth'
.\.venv\Scripts\python.exe -m research.pilot.runner --output artifacts/phase-7-pilot/v1
.\.venv\Scripts\python.exe -m research.pilot.runner --verify <pilot-manifest.json>
.\.venv\Scripts\python.exe -m research.pilot.freeze <pilot-manifest.json>
.\.venv\Scripts\python.exe -m research.pilot.freeze <freeze-manifest.json> --verify
.\.venv\Scripts\python.exe -m research.pilot.reproduce <freeze-manifest.json>
```

The last command verifies and extracts the frozen source archive, starts a
separate Docker project with no host ports and two empty PostgreSQL volumes,
runs a selected P3 case through the same drivers and independent oracle, and
compares its binary metric rows exactly. New IDs/timings are new observations,
not expected byte-identical logs. Its source mount is read-only. Only the newly
created project's containers/volumes are removed; raw evidence and source remain.

The freeze guard fails on source, fixture, schema, lockfile or analysis drift.
Changing any such input requires a new protocol version before a campaign can
continue. This is a detectable content freeze, not filesystem edit prevention.

## Contract decisions retained

- Keep SQL UUIDv4 defaults per the approved Phase 1 exception.
- Cancellation has no authoritative decisive-speech enum: withhold it and expose
  a zero-denominator conditional cancellation metric.
- No new migration or API/event shape is required in Phase 7; migrations through
  `0011_phase6_b3_audio`, event envelope v1 and existing metric versions are frozen.
- Counterfactual unpermitted baseline audio stays in isolated synthetic research.
- Reports and fixture variants retain task failures; no successful rerun silently
  replaces an earlier failure.

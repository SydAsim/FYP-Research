# Phase 7 — pilot and protocol freeze

Status: **COMPLETE** for the defined pilot/freeze scope. All required gates pass.
Phase 8 has not started. Pilot results are not final research evidence.

## Scope implemented

Predeclared 40-instance pilot, 45 versions/267 planned executions, actual local
cascade evidence, independent replay verification, exact paired analysis,
failure inspection, source archive/freeze and clean Docker reproduction tooling.
The pilot is protocol debugging and not final research evidence.

## Files changed and invariants

- `research/pilot/plan.py`: external inputs and correct independent-unit counting.
- `research/pilot/runner.py`: fresh executions, trace-linked retained attempts,
  independently recomputed metrics and complete failure review.
- `research/pilot/freeze.py`: hashed protocol/configuration/source freeze and drift
  detection; PostgreSQL freeze record.
- `research/pilot/clean.py`, `reproduce.py`: original replay validation and fresh
  isolated provider/controller truth, same binary metric rows.
- `research/analysis/pilot.py`: exact counts, paired discordance and conservative
  clean-task utility bound, with no pilot confirmatory claim.
- `tests/unit/test_phase7_analysis.py`, `tests/integration/test_phase7_pilot.py`:
  arithmetic, repetition detection and real PostgreSQL failure preservation.
- `deployment/phase7-clean.compose.yaml`: empty isolated reproduction services.
- `docs/09_PHASE7_PROTOCOL.md`: endpoints, arm applicability, budgets, versions,
  analysis, exclusions and final campaign manifest template.

## Migrations

None added. Existing migration/schema/event contracts remain unchanged.

## Tests executed so far

- Ruff formatting and lint: PASS.
- Configured mypy: PASS, 105 source files.
- New analysis unit checks: 4 passed.
- New PostgreSQL wrapper integration: 1 passed, including rejected missing review
  and mismatched workflow evidence. XML: `phase-7-wrapper-tests.xml`.

## Pilot results and frozen evidence

The completed pilot has **40 fresh scenario instances, 45 versions and 267
executions**. There were zero infrastructure failures, excluded slots or reruns.
All 267 executions were independently reverified; 112 unsuccessful/unsafe
endpoint traces were reviewed and retained. Additional regression and clean
reproduction executions do not increase the pilot's sample count.

- [Pilot manifest](phase-7-pilot/v1/pilot-c1cf3fdf4dda.json), hash
  `c1cf3fdf4ddaa67417148191dae133896b347dce9db087db3cb997354de52a3e`.
- [Protocol freeze](phase-7-pilot/v1/freeze-90901263019a.json), hash
  `90901263019a6ebb1c4b4981b06279687618f9f2aeb00a52e69b45c46e160f4a`.
- Frozen source inventory hash
  `537b5984f585dbf78bbe41c4ef1d85e091c5369ceb5222546ab962a41b339c09`,
  202 source/contract/fixture/deployment/lockfile members. ZIP archive and actual
  container/model/audio identities are named in the freeze. Code remained
  identical throughout the pilot. No previous fixture was edited.
- [Raw counts](phase-7-raw-counts.json),
  [raw observations CSV](phase-7-observations.csv),
  [paired discordance](phase-7-paired-discordance.json),
  [sample justification](phase-7-sample-justification.json),
  [all failure reviews](phase-7-failure-reviews.json),
  [final manifest template](phase-7-final-manifest-template.json).

Primary observation counts (audio variants excluded from independent n):

| Arm | Correction success | Clean success | Unsupported confirmations, all primary tasks | Useful outcome coverage | Played-span repair |
|---|---:|---:|---:|---:|---:|
| B0 | 15/34 | 5/5 | 0/39 | 15/39 | 0/2 |
| B1 | 29/34 | 5/5 | 0/39 | 30/39 | 0/2 |
| B2 | 29/34 | 5/5 | 0/39 | 30/39 | 0/2 |
| B3 | 29/35 | 5/5 | 0/40 | 30/40 | 0/2 |
| P1 | 29/35 | 5/5 | 0/40 | 30/40 | 0/2 |
| P2 | 29/35 | 5/5 | 0/40 | 30/40 | 2/2 |

The post-commit ambiguity primary subset has **0/21 unsupported confirmations**
for each core arm. B3/P1/P2 have zero paired primary-endpoint discordance:
correction 0/35 (nominal exact 95% interval 0–10.00%), unsupported confirmation
0/21 (0–16.11%). Descriptive exact McNemar p=1 in both comparisons. These purposive
shared-template samples cannot establish population independence or superiority.
The visible separation is the two repair cases, a mechanism finding rather than
primary-endpoint superiority. This pilot does not justify an assertion that 500
cases will reveal a primary benefit.

The five clean primary instances succeeded in every arm. The conservative
one-sided lower paired NI bound is -52.18 percentage points, so a 5-point NI
condition is **not established by this pilot**. All six actual local acoustic
versions are reported separately: recorded clean succeeds; five synthetic
conditions clarify and retain zero writes/claims. Those 30 exploratory arm
failures remain in the raw 267-record data and failure reviews.

The sample plan freezes 500 *new* instances: 100 clean, 200 ambiguity, 100 playout,
100 other provider boundaries. The analytical 500-trial rare-event bound is
0.735% with zero failures; actual smaller stratum bounds are wider. The saved
`expected_discordant_at_500` values are explicitly hypothetical 500-trial
projections, not forecasts for every allocated stratum and not power guarantees.
For the actual allocation, the pilot's nominal discordance upper bounds imply
about 40 discordant revision pairs out of 400 and 32 ambiguity pairs out of 200;
the estimate itself is zero. Main inference and allocation remain separate from
the debugging pilot.

## Failure inspection

All 112 reviews retain provider history, exposure and mechanism evidence, linked
to workflow/execution IDs. Classifications:

| Class | Reviews |
|---|---:|
| Baseline mechanism limitations | 18 |
| Unobservable provider / withheld outcome | 30 |
| Cancellation speech contract limit | 15 |
| Partial effect with unresolved handoff | 6 |
| Concurrent resource conflict with handoff | 3 |
| Missing explicit played-span repair in ablation arms | 10 |
| Actual cascade clarification task failure | 30 |

No unsupported confirmation, duplicate effect or unexpected P2 final-state
failure was found. Unavailable, partial and conflicting resource cases retain
unresolved task grades; v2 safe-resolution process credit for an evidenced honest
handoff does not turn them into successful appointments. Failure reviews also
retain the older oracle completion component, so an expected handoff can have a
false completion component alongside true policy-level safe resolution.

Implementation defects needing correction: **none found in the pilot**. The new
code's initial lint/format/type issues were corrected before the first pilot
execution. No protocol, schema, arm or fixture change was made during the pilot.

## Successful trace

[Selected P3 replay](phase-7-pilot/v1/703ecbee-0b3d-48da-b98b-efeb24737c91.json):
P2 execution `b484a242-259a-4c7f-b956-e6b23b221959`, workflow
`48791462-1d10-4c41-a992-140daa8c031a`. The provider commits the original 3 PM
appointment and drops its response. Revision 2 requests November 23 at 4 PM
Asia/Karachi; reconciliation finds and reschedules the original effect. Independent
truth has one confirmed final appointment, version 1, and no duplicate or
prohibited original active effect. Revision-2 permit
`9e31f3c8-602b-4852-98f1-91bd1f054859` backs the recorded 500ms client exposure.

The [P8 repair replay](phase-7-pilot/v1/p8-paired-35dd180f-8cad-4feb-80e0-5d7158aafb03.json)
also records P2 workflow `f8a08046-7740-47a3-92aa-8c7fb936d4f2`, 500ms/8000 frames
of old decisive audio, a durable repair obligation and complete corrected
evidence-backed playback.

## Expected failure trace

[Partial-effect replay](phase-7-pilot/v1/75c0ff0b-22d0-4320-a5f5-f5ff03c66c58.json):
P2 execution `93177b1a-f2d6-4453-ac54-f3e94f31edbd`, workflow
`fed3dc6b-a67e-46bc-bee2-c28135e210d6`. The independent simulator records one HELD
partial effect. Eight reconciliation attempts end in durable OPEN handoff
`c5f34fa4-61be-44d7-b419-f6a230814ae3`; known PARTIAL remains separate from unknown
final intent resolution. A VIOLATED historical-effect receipt cannot authorize
speech: HTTP 409 denial trace `7b47f18a-3bb8-421e-9ff6-2739a35f5a03`. There is no
second provider write, claim permit or outcome audio. Correction success and
useful outcome coverage remain false.

## Clean-environment exit gate

[Reproduction gate](phase-7-pilot/v1/phase7-clean-61dae8506afb/reproduction-gate.json)
passed, hash
`31c3fb7d295e422863f89114fbb0f895968a11727de738ad2547ad91205d9981`.
The verified frozen source was extracted and mounted read-only in a separate
Docker project/network with two fresh PostgreSQL volumes and no host ports.
Evaluation runs, workflows and operations were all zero before execution. All
six arms reran the selected P3 case; the independent oracle reproduced every
binary metric row exactly. New IDs/timing observations differ as expected.

[Fresh replay](phase-7-pilot/v1/phase7-clean-61dae8506afb/evidence/reproduced.json)
hash `3d69a27a372199e16b2ced6f5f8c784c7e61a3466c3f2861b15e83fc0ee04813`.
The temporary project's containers/volumes were removed after evidence export;
the main application's services and volumes remain intact.

## Commands and final verification

- `python -m research.pilot.runner --output artifacts/phase-7-pilot/v1 --ni-margin 0.05`: 267 verified pilot executions.
- `python -m research.pilot.freeze artifacts/phase-7-pilot/v1/pilot-c1cf3fdf4dda.json`: verified protocol/source archive and PostgreSQL freeze record.
- `python -m research.pilot.reproduce artifacts/phase-7-pilot/v1/freeze-90901263019a.json`: six fresh executions and exact metric-row reproduction.
- `ruff format --check .`, `ruff check .`, `mypy`: PASS; 139 formatted Python files / 105 checked source files.
- `pytest -q tests/unit tests/contract`: 57 passed before adding the three final frozen-evidence regression tests.
- `pytest -q tests/integration/test_phase7_pilot.py`: 1 passed, with real PostgreSQL failure and tamper checks.
- Full `pytest -q --junitxml=artifacts/phase-7-final-tests.xml`: **158 passed, zero failures, zero skips**, in 918.49 seconds (15m18s). Four existing FastAPI/Starlette dependency deprecation warnings remain. [Final XML](phase-7-final-tests.xml).
- Final frozen-evidence tests reject omitted planned versions, rehashed changed counts, source drift and rehashed budget edits; they passed in the full suite.
- Web `pnpm format:check`, `pnpm lint`, `pnpm typecheck`, `pnpm test`: PASS, six tests in three files; existing Vite configuration warning remains.
- Disposable PostgreSQL upgrade head → downgrade base → upgrade head: PASS, 38 tables at `0011_phase6_b3_audio`. See [migration gate](phase-7-migration-gate.json).
- Standalone clean Compose configuration: PASS. Phase 7's applicable end-to-end test is the clean isolated CLI/provider/controller replay; no UI route or public API shape changed.
- No paid API keys are required.

## Known limitations and deferred work

Five synthetic acoustic versions failed recognition safely in this pilot; their
actual outputs and unsuccessful task outcomes are retained. Client exposure is
not physical hearing. Synthetic templates are correlated; no population effect
or sample power guarantee follows from the pilot. There was no primary-endpoint
separation between B3/P1/P2, and the small clean subset cannot establish NI.
The 500-instance evaluation and statistical analyses, native-audio comparisons
and product extensions are deferred to their respective phases. Before starting
Phase 8, materialize its 500 distinct external inputs and execution slots against
the frozen template; no main runs were executed here. Source is uncommitted, so
content inventories/archive hashes identify it. Reports/docs are descriptive;
the executable freeze's source/contract/fixture inventory is the drift authority.

## Ambiguities

The 5-percentage-point NI margin is a documented Phase 7 design choice; UUID and
cancellation-speech exceptions remain as previously approved/documented. No new
prose-versus-executable-contract conflict was identified.

> **Completed study - updated 27 October 2026:** all **500 inputs across B3/P1/P2 (1,500 original executions)** and the computational analyses are complete. Each arm achieved **455/500 correct final business states**; the co-primary comparisons do not demonstrate an incremental benefit. A narrower, qualified difference appears in explicit corrective communication. This is a synthetic protocol study, not a real-speech or human-understanding benchmark.
>
> Start with [final findings and limitations](artifacts/phase-8-final-analysis/v1/FINAL_REPORT.md), [all 1,500 original rows](artifacts/phase-8-final-analysis/v1/analysis/original-results.csv), [the research manuscript](output/pdf/commit-aware-agents-full-v1/commit-aware-agents-full.pdf), and [publication scope](PUBLICATION.md). The paper is a review draft, not an accepted publication. Older sections below are preserved historical documentation; their "not started" or "paused" statements are superseded by the final report. This public copy is not the complete private frozen deployment/recovery package.

# Commit-Aware Voice Agent

## Phase 7 pilot and freeze

Phase 7 runs 40 fresh synthetic scenario instances through the research harness.
Five additional acoustic versions stay clustered under one instance: 45 versions
and 267 executions are separate counts. Pilot outcomes are descriptive protocol
debugging; the 500-case main evaluation has not started. See
`docs/09_PHASE7_PROTOCOL.md` and `artifacts/phase-7-report.md` for the frozen
endpoints, utility condition, arm limits, budgets, exclusions and evidence.

Offline pilot and freeze checks:

```powershell
.\.venv\Scripts\python.exe -m research.pilot.runner --verify artifacts/phase-7-pilot/v1/pilot-c1cf3fdf4dda.json
.\.venv\Scripts\python.exe -m research.pilot.freeze artifacts/phase-7-pilot/v1/freeze-90901263019a.json --verify
```

To reproduce the selected P3 fixture with two new empty PostgreSQL databases and
the frozen source archive:

```powershell
.\.venv\Scripts\python.exe -m research.pilot.reproduce artifacts/phase-7-pilot/v1/freeze-90901263019a.json
```

Docker must be running and the frozen Python/PostgreSQL images available. The
command creates an isolated Compose project with no host ports, preserves raw
replay evidence, and removes only its own temporary containers and volumes. The
current application data remains intact. No paid API keys are needed. Frozen
source drift requires a new protocol version before campaign work.

## Phase 0 repository and local boot

The extracted implementation pack remains the behavioral specification. Phase 0 added the reproducible monorepo scaffold; Phase 1 added deterministic local PostgreSQL appointment transactions; Phase 2 added isolated external-provider recovery; Phase 3 adds revision-bound verification and deterministic claim permits. No audio playback or screen workflow is active yet. Read `AGENTS.md` and its ordered sources before implementation changes. Source conflicts and the proposed topology are recorded in `docs/06_SOURCE_CONFLICT_REPORT.md` and `docs/07_PROPOSED_REPOSITORY_TREE.md`.

Prerequisite: Docker Desktop or Docker Engine with Compose. From a clean clone, run:

```sh
docker compose up --build -d --wait
```

Local health URLs: web `http://127.0.0.1:3000/api/health`, API `http://127.0.0.1:8000/health/ready`, voice worker `http://127.0.0.1:8001/health/live`, durable worker `http://127.0.0.1:8002/health/ready`, provider simulator `http://127.0.0.1:8010/health/live`. If host port 5432 is occupied, set `POSTGRES_HOST_PORT=15432` for Compose and set the host test `DATABASE_SYNC_URL` to use port 15432; container connections remain on `postgres:5432`. `migrate` applies the Phase 0 baseline and Phase 1 schema/command migrations after PostgreSQL becomes healthy. The supplied `database/001_initial_schema.sql` remains untouched and hash-pinned by migration `0001`. Explicit migration check: `docker compose run --rm migrate alembic upgrade head`. Stop with `docker compose down`.

Optional profiles: `docker compose --profile redis up --build -d --wait` and `docker compose --profile observability up --build -d --wait`. Redis is disposable and is not a correctness authority. Copy `.env.example` to `.env` only to override local defaults or add future provider credentials; `.env` is ignored by Git. The shipped local password is for loopback development only.

## Phase 2 external operation replay

Phase 2 adds an isolated simulator PostgreSQL database on loopback port 5433, an append-only provider commit log, configurable capabilities and faults, and a PostgreSQL-leased durable worker. The worker records a dispatch attempt before calling the provider. Ambiguous outcomes remain `UNKNOWN` until status or resource evidence resolves them; automatic retries require authoritative absence, provider idempotency, and an available retry budget. If those conditions cannot be established, the workflow gets a durable handoff. No voice or decisive outcome speech is implemented in this phase.

After `docker compose up --build -d --wait`, replay the 3 PM hidden commit and 4 PM correction with one command:

```sh
uv run python -m research.replay.phase2_decisive
```

This prints the normalized workflow timeline and the independent simulator truth log. Set `PHASE2_REPLAY_OUTPUT=artifacts/phase-2-decisive-replay.json` to save it. Run `uv run pytest -q` for the integration gate; the simulator tests require both PostgreSQL services and the simulator HTTP service. The deterministic worker step endpoint is enabled only with `EXPERIMENT_MODE=true` and is used by the replay and fault tests. The UUIDv4 SQL defaults remain the documented exception to the sortable UUID instruction, per the Phase 1 decision.

The repo has `apps/web` (Next.js App Router, strict TypeScript, Tailwind, TanStack Query, Zod, Vitest, Playwright), `apps/api_controller`, `apps/voice_worker`, and `apps/durable_worker` (Python 3.12, FastAPI health where applicable, Pydantic v2, SQLAlchemy 2, Alembic, asyncpg, pytest). `packages/domain` and `packages/protocol` are framework-free boundaries. `research/` contains simulator, oracle, replay, DSL, analysis, and versioned fixture locations. `database/migrations/` holds Alembic revisions. `tests/` separates unit, integration, contract, E2E, and experiments. `deployment/` contains profile configuration, `docs/adr/` records architecture decisions, and `.github/workflows/ci.yml` runs the phase gates.

Host checks after installing locked dependencies: `uv sync --locked`, `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy`, `uv run pytest -q tests/unit tests/contract`, then with PostgreSQL migrated `uv run pytest -q tests/integration`; `pnpm install --frozen-lockfile`, `pnpm format:check`, `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`, and `pnpm --dir apps/web test:e2e`. Dependencies are pinned in `uv.lock` and `pnpm-lock.yaml`; do not upgrade during an experiment campaign.

## Phase 3 evidence and text publication

`POST /internal/phase3/verifications` records independent evidence and a `SATISFIED`, `VIOLATED`, or `UNKNOWN` receipt tied to an intent revision and observed resource version. A `SATISFIED` receipt can authorize a typed claim permit. The permit is queued and rechecked against fresh evidence before a single deterministic outcome text is published. Accepting a newer revision invalidates older receipts and unplayed permits in PostgreSQL. Progress and uncertainty use fixed language that makes no decisive claim. Phase 4 adds the voice scheduler, playback measurements, and repair.

With Compose healthy, run `uv run python -m research.replay.phase3_decisive` to reproduce the hidden 3 PM commit followed by the authorized 4 PM revision-2 text. Set `PHASE3_REPLAY_OUTPUT=artifacts/phase-3-decisive-replay.json` to save the trace. The integration tests require both PostgreSQL databases and the provider simulator.

## LLM implementation master guide

This package is the executable specification for building the FYP application described in the research and backend architecture proposal. It is written for an implementation LLM and for the human supervisor reviewing its work.

The application is a research instrument for one precise failure class:

> A user accepts an instruction, an external operation may commit without the controller learning its outcome, and the user then revises the instruction while stale confirmation audio may be generated, queued, or partly played.

The system must reconcile the earlier effect without duplicating it, establish whether the latest desired state holds, and prevent or repair spoken claims backed by stale evidence.

## 1. Non-negotiable research contract

The implementation must preserve these invariants.

1. **Accepted intent is durable.** A model transcript or tool proposal is not authoritative until an intent revision is accepted inside a PostgreSQL transaction.
2. **Stable logical operation identity.** Retries of one logical request reuse the same operation ID and idempotency key. A materially changed intent creates a linked new operation.
3. **Unknown is not failure.** A timeout after a request may have been sent becomes `UNKNOWN`, never automatic `FAILED`.
4. **Reconcile before retry.** After an ambiguous send, inspect provider status, resource state, or postconditions before retrying.
5. **Evidence is revision-bound.** A receipt must name the workflow, operation, intent revision, claim predicates, observed resource version, source, and validity window.
6. **Speech requires a claim permit.** A model or tool result cannot directly authorize a consequential success, failure, cancellation, or compensation statement.
7. **Playback is measured separately from generation.** Generated, queued, published, started, partly played, completed, and interrupted are distinct facts.
8. **Stale decisive audio creates durable repair.** If a stale success or cancellation claim was partly played, a repair obligation survives browser disconnects and worker restarts until corrected or escalated.
9. **PostgreSQL owns correctness.** Redis is optional and disposable. Losing every Redis key must not duplicate an effect, change the accepted revision, validate a claim, or erase a recovery obligation.
10. **The oracle is independent.** Research grading uses the deterministic provider's append-only commit log and externally scripted final intent, not the controller's receipt or belief.
11. **The model proposes; deterministic code authorizes.** No LLM may construct SQL, choose an actor, choose an arbitrary URL, issue a receipt, declare a provider result, or mutate business state directly.
12. **Closing media does not close durable work.** A call may end while reconciliation continues.

If an implementation choice conflicts with one of these rules, the rule wins.

## 2. Product scope

### Included

- Browser-based, full-duplex voice session with a synthetic resident.
- Create a maintenance ticket and appointment.
- Read, reschedule, and cancel appointments.
- Accept a user's mid-call correction at controlled timing boundaries.
- Verify business state independently of the tool response.
- Reconcile ambiguous provider outcomes.
- Issue receipt-gated confirmation speech.
- Record playback exposure and repair stale claims.
- Continue durable recovery after a disconnect.
- Human handoff when safe automatic resolution is impossible.
- Research dashboard, event trace, replay, fault injection, and evaluation.

### Explicitly excluded

- RBAC or RABAC research, permission administration, and role hierarchy.
- Real medical data, allergies, diagnoses, or emergency dispatch.
- Automated notification of police, ambulance, fire, or public authorities.
- General multi-industry SaaS scope.
- Arbitrary model-selected tools or unrestricted external URLs.
- Exactly-once claims across an opaque external provider.
- Treating compensation as if history were erased.
- Assuming a playback acknowledgement means the person heard or understood a statement.

The demo still uses a server-issued actor identity and resource association. This is an implementation precondition, not an authorization contribution.

## 3. Canonical architecture

Use a modular monolith in one repository with independently runnable processes.

```mermaid
flowchart TB
    Browser[Next.js browser client] --> LiveKit[LiveKit media transport]
    LiveKit --> Voice[Voice worker]
    Browser --> API[FastAPI controller]
    Voice --> API
    API --> DB[(PostgreSQL durable truth)]
    API -. hints only .-> Redis[(Redis ephemeral)]
    Worker[Durable worker] --> DB
    Worker --> Provider[Provider adapter or simulator]
    Worker --> Verify[Verifier]
    Speech[Speech scheduler] --> LiveKit
    Worker --> Speech
    Lab[Experiment runner and oracle] --> Provider
    Lab --> DB
```

### Runtime processes

| Process | Owns | Must not do |
|---|---|---|
| `web` | UI, LiveKit client, frame acknowledgements, dashboards | Write PostgreSQL or infer durable success |
| `api-controller` | Command validation, intent acceptance, local transactions, queries, SSE/WebSocket timelines | Hold database locks during network or audio calls |
| `voice-worker` | STT/native-audio adapter, turn events, candidate intent, safe speech playback | Call business providers directly or announce free-form outcomes |
| `durable-worker` | Queue leasing, dispatch, verification, reconciliation, compensation, outbox | Blindly retry an ambiguous external write |
| `experiment-runner` | Fixtures, named barriers, faults, independent oracle, replay bundles | Reuse production verifier conclusions as ground truth |

### Technology baseline

- Frontend: Next.js App Router, React, TypeScript, Tailwind CSS, TanStack Query, Zod, Playwright.
- Media: LiveKit client/server SDK.
- Backend: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, async PostgreSQL driver.
- Durable store: PostgreSQL 16 or later.
- Ephemeral store: Redis 7 or later, optional.
- Worker queue: PostgreSQL rows leased with `FOR UPDATE SKIP LOCKED`.
- Telemetry: OpenTelemetry, Prometheus metrics, Grafana dashboard, structured JSON logs.
- Testing: pytest, pytest-asyncio, Testcontainers, Hypothesis where useful, Vitest, Playwright.
- Local environment: Docker Compose.

Pin verified versions in lockfiles at project initialization. Do not silently upgrade dependencies during an experiment campaign.

## 4. Repository topology

```text
apps/
  web/
  api_controller/
  voice_worker/
  durable_worker/
packages/
  domain/
  protocol/
  event_schemas/
  provider_adapters/
  speech_policy/
  observability/
research/
  scenario_dsl/
  fixtures/
  fault_schedules/
  provider_simulator/
  oracle/
  replay/
  analysis/
  tla_model/
database/
  migrations/
  seeds/
tests/
  unit/
  integration/
  contract/
  e2e/
  experiments/
docs/
deployment/
```

Backend modules must depend inward on domain and protocol packages. Provider, model, LiveKit, Redis, and web frameworks are adapters. The domain layer imports none of them.

## 5. Canonical domain model

### Aggregate roots

- `Actor`: synthetic caller identity bound by the server.
- `Resident`: synthetic maintenance customer record.
- `CallSession`: media session and conversation lifecycle.
- `Workflow`: unit of user intent and durable action history.
- `IntentRevision`: immutable accepted interpretation of a user request.
- `Operation`: one logical mutation or verification action.
- `Appointment`: controlled business resource.
- `MaintenanceTicket`: issue being scheduled.
- `VerificationReceipt`: three-valued evidence about a claim.
- `ClaimPermit`: durable authorization to publish one semantic claim.
- `AudioSegment`: generated and scheduled speech unit.
- `RepairObligation`: durable requirement to correct stale decisive audio.
- `Handoff`: unresolved work assigned for human review.
- `EvaluationRun`: frozen experiment configuration and results.

### Orthogonal operation dimensions

Do not compress the operation into one attractive but incorrect linear A3 state.

| Dimension | Values |
|---|---|
| Processing phase | `DRAFT`, `READY`, `DISPATCH_RECORDED`, `RESPONSE_RECEIVED`, `VERIFYING`, `RECONCILING`, `COMPENSATING`, `TERMINAL` |
| Effect knowledge | `NOT_ATTEMPTED`, `ABSENT`, `PRESENT`, `PARTIAL`, `UNKNOWN`, `COMPENSATED` |
| Applicability | `CURRENT`, `SUPERSEDED`, `REUSABLE`, `INCOMPATIBLE` |
| Speech eligibility | `BLOCKED`, `PROGRESS_ONLY`, `CLAIM_PERMITTED`, `REPAIR_REQUIRED` |

The UI may show the familiar Plan/Observe/Execute/Verify/Recover/Complete labels as explanatory stages, but persistence and tests use the orthogonal fields above.

## 6. Required end-to-end trace

No work beyond the deterministic vertical slice is accepted until this trace passes.

1. Create synthetic resident, maintenance ticket, and empty workflow.
2. Accept revision 1 requesting a 3 PM appointment.
3. Create operation A with stable operation ID, request hash, and idempotency key.
4. Record `DISPATCH_RECORDED` before network send.
5. Provider simulator commits the 3 PM appointment to its append-only truth log.
6. Fault barrier drops the response after commit.
7. Worker records effect knowledge `UNKNOWN`; it does not call the write again.
8. User correction proposes 4 PM.
9. Accept revision 2 while locking the workflow row.
10. Mark operation A `SUPERSEDED`, invalidate unpublished revision-1 claim permits, and schedule reconciliation.
11. Provider status/postcondition lookup finds the 3 PM effect.
12. Domain policy performs atomic reschedule where supported; otherwise it executes an explicitly linked compensation plus new operation.
13. Independent verifier checks the desired 4 PM state and forbidden 3 PM state.
14. A revision-2 `SATISFIED` receipt is persisted with its evidence items and observed version.
15. Speech policy issues one revision-2 claim permit.
16. The scheduler renders the deterministic confirmation template.
17. The client records queued, started, and completed playback events.
18. The independent oracle grades final intent, provider commit log, forbidden effects, speech claims, and replay trace.

Acceptance requires one 4 PM appointment, no prohibited 3 PM appointment, no duplicate provider effect, no revision-1 confirmation after revision 2, and a replayable trace.

## 7. Development order

The implementation LLM must complete one phase, run all gates, and produce an evidence report before advancing.

| Phase | Deliverable | Exit gate |
|---|---|---|
| 0 | Repository, ADRs, locked dependencies, Compose, CI | Empty services boot; lint and tests run |
| 1 | PostgreSQL domain, migrations, local appointment transaction | Revision and local commit race tests pass |
| 2 | Deterministic provider simulator, operation identity, unknown outcome | Lost-response trace resumes without duplicate |
| 3 | Verification receipts, claim permits, deterministic speech policy | No unsupported outcome sentence can be released |
| 4 | LiveKit cascade voice path and playback telemetry | Queued/started/played/interrupted are observable |
| 5 | Web screens for call, business records, traces, handoff | Every screen uses real API data and handles empty/error states |
| 6 | B0-B3 baselines, P1/P2 protocols, fault scheduler, oracle | One command replays paired scenarios |
| 7 | 30-50 case pilot and schema freeze | Outcomes, exclusions, and metrics frozen |
| 8 | 500 paired-case evaluation | All planned runs accounted for, including timeouts |
| 9 | Optional native-audio and second-domain transfer study | Added only after core results are stable |

See the remaining files in this package for exact screen contracts, APIs, database rules, events, tests, and per-phase prompts.

## 8. Definition of done

The application is not complete because it looks like the supplied mockups. It is complete when:

- Every mutation is traceable to an accepted revision and stable actor/resource binding.
- Every ambiguous external outcome remains unknown until reconciled or escalated.
- Every decisive spoken claim maps to an applicable receipt and claim permit.
- A stale partly played claim creates and later satisfies a durable repair obligation.
- Redis deletion cannot change correctness.
- A process can crash at each named barrier and safely resume.
- The independent oracle can disagree with the controller.
- The exact decisive trace can be replayed from a frozen manifest.
- B3, P1, and P2 run through the same interfaces, fixtures, budgets, and faults.
- UI screenshots, API schemas, migrations, trace files, raw outcomes, and analysis code are versioned together.
# Phase 1 local transaction slice

Phase 1 adds the complete PostgreSQL source schema plus a separate command receipt
migration. With Docker Desktop running, `docker compose up --build -d --wait`
applies both migrations. The deterministic HTTP sequence is:

1. `POST /internal/phase1/fixtures` with a `command_id` to create a synthetic call,
   workflow, ticket and two finalized utterances.
2. `POST /v1/workflows/{workflow_id}/revisions` with the supplied first utterance,
   `expected_revision: 0`, and the 3 PM desired appointment.
3. `POST /v1/operations/appointments` with revision 1, resource version 0 and
   a stable idempotency key; then `POST /v1/operations/{operation_id}/commit-local`.
4. Accept revision 2 with the second utterance and the returned appointment ID
   at 4 PM. Prepare with resource version 0 and a new idempotency key; commit it.
5. `GET /v1/workflows/{workflow_id}/history` shows both revisions, both effects,
   the superseded first operation, and one active appointment at 4 PM.

No voice, provider, Redis or claim permit runs in this slice. A committed local
effect remains speech-blocked until later verification and claim authorization.

## Phase 4 voice and repair replay

The strict research path is a provider-neutral cascade: WAV input goes to a
transcription adapter, a typed intent adapter, server revision acceptance,
verification, a deterministic speech scheduler, and LiveKit. The checked-in
`p8_correction.wav` is a synthetic prerecorded correction. The scripted STT and
intent adapters let the P8 replay test the protocol deterministically; a real
model implementation can use the same interfaces without changing claim or
repair authority. Native-audio comparison remains a later research adapter.

On this Windows machine, another process already owns host port 5432. From
PowerShell, keep the main PostgreSQL container on host port 15432. The local
ignored `.env` also sets this port, so starting Compose from Docker Desktop
uses the same mapping:

```powershell
$env:POSTGRES_HOST_PORT='15432'
docker compose --profile media up -d --build --wait
$env:DATABASE_SYNC_URL='postgresql://voice_agent:voice_agent_local@127.0.0.1:15432/voice_agent'
$env:SIMULATOR_DATABASE_URL='postgresql://simulator:simulator_local@127.0.0.1:5433/simulator_truth'
$env:SIMULATOR_BASE_URL='http://127.0.0.1:8010'
$env:PHASE4_LIVEKIT_SMOKE='true'
$env:PHASE4_REPLAY_OUTPUT='artifacts/phase-4-p8-replay.json'
.\.venv\Scripts\python.exe -m research.replay.phase4_p8
```

The playback client sends stable event IDs and acknowledged millisecond,
frame, and word progress. A stopped stale decisive segment opens one durable
repair obligation for its exposed span. A corrected claim closes it only after
full playback acknowledgement. Phase 5 connects the client reporter to the
live call screen; Phase 4 separately exercises the full P8 path with a
scripted client. The word timeline is an even-duration proxy generated from
the deterministic text, so client word counts are exposure estimates rather
than phonetic alignment. LiveKit carries media and segment metadata; it does
not authorize claims. PostgreSQL remains the repair and playback authority.

## Phase 5 browser workspace

Phase 5 adds the Indigo Intelligence style shell and 17 caller, operations,
and research routes in `apps/web/app`. Pages read PostgreSQL-backed controller
projections through the Next.js `/api/backend/v1/*` proxy. Call creation, end,
scoped human notes, handoff updates, and evaluation drafts are durable commands.
The UI shows a verified appointment only with a current applicable receipt for
the accepted revision and resource version. The live page acknowledges playback
progress to the Phase 4 controller.

A new call asks the local voice worker to join its LiveKit room. The media-token
API reports `voice_agent_status=READY` only after that join succeeds. On the live
page, click **Start microphone** and allow Chrome microphone access. Speak a
maintenance appointment date and time; a later time-only correction uses the
current appointment date. Vosk transcribes, a local Qwen model proposes typed
intent, and server verification and claim permits control eSpeak outcome audio.
The worker records a clarification or failure event instead of speaking an
unsupported outcome. No paid API key is required for this local profile.

Put the extracted `vosk-model-small-en-us-0.15` directory and
`qwen2.5-0.5b-instruct-q4_k_m.gguf` in the ignored `models/` directory. They
are already present in this local checkout. Start with
`docker compose --profile media --profile local-voice --profile redis up -d --build --wait`
and open `http://localhost:3000`. On this machine the ignored `.env` maps the
main PostgreSQL port to 15432. Migration `0006` seeds a synthetic resident;
`0007` adds a unique command ID for evaluation drafts. Generate API types with
`pnpm --dir apps/web generate:api`.

The local LiveKit container advertises `127.0.0.1` for WebRTC, matching its
loopback-only Docker port mappings on this Windows machine. The browser and
containerized voice worker both passed connection/publish checks with this
setting. A remote-device deployment needs a different reachable media address.

The browser checks use the real controller, simulator, worker, PostgreSQL, and
LiveKit services. With system Chrome installed on Windows, run:

```powershell
$env:PLAYWRIGHT_BASE_URL='http://localhost:3000'
$env:PLAYWRIGHT_API_URL='http://127.0.0.1:8000'
$env:PLAYWRIGHT_CHANNEL='chrome'
$env:PLAYWRIGHT_REDIS_FAULT='1'
pnpm --dir apps/web test:e2e
```

The Redis test temporarily stops and restarts this Compose project's Redis
container. Leave `PLAYWRIGHT_REDIS_FAULT` unset where Docker control is not
available and report that skip. Run the reproducible spoken audio acceptance
with `.\.venv\Scripts\python.exe acceptance\phase5_live_voice.py`; it sends two
recorded utterances through LiveKit and requires a verified 3 PM booking, a
verified 4 PM correction, and two published permit-bound speech segments.
The evidence is saved at `artifacts/phase-5-live-voice.json`.

## Phase 6 paired research replay

Migrations `0008_phase6_research` and `0009_phase6_baselines` store named barrier
transitions, scripted client playback acknowledgements, the simulator scenario
binding, and hashed raw/normalized observations for the B0-B2 provider drivers. With
the Compose stack running, set `DATABASE_SYNC_URL` to the main PostgreSQL
loopback port (15432 on this machine) and `SIMULATOR_DATABASE_URL` to the
independent simulator PostgreSQL port (5433). Then run:

```powershell
.\.venv\Scripts\python.exe -m research.runner.paired
.\.venv\Scripts\python.exe -m research.runner.paired --all-arms
.\.venv\Scripts\python.exe -m research.runner.paired --phase P0
.\.venv\Scripts\python.exe -m research.runner.paired --phase P5
.\.venv\Scripts\python.exe -m research.runner.paired --phase P3 --compensation-case
.\.venv\Scripts\python.exe -m research.runner.paired --phase P3 --delayed-visibility-case
.\.venv\Scripts\python.exe -m research.runner.paired --phase P2 --provider-delay-case
.\.venv\Scripts\python.exe -m research.runner.paired --phase P2 --provider-refusal-case
.\.venv\Scripts\python.exe -m research.runner.paired --phase P3 --unavailable-evidence-case
.\.venv\Scripts\python.exe -m research.runner.paired --phase P5 --provider-conflict-case
.\.venv\Scripts\python.exe -m research.replay.verify_phase6 artifacts\phase-6-replays\<run-id>.json
.\.venv\Scripts\python.exe -m research.runner.clean_paired
.\.venv\Scripts\python.exe -m research.replay.verify_clean_paired artifacts\phase-6-replays\clean-paired-<run-id>.json
```

The default paired gate drives the same P3 hidden-commit response-loss schedule
under B3, P1, and P2. `--all-arms` adds the live B0-B2 drivers at P3. B0 stops
with UNKNOWN after the lost response because it lacks safe retry evidence; B1
uses status lookup and best-effort cancellation before recreating, while B2
uses status lookup and atomic reschedule. The frozen bundle includes provider
truth, hashed raw and normalized observations, the fault occurrence, independent
oracle result, and metric rows. The paired API now supports all six arms at P0-P5,
and the playout runners support all six at P6-P9. P0 records the correction before any accepted revision,
then creates only the final appointment at revision one. The unit suite covers
named wait/release control for P0-P9.
The audio hash is captured for reproducibility; this runner accepts the scripted
transcript directly, so acoustic performance is not measured in this run. The
Phase 6 closure is indexed in `artifacts/phase-6-completion/completion-0ce13a086fe0.json`;
see `artifacts/phase-6-report.md` for gate results and limitations.
The compensation case changes provider capability and requires CREATE, CANCEL,
CREATE in the independent simulator truth log. The clean-task runner accepts one
intent and measures correct state plus useful supported outcome speech under
B3/P1/P2. Its paired risk difference is descriptive; the non-inferiority margin
and decision remain unset until the research protocol is frozen.
The delayed-visibility case keeps the P3 hidden-commit fault and makes the
provider's first two status and resource reads inconclusive. The worker must
retain UNKNOWN, reconcile the original commit, and avoid a duplicate write.
The provider-delay case applies a named P2 `DELAY` rule before the first commit.
Its replay records the held barrier, empty simulator truth while held, correction
time, and release time; the offline verifier requires the first commit to follow
release. This is a controlled barrier delay, not a wall-clock latency sample.
The provider-refusal case injects an HTTP 503 before the first commit. The
worker records UNKNOWN for the response, then obtains authoritative ABSENT
status and resource evidence before creating the corrected booking. Its replay
verifier requires that ordering and exactly one final provider commit.
The unavailable-evidence case combines the P3 hidden commit with permanently
unavailable status and resource reads. The worker retains UNKNOWN and creates a
durable review handoff when its reconciliation budget is exhausted. The replay
requires one original write, no follow-up operation, no claim or audio segment,
and a rejected claim request backed by an UNKNOWN receipt. The independent oracle
records correction failure and censored outcome latency; handoff does not count
as a successful booking.
The provider-conflict case accepts a P5 correction, then holds the second
provider request before commit. A concurrent provider writer increments the
appointment version, so the stale reschedule returns HTTP 409. Authoritative
reconciliation proves that reschedule absent; a durable handoff preserves the
newer resource, and a violated receipt cannot authorize decisive speech. The
replay records separate correction and fault barriers and checks both.

For the separate **P2-only P8 live witness**, run:

```powershell
.\.venv\Scripts\python.exe -m research.replay.phase6_p8_witness
.\.venv\Scripts\python.exe -m research.replay.phase6_p8_witness --verify 'artifacts\phase-6-replays\p8-p2-witness-<scenario-id>.json'
```

The first command saves a frozen bundle under `artifacts/phase-6-replays/`;
the second verifies that saved bundle offline.
This witness captures the exact client playback requests, grades the partial
stale span and completed correction against simulator truth, and ignores the
controller's repair-state label when grading. It is not a B3/P1/P2 paired
comparison.

The P8 **B3/P1/P2 paired ablation** now uses explicit research workflow profiles
and a durable named barrier tied to the client's 500 ms / 8000-frame progress
event. B3 records deterministic scripted outcome audio through an experiment-only,
PostgreSQL-guarded path with no claim permit; its marked WAV cannot be downloaded
through the normal route or sent over LiveKit. P1 retains revision-bound permits
but omits durable played-span repair; P2 creates and completes it. Normal
workflows have a null research profile and retain full repair behavior. Run and verify:

```powershell
.\.venv\Scripts\python.exe -m research.runner.p8_paired
.\.venv\Scripts\python.exe -m research.replay.verify_p8_paired 'artifacts\phase-6-replays\p8-paired-<run-id>.json'
```

Set `DATABASE_SYNC_URL` to the main PostgreSQL host port 15432 and
`SIMULATOR_DATABASE_URL` to 5433 before the paired command. When running
Alembic from the host, set `DATABASE_ADMIN_URL` explicitly to port 15432;
the repository's fallback Alembic URL uses port 5432, which is a different
local database on this machine. Migration `0011_phase6_b3_audio` is required
for B3's guarded no-permit research speech.

The **P6, P7, and P9 paired audio boundaries** use the same B3/P1/P2 arms and
prerecorded correction audio. P7 reaches the published segment before any
client playback acknowledgement; correction cancels that stale segment. P9
waits for the client's full stale-audio completion acknowledgement before the
correction; P2 then completes a durable repair. P6 reaches a generated segment
before publication; accepting the correction cancels it. Run and verify each
boundary:

```powershell
.\.venv\Scripts\python.exe -m research.runner.playout_paired P6
.\.venv\Scripts\python.exe -m research.runner.playout_paired P7
.\.venv\Scripts\python.exe -m research.runner.playout_paired P9
.\.venv\Scripts\python.exe -m research.replay.verify_playout_paired 'artifacts\phase-6-replays\p6-paired-<run-id>.json'
.\.venv\Scripts\python.exe -m research.replay.verify_playout_paired 'artifacts\phase-6-replays\p7-paired-<run-id>.json'
.\.venv\Scripts\python.exe -m research.replay.verify_playout_paired 'artifacts\phase-6-replays\p9-paired-<run-id>.json'
```

Each bundle has one independent scenario and three arm executions. The
verifier checks the durable barrier, exact client exposure, simulator truth,
oracle grade, and metric rows. These scripted cases do not measure acoustic
recognition quality or estimate a treatment effect.

### Phase 6 complete harness and offline closure

The closure entry point covers all six profiles, every P0–P9 boundary, the
constrained secondary array, partial/stale/unavailable provider evidence,
cache-loss recovery, revision semantics, multiple resources and actual local
acoustic fixtures. No paid API key is required. The local voice models described
above must be present for a new acoustic run. Use the configured PostgreSQL host
URLs described above.

```powershell
docker compose --profile redis --profile media --profile local-voice up -d --wait
.\.venv\Scripts\python.exe -m research.runner.completion
.\.venv\Scripts\python.exe -m research.runner.completion --verify artifacts\phase-6-completion\completion-0ce13a086fe0.json
```

Offline verification needs neither Docker nor model inference: the child
bundles contain raw evidence and model outputs. The selected closure covers
43 paired fixtures and one auxiliary repair witness, totaling 256 verified
executions. Existing child checkpoints are reverified before reuse; failed
attempts remain in the ledger. Each child retains its source/image identity.

See [coverage and constraints](docs/08_PHASE6_COVERAGE_MATRIX.md) and
[Phase 6 report](artifacts/phase-6-report.md). Five synthetic acoustic conditions
currently fail recognition safely; recorded clean speech succeeds. Protocol
playout uses synthetic TTS and client acknowledgements, which do not establish
physical hearing. The Phase 7 pilot, global protocol freeze and inferential
non-inferiority evaluation have not started.

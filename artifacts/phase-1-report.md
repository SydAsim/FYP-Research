# Phase 1 report — deterministic local appointment transactions

Status: **Phase 1 exit gate passed locally on 2026-09-25 against Docker Compose PostgreSQL 16.9.** The functional gate also passed earlier against PostgreSQL 18 in WSL while Docker Desktop was unavailable. No Phase 2 work was started.

## Scope implemented

- Installed the authoritative source SQL as a hash-pinned Alembic migration, preserving its enum types, keys, checks, foreign keys, partial indexes, and active-appointment GiST exclusion constraint.
- Added a separate durable `command_receipts` table for command ID idempotency and stable replay responses.
- Added pure domain types for workflows, immutable revisions, four operation dimensions, tickets, appointments, verification result, and local transition rules.
- Added a synthetic call/workflow fixture, revision acceptance, local appointment preparation and commit, correction handling, and an auditable workflow history endpoint.
- Kept resource ownership and resource keys server-derived. The local commit locks workflow → operation → ticket/appointment, checks accepted revision and expected resource version, updates the appointment and effect ledger, appends a workflow event/outbox row, and commits as one PostgreSQL transaction.
- Kept consequential speech blocked. No model, provider, Redis, LiveKit, or TTS is called.

## Files changed

Created `database/migrations/versions/0001_phase1_source_schema.py`, `0002_phase1_command_receipts.py`, `packages/domain/phase1.py`, `apps/api_controller/phase1_models.py`, `phase1_service.py`, `phase1_routes.py`, `tests/unit/test_phase1_domain.py`, and `tests/integration/test_phase1_postgres.py`. Updated `apps/api_controller/main.py`, `compose.yaml`, `contracts/openapi.yaml`, `pyproject.toml`, `.github/workflows/ci.yml`, `README.md`, and `docs/06_SOURCE_CONFLICT_REPORT.md`.

The original `database/001_initial_schema.sql` and Phase 0 migration remain unchanged.

## Migrations added

1. `0001_phase1_schema` executes the supplied SQL within Alembic's transaction only if its SHA-256 is `4884f8e22e26a8f2c20b47e856da337bbaadacaf956a7a230fcbefe3126b35ed`.
2. `0002_phase1_commands` adds durable command ID, command type, workflow, request hash, and response JSON. It is separate because the supplied SQL does not define command receipt storage, while the Phase 1 API contract requires command ID idempotency.

A fresh database upgraded to head. A separate migration-test database upgraded, downgraded to base, and re-upgraded to `0002_phase1_commands (head)`. The first downgrade attempt found the source SQL's late `call_sessions_evaluation_run_fk`; the Phase 1 downgrade now removes that FK before dropping `evaluation_runs`.

## Invariants covered

| Invariant | Evidence |
|---|---|
| Concurrent revision acceptance yields one revision 2 | Named-barrier PostgreSQL integration test: one HTTP 201, one RFC 9457 HTTP 409 |
| Stale revision and stale resource version block mutation | HTTP 409 tests with problem type and trace ID |
| Obsolete revision 1 cannot commit after revision 2 | Prepared operation becomes terminal/ABSENT/SUPERSEDED; old commit returns 409 |
| Committed revision 1 remains in history when revision 2 arrives | Effect ledger retains creation and reschedule entries; old operation is PRESENT/SUPERSEDED |
| One final active appointment at 4 PM | HTTP vertical slice finds one CONFIRMED appointment with version 1 and two auditable effects |
| PostgreSQL prevents overlapping active appointments | Direct insert raises PostgreSQL `ExclusionViolation` |
| Command replay and operation idempotency are durable | Fixture, revision, preparation and commit replay tests; changed request under same key returns 409 |
| Local effect cannot authorize outcome speech | Committed operation remains `speech_eligibility=BLOCKED` |
| Workflow event and outbox are atomic | Seven ordered events in the vertical slice, each with a matching outbox row |

## Commands executed and results

| Command/check | Result |
|---|---|
| `alembic upgrade head --sql` | Passed; 19,348-byte offline SQL output |
| Fresh PostgreSQL `alembic upgrade head` | Passed |
| Separate PostgreSQL upgrade → downgrade base → upgrade head → current | Passed after correcting the Phase 1 downgrade FK order |
| `ruff format --check .`, `ruff check .`, `mypy` | Passed; 29 formatted files and 22 checked Python source files |
| `pytest -q tests/unit tests/contract` | 4 passed, 0 failed |
| `pytest -q tests/integration` | 8 passed, 0 failed against PostgreSQL 18 |
| Final `pytest -q` with PostgreSQL available | 12 passed, 0 failed; 2 third-party deprecation warnings |
| `docker compose up --build -d --wait` after Docker Desktop recovered | Passed; PostgreSQL, API, web, voice worker, durable worker and simulator healthy; one-shot migration exited 0 |
| `docker compose run --rm migrate alembic current` | `0002_phase1_commands (head)` against Compose PostgreSQL 16.9 |
| `pytest -q` against Compose PostgreSQL 16.9 | 12 passed, 0 failed; 2 third-party deprecation warnings |
| Live API `/health/ready` and `POST /internal/phase1/fixtures` | Passed through the rebuilt API container; database reachable and two utterances returned |
| OpenAPI YAML parse and Phase 1 route check using locked `js-yaml` | Passed |
| Event envelope JSON parse and required-field check | Passed |
| `docker compose config --quiet` | Passed; Compose syntax validated without the engine |
| `pnpm format:check`, `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` | Passed; 1 Vitest test |
| `pnpm --dir apps/web test:e2e` | Passed; 1 Playwright health test |

## Successful trace

`test_three_pm_to_four_pm_http_audit_history`: synthetic call/ticket/utterances → revision 1 accepts 3 PM → operation 1 prepared and locally commits one appointment at 3 PM, version 0 → revision 2 accepts 4 PM and marks operation 1 PRESENT/SUPERSEDED → operation 2 prepares against appointment version 0 and commits its reschedule → one final appointment at 4 PM, version 1. The audit endpoint returns both immutable revisions, both ledger effects, and workflow sequence 1–7 with seven matching outbox rows. Both operations remain speech-blocked.

## Expected failure trace

`test_revision_two_before_commit_blocks_obsolete_revision_one`: revision 1 accepts 3 PM and prepares an operation → revision 2 accepts 4 PM before local commit → old operation becomes TERMINAL/ABSENT/SUPERSEDED → attempted revision-1 commit returns RFC 9457 HTTP 409 `stale-intent-revision` → no appointment exists. The failure is durable and auditable, not treated as an ambiguous external outcome.

## Known limitations

- Docker Desktop initially crashed while initializing its inference runtime socket (`dockerInference`). It later recovered; the rebuilt Compose PostgreSQL 16.9 gate now passes. CI is configured to rerun the integration tests remotely but has not executed on a CI runner.
- The internal synthetic fixture endpoint is for the Phase 1 research slice; production identity and consent flows are deferred. The sourced `/v1/calls` and appointment list/reschedule routes that do not participate in the Phase 1 slice remain unimplemented.
- Two dependency deprecation warnings appear in pytest's FastAPI/Starlette test client. Tests pass.
- The web E2E remains a Phase 0 health check; Phase 1's end-to-end business path is exercised through HTTP `TestClient` with live PostgreSQL.

## Deferred work

External provider simulator, ambiguous outcomes and reconciliation (Phase 2); evidence/claim permits (Phase 3); voice/playback/repair (Phase 4); UI screens (Phase 5); research harness and evaluation (later phases).

## Contract ambiguity and decision

`AGENTS.md` requests sortable UUIDs, while the authoritative source SQL uses `gen_random_uuid()` defaults. The user explicitly chose to keep the SQL defaults and document a UUID exception on 2026-09-25. Phase 1 uses UUIDv4 for application-created IDs to match those defaults. Any future change to sortable UUIDs requires a separate migration and review. The authoritative SQL was not edited.

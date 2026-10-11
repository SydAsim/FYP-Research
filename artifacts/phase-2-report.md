# Phase 2 report — external simulator and ambiguous-outcome recovery

Status: **Phase 2 exit gate passed locally on 2026-09-25.** The one-command replay produced a normalized timeline and the isolated simulator truth log in `artifacts/phase-2-decisive-replay.json`. Phase 3 has not started.

## Scope implemented

- Added a separate simulator PostgreSQL database with configurable idempotency, status/resource lookup, immediate/delayed/stale/unavailable visibility, named barriers, and drop/delay/duplicate/reorder/5xx/crash/partial/concurrent-change faults. Provider commits are append-only and independent of controller state.
- Added external operation preparation, stable operation IDs and idempotency keys, durable dispatch attempts, raw and normalized provider events, PostgreSQL job leases, UNKNOWN outcomes, status/resource reconciliation, bounded safe retry, linked reschedule or cancel/create compensation, and durable human handoff.
- Added a deterministic worker step endpoint for research replay. Consequential speech remains blocked; no Phase 3 receipt, claim permit, voice, or UI outcome path was added.

## Files changed

Created `database/migrations/versions/0003_phase2_provider_recovery.py`, `research/provider_simulator/schema.sql`, `models.py`, and `store.py`, `apps/api_controller/phase2_models.py`, `phase2_service.py`, and `phase2_routes.py`, `apps/durable_worker/phase2.py`, `packages/provider_adapters/simulator.py`, `research/replay/phase2_decisive.py`, and the two Phase 2 integration test files. Updated `research/provider_simulator/main.py`, `apps/api_controller/main.py`, `apps/api_controller/phase1_service.py`, `apps/durable_worker/main.py`, `compose.yaml`, `.env.example`, `contracts/openapi.yaml`, `pyproject.toml`, `.github/workflows/ci.yml`, and `README.md`. This report and the replay JSON are artifacts. No earlier migration or frozen fixture was edited.

## Migration added

`0003_phase2_recovery` adds durable `provider_events` containing each raw exchange beside its normalized observation and an active-job uniqueness index. The provider simulator owns a separate schema and connection. The controller cannot use the simulator database as its correctness store. The full controller migration chain downgraded to base and re-upgraded to head successfully on Docker Compose PostgreSQL 16.9.

## Invariants covered

| Invariant | Evidence |
|---|---|
| Dispatch marker is durable before a provider write | Worker commits `DISPATCH_RECORDED` and a WRITE attempt before recording send and issuing HTTP; crash-boundary tests cover both commits. |
| Ambiguity is not failure | Dropped response records UNKNOWN; unavailable lookup exhausts eight reconciliation attempts and creates a handoff while the operation remains UNKNOWN. |
| Reconcile before retry | Recovery after a send marker checks provider status/resource state; retry requires authoritative absence, idempotency support, and a bounded write budget. |
| No duplicate provider effect | Eight crash-boundary cases each end with one simulator truth commit, including a crash after provider commit and before recording its response. |
| Correction retains historical effect | Hidden 3 PM commit is observed as PRESENT/SUPERSEDED; revision 2 gets a linked reschedule and one final 4 PM appointment. |
| Compensation preserves history | Provider without atomic reschedule produces CREATE, CANCEL, CREATE truth entries linked through operation parent/supersedes IDs. |
| Raw and normalized provider observations survive | `provider_events`, attempts, workflow events and outbox rows are PostgreSQL records; operation detail exposes both event forms. |
| PostgreSQL owns correctness | Redis is absent from the default Compose profile and is not read by the Phase 2 worker, controller, or simulator. |

## Commands executed and results

| Command/check | Result |
|---|---|
| `docker compose up -d --build --wait migrate api-controller durable-worker provider-simulator` | All four services and both PostgreSQL databases healthy. |
| `python -m ruff format --check .`, `ruff check .`, `mypy` | Passed; 41 Python files formatted and 31 source files type checked. |
| `python -m pytest -q` | 31 passed, 0 failed; two third-party TestClient deprecation warnings. |
| `docker compose run --rm migrate alembic downgrade base` then `upgrade head` | Passed through the Phase 2 migration in both directions. |
| `python -m research.replay.phase2_decisive` | Passed after clean re-upgrade; 16 workflow events, two provider commits, final revision 2 at 4 PM. |
| OpenAPI YAML parse and Phase 2 route check | Passed with locked `js-yaml`. |
| `pnpm format:check`, `pnpm lint`, `pnpm typecheck`, `pnpm test` | Passed; one existing Vitest test. |

## Successful trace

Revision 1 accepts 3 PM → dispatch marker and send are durable → simulator commits the appointment → `AFTER_COMMIT_BEFORE_RESPONSE:1` barrier holds the response → revision 2 accepts 4 PM → barrier releases and the response is dropped → operation 1 becomes UNKNOWN and is reconciled from provider status → operation 1 becomes PRESENT/SUPERSEDED → linked reschedule commits → revision 2 operation becomes PRESENT and the workflow resolves. The independent truth log contains exactly CREATE then RESCHEDULE; the final provider start is `2026-10-01T11:00:00+00:00` (4 PM Asia/Karachi). See `artifacts/phase-2-decisive-replay.json`.

## Expected failure trace

A provider with no idempotency, operation lookup, or resource lookup commits once and drops the response. The controller records UNKNOWN, performs eight bounded reconciliation attempts, then creates a durable human handoff. It does not retry the write, assert ABSENT, or emit an OperationFailed event. The simulator truth log still contains the hidden commit.

## Known limitations

- The research Compose profile drives the worker through `/internal/phase2/step` to make barriers and crash recovery deterministic; autonomous scheduling and operational supervision are deferred.
- `CRASH` is modeled as a provider-side connection loss after the selected barrier rather than killing the simulator process. `DELAY` and `REORDER` are controlled through held named barriers.
- The Phase 2 simulator is intentionally synthetic and limited to appointment create, reschedule, and cancel. Provider credentials and non-research adapters are not present.
- Phase 3 receipts and claim permits are not implemented. `speech_eligibility` remains BLOCKED even for a provider effect observed in Phase 2.
- CI is configured to run the integration suite and replay, but this local run does not prove a remote CI runner has passed.

## Deferred work

Phase 3 evidence and claim permits; Phase 4 provider-neutral cascaded voice and playback repair; Phase 5 UI; later independent experiment oracle, fixture freeze, statistical analysis, and comparison arms.

## Contract ambiguity requiring human decision

No new ambiguity arose in Phase 2. The earlier user decision to keep `gen_random_uuid()` SQL defaults remains the explicit UUIDv4 exception documented in `docs/06_SOURCE_CONFLICT_REPORT.md`. The supplied implementation pack and original schema were not altered.

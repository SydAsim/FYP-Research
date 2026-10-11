# Phase 0 report — repository and reproducible environment

Status: **Phase 0 exit gate passed locally on 2026-09-23**. Docker Compose built and booted the stack, PostgreSQL migration upgraded and downgraded, all six running services were healthy, and the repository checks passed. No Phase 1 work has started.

## Scope implemented

- Extracted the authoritative implementation pack and read `AGENTS.md` followed by every ordered source.
- Inspected all supplied UI reference screens and the architecture image. Recorded contradictions in `docs/06_SOURCE_CONFLICT_REPORT.md` and the proposed topology in `docs/07_PROPOSED_REPOSITORY_TREE.md` before service coding.
- Added the Phase 0 monorepo topology, locked Python and web dependencies, health-only processes, empty Alembic baseline, Compose with optional Redis/observability profiles, JSON logging bootstrap, pre-commit, CI, and four ADRs.
- Preserved `database/001_initial_schema.sql` for Phase 1. No business logic, UI workflow screen, external write, voice path, verification, or speech policy was implemented.

## Files changed

The pack files are extracted at repository root. New implementation files include `pyproject.toml`, `uv.lock`, `alembic.ini`, `database/migrations/**`, `apps/**`, `packages/**`, `research/**`, `tests/**`, `Dockerfile.python`, `compose.yaml`, `deployment/otel-collector.yaml`, `deployment/prometheus.yaml`, `.env.example`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, and `docs/adr/**`. `README.md` was extended with the topology and run commands. The authoritative SQL, OpenAPI, and event schema were not modified.

## Migrations added

`0000_phase0_baseline` creates Alembic revision bookkeeping only. Compose initialized a fresh PostgreSQL volume and ran the migration. `docker compose run --rm migrate alembic downgrade base` and `docker compose run --rm migrate alembic upgrade head` both passed. `alembic current` returned `0000_phase0 (head)`.

## Invariants covered by the scaffold

PostgreSQL is configured as the future durable authority. Redis is optional and unused by Phase 0 code. The domain and protocol package boundaries import no frameworks. The API/worker/simulator processes expose health only; they cannot make a business claim or send an external write. The model-proposal boundary and strict cascade research path are recorded in ADRs, without implementing either yet.

## Commands and results

| Check | Result |
|---|---|
| `docker compose config --quiet` | Passed |
| `uv lock --check`, `uv sync --locked` | Passed |
| `uv run ruff format --check .`, `uv run ruff check .` | Passed |
| `uv run mypy` | Passed: 18 Python source files |
| `uv run pytest -q` | Passed: 2 tests; 2 third-party deprecation warnings |
| `pnpm install --frozen-lockfile`, `pnpm peers check` | Passed |
| `pnpm format:check`, `pnpm lint`, `pnpm typecheck` | Passed |
| `pnpm test` | Passed: 1 Vitest test |
| `pnpm build` | Passed: Next.js production build |
| `pnpm --dir apps/web test:e2e` | Passed: 1 Playwright API-health test |
| `uv run alembic upgrade head --sql` | Passed: offline migration SQL generation |
| Secret-pattern scan of repository and server-only names in web static bundle | No matches |
| `docker compose up --build -d --wait` | Passed: PostgreSQL, web, API, voice worker, durable worker, and provider simulator healthy; migration exited successfully |
| Live Alembic downgrade, upgrade, and current revision | Passed: `0000_phase0 (head)` after re-upgrade |
| HTTP health URLs on ports 3000, 8000, 8001, 8002, and 8010 | Passed: all returned `status=ok` |

## Successful trace

From a first Compose build, PostgreSQL became healthy, `migrate` exited successfully, and all five application processes reached healthy status. The API and durable worker readiness endpoints queried PostgreSQL. A live Alembic downgrade and re-upgrade returned to revision `0000_phase0`. Playwright also started Next.js separately and passed the web health request.

## Expected failure trace

With `DATABASE_URL` set to an unreachable local port, the API `/health/ready` returned HTTP 503 and `Database unavailable`. This confirms readiness fails closed when PostgreSQL cannot be reached. Earlier, before the user started Docker Desktop, `docker info` failed because the Linux engine pipe was unavailable; that environment block is now resolved.

## Known limitations and deferred work

- CI configuration is written but has not run on a CI runner.
- Provider simulator is health only; durable jobs, database schema, domain transactions, and voice behavior belong to later phases.
- Current health tests are smoke checks. Database integration and contract behavior tests begin with the relevant implementation phases.

## Contract ambiguity requiring later decision

`AGENTS.md` asks for sortable UUIDs, while the supplied SQL uses `gen_random_uuid()`. This is reported in `docs/06_SOURCE_CONFLICT_REPORT.md` and must be resolved before translating the schema in Phase 1.

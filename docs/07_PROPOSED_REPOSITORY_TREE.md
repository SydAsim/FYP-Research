# Proposed Phase 0 repository tree

```text
AGENTS.md, README.md, pyproject.toml, uv.lock, package.json, pnpm-lock.yaml
compose.yaml, .env.example, .gitignore, .pre-commit-config.yaml
.github/workflows/ci.yml
apps/
  web/                 Next.js App Router, strict TypeScript, Tailwind, query/Zod setup, health
  api_controller/      FastAPI health and database readiness
  voice_worker/        process health; no voice or business behavior
  durable_worker/      process health; no queue processing yet
packages/
  domain/              pure Python package boundary
  protocol/            pure Python package boundary
  event_schemas/       future event code
  provider_adapters/   future provider interfaces
  speech_policy/       future deterministic policy
  observability/       structured logging bootstrap
research/
  scenario_dsl/ fixtures/ fault_schedules/ provider_simulator/
  oracle/ replay/ analysis/ tla_model/
database/
  001_initial_schema.sql  authoritative Phase 1 input, unchanged
  migrations/            empty Phase 0 Alembic baseline
  seeds/
tests/
  unit/ integration/ contract/ e2e/ experiments/
deployment/             source blueprints and observability configuration
docs/                   source specifications, conflicts, tree, ADRs
artifacts/              phase report and gate evidence
```

## Phase boundary and invariants

The scaffold contains no business mutation, state transition, verification receipt, claim permit, audio scheduling, or UI screen implementation. The API and workers expose health only. The database migration establishes an Alembic baseline but does not install `001_initial_schema.sql`; that translation belongs to Phase 1.

Compose starts PostgreSQL, web, API, voice worker, durable worker, and a health-only provider simulator. Redis is profile-gated and optional. Observability services are profile-gated. This topology leaves PostgreSQL as the future durable authority and keeps external model/provider calls outside the Phase 0 scaffold.

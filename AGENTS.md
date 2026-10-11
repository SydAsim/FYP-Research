# Instructions for implementation agents

## Source of truth

Read in this order before editing code:

1. `README.md`
2. `docs/01_UI_SCREEN_SPEC.md`
3. `docs/02_BACKEND_ARCHITECTURE.md`
4. `docs/03_DATA_EVENTS_AND_APIS.md`
5. `docs/04_TEST_EVALUATION_AND_TRACEABILITY.md`
6. `docs/05_PHASED_LLM_BUILD_PROMPTS.md`
7. `database/001_initial_schema.sql`
8. `contracts/openapi.yaml`
9. `contracts/event-envelope.schema.json`

When prose conflicts with executable contracts, stop and report the conflict. Do not silently choose one.

## Working rules

- Implement only the active phase.
- Begin every phase by listing files to create or modify and the invariant each file supports.
- Do not alter an earlier migration. Add a new migration.
- Do not edit experiment fixtures after the pilot freeze without creating a new fixture version.
- Do not let HTTP controllers contain domain decisions.
- Do not let models or prompts create database records directly.
- Do not use Redis as the only copy of any correctness-relevant fact.
- Do not add Kafka, Temporal, Celery, Kubernetes, or a vector database unless a measured requirement and ADR justify it.
- Do not add RBAC/RABAC, medical workflows, or emergency-service automation.
- Do not call an external write after an ambiguous timeout until reconciliation proves retry is safe.
- Do not emit success/cancellation/compensation audio from an LLM tool response.
- Do not mock the independent oracle with controller state.
- Do not hide failures by catching broad exceptions without a durable event and trace ID.
- Do not advance phases with failing tests or undocumented skips.

## Required output after every implementation phase

Produce `artifacts/phase-N-report.md` containing:

- Scope implemented.
- Files changed.
- Migrations added.
- Invariants covered.
- Commands executed.
- Test totals and failures.
- One successful trace.
- One expected failure trace.
- Known limitations.
- Deferred work.
- Any contract ambiguity requiring human decision.

## Code quality

- Python must be typed and pass the configured type checker.
- TypeScript must use strict mode and avoid `any` except at isolated third-party boundaries.
- Validate all network input with Pydantic or Zod.
- Use UTC timestamps and retain the original IANA time zone for appointments.
- Use UUIDv7 or another sortable UUID implementation consistently.
- Hash normalized requests, prompts, fixtures, audio, model outputs, and experiment configurations.
- Use structured logs with `trace_id`, `call_id`, `workflow_id`, `intent_revision`, `operation_id`, and `experiment_run_id` where applicable.
- Persist raw provider events beside normalized events.
- Error responses follow RFC 9457 problem details.

## Testing rules

- A unit test is not a substitute for a PostgreSQL integration test when locks, uniqueness, transactions, or exclusion constraints matter.
- Every command handler needs success, stale revision, duplicate key, and retry tests.
- Every worker transition needs crash-before and crash-after tests.
- Every UI route needs loading, empty, populated, permission/identity failure, recoverable error, and offline/reconnect behavior where relevant.
- Use named barriers, not timing sleeps, for race-condition experiments.
- The final-state oracle must read the simulator truth log independently.
- Repetitions do not increase the number of independent scenarios in statistical analysis.

## Commit discipline

- One phase or narrowly scoped invariant per change set.
- Include migration, code, tests, and documentation together.
- Never mix research-arm behavior. B0, B1, B2, B3, P1, and P2 must be explicit configuration profiles whose differences are recorded.


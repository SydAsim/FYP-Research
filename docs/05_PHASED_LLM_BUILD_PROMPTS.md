# Phased prompts for the implementation LLM

Use one prompt at a time. Do not send the entire project as a single “build everything” request. Before each phase, attach or place this implementation pack in the repository and require the LLM to read `AGENTS.md` first.

## Master instruction used in every phase

```text
You are implementing the Commit-Aware Voice Agent research application.

Read AGENTS.md and every source file it lists before editing. The implementation pack is authoritative. Work only on the requested phase. Do not weaken an invariant, invent an unlisted feature, add RBAC/RABAC, introduce medical/emergency workflows, or replace PostgreSQL truth with Redis.

Before coding:
1. Restate the phase boundary.
2. List the invariants affected.
3. List files you will create or edit.
4. Identify contract ambiguities and stop for a decision if any change would alter research meaning.

While coding:
- Keep domain decisions out of controllers and framework adapters.
- Add migration, implementation, tests, and documentation together.
- Preserve stable command/operation identities across retries.
- Use named barriers rather than sleep-based race tests.

After coding:
1. Run formatter, linter, type checker, unit tests, PostgreSQL integration tests, contract tests, and applicable E2E tests.
2. Produce artifacts/phase-N-report.md with commands, results, traces, limitations, and deferred work.
3. Do not claim completion while a required test fails or is silently skipped.
```

## Phase 0 Repository and reproducible environment

```text
Implement Phase 0 only.

Create the monorepo topology in README.md. Scaffold:
- apps/web using Next.js App Router, TypeScript strict mode, Tailwind, TanStack Query, Zod, Vitest, Playwright.
- apps/api_controller, apps/voice_worker, apps/durable_worker using Python, FastAPI where applicable, Pydantic v2, SQLAlchemy 2, Alembic, pytest, and async PostgreSQL.
- packages/domain and packages/protocol with no framework dependencies.
- research packages and empty fixture directories.

Create Docker Compose for PostgreSQL, optional Redis, services, provider simulator, and observability. Add health checks, example environment variables, lockfiles, pre-commit checks, CI, structured logging bootstrap, and ADRs for modular monolith, PostgreSQL queue, Redis non-authority, and model-proposal boundary.

Do not implement business logic or UI screens yet.

Exit gate:
- Clean clone boots with one documented command.
- Database migration command works against an empty database.
- All services expose health endpoints.
- Formatting, linting, types, and empty test suites pass in CI.
- No secret appears in repository or browser bundle.
```

## Phase 1 Domain, schema, and local deterministic transaction

```text
Implement Phase 1 only.

Translate database/001_initial_schema.sql into reviewed Alembic migrations without losing constraints. Implement pure domain types for workflow, immutable intent revision, operation dimensions, ticket, appointment, receipt result, and legal transitions.

Implement command handlers and repositories for:
- creating a synthetic call/workflow fixture,
- accepting intent revision 1,
- preparing a local appointment operation,
- committing a locally owned appointment in one short PostgreSQL transaction,
- accepting revision 2 and rejecting or transitioning stale work.

Use deterministic lock order and expected revision/resource version. Do not call a model, provider, Redis, LiveKit, or TTS.

Required tests:
- concurrent revision acceptance yields one revision 2,
- stale expected revision returns RFC 9457 409,
- overlapping active appointment is rejected by PostgreSQL,
- revision 2 before local commit blocks obsolete revision 1,
- revision 1 before revision 2 is preserved in effect history and transitioned,
- same command ID is idempotent,
- same idempotency key plus different request hash is rejected.

Exit gate: a deterministic HTTP test creates 3 PM, changes to 4 PM, and preserves an auditable history with one final active appointment.
```

## Phase 2 External provider simulator and unknown outcome recovery

```text
Implement Phase 2 only.

Build an isolated deterministic provider simulator with:
- append-only commit truth log,
- idempotency key behavior configurable as present/absent,
- operation status lookup configurable as present/absent,
- immediate, delayed, stale, and permanently unavailable visibility,
- named barriers before commit, after commit before response, and after response,
- faults for drop, delay, duplicate, reorder, 5xx, crash, partial effect, and conflicting concurrent change.

Implement operation attempts, DISPATCH_RECORDED-before-send, PostgreSQL worker leasing, UNKNOWN outcome, reconcile-before-retry, provider lookup/postcondition verification, bounded recovery, compensation linking, and handoff creation.

Implement the decisive trace:
3 PM accepted -> provider commits -> response dropped -> user changes to 4 PM -> old effect found -> safe reschedule or linked compensation -> final state checked.

Do not implement voice or decisive speech.

Required tests crash the worker before/after every durable boundary. Redis may be completely absent. Prove that no duplicate effect occurs and unresolved ambiguity is never reported as failure.

Exit gate: one command replays the decisive trace and emits a normalized timeline plus simulator truth log.
```

## Phase 3 Evidence, claim permits, and deterministic outcome language

```text
Implement Phase 3 only.

Add verification receipts and evidence items. Verification returns SATISFIED, VIOLATED, or UNKNOWN. Add invalidation/freshness rules and receipt applicability checks.

Add typed semantic claims and single-use claim permits. Implement deterministic templates for:
- progress: “I am still checking the appointment. It is not confirmed yet.”
- unknown: “I cannot yet determine whether the earlier request completed. I am continuing to check.”
- satisfied current appointment,
- compensated/rescheduled appointment,
- handoff/unresolved state.

The outcome sentence must be impossible to schedule without a current applicable SATISFIED receipt. Recheck the permit immediately before publication. Free-form model text must not enter the decisive-outcome channel.

Required tests:
- tool success without postcondition evidence cannot issue a permit,
- revision-1 receipt cannot authorize revision-2 current-state claim,
- historical claim and current-state claim have different predicates,
- receipt invalidated between synthesis and publication blocks audio,
- UNKNOWN permits progress/uncertainty but not success or cancellation,
- template variables cannot introduce unverified claims.

Exit gate: the decisive trace ends with a revision-2 receipt and authorized 4 PM template; no revision-1 success sentence is publishable.
```

## Phase 4 Voice pipeline and playback-aware repair

```text
Implement Phase 4 only.

Use LiveKit and a provider-neutral VoiceAdapter event interface. Implement the strict research path first: STT -> typed intent LLM -> deterministic speech scheduler/TTS. Add native-audio as a later adapter, not as the protocol authority.

Normalize SpeechStarted, TranscriptDelta, TranscriptFinal, PossibleEndOfTurn, ConfirmedEndOfTurn, SpeechResumed, InterruptionCandidate, InterruptionAccepted, AssistantAudioGenerated, AssistantAudioQueued, AssistantAudioPlayed, AssistantAudioStopped, and ToolProposalReceived.

Implement client playback events with idempotent event IDs and frame/word progress. On interruption, stop the buffer, accept the new revision through the server, invalidate stale permits, and create a durable repair obligation only if a decisive stale span was acknowledged as played.

Required tests:
- queued stale audio never starts,
- already playing stale audio records exact exposed span,
- repair obligation survives API, voice worker, browser, and Redis restart,
- corrected evidence-backed claim satisfies the obligation only after playback acknowledgement,
- backchannel resume rechecks permit applicability,
- browser disconnect does not cancel durable reconciliation.

Exit gate: prerecorded audio drives the P8 correction scenario with a complete playback and repair trace.
```

## Phase 5 UI implementation

```text
Implement Phase 5 only.

Read docs/01_UI_SCREEN_SPEC.md and reproduce the supplied Indigo Intelligence style, but apply every research correction in the specification. Do not copy incorrect mockup semantics.

Build the shared shell/components and the screens in this order:
1. Landing/consent.
2. Live call.
3. Call summary.
4. Calendar and appointment list/detail.
5. Resident list/record and notes.
6. Call history.
7. Workflow trace/replay.
8. Human handoffs.
9. Dashboard.
10. Evaluation overview/run detail/experiment launcher.
11. Settings.

Generate TypeScript API types from OpenAPI. Use real APIs; mock data is allowed only in isolated Storybook/component fixtures. Implement loading, empty, populated, conflict, degraded, reconnecting, and fatal states. Preserve keyboard navigation, focus, mobile responsiveness, and reduced motion.

Critical rule: never render Confirmed/Cancelled/Compensated from a tool response or optimistic mutation. Those visual states require server evidence state.

Exit gate: Playwright executes normal booking, hidden commit correction, partial stale playback repair, Redis loss, and call-end recovery through the browser.
```

## Phase 6 Research harness and baselines

```text
Implement Phase 6 only.

Build the scenario DSL, named P0-P9 barriers, fault scheduler, independent oracle, replay bundle, metric pipeline, and system profiles B0, B1, B2, B3, P1, P2. Profiles must share interfaces and differ only in documented mechanisms.

The oracle reads initial fixture, external final intent, domain policy, simulator commit log, and playback acknowledgements. It must be capable of disagreeing with the controller verifier.

Create fixtures across revision type, action semantics, workflow shape, acoustic condition, provider capability/visibility, speech exposure, and fault family. Do not run the full Cartesian product; define mandatory high-risk cells and a documented covering array for secondary combinations.

Required output: frozen replay bundle containing manifest, hashes, normalized events, fault occurrences, simulator truth, oracle result, and metric rows.

Exit gate: a small paired run executes the same case under B3, P1, and P2 and reproduces identical fault placement.
```

## Phase 7 Pilot and freeze

```text
Implement and execute Phase 7 only.

Run 30-50 independent pilot scenarios. Treat this as protocol debugging, not final evidence. Inspect every failure trace. Fix implementation defects, refine metric code, and document any changed schema or exclusion.

Then freeze:
- primary endpoints and non-inferiority condition,
- system-arm definitions,
- scenario/fault fixtures,
- retry and timeout budgets,
- provider/model/audio versions,
- analysis plan,
- exclusion rules,
- migration and event schema versions.

Produce pilot report, raw counts, paired discordance estimate, sample justification, and final manifest template.

Exit gate: a new clean environment can reproduce a selected pilot case and its metric row from the replay bundle.
```

## Phase 8 Main evaluation

```text
Execute Phase 8 only; do not change frozen protocol code during the campaign.

Run 500 independently specified paired scenarios under preregistered arms. Repetitions for model/audio nondeterminism remain clustered under scenarios. Account for every planned execution, including timeout, exclusion, infrastructure failure, and rerun reason.

Produce raw data, exact counts, confidence intervals, paired analysis, clustered latency intervals, clean-case non-inferiority, ablations, and threat analysis. Separate confirmatory results from exploratory causal-schedule findings.

If a defect requires code change, pause the campaign, version the protocol, and restart affected comparisons. Never silently replace outcomes.
```

## Phase 9 Optional transfer studies

```text
Proceed only if the core result is stable.

Possible extensions:
- Native-audio Gemini/OpenAI comparison through the same provider-neutral event adapter.
- Frozen sandbox external provider subset.
- Semantic provisional dispatch barrier.
- Automated schedule exploration.
- Ethics-approved human study of belief accuracy.

Do not mix these exploratory extensions into the core contribution unless they have independent evidence and a revised study plan.
```

## Code-review prompt after every phase

```text
Review the completed phase as a skeptical systems researcher and production backend reviewer.

Search for:
- any path that turns timeout into failure,
- any blind retry after possible send,
- any outcome speech without applicable receipt/permit,
- any Redis correctness dependency,
- any model-selected actor, resource, URL, SQL, receipt, or provider result,
- any lock held across network/model/audio calls,
- any stale revision/resource overwrite,
- any repair state that disappears on restart,
- any oracle dependency on controller belief,
- any sleep-based experiment race,
- any UI that visually overclaims certainty,
- any medical/emergency/RBAC scope creep.

Report findings by severity with exact file/function, violated invariant, reproducible trace, and smallest safe fix. Do not implement fixes until the report is accepted.
```


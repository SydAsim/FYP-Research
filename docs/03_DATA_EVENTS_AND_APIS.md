# Data, events, and API contracts

## 1. Data ownership

PostgreSQL is the only durable source for accepted intent, logical operation identity, business resources owned by the application, evidence, speech authorization, repair, event history, and experiment results.

The external provider simulator owns a separate append-only truth log. The production verifier and research oracle must not read the controller's conclusion as truth.

## 2. Principal tables

| Group | Tables | Critical constraint |
|---|---|---|
| Identity/calls | `actors`, `residents`, `properties`, `call_sessions`, `utterances` | Synthetic identity and recording consent are distinct from workflows |
| Intent | `workflows`, `intent_revisions` | `(workflow_id, revision)` unique and monotonically accepted |
| Execution | `operations`, `operation_attempts`, `effect_ledger`, `reconciliation_jobs` | Idempotency key unique; same key must have same request hash |
| Domain | `maintenance_tickets`, `appointments` | Row version and exclusion constraint for active overlapping slots |
| Evidence | `verification_receipts`, `evidence_items` | Three-valued result; receipt invalidation preserved |
| Speech | `claims`, `claim_permits`, `audio_segments`, `playback_events`, `repair_obligations` | Claim permit binds receipt/revision/template; played stale claim creates repair |
| Handoff | `handoffs` | Known and unknown facts recorded separately |
| Events | `workflow_events`, `outbox`, `inbox_deliveries` | Per-workflow sequence; at-least-once delivery |
| Research | `evaluation_runs`, `scenario_cases`, `executions`, `fault_occurrences`, `oracle_results`, `metrics` | Frozen hashes and independent truth |

The complete first migration is supplied in `database/001_initial_schema.sql`. The implementation LLM must translate it into Alembic while preserving all constraints.

## 3. Appointment time and conflicts

- Store start/end as `timestamptz` and original IANA zone.
- Preserve the requested local representation for display/audit.
- Use a generated `tstzrange` or equivalent exclusion constraint to prevent overlapping active appointments for the same resource.
- Every update carries `expected_version`; mismatch returns `409`.
- Verification receipts record the observed appointment version.

## 4. Event envelope

All events use the supplied JSON Schema. Required fields include event ID, name, version, occurred time, workflow ID, workflow sequence, correlation/causation IDs, trace ID, actor assumption, and payload.

### Essential event names

**Conversation:** `CallCreated`, `UtteranceStarted`, `UtteranceFinalized`, `TranscriptRevised`, `InterruptionCandidate`, `InterruptionAccepted`, `CallMediaEnded`.

**Intent:** `CandidateIntentProduced`, `IntentRevisionAccepted`, `IntentRevisionRejected`.

**Execution:** `OperationProposed`, `OperationReady`, `OperationCancelledBeforeDispatch`, `DispatchRecorded`, `ProviderRequestSent`, `ProviderResponseReceived`, `OperationOutcomeUnknown`.

**Verification/recovery:** `VerificationStarted`, `VerificationSatisfied`, `VerificationViolated`, `VerificationUnknown`, `ReconciliationScheduled`, `CompensationPlanned`, `CompensationStarted`, `CompensationVerified`, `WorkflowResolved`, `WorkflowEscalated`.

**Speech:** `ClaimPrepared`, `ReceiptIssued`, `ReceiptInvalidated`, `ClaimAuthorized`, `ClaimPermitInvalidated`, `AudioGenerated`, `AudioPublished`, `PlaybackStarted`, `PlaybackInterrupted`, `PlaybackCompleted`, `RepairRequired`, `RepairSatisfied`.

**Research:** `CaseInitialized`, `BarrierReached`, `FaultInjected`, `BarrierReleased`, `OracleEvaluated`, `MetricRecorded`, `ReplayBundleFinalized`.

## 5. Public APIs

### Calls

- `POST /v1/calls` creates call and synthetic actor binding.
- `GET /v1/calls/{call_id}` returns media and business-resolution status separately.
- `POST /v1/calls/{call_id}/end` ends media idempotently.
- `GET /v1/calls/{call_id}/summary` returns evidence-bounded result.
- `GET /v1/calls/{call_id}/timeline` returns normalized event projection.
- `WS /v1/calls/{call_id}/timeline` streams normalized updates.
- `POST /v1/calls/{call_id}/playback-events` records client exposure.

### Workflows and revisions

- `POST /v1/workflows` creates workflow.
- `GET /v1/workflows/{workflow_id}` returns aggregate state.
- `POST /v1/workflows/{workflow_id}/candidate-intents` stores provenance-bearing proposal.
- `POST /v1/workflows/{workflow_id}/revisions` accepts/rejects against expected revision.
- `GET /v1/workflows/{workflow_id}/events` returns ordered events.

### Operations and evidence

- `GET /v1/operations/{operation_id}`.
- `GET /v1/operations/{operation_id}/attempts`.
- `GET /v1/operations/{operation_id}/receipt`.
- `POST /internal/operations/{operation_id}/reconcile` internal/experiment only.
- `POST /internal/operations/{operation_id}/compensations` internal/experiment only.

### Domain

- `GET /v1/residents`; `GET /v1/residents/{id}`.
- `GET /v1/appointments`; `POST /v1/appointments`.
- `POST /v1/appointments/{id}/reschedule`.
- `POST /v1/appointments/{id}/cancel`.
- `GET /v1/maintenance-tickets`; `GET /v1/maintenance-tickets/{id}`.
- `GET /v1/notes`; `POST /v1/notes`.

### Handoffs and research

- `GET /v1/handoffs`; acknowledge/resolve endpoints.
- `GET /v1/evaluation/runs`; `POST /v1/evaluation/runs`.
- `POST /v1/evaluation/runs/{id}/start`.
- `GET /v1/evaluation/runs/{id}`; executions; metrics; replay bundle.

The starter OpenAPI contract intentionally defines the high-risk command shapes. Expand it incrementally and keep generated frontend types synchronized in CI.

## 6. Mutation request contract

Every consequential command contains:

```json
{
  "command_id": "uuid",
  "workflow_id": "uuid",
  "expected_intent_revision": 2,
  "expected_resource_version": 7,
  "command": {
    "type": "reschedule_appointment",
    "appointment_id": "uuid",
    "requested_start": "2026-09-24T15:00:00+05:00",
    "requested_end": "2026-09-24T15:30:00+05:00",
    "timezone": "Asia/Karachi"
  },
  "candidate_source": {
    "utterance_id": "uuid",
    "model": "pinned-model-id",
    "prompt_hash": "sha256",
    "audio_start_ms": 18420,
    "audio_end_ms": 21680,
    "transcript_version": 11
  }
}
```

Actor and resource scope are injected server-side. The API rejects stale revision, stale resource version, schema failure, unsupported transition, provider-host mismatch, and changed request under a reused idempotency key.

## 7. Error contract

Use RFC 9457 problem details:

```json
{
  "type": "https://example.invalid/problems/stale-intent-revision",
  "title": "Stale intent revision",
  "status": 409,
  "detail": "Expected revision 2 but revision 3 is current.",
  "instance": "/v1/workflows/.../revisions",
  "trace_id": "...",
  "retryable": false,
  "current_revision": 3
}
```

Do not expose stack traces, prompts, credentials, or raw provider secrets.

## 8. Concurrency and transaction rules

- Lock rows in deterministic order: workflow → operation → domain resource → claim permit/repair obligation.
- Do not hold transactions across model, provider, audio, or browser calls.
- Use optimistic row versions for interactive appointment edits.
- Use unique constraints for idempotency and inbox/outbox deduplication.
- Use exclusion constraints for conflicting active appointments.
- Retry serialization failures at the application-command boundary with the same command/operation identity.
- Record `DISPATCH_RECORDED` before send; record outcome separately.

## 9. Retention and reproducibility

Separate retention policies for raw audio, transcript, business metadata, and anonymized research traces. A replay bundle contains hashes and normalized events; it need not contain raw audio when consent forbids it.

Every evaluation run freezes:

- Source commit and container digests.
- Migration version and fixture hash.
- Scenario/fault schedule seed and barrier map.
- Provider simulator and oracle versions.
- Model/provider identifiers, region/date, prompt/tool schema hashes, and sampling settings.
- Audio/transcript hashes and annotations.
- Retry/timeout budgets and speech policy version.
- Analysis code version and primary endpoints.


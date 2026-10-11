# Phase 3 report — evidence and deterministic claim text

Status: **Phase 3 exit gate passed locally on 2026-09-26.** Docker Desktop recovered. The host's port 5432 was owned by an unrelated WSL relay, so this Compose run used `POSTGRES_HOST_PORT=15432` without stopping that process. The final source passed the full PostgreSQL suite, a fresh decisive replay, and clean migration upgrade/downgrade/upgrade.

## Scope implemented

- Independent simulator resource and operation-status reads produce durable `SATISFIED`, `VIOLATED`, or `UNKNOWN` verification receipts with raw evidence, normalized result, observation time, intent revision, source version, verifier version, and a short validity window.
- Typed semantic claims use closed deterministic templates. A current applicable `SATISFIED` receipt can authorize a single-use permit; queue and publication recheck revision and applicability, and publication reads fresh source facts. Model text is rejected at the command boundary.
- Accepting a corrected revision invalidates older receipts and queued/authorized permits in PostgreSQL. A source version or final-state change before publication invalidates the affected receipt and permit. Safe progress and uncertainty language remains available without a decisive claim.
- Phase 3 remains text only. The voice scheduler, client playback acknowledgement, and repair obligation are Phase 4 work.

## Files changed

Added `database/migrations/versions/0004_phase3_evidence_policy.py`, `packages/domain/phase3_verification.py`, `packages/speech_policy/phase3.py`, `apps/api_controller/phase3_models.py`, `phase3_verification_service.py`, `phase3_claim_service.py`, `phase3_routes.py`, `research/replay/phase3_decisive.py`, `tests/unit/test_phase3_policy.py`, and `tests/integration/test_phase3_postgres.py`. Updated `apps/api_controller/main.py`, `phase1_service.py`, `compose.yaml`, `contracts/openapi.yaml`, `.github/workflows/ci.yml`, `README.md`, and `acceptance/traceability.csv`. The Compose host PostgreSQL port is configurable so a separate WSL service can keep port 5432. No earlier migration or frozen fixture was edited.

## Migration added

`0004_phase3_evidence` adds receipt and permit validity constraints, a receipt-to-operation scope foreign key, a unique active claim permit index, an evidence applicability index, and an `OUTCOME`/`REPAIR` audio segment permit constraint. It passed upgrade, downgrade to base, and upgrade again in a new temporary PostgreSQL database. That database was then dropped.

## Invariants covered

| Invariant | Evidence |
|---|---|
| UNKNOWN is separate from failure | Three-valued verification result and no permit for UNKNOWN; the no-resource-lookup test expects UNKNOWN after a successful provider response. |
| Evidence is revision and resource bound | Receipt stores workflow, operation, revision, predicates, source version, observation and expiry; correction invalidates old evidence in the same transaction. |
| No decisive claim from model text or tool response | Claim preparation accepts a receipt ID and revision only; rendering uses a closed template and validated predicates. |
| Permit is single-use and rechecked | Queue checks receipt; publication reads fresh provider state, locks workflow/operation/permit, and changes QUEUED to PUBLISHED once. |
| Historical and current claims differ | Historical effect relies on old operation status; current appointment relies on present resource state. |
| PostgreSQL owns correctness | Receipts, evidence, claims, permits and invalidations are all durable PostgreSQL records; Redis is not consulted. |

## Commands executed and results

| Command/check | Result |
|---|---|
| `python -m ruff format --check .`, `ruff check .`, `mypy` | Passed; 51 files formatted and 38 source files type checked. |
| `python -m pytest -q` with PostgreSQL on host port 15432 and simulator on 5433 | 40 passed, 0 failed; two third-party TestClient deprecation warnings. |
| `POSTGRES_HOST_PORT=15432 docker compose up -d --build --wait` | All eight services healthy; migration applied. |
| `python -m research.replay.phase3_decisive` | Passed against final source and refreshed `artifacts/phase-3-decisive-replay.json`. |
| `alembic upgrade head`, `downgrade base`, `upgrade head` via Compose migrate against fresh temporary database | All passed; temporary database removed after verification. |
| OpenAPI YAML parse with isolated pinned PyYAML 6.0.3 | Passed; 19 paths parsed. |

## Successful trace

The refreshed replay records the revision-1 hidden 3 PM provider commit, revision-2 correction and reconciled 4 PM resource, a revision-2 `RESCHEDULED_APPOINTMENT` receipt, an authorized permit, and publication of the deterministic text: “Your maintenance appointment has been moved to 4:00 PM on 2026-10-01 (Asia/Karachi).” No revision-1 `ClaimPublished` event appears.

## Expected failure trace

The policy unit test gives an authoritative read with no matching appointment or a conflicting active appointment; the verifier returns `VIOLATED`. Missing authoritative resource evidence or a `HELD` intermediate state returns `UNKNOWN`. Neither result satisfies receipt applicability or permits a success template. The PostgreSQL integration case confirms that a successful provider response without postcondition evidence yields `UNKNOWN` and HTTP 409 when attempting claim authorization. Other integration cases confirm stale revision and changed resource version block queued publication.

## Known limitations

- The Phase 3 endpoint publishes deterministic text as a durable event; no sound is generated, queued to a client, or acknowledged as played.
- The simulator source supplies the independent external facts; a production provider adapter is deferred. The verification window is currently 30 seconds, so late publication must acquire a new receipt.
- A separate WSL service holds host port 5432 on this computer. Set `POSTGRES_HOST_PORT=15432` for Compose and the matching host `DATABASE_SYNC_URL` for local integration tests.

## Deferred work

Phase 4 implements the provider-neutral cascaded voice path, normalized voice events, playback acknowledgements, interruption handling, and durable repair. Phase 5 UI and later research-arm evaluation remain deferred.

## Contract ambiguity requiring human decision

No new Phase 3 prose/executable contract conflict was found. The earlier user-selected UUID exception remains: keep authoritative `gen_random_uuid()` SQL defaults instead of changing migrations to sortable UUIDs. No further human contract decision is needed.

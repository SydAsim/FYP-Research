# Testing, evaluation, and research traceability

## 1. Test pyramid

### Domain unit tests

- Legal and illegal transitions for every orthogonal operation dimension.
- Intent-change classification.
- Receipt applicability and predicate entailment.
- Claim-permit issue/invalidation.
- Played-span semantic classification and repair requirement.
- Domain reschedule/compensation policy.

### PostgreSQL integration tests

- Concurrent revision acceptance.
- Revision acceptance racing local commit.
- Idempotency key reuse with same/different request hash.
- Appointment exclusion constraint.
- Outbox atomicity and duplicate delivery.
- Worker lease expiry and reclaim.
- Receipt invalidation and permit release race.
- Repair obligation survives restart.

### Adapter contract tests

Run the same suite against the deterministic simulator and each real/sandbox provider adapter:

- Stable identity propagation.
- Idempotency semantics.
- Status lookup.
- Immediate/delayed visibility.
- Timeout before/after send.
- Duplicate/reordered response.
- Partial multi-step effect.

### End-to-end tests

- Normal 3 PM booking.
- Correction before dispatch.
- Hidden 3 PM commit, lost response, correction to 4 PM.
- Correction during stale outcome playback.
- Provider permanently unobservable.
- Redis loss.
- Worker crash after dispatch marker.
- Browser disconnect with continuing reconciliation.
- Handoff after bounded unresolved recovery.

### UI tests

Use Mock Service Worker only for component states. Critical acceptance uses real FastAPI/PostgreSQL/simulator through Playwright.

## 2. Named timing barriers

| Phase | Barrier |
|---|---|
| P0 | Correction starts before original intent is accepted |
| P1 | Original accepted; correction accepted before dispatch authorization |
| P2 | Request dispatched; external service not committed |
| P3 | External service committed; acknowledgement withheld |
| P4 | Acknowledgement received; postcondition verification incomplete |
| P5 | Verification complete; no claim permit |
| P6 | Claim authorized/generated; not published |
| P7 | Audio published/buffered; not played |
| P8 | Decisive outcome audio is playing |
| P9 | Decisive outcome audio completed before correction |

Mandatory core phases: P1, P2, P3, P5, P8. P3 is the decisive hidden-commit condition.

Barriers must be explicit events with wait/release control. Do not simulate races using approximate sleeps.

## 3. System arms

| Arm | Capability |
|---|---|
| B0 | Ordinary tool agent with best-effort cancellation |
| B1 | Durable idempotency, postcondition/status verification, verify-before-retry |
| B2 | B1 plus established transaction staging, compensation, and revision invalidation where applicable |
| B3 | Competent integration of B2 and current playback tracking, without the proposed cross-layer permit/repair rules |
| P1 | B3 plus revision-bound claim permits and explicit product-state invariants |
| P2 | P1 plus durable played-span repair obligations |

All arms share models, prompts, tools, fixtures, provider behaviour, audio, retry budgets, and timeouts unless the difference is the explicit ablation.

## 4. Primary research questions

- **RQ1:** Does revision-aware reconciliation improve correction success under commit ambiguity without unacceptable clean-case loss?
- **RQ2:** Does explicit `UNKNOWN` plus reconcile-before-retry reduce duplicate effects and unsafe false cancellations?
- **RQ3:** Do revision-bound evidence rules prevent old valid receipts from authorizing new or stale claims?
- **RQ4:** Does receipt-gated speech reduce unsupported audible confirmations at useful outcome coverage?
- **RQ5:** Does durable playback repair reduce misleading audio exposure and improve evidence-backed correction after partial stale playback?
- **RQ7:** Do named commit/playout barriers expose failures missed by end-of-task evaluation?

RQs 6, 8, and 9 remain optional extensions: semantic provisional dispatch barrier, causal schedule exploration, and human belief study.

## 5. Primary endpoints

Preregister no more than two primary endpoints:

1. Correction success.
2. Per-task unsupported confirmation under post-commit ambiguity.

Treat clean task success as a non-inferiority endpoint so a silent/refusing system cannot win by avoiding useful outcomes.

### Metric definitions

| Metric | Definition |
|---|---|
| Correction success | Revision scenarios ending in a domain-permitted final state for externally specified final intent with no forbidden effect |
| Unsupported confirmation | Task has an audible decisive claim lacking applicable evidence at release/play time |
| Stale confirmation rate | Audible claims refer to superseded incompatible revision / relevant claims |
| Duplicate effect rate | Logical operation yields more durable effects than permitted |
| Unsafe false cancellation | System claims cancellation while effect is present or unknown |
| Clean task success | Correct clean tasks / clean tasks |
| Safe resolution | Correct completion, cancellation, refusal, honest unresolved status, or appropriate handoff |
| Outcome coverage | Tasks receiving a definitive correct result rather than only silence/uncertainty/handoff |

Latency measures include end-of-turn to useful response, correction to old-audio cessation, correction to accepted revision, accepted revision to dispatch decision, external commit to controller knowledge, verification to authorization, authorization to playback, and correction to final resolution.

## 6. Independent oracle

The oracle reads:

- Initial fixture.
- Complete user script and externally specified final intent.
- Domain transition policy.
- Provider simulator append-only commit log.
- Client playback acknowledgements.

It does not read the verifier's conclusion as truth. Report controller safety and end-to-end correctness separately; accepting the wrong intent is an end-to-end failure even if the controller safely fulfills it.

## 7. Sample plan and analysis

1. Run 30-50 pilot cases to debug protocol and estimate paired discordance.
2. Freeze schemas, outcomes, exclusions, retry budgets, fixtures, and endpoints.
3. Run 500 independently specified paired scenario instances through all compared arms.
4. Use repeated executions only for model/audio nondeterminism; cluster repetitions under the scenario.
5. Use McNemar analysis for paired binary outcomes with one observation per scenario.
6. For multiple seeds/audio versions, use a logistic mixed-effects model with fixed effects for arm, phase, fault, revision type, and action class; random intercepts for scenario template and speaker/audio.
7. Use clustered bootstrap intervals for paired latency differences.
8. Use exact counts and binomial intervals for rare failures.
9. Use survival/accelerated-failure-time analysis for timeout-censored resolution.
10. Correct secondary comparisons and separate confirmatory from exploratory schedule discovery.

## 8. Required ablations

- Remove dispatch revision comparison.
- Remove durable accepted-intent log.
- Use Redis-only idempotency.
- Remove provider status lookup.
- Retry before verification.
- Remove explicit `UNKNOWN`.
- Remove receipt-revision binding.
- Remove freshness revalidation.
- Remove outbox/recovery lease.
- Remove claim permit.
- Remove playback gate.
- Remove durable repair obligation.
- VAD-only interruption barrier.
- Native-audio versus cascade adapter.

## 9. Traceability matrix

| Requirement | Main code area | API/UI evidence | Test evidence | Research link |
|---|---|---|---|---|
| Accepted revision is durable | `domain/intent`, revision repository | S12 revision track | concurrent accept test | RQ1/RQ3 |
| Unknown is not failure | operations/reconciliation | S03/S12 unknown state | lost-response trace | RQ2 |
| Reconcile before retry | durable worker/provider adapter | operation detail | duplicate-effect test | RQ2 |
| Receipt is revision-bound | verification/speech policy | S12 receipt panel | stale receipt test | RQ3 |
| Speech needs permit | speech policy/scheduler | S02/S03 permit link | release-race test | RQ4 |
| Played stale claim requires repair | playback/repair worker | S02 repair badge, S12 span | partial-play restart test | RQ5 |
| Redis is disposable | cache adapter | degraded banner | Redis wipe E2E | Threat control |
| Oracle is independent | research/oracle | S14/S15 | controller-oracle disagreement | RQ7 |
| Named phase faults | research/barriers | S16 launcher, S12 marker | P0-P9 suite | RQ7 |

Maintain the expanded CSV in `acceptance/traceability.csv` as code is added.

## 10. Phase acceptance checklist

No phase is complete until:

- Migration upgrades and downgrades in a clean database.
- Unit, integration, contract, and applicable E2E tests pass.
- No skipped critical test exists without issue and justification.
- OpenAPI and generated frontend types are synchronized.
- Event schemas validate emitted examples.
- One happy and one failure trace are attached.
- Redis wipe/restart behavior is tested when relevant.
- Logs contain required IDs without secrets.
- Documentation and traceability are updated.


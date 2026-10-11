# Revised research-readiness report — Phase 7 remedies v2

Date: 2026-10-04 (Asia/Karachi). **Phase 8 verdict: NOT READY for the 500-case campaign.**

The revised local instrument and targeted remedy gates pass. The main study still needs a complete new input, analysis and campaign freeze (F8). The original v1 instrument is not valid for new repair measurements. **The 500-case evaluation remains unstarted.**

## 1. Implemented scope and preserved evidence

Implemented the outcome grader, semantic exposure boundaries, uniform repair capability, late/duplicate ACK handling, repeated-correction verification and durable repair consumer. Ran six requested fixture families once each under B3/P1/P2, with a plan frozen before execution. PostgreSQL remains the durable correctness authority. No Redis-only correctness facts, blind ambiguous retries, model-created records, RBAC, medical workflows or emergency automation were added.

All **273 historical evidence files** match their before/after SHA-256 inventories. The original v1 manifests, source archive, traces, grades, reports and audit were not rewritten. Historical offline replay verifies **267 executions, 40 instances, 45 versions and 112 failure reviews**. Archive verification passes with `check_workspace=False`; the working-source drift guard is expected to fail after versioned changes.

A recursive lint invocation temporarily created seven cache files under an extracted historical source directory. Those new cache files were preserved separately and removed from v1. No original file hash changed. Later lint uses explicit source directories and `--no-cache`.

[Before hashes](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/historical-hashes-before.json>) · [After hashes](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/historical-hashes-after.json>) · [Revised source archive](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/source-v2.zip>)

The revised source archive contains **257 files**, including tests and the pre-execution document. Executions retain source, configuration, fixture, request, observation and audio hashes. Planned tone WAV bytes are retained and verified. Diagnostics and revised measurements have separate directories; none replaces historical results.

- Plan: `f1660f250c3c75908bf9d19df59f5d7d4f266583ae0466b9b901248b474f96d6`
- Fixture: `1c864178ef94b5257a3119b9b489cea08b77d927bf11aeb4e45a657130692df5`
- Source: `1d8a0730a6f4e1231d31b0405ae9bfa62fb60cc6e0013ab45220c33e588743bc`
- Archive SHA-256: `a56e875a966a2f72a65574d82f897363c9188d5c282508de152fa95303233fd2`

[Frozen plan](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/exploratory-plan.json>) · [Pre-execution definitions and budgets](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/docs/10_RESEARCH_REMEDIES_V2.md>) · [Source inventory](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/source-freeze.json>)

## 2. Audit findings

| Finding | Status | Remedy and practical limit |
|---|---|---|
| F1: arm-dependent grading | Resolved in v2 | Observable outcomes ignore arm labels, permits, receipt verdicts and obligation rows. Seven-label invariance and behavioral equivalence tests pass. All actual trace grades also replay invariantly under changed labels/permit metadata. Legacy grading is retained only for historical verification. |
| F2: late-ACK leak and constraint failure | Resolved | Reproduced PROGRESS and COMPLETED using real PostgreSQL before changing behavior. Both B3 cases returned 409 database-constraint; both P1 cases incorrectly persisted repair; P2 persisted repair. Revision and ACK paths now share capability rules, reinforced by a new DB trigger. Duplicate/delayed ACKs retain raw inputs and merge progress monotonically. |
| F3: introductory words treated as decisive | Resolved for protocol proxy; actual voice unmeasured | Two-word intro control is retained. E3 reaches eight words through `3:00 PM`. Confirmation status, time, date and zone have separate predicate boundaries. Confirmation alone is not incompatible time exposure. Tone and equal-duration metadata are explicitly synthetic. |
| F4: truth-only support and synthetic timestamps | Resolved for scoped simulator contract | Truth and ordinary available evidence are separate at persisted publication and recorded client exposure. Baseline evidence requires no P1/P2 receipt object. Resource version, observation availability and freshness are checked independently. Missing evidence/alignment/ACKs remain UNKNOWN. Client testimony does not prove physical hearing. |
| F5: mechanisms not exercised | Resolved for the targeted set | Normal arm interfaces exercise stale claims, post-publication resource changes and exposed corrections. First blockers and ties are reported below. Six deliberately selected families do not establish population benefit. |
| F6: no outstanding-repair consumer | Resolved for discovery/publication; media limits remain | New leased PostgreSQL consumer discovers obligations on startup. E4 uses an actual worker restart; no obligation ID is supplied to the restarted worker. Seven process-crash boundaries and concurrent consumers pass integration checks. E5 is logical client reconnection, not an actual WebRTC outage. |
| F7: incomplete budgets/adapters | Resolved for v2 | Per-path HTTP, TTL, lease and drain-pass budgets match code and are frozen. Raw requests, worker steps and processes are retained. A drain pass is not a global transition count. Typed intent/tone is not represented as an actual STT/LLM/TTS trial. |
| F8: dependence/main analysis readiness | Partially resolved; Phase 8 blocker | Six generator-family IDs, tone/no-speaker provenance, 18 slots and all missingness are retained. Analysis is descriptive and paired by family. All 500 independently specified inputs, applicability/strata, comparison-family freeze and required mixed-effects/survival/AFT analysis are not complete. |
| F9: reachable truth endpoint | Local boundary verified; deployment limit remains | V2 enables an optional oracle-only header credential. Access without it is denied. Controller/worker receive neither token nor simulator DSN. Same-host privileged access remains possible; legacy deployments remain open unless the credential is configured. This is an application boundary, not OS isolation. |

An additional diagnostic found that verification accepted only a fixed CREATE → RESCHEDULE chain. It incorrectly rejected a second correction. All three arms now share the bounded CREATE → RESCHEDULE → RESCHEDULE check. Deeper chains remain UNKNOWN. The unsuccessful diagnostic traces remain saved.

[Retained six pre-fix PostgreSQL reproduction traces](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/debug/pre-fix-late-ack.json>)

## 3. Separated endpoints and anchors

- **Final business state:** externally scripted start, end and IANA zone plus the fixture property-resource binding, established before operation preparation, compared with independent simulator truth.
- **Claim truth and applicable evidence:** separate publication and decisive-playback endpoints. Ordinary baseline observations count when they support the claim and remain applicable; no receipt representation is required. A moved claim additionally needs observed reschedule evidence.
- **Incompatible stale content:** acknowledged semantic predicates compared with intent accepted at exposure time, independent of whether provider facts were still true.
- **Correct final update:** current, supported update with full completion testimony. Publication or STARTED alone is insufficient.
- **Explicit retraction:** specified corrective wording plus a supported completed current update after incompatible content was exposed. The same baseline wording would receive the same credit.
- **Durable repair:** internal persistence, pending, completion and escalation telemetry, excluded from observable grading.

Publication uses recorded `published_at`. Exposure uses recorded client `client_time`; late delivery retains a separate server receipt time. Staleness uses PostgreSQL `accepted_at`, with the earlier external `scripted_at` retained separately. A supported statement later needing correction is not retroactively false.

Only complete semantic predicates are credited. `Your maintenance` does not confirm anything; `confirmed` conveys status; eight initial words convey the time through AM/PM. Date and zone have later boundaries. Equal-duration word/frame metadata is not acoustic alignment. Missing observations, alignment or completion stay UNKNOWN. A rejected STARTED request does not prove physical silence.

## 4. All 18 planned execution outcomes

All 18 slots completed procedurally: **0 harness failures, 0 timeouts, 0 missing slots**. This is not 18 successful business outcomes. E2 retains three provider conflicts and unresolved updates.

T=TRUE, F=FALSE, U=UNKNOWN, N=NOT_APPLICABLE. Pub/Play are truth/evidence. For multiple claims, each dimension conservatively aggregates their checks; per-claim details remain in traces. Repair counts are internal persisted/completed telemetry.

| Case | Arm | Business | Pub T/E | Play T/E | Stale | Update | Retraction | Repairs persisted/completed | Trace |
|---|---|---|---|---|---|---|---|---|---|
| E1 | B3 | T | T/T | T/T | F | T | N | 0/0 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E1-B3-e797fd60-ba55-4768-b50b-085519516a97.json>) |
| E1 | P1 | T | T/T | T/T | F | T | N | 0/0 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E1-P1-b5b79078-235f-4471-a5e5-e76ea392dc63.json>) |
| E1 | P2 | T | T/T | T/T | F | T | N | 0/0 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E1-P2-c1b9f6f6-7317-4f47-8ab7-93ec3a4a5643.json>) |
| E2 | B3 | F | T/T | T/F | F | F | F | 0/0 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E2-B3-28a9c86b-d902-48ec-9382-22840e501d02.json>) |
| E2 | P1 | F | T/T | U/U | U | U | N | 0/0 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E2-P1-de788c41-0306-47b2-9d9c-ed7a1e9482e8.json>) |
| E2 | P2 | F | T/T | U/U | U | U | N | 0/0 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E2-P2-c34156d8-25ee-4d37-98b9-e7d0fc983a8a.json>) |
| E3 | B3 | T | T/T | T/T | F | T | F | 0/0 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E3-B3-e3713109-8b49-4764-8992-851763f69895.json>) |
| E3 | P1 | T | T/T | T/T | F | T | F | 0/0 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E3-P1-b27ad693-6ef1-42be-8bcc-7f35d60bad61.json>) |
| E3 | P2 | T | T/T | T/T | F | T | T | 1/1 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E3-P2-8db21440-2fa9-418d-ae24-e44d1977d205.json>) |
| E4 | B3 | T | T/T | T/T | F | T | F | 0/0 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E4-B3-812ddca6-d4dd-4aae-96e4-23081ce78aa9.json>) |
| E4 | P1 | T | T/T | T/T | F | T | F | 0/0 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E4-P1-8e566c78-e0c7-48cd-9fbb-e006d08b26ab.json>) |
| E4 | P2 | T | T/T | T/T | F | T | T | 1/1 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E4-P2-8762dec8-bed9-49a2-8ca3-e04a7f03db12.json>) |
| E5 | B3 | T | T/T | T/T | F | T | F | 0/0 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E5-B3-a71f5501-a8c2-4a52-a97d-c3b2ef7f8a91.json>) |
| E5 | P1 | T | T/T | T/T | F | T | F | 0/0 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E5-P1-d55d99e9-f7ec-49fb-aa01-dfd3c4951cd0.json>) |
| E5 | P2 | T | T/T | T/T | F | T | T | 1/1 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E5-P2-96567d88-67dd-43be-ace1-a3b075f4680c.json>) |
| E6 | B3 | T | T/T | T/T | T | T | F | 0/0 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E6-B3-aa62be6e-3d7e-4f4c-bbf0-b17e5c7a8af8.json>) |
| E6 | P1 | T | T/T | T/T | T | T | F | 0/0 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E6-P1-09c04153-bed2-4809-b9b8-d391b633b5ba.json>) |
| E6 | P2 | T | T/T | T/T | T | T | T | 2/2 | [trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E6-P2-9d02f2fb-eca3-4b25-84ee-0b2a07e9701a.json>) |

[Raw CSV](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/exploratory-outcomes.csv>) · [Descriptive paired summary](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/exploratory-summary.json>) · [Manifest](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/manifest.json>) · [Offline verification](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/offline-verification.json>)

## 5. Comparisons and first relevant mechanisms

| Fixture | First relevant mechanism | Observed comparison |
|---|---|---|
| E1: stale claim after verification | B3 synthesis-input current-revision check (`b3-scope`); P1/P2 claim authorization revision check (`stale-intent-revision`). Both return 409 before stale publication. | All three correctly update. Business and safety tie. B3's verification is a pre-correction milestone; its ordinary scheduling path remains unchanged. No additional protection is demonstrated here. |
| E2: version-only resource change | P1/P2 STARTED revalidation rejects `fresh-evidence-required` (409). B3's existing revision check permits STARTED (202); its pre-publication verification remains intact. | B3's statement is factually true but its evidence is no longer version-applicable. P1/P2 lack decisive accepted playback testimony, so exposure is UNKNOWN. All three next encounter provider version conflict, reconcile ABSENT, and retain PROVIDER_CONFLICT handoff. Business completion ties at failure. |
| E3: delayed decisive progress | Shared revision acceptance stops old audio; uniform capability check limits durable repair to P2. | All three correctly update. P2 persists one obligation and explicitly retracts. B3/P1 retain ordinary corrections without repair rows or ACK transaction failure. Exact retries and lower-progress late ACKs are safe. The recorded decisive client timestamp precedes acceptance, so it is not post-acceptance stale exposure. |
| E4: restart before repair delivery | PostgreSQL discovery/lease and ordinary verification/permit publication gates. Replay supplies no obligation ID to the restarted worker. | P2 autonomously publishes the persisted repair; B3/P1 ordinary updates also complete. Business/update tie. This demonstrates automatic repair publication, conditional on available current evidence, not autonomous listener playback or all business processing. |
| E5: missing COMPLETED and reconnect | Completion requires full acknowledgement; publication and STARTED cannot satisfy repair. | At the missing-ACK checkpoint all updates are UNKNOWN and P2 remains REPAIR_AUTHORIZED/pending. Logical reconnect supplies duplicate-safe completion. All update correctly; P2 explicitly retracts and closes its obligation. |
| E6: another revision during repair | Shared revision stop; P2 retargets pending obligations, and completion checks current revision/repair claim ID. | All three retain scripted incompatible r2 exposure after r3 acceptance, then correctly update to r3. P2's r2 completion closes neither r3 obligation. Both are OPEN at checkpoint, then complete using r3 repair. Already acknowledged words are not claimed to have been prevented. |

**Business correctness ties at 5/6 in each arm.** Correct final updates are five TRUE and one FALSE in B3; five TRUE and one UNKNOWN in P1/P2. P2 has four explicit-retraction TRUE results and five completed durable obligations. B3/P1 have no durable repair capability by design and still supply ordinary corrective updates.

E2 demonstrates an additional version-bound playback check. E3–E6 demonstrate additional durable correction accountability and delivery. P2 does not improve final business completion in this set. Passing tests and these selected races establish neither novelty nor population superiority, noninferiority or effect size.

## 6. Synthetic versus actual voice; recovery limits

**All revised executions are scripted tone semantic proxies.** They use typed intent, deterministic tone WAVs and logical client ACKs. No intelligible speech/forced-alignment trial was performed here. No human hearing or understanding is inferred. Historical v1 local voice evidence remains historical; it is not relabeled as new voice evidence. E5 is not a measured WebRTC disconnect or real browser reconnection.

`REPAIR_DELIVERY_ENABLED=true` starts the application's PostgreSQL repair consumer in the durable worker. Its bounded one-pass equivalent is `python -m apps.durable_worker.repair`; it discovers obligations itself. It uses leases and stable command IDs, resumes generated/queued segments, publishes through existing claim gates, and waits for client acknowledgements. Waiting/errors are durable. Deadline or exhausted delivery errors produce human handoff instead of invented speech completion. A stopped consumer makes worker readiness fail.

E4/P2 restarts worker PID **17200** as PID **19492** with recovery enabled. The OPEN obligation exists before restart. The new worker discovers and publishes it; scripted client completion later satisfies it. This proves unattended discovery/publication after process restart, conditional on a current PRESENT operation and applicable evidence. It does not prove uninterrupted media or automatic recovery of every business reconciliation job. Stable cached verification commands may remain UNKNOWN/stale until handoff rather than obtaining new authority; that conservative limitation remains.

New code was tested in isolated `readiness_v2`/`readiness_v2_truth` databases and services on ports 18000/18001/18002/18010. The existing application containers were not rebuilt to deploy these changes. Compose now enables the consumer when the revised worker is built.

## 7. Validation and retained unsuccessful attempts

| Check | Result |
|---|---|
| New remedy properties and PostgreSQL/HTTP integration | **42 passed**, 0 current failures: 21 unit/properties and 21 integration cases |
| Scoped unit/contract and Phase 1–5 PostgreSQL/simulator/UI read-model regression | **135 passed**, 0 failures |
| Final unit/contract rerun | **81 passed**, 0 failures |
| Resource-reuse assertion recheck | Two separate runs, **1 passed each**; diagnostics, not new research samples |
| Ruff | Pass |
| Strict mypy | Pass, **118 source files** |
| New empty-database migration round trip | Upgrade head → downgrade base → upgrade head; all three exit 0 |
| Offline revised verification | **18/18** slot accounting, trace/config/fixture/source hashes, actual audio bytes, independent regrading, checkpoints and label/permit invariance pass |
| Historical evidence | **273/273** hashes match; v1 archive and **267** historical executions verify |

The suites overlap; do not sum their totals as independent tests. The scoped regression plus remedy suite covers 156 distinct parameterized test cases. Existing FastAPI/httpx lifecycle deprecation warnings remain.

The first mixed regression attempt retained **22 failures**: one new assertion incorrectly expected FALSE for absent operation evidence (correct result UNKNOWN); subsequent failures included DB timeouts/HTTP 500s and a resource-reuse assertion while Docker restarted. A complete later regression passed; the resource-reuse case additionally passed twice. The first remedy collection also failed because unit/integration files shared a module basename; the integration file was renamed. The logs are retained.

Separate debugging manifests retain **27 executions**, including five harness failures: three incorrect provider-event query-column errors and two reschedule-chain rejections. The initial P2 r3 diagnostic also completed procedurally without a correct update and with pending repair. All remain saved. Six pre-fix late-ACK reproductions are separate again. None counts toward the planned 18 or Phase 8.

The old live P8/P9 generators and arm-dependent repair grader are not revised-instrument gates. Their source and results remain v1. This report does not claim the entire historical live-generator suite passed under the corrected semantic policy. The full campaign must adopt the revised instrument before admission. No UI component changed; scoped UI/API regressions pass.

[Validation logs](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/validation>) · [Separate diagnostic traces](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/debug>)

Commands executed:

```powershell
.venv\Scripts\python.exe -B -m research.remedies.preserve
.venv\Scripts\python.exe -B -m research.remedies.reproduce_late_ack
.venv\Scripts\python.exe -B -m research.remedies.runner
.venv\Scripts\python.exe -B -m research.remedies.runner --fixture E6
.venv\Scripts\python.exe -B -m research.remedies.validate
.venv\Scripts\python.exe -B -m research.remedies.validate --regression
.venv\Scripts\python.exe -B -m research.remedies.migrations
.venv\Scripts\python.exe -m ruff check --no-cache apps packages research database tests
.venv\Scripts\python.exe -m mypy
.venv\Scripts\python.exe -B -m pytest -q tests/unit tests/contract
.venv\Scripts\python.exe -B -m research.remedies.runner --planned
.venv\Scripts\python.exe -B -m research.remedies.verify
.venv\Scripts\python.exe -B -m research.remedies.summarize
.venv\Scripts\python.exe -B -m research.remedies.preserve --after
.venv\Scripts\python.exe -B -m research.pilot.runner --verify artifacts/phase-7-pilot/v1/pilot-c1cf3fdf4dda.json
# Historical archive: verify_freeze(..., check_workspace=False)
```

Exact validation evidence:

- [remedies-ad5dd683-9712-4c8a-8e19-9146cfbf5aa1.log](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/validation/remedies-ad5dd683-9712-4c8a-8e19-9146cfbf5aa1.log>)
- [regression-4d00fc42-58d3-4f38-be4a-092205423968.log](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/validation/regression-4d00fc42-58d3-4f38-be4a-092205423968.log>)
- [regression-f4b0d5bf-19a5-43c0-bc70-e3eb51e661cc.log](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/validation/regression-f4b0d5bf-19a5-43c0-bc70-e3eb51e661cc.log>)
- [resource-reuse-c5a8dec4-390d-4e4e-ba5a-d83cbbb13a5d.json](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/validation/resource-reuse-c5a8dec4-390d-4e4e-ba5a-d83cbbb13a5d.json>)
- [migrations-readiness_migrations_864429b8d6604a56b041d8c3b0d24651.json](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/validation/migrations-readiness_migrations_864429b8d6604a56b041d8c3b0d24651.json>)

## 8. Files changed, migrations and example traces

Migrations added: `0012_readiness_repair` (delivery leases/attempts/errors/index), `0013_readiness_capability` (repair capability trigger). Earlier migrations were not changed. The complete revised source and test inventory is archived.

- [apps/api_controller/phase1_service.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/api_controller/phase1_service.py>)
- [apps/api_controller/phase3_verification_service.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/api_controller/phase3_verification_service.py>)
- [apps/api_controller/phase4_audio_service.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/api_controller/phase4_audio_service.py>)
- [apps/api_controller/phase4_playback_service.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/api_controller/phase4_playback_service.py>)
- [apps/durable_worker/main.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/durable_worker/main.py>)
- [compose.yaml](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/compose.yaml>)
- [packages/speech_policy/phase4.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/packages/speech_policy/phase4.py>)
- [research/provider_simulator/main.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/provider_simulator/main.py>)
- [apps/durable_worker/repair.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/durable_worker/repair.py>)
- [database/migrations/versions/0012_readiness_repair_delivery.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/database/migrations/versions/0012_readiness_repair_delivery.py>)
- [database/migrations/versions/0013_readiness_repair_capability.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/database/migrations/versions/0013_readiness_repair_capability.py>)
- [research/fixtures/readiness_v2/fixtures.json](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/fixtures/readiness_v2/fixtures.json>)
- [research/oracle/readiness_v2.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/oracle/readiness_v2.py>)
- [research/remedies/__init__.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/remedies/__init__.py>)
- [research/remedies/migrations.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/remedies/migrations.py>)
- [research/remedies/plan.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/remedies/plan.py>)
- [research/remedies/preserve.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/remedies/preserve.py>)
- [research/remedies/provenance.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/remedies/provenance.py>)
- [research/remedies/reproduce_late_ack.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/remedies/reproduce_late_ack.py>)
- [research/remedies/runner.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/remedies/runner.py>)
- [research/remedies/runtime.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/remedies/runtime.py>)
- [research/remedies/summarize.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/remedies/summarize.py>)
- [research/remedies/validate.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/remedies/validate.py>)
- [research/remedies/verify.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/remedies/verify.py>)
- [tests/integration/test_phase4_postgres.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/tests/integration/test_phase4_postgres.py>)
- [tests/unit/test_phase4_playback_policy.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/tests/unit/test_phase4_playback_policy.py>)
- [tests/unit/test_readiness_v2.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/tests/unit/test_readiness_v2.py>)
- [tests/integration/test_readiness_v2_postgres.py](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/tests/integration/test_readiness_v2_postgres.py>)
- [docs/10_RESEARCH_REMEDIES_V2.md](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/docs/10_RESEARCH_REMEDIES_V2.md>)

Successful trace: [E4/P2 worker restart and completed repair](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E4-P2-8762dec8-bed9-49a2-8ca3-e04a7f03db12.json>). Expected rejection/unresolved trace: [E2/P1 freshness rejection and provider conflict](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/research-remedies/v2/planned/E2-P1-de788c41-0306-47b2-9d9c-ed7a1e9482e8.json>). Safety rejection and unresolved business completion remain separate outcomes.

## 9. Remaining Phase 8 blockers and verdict

1. Materialize and freeze **500 new independently specified inputs**, generator/speaker/audio clusters, applicability strata and complete comparison families. Six tone families and renamed IDs do not meet this gate.
2. Integrate the revised observable oracle into the full campaign driver; retire v1 repair scoring for new measurements; freeze primary/secondary endpoints and missingness rules.
3. Implement and validate the required main-study mixed-effects and censoring-aware survival/AFT analysis and its multiplicity/noninferiority design. Existing descriptive/observed-only analysis is insufficient. The exploratory summary deliberately makes no confirmatory inference.
4. Review/adopt the revised semantic/evidence definitions and create the corresponding new protocol/design freeze. No executable-contract conflict was found; the approved SQL UUID-default exception is retained. Inferential design decisions remain pending instead of being silently chosen from these outcomes.
5. Any claim about actual spoken-content exposure requires intelligible speech, appropriate alignment and real media/playback evidence. These protocol-proxy results cannot support that claim.

The revised implementation remedies and targeted exploratory work are complete. **Phase 8 readiness: NOT READY for the 500-case campaign until the remaining study-design, input and analysis gates pass.** The campaign remains unstarted. No superiority or novelty claim is made from tests or these selected exploratory cases.

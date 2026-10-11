# Phase 6 implementation report

Status: **Phase 6 complete. All required harness, coverage, replay and regression gates passed.** The closure manifest verifies 256 executions over 43 paired fixtures plus one auxiliary Redis repair witness. The final full Python suite passed 150 tests with zero failures and zero skips. No Phase 7 pilot or global protocol freeze has started. Earlier sections preserve development history; the closure section below is the current scope and evidence.

## Scope implemented

- Strict, hashed scenario cases, ten named timing boundaries (P0-P9), and deterministic fault placement. The catalog identifies the five mandatory high-risk phases and secondary phase coverage.
- Explicit B0, B1, B2, B3, P1, and P2 mechanism profiles. B0-B2 have live P3 drivers; B3/P1/P2 have live P1-P5 drivers. All arms share the P3 hidden-commit fault schedule.
- Durable reach/release barrier records, a response-loss fault occurrence linked to the reached P3 event, and an experiment-scoped operation filter for deterministic worker stepping amid unrelated queued jobs.
- An independent oracle that reads the externally scripted final intent, simulator append-only commit log, and client playback acknowledgements. It checks provider truth at both audio release and play. It does not read the controller's verifier result as truth.
- PostgreSQL run/case/execution, oracle, and metric records; an immutable JSON replay bundle with manifest, source and image hashes, normalized events, raw operation evidence, fault occurrence, simulator truth, oracle result, and metric rows. Offline verification recomputes hashes, oracle grades, metrics, and the paired summary.

## Files changed

- Research harness: `research/scenario_dsl/`, `research/arms.py`, `research/barriers/`, `research/oracle/`, `research/analysis/`, `research/run_store.py`, `research/runner/paired.py`, `research/runner/baselines.py`, and `research/replay/verify_phase6.py`.
- Experiment-only worker scoping: `apps/durable_worker/main.py` and `apps/durable_worker/phase2.py`.
- Tests and documentation: `tests/unit/test_phase6_research.py`, `tests/integration/test_phase6_postgres_and_paired.py`, `README.md`, `acceptance/traceability.csv`, and this report.
- Evidence: `artifacts/phase-6-replays/fd9fbec1-e084-4f92-b6be-0ac288f33873.json` (original gate) and `artifacts/phase-6-replays/59d024ed-9469-47c2-a1c5-7725bfdbfb66.json` (six-arm continuation).

## Migrations added

- `database/migrations/versions/0008_phase6_research_trace.py` adds simulator/scenario binding fields, durable named barrier rows, and scripted client playback acknowledgements.
- `database/migrations/versions/0009_phase6_baseline_events.py` adds ordered, trace-linked, hashed raw and normalized baseline provider observations.
- `database/migrations/versions/0010_phase6_research_arm.py` adds a nullable, constrained research arm to workflows. Normal workflows retain full repair. No prior migration was changed. Fresh temporary database upgrade, downgrade, and re-upgrade to `0010` passed at that step. The main project database on host port 15432 is now at `0011_phase6_b3_audio`.

## Invariants covered

- Each arm receives the same scenario fixture and P3 `AFTER_COMMIT_BEFORE_RESPONSE:1` response-loss placement hash; the six executions have isolated simulator truth logs.
- A hidden provider commit is `UNKNOWN` until reconciliation observes it. B0 stops without another provider write; B1/B2 use authoritative status before further writes.
- P1 and P2 publish only through a current revision-bound receipt and claim permit. B3's scripted baseline playback is recorded without a permit, preserving the intended profile distinction for this case.
- The oracle can reject an apparently permitted 4 PM claim when simulator truth still says 3 PM. Release-time truth and play-time truth are both checked.
- PostgreSQL stores correctness evidence and run metadata; Redis is not used by the Phase 6 oracle or schedule. Repetitions remain nested under one independent scenario key.
- P0-P9 controls use explicit reach/wait/release events. P1-P5 are connected to the live paired runner for B3/P1/P2; B0-B2 are connected at P3.

## Commands executed and results

- `python -m ruff format --check .`: 102 files formatted; `python -m ruff check .`: passed.
- `python -m mypy apps packages research`: passed across 75 source files.
- `python -m pytest -q`: **85 passed, 0 failed, 0 skipped**; four existing dependency/FastAPI deprecation warnings. Focused P8 ablation and experiment-mode guard tests passed.
- Alembic on a fresh temporary database: upgrade to `0010`, downgrade to `0009`, re-upgrade to `0010`: passed; temporary database removed. The main project database migration passed.
- Final six-arm P3 paired run and offline verifier: **6/6 executions completed, 1 independent scenario, identical fault placement, all replay hashes and oracle grades verified**. Bundle hash: `377fa5a33d666a3132e92d71730ef4b09dbff4f4ec06dd2a306ddeab23238133`.
- P1, P2, P4, and P5 each passed a three-arm live run and offline replay verifier. They exercise timing boundaries but do not add independent semantic scenarios.
- Early diagnostic paired runs failed while the worker selected unrelated queued jobs and, later, while the runner stopped before the correction operation was created. A scoped experiment step and workflow-driven draining fixed those issues. A stale Compose image reference made `docker compose images` fail after rebuilding the migration image; digest capture now reads the running containers' immutable image labels. The final gate and verifier passed.

## Successful trace

Run `fd9fbec1-e084-4f92-b6be-0ac288f33873` used the same scripted 3 PM to 4 PM correction and P3 response-loss schedule for B3, P1, and P2. The simulator recorded exactly two commits per arm: CREATE then RESCHEDULE. The independent oracle found one confirmed 4 PM appointment and no unsupported audible confirmation in each arm. P1 and P2 each had a current claim permit; B3's baseline speech record did not. All three final correction-success metrics were 1/1; these are three executions of **one** scenario, not three independent scenarios.

The continuation run `59d024ed-9469-47c2-a1c5-7725bfdbfb66` added B0-B2 with the same schedule. B1 cancelled the observed 3 PM commit and created 4 PM (three simulator commits). B2, B3, P1, and P2 reached 4 PM (two commits each). The independent oracle returned correction success and no unsupported confirmation for these five arms.

## Expected fault and failure traces

- In each P3 execution the first WRITE response was `AMBIGUOUS` after provider commit. B1/B2 and B3/P1/P2 used authoritative status evidence before correction; B0 stopped. The replay bundle includes raw observations, the durable fault/barrier link, and independent truth logs.
- B0 received the ambiguous first response and persisted `REQUEST_SENT`, `PROVIDER_RESPONSE`, `UNRESOLVED_STOP`. It made no second provider write and emitted no decisive playback. The oracle reported correction success=false and outcome coverage=false, with one 3 PM commit. An earlier exploratory diagnostic bundle attempted a blind retry; it is superseded and excluded from results because it violated reconcile-before-retry.
- `test_oracle_disagrees_with_a_permitted_claim_when_provider_truth_disagrees` gives the oracle an apparent 4 PM claim with a permit ID while the simulator truth contains only the 3 PM appointment. It reports `unsupported_confirmation=true`, `correction_success=false`, and `safe_resolution=false`. The permit cannot override external truth.

## Known limitations

- This gate uses a **scripted transcript and scripted playback acknowledgement**. It records an audio fixture hash but does not stream that audio through STT, intent, or TTS in the Phase 6 run. Phase 5 separately validated the local cascaded voice path; this run makes no acoustic accuracy claim.
- B0-B2 live drivers cover P3 only. B3/P1/P2 now cover P0-P9 through the paired correction and audio runners. The secondary catalog varies timing boundary rather than all scenario dimensions.
- One P3 scenario and one P8 scenario cannot estimate effect sizes or establish clean-case non-inferiority. Clean-task and latency analysis remain to be added before the pilot.
- The repository has no Git commit. The manifest records `uncommitted:<source-tree-hash>` plus active Docker image digests, so it is integrity-checkable but not yet tied to a committed revision.

## Deferred work

- Add semantically varied covering fixtures across revision, action, workflow, acoustic, provider, speech, and fault dimensions.
- Add clean-task non-inferiority and latency/censoring metrics and broader paired replay before the Phase 7 pilot and freeze.

## Contract ambiguity requiring human decision

The B0 research description calls for an ordinary tool agent with best-effort cancellation, while the global safety rule forbids another external write after an ambiguous timeout until reconciliation proves it safe. In this P3 lost-response case B0 has neither an appointment ID nor status lookup in its mechanism profile. The safe measured behavior is UNKNOWN-stop. A future B0 cancellation experiment needs a separately specified provider capability or revised baseline definition; it must not be a blind retry.

No new executable-contract conflict was found. The previously approved UUID exception remains: authoritative SQL keeps `gen_random_uuid()` defaults rather than AGENTS.md's sortable UUID preference. UI mutation and streaming route gaps remain documented in `docs/06_SOURCE_CONFLICT_REPORT.md`.

## P8 live witness preceding the paired ablation

- Scope: a **P2-only live P8 witness**, separate from the paired arm results. The Phase 4 replay now saves the exact submitted client STARTED, PROGRESS, INTERRUPTED, and COMPLETED requests, correction time, and corrected segment text. `research/oracle/p8_witness.py` grades the partial stale span and fully heard correction against the independent simulator truth log and the externally specified 4 PM intent. It ignores the controller's repair-state label.
- Files added or changed: `research/replay/phase4_p8.py`, `research/replay/phase6_p8_witness.py`, `research/oracle/p8_witness.py`, `tests/integration/test_phase6_postgres_and_paired.py`, `README.md`, and this report. No migration was added for this witness; the six-arm P3 migration remains `0009`.
- Commands: rebuilt the current API, durable worker, voice worker, and migration images after Docker's older migration image failed to locate `0009`; the rebuilt services became healthy. The live P8 replay and P2 witness passed. The full 83-test suite, Ruff, and mypy passed. A separate offline verifier recomputed the final witness grade and bundle hash.
- Successful trace: `artifacts/phase-6-replays/p8-p2-witness-28a76a44-42f4-4b4c-88e5-d6322844178a.json` records 500 ms / 8000 frames of the 3 PM claim, an interrupted segment, and complete 3240 ms / 51840 frames of the corrected 4 PM repair. Independent simulator truth ends with one confirmed 4 PM appointment. Oracle results: correction_success=true, played_span_repair_complete=true. Bundle hash: `12f631db727d286b77e707b18cfcc5784012c22b76f145e83c0abff10ff12c8c`.
- Expected failure checks: changing only `repair_played.state` to OPEN leaves the oracle grade unchanged; reducing the client's completed frame count makes repair completion false; changing the simulator's final appointment time makes correction success false.
- Limits: this witness is one P2 execution, not a paired comparison or an effect estimate. The later P1/P2 run below adds arm-scoped repair behavior and a named P8 barrier. The exact expected repair text is fixture-specific; the oracle does not establish phonetic fidelity of the generated WAV.

## P8 P1/P2 paired ablation continuation

- Scope and invariant: synthetic workflows now pin an explicit research arm only when `EXPERIMENT_MODE=true`. Null-arm production workflows retain durable repair. P1 keeps revision-bound permits and playback tracking but omits the played-span repair obligation; P2 creates and completes it. Both receive the same correction WAV and a named P8 barrier bound to the client's PROGRESS event at 500 ms / 8000 frames. The run stores barriers, fault occurrences, client acknowledgements, oracle outcomes, and metrics in PostgreSQL.
- Files: `database/migrations/versions/0010_phase6_research_arm.py`, `apps/api_controller/phase1_models.py`, `apps/api_controller/phase1_service.py`, `apps/api_controller/phase4_playback_service.py`, `compose.yaml`, `research/runner/p8_paired.py`, `research/replay/verify_p8_paired.py`, `research/replay/phase4_p8.py`, `research/oracle/p8_witness.py`, `research/analysis/metrics.py`, `research/run_store.py`, `tests/unit/test_phase6_research.py`, `tests/integration/test_phase6_postgres_and_paired.py`, `README.md`, and this report.
- Commands and tests: `docker compose up -d --build --wait api-controller durable-worker voice-worker` passed. Migration `0010` passed fresh upgrade/downgrade/re-upgrade. `python -m research.runner.p8_paired` and the separate offline `python -m research.replay.verify_p8_paired` passed. The full Python suite passed **85/85**; Ruff format/lint and mypy passed. The experiment-mode guard rejects arm-tagged fixture creation outside experiment mode.
- Successful paired trace: `artifacts/phase-6-replays/p8-paired-18abd454-6efb-4d88-ab03-b63c3233057e.json` has two executions of one scenario. Both used partial 3 PM playback and ended with one confirmed 4 PM appointment. P1 had no `RepairRequired` event and no completed repair; P2 had one obligation and `REPAIR_PLAYED`. The independent oracle graded played-span repair complete as P1=0, P2=1. This is a mechanism check, not an effect-size estimate. Bundle hash: `0c748422ad080496f4a3ad13233b93f9c7f51d8a9b3222f8efd424bb956bdddc`.
- Expected failure checks: mutating the replay's final simulator truth while recomputing its bundle hash makes the offline oracle reject the saved grade. An incomplete client frame acknowledgement also makes the P8 repair witness fail. Merely changing a controller repair-state label does not change the independent witness grade.
- Database correction: a host Alembic command initially used the repository fallback URL on port 5432. That separate local database was at `0002`; the unintended migrations were reversed after confirming their new tables were empty. Its original 20 operations and 34 workflows remained, and it is back at `0002_phase1_commands`. The intended project database on 15432 advanced from `0010` to `0011` in the continuation below. The README now requires an explicit host `DATABASE_ADMIN_URL` for migration commands.
- Limits and deferred work: this historical **P1/P2** P8 ablation preceded the B3 adapter below. The acoustic input is a synthetic prerecorded fixture with scripted transcription, and one paired scenario cannot support inferential claims. P0/P6/P7/P9 live boundaries, diverse covering fixtures, clean-task non-inferiority, and latency/censoring analysis remain open. No new executable-contract conflict was found.

## P8 B3/P1/P2 paired continuation

- Scope: migration `0011_phase6_b3_audio` adds a durable `research_unpermitted` marker, a permit constraint, a B3-workflow trigger, and one-outcome-per-revision index. The API controller derives B3 speech from current provider facts and the deterministic text policy without creating a receipt or permit. Only experiment-tagged B3 workflows may create this scripted baseline audio. The voice worker synthesizes it through the same deterministic local TTS as P1/P2. Normal audio download and LiveKit transport reject marked B3 audio, keeping it from real callers. Production and null-arm workflows remain permit-gated.
- Files changed: `database/migrations/versions/0011_phase6_b3_audio.py`, `apps/api_controller/phase6_b3_audio.py`, `apps/api_controller/phase6_routes.py`, `apps/api_controller/phase4_audio_service.py`, `apps/api_controller/main.py`, `apps/voice_worker/main.py`, `apps/voice_worker/scheduler.py`, `apps/voice_worker/livekit_transport.py`, `research/replay/phase4_p8.py`, `research/runner/p8_paired.py`, `research/replay/verify_p8_paired.py`, `research/oracle/p8_witness.py`, `research/run_store.py`, `tests/integration/test_phase6_postgres_and_paired.py`, `README.md`, `docs/06_SOURCE_CONFLICT_REPORT.md`, and this report. No earlier migration or frozen fixture was edited.
- Commands and tests: host Alembic upgraded the main project database on port 15432 to `0011`. A disposable PostgreSQL database passed fresh upgrade, downgrade to `0010`, and re-upgrade to `0011`, then was removed. `docker compose up -d --build --wait api-controller voice-worker` passed after the final guard. `python -m research.runner.p8_paired` and `python -m research.replay.verify_p8_paired` passed on the final code. Ruff lint/format and mypy passed. The final full Python suite passed **87 tests, 0 failed, 0 skipped**, with four dependency/FastAPI deprecation warnings.
- Successful trace: `artifacts/phase-6-replays/p8-paired-5e475cea-a5ea-482c-a6ba-af41ddda7a7a.json`, bundle hash `b4a2698c01ced78e696081c150f15e013cd561619e659339c7fccbac1efd9f46`. Three executions of **one independent scenario** shared the P8 500 ms / 8000-frame client-progress fault. All reached the corrected 4 PM simulator state. B3 used no receipt or permit and had no repair; P1 used permits and no repair; P2 used permits and completed one durable repair. The independent oracle graded played-span repair complete B3=0, P1=0, P2=1, and correction success true for all three.
- Expected failure traces: PostgreSQL rejects `research_unpermitted=true` on a P1 outcome even when claim and permit fields are cleared. A stale B3 revision cannot obtain synthesis text. Reusing a B3 command ID with changed request facts is rejected, and experiment mode disabled returns 404. Tampering with the saved simulator truth or B3 permit evidence makes the offline verifier reject the bundle.
- Remaining limits: B3 still reads current provider facts before synthesis and scripted client acknowledgement, while it deliberately lacks a durable claim permit and playback-time evidence recheck. This isolates the permit mechanism in P8 without treating B3 as production-safe. Prerecorded scripted transcription and deterministic tone TTS do not measure acoustic quality. The one P8 scenario does not provide an effect estimate. Diverse scenarios, clean-task non-inferiority, and latency/censoring analysis remain open. The research-only baseline exception to the user-level no-permit speech rule is documented in the source conflict report.

## P7 and P9 live paired playout continuation

- Scope: the same frozen correction WAV and B3/P1/P2 profile set now cross two additional live speech boundaries. P7 reaches a published first segment without a client playback event; accepting the correction cancels it with no repair obligation. P9 reaches a full client COMPLETED acknowledgement before correction; only P2 creates and completes a durable repair. Explicit durable reach/release barriers use the published segment ID for P7 and the client's completion event ID for P9. No migration was added, and no earlier migration or frozen fixture was edited.
- Files changed: `research/replay/phase4_p8.py`, `research/oracle/playout_witness.py`, `research/runner/playout_paired.py`, `research/replay/verify_playout_paired.py`, `tests/integration/test_phase6_postgres_and_paired.py`, `README.md`, `acceptance/traceability.csv`, and this report. The replay gained an optional P7/P9 boundary while preserving its default P8 behavior.
- Commands and tests: `python -m research.runner.playout_paired P7` and `P9` passed, as did `python -m research.replay.verify_playout_paired` for both saved bundles. The focused P7/P9/P8 integration tests passed **3/3**. Ruff lint/format and mypy passed. The full Python suite passed **89 tests, 0 failed, 0 skipped**, with four existing dependency/FastAPI deprecation warnings. A final oracle refinement removed arm-name dependence from the repair grade; both saved bundles reverified offline, the two focused P7/P9 integration tests passed again, and Ruff/mypy passed again. The full suite was not rerun after this focused oracle change.
- Successful traces: `artifacts/phase-6-replays/p7-paired-823fa9fc-80e8-45c4-ba65-a25925868c55.json` (hash `437c9cfa228f8cb1e2fb647105fad6df66b858bc65f98578f366b73b4d253251`) has safe resolution B3=1, P1=1, P2=1. `artifacts/phase-6-replays/p9-paired-0c4e96c1-d078-4c5c-b824-1f0cb971546b.json` (hash `12516ab29b8f32ef72b93616ffcca6d3ac0da6c29c7c417e0b28f27e6c97e433`) has P2 played-span repair complete and safe resolution, while B3/P1 have no repair. Each bundle contains three executions of **one independent scenario**.
- Expected failure traces: the oracle rejects a client playback acknowledgement for the P7 stale segment. Changing only the controller's P9 repair-state label does not change the independent grade. Tampering with simulator truth and recomputing the outer bundle hash causes offline verification to reject the saved oracle result. The verifier also rejects a mismatched barrier source or stored client acknowledgement.
- Known limits and deferred work: these are scripted audio/playback cases, not a physical acoustic assessment. P0 and P6 were added in the continuation below. The covering fixture catalog varies timing boundaries but not enough independent semantic dimensions for effect estimates. Clean-task non-inferiority and latency/censoring metrics remain. No new contract ambiguity was found.

## P0 pre-accept and P6 generated-audio continuation

- Scope: P0 records an explicit durable barrier while the workflow remains at revision zero with no provider operation, then accepts the corrected request as revision one. The simulator makes exactly one CREATE at the final intent. P6 stages a deterministic WAV as a durable `GENERATED` segment, without publication or client playback. Correction cancels that segment. B3 staging is experiment-only and carries the existing `research_unpermitted` database guard; P1/P2 staging uses a queued permit and the normal `prepare_audio` command. No migration was added, no earlier migration was altered, and no frozen fixture was edited.
- Files changed: `apps/api_controller/phase6_b3_audio.py`, `apps/api_controller/phase6_routes.py`, `apps/voice_worker/scheduler.py`, `apps/voice_worker/main.py`, `research/replay/phase4_p8.py`, `research/oracle/playout_witness.py`, `research/oracle/grade.py`, `research/scenario_dsl/catalog.py`, `research/runner/playout_paired.py`, `research/runner/paired.py`, `research/replay/verify_playout_paired.py`, `research/replay/verify_phase6.py`, `tests/integration/test_phase6_postgres_and_paired.py`, `README.md`, `acceptance/traceability.csv`, and this report.
- Commands and tests: rebuilt the API controller and voice worker with `docker compose up -d --build --wait`; the services became healthy. `python -m research.runner.paired --phase P0`, `python -m research.runner.playout_paired P6`, and their offline verifiers passed. The P6 verifier also reverified the older P7/P9 bundles after the versioned oracle extension. Focused P0/P6/P7/P9 and B3 staging tests passed **5/5**. Ruff lint/format and mypy passed. The full Python suite passed **92 tests, 0 failed, 0 skipped**, with four existing dependency/FastAPI deprecation warnings.
- Successful traces: `artifacts/phase-6-replays/be5a5f61-ecc8-4e8d-86eb-ba3efbd2ec38.json` (P0, hash `884e30fe15c14b4acb7003ea6d59a56b35d00367e5cc8c44d5ed5e2528e67b9a`) has one final-intent CREATE per arm and no accepted original revision. `artifacts/phase-6-replays/p6-paired-bbc38849-55cc-4c1a-952c-d52b29f6dbb2.json` (P6, hash `43379afb0a1f8d4019ad4fc658055667bc06879382625201a4da1a818ef511de`) has generated, unpublished stale audio cancelled by correction in all three arms. Each bundle contains **one independent scenario** with three arm executions.
- Expected failure traces: the P0 verifier rejects a tampered pre-accept revision even if the outer bundle hash is recomputed. The P6 verifier rejects a publication timestamp or stale client playback at the generated-audio boundary. B3 stage replay returns the original command receipt; a changed request with the same command ID, a fresh stale-revision command, and an experiment-disabled request are rejected.
- Known limits and deferred work: P0 and P6 are scripted clean-acoustic examples, not timing distributions. All ten named boundaries now have live B3/P1/P2 paths, but semantic scenario diversity, clean-task non-inferiority, and latency/censoring analysis remain. B0-B2 remain P3-only. No new contract ambiguity was found.

## Correction-to-outcome latency and censoring continuation

- Scope: Phase 6 paired P0-P5 bundles now record an observation end timestamp for every arm and derive correction-to-playback duration from the scripted correction and client playback acknowledgement. An arm without decisive playback is right-censored at its observation end. Paired analysis clusters repetitions under the scenario key and counts censored pairs explicitly. It reports an observed-only mean difference, with a bootstrap interval only when at least two independent observed pairs exist. This is a descriptive diagnostic, not a survival estimate or an inferential claim from one scenario.
- Files changed: `research/analysis/latency.py`, `research/runner/paired.py`, `research/runner/baselines.py`, `research/replay/verify_phase6.py`, `tests/unit/test_phase6_research.py`, `tests/integration/test_phase6_postgres_and_paired.py`, and this report. The paired runner manifest now records `phase6-paired-runner-v3` and `phase6-correction-latency-v1`. No migration was added, no earlier migration or fixture was altered, and no Phase 7 work began.
- Invariants: playback must occur within the recorded observation window; missing playback stays censored rather than receiving an invented latency; repeated executions do not become independent scenarios; the offline verifier recomputes each latency and the paired summary and rejects tampering even when the outer bundle hash is recomputed. Earlier replay bundles without the latency field remain verifiable. Two intermediate latency bundles made before the final analysis version were retained under `artifacts/phase-6-diagnostics/` rather than presented as current replays.
- Commands and tests: `docker compose up -d --build --wait` returned all required services healthy. `python -m research.runner.paired --phase P3 --all-arms` and `python -m research.replay.verify_phase6` passed on the final bundle. Ruff format/lint and mypy passed. The full Python suite passed **94 tests, 0 failed, 0 skipped**, with four existing dependency/FastAPI deprecation warnings. After the final analysis version stamp and tamper assertion, the focused Phase 6 unit tests passed **18/18** and the live six-arm integration test passed **1/1**; Ruff and mypy passed again.
- Successful trace: `artifacts/phase-6-replays/184b8c5f-78e5-44d6-ac56-bead773546d4.json` (bundle hash `ea0a3d3733b29246294320d23a0f3dd6d2ceb391ae0ec3ece77fd7b9966d1902`) contains six arm executions of **one independent P3 scenario**. B1, B2, B3, P1, and P2 reached the final appointment and played an outcome. Their observed latency differences versus B3 are present in the bundle, while every bootstrap interval is null because there is only one independent scenario.
- Expected failure trace: B0 stopped after the ambiguous provider response and made no outcome claim. Its latency row is censored and the B0-versus-B3 pair has `observed_pairs=0`, `censored_pairs=1`, and no mean difference. The integration test changes the saved B0 duration, recomputes the outer hash, and confirms that offline verification still rejects the inconsistent evidence.
- Known limitations and deferred work: scripted playback timestamps are not measured physical hearing or acoustic quality. The current metric covers correction-to-decisive-playback on the paired P0-P5 runner; P6-P9 playout bundles use a separate trace shape. Observation windows differ by arm because each arm finishes at a different time. Full latency endpoints, a censor-aware resolution-time model, clean-task non-inferiority, and semantically varied scenario fixtures remain before Phase 6 can be closed. No new contract ambiguity requiring human decision was found.

## Non-atomic provider capability continuation

- Scope: a second P3 scenario declares a provider without atomic reschedule and runs the same hidden-commit response-loss barrier under B3, P1, and P2. The live runner passes the declared capability into the simulator. Each arm reconciles the first CREATE, compensates with CANCEL, and creates the corrected appointment. The fixture hash and scenario key distinguish this from the atomic-reschedule case. The CLI command is `python -m research.runner.paired --phase P3 --compensation-case`.
- Files changed: `research/scenario_dsl/models.py`, `research/scenario_dsl/catalog.py`, `research/runner/paired.py`, `research/replay/verify_phase6.py`, `tests/unit/test_phase6_research.py`, `tests/integration/test_phase6_postgres_and_paired.py`, and this report. No migration or earlier fixture changed. B0-B2 are rejected for this case because their non-atomic live drivers are not implemented; no silent baseline behavior substitution occurs.
- Invariants: the provider capability is validated as an explicit scenario value; all three compared arms receive the same P3 response-loss schedule; offline verification requires the simulator truth action sequence `CREATE, CANCEL, CREATE`; the independent oracle requires one active appointment at the corrected final intent and no duplicate logical effect.
- Commands and tests: the compensation CLI run and `python -m research.replay.verify_phase6` passed. The focused unit and live integration tests passed **20/20** after this change. Ruff lint and mypy passed. The final full Python suite passed **96 tests, 0 failed, 0 skipped**, with four existing dependency/FastAPI deprecation warnings.
- Successful trace: `artifacts/phase-6-replays/5653fb97-d157-46a8-9e24-f6094efcee44.json` (hash `77b5adf60a0813dcfd27a29310ae71d53ca367f9442a8e0438d8e2ec01cd6f5b`) passed offline verification with three arms and **one independent non-atomic scenario**. Each simulator truth log has exactly the three declared actions and ends with one confirmed 4 PM appointment.
- Expected failure trace: the integration test changes the stored CANCEL action to RESCHEDULE and recomputes the outer bundle hash. The offline verifier rejects it because the truth sequence no longer matches the declared non-atomic capability.
- Known limitations and deferred work: this adds provider-capability variation but still uses scripted clean audio, one ticket, one parameter correction, immediate visibility, and one response-loss fault. The separate clean-task non-inferiority endpoint, broader scenario covering array, and censor-aware analysis remain. No new contract ambiguity requiring human decision was found.

## Clean-task endpoint continuation

- Scope: a separate clean fixture accepts one initial booking intent, makes one provider CREATE, and records a scripted outcome playback acknowledgment under B3, P1, and P2. A generated English WAV fixture is hashed and versioned for the clean script. The independent clean oracle reads simulator truth and playback evidence. `clean_task_success` requires one correct confirmed appointment and useful supported decisive speech; a silent system cannot score success. P1/P2 use current receipt-bound claim permits; B3 remains an experiment-only synthetic baseline acknowledgement without a permit.
- Files changed: `research/scenario_dsl/models.py`, `research/scenario_dsl/catalog.py`, `research/fixtures/audio/clean_booking.wav`, `research/oracle/grade.py`, `research/analysis/metrics.py`, `research/run_store.py`, `research/runner/clean_paired.py`, `research/replay/verify_clean_paired.py`, `tests/unit/test_phase6_research.py`, `tests/integration/test_phase6_postgres_and_paired.py`, `README.md`, and this report. No migration or earlier fixture changed; the Phase 7 pilot and freeze were not started.
- Invariants: PostgreSQL stores the run, case, execution, oracle, playback, and metric rows. The final-state oracle reads the simulator append-only truth log and externally specified intent, not controller verifier state. The offline verifier checks the clean audio bytes, manifest, one accepted revision, one CREATE, arm-specific permit distinction, oracle grade, metric rows, and paired summary. Repetitions remain clustered under the scenario key.
- Commands and tests: `python -m research.runner.clean_paired` and `python -m research.replay.verify_clean_paired` passed on the final bundle. The full Python suite passed **99 tests, 0 failed, 0 skipped** with four existing deprecation warnings before the WAV header correction. The final 22,050 Hz mono WAV has an exact 93,434-frame header and SHA-256 `81674090c5697f0578ce42d416f7215343c01f72f047a1ec9c4a57862b1b0163`; the replay was regenerated and independently verified after that correction. The focused unit and live integration tests then passed **23/23**. Ruff format/lint and mypy passed on the final tree.
- Successful trace: `artifacts/phase-6-replays/clean-paired-d7df3656-45c7-490c-83a6-6c7e07d6b408.json` (hash `3b29d0f4472d1ec7cb1662e75e79a70b7004971646983982fbdfcaf9d352c669`) verified three arm executions of **one independent clean scenario**. B3, P1, and P2 each had one CREATE, one correct active appointment, and a supported outcome acknowledgement. The descriptive P1/B3 and P2/B3 risk differences are zero. Their confidence intervals and non-inferiority conclusion remain unset with one scenario and no frozen margin.
- Expected failure trace: the unit oracle grades a correct provider state with no audible outcome as `clean_task_success=false`; it also rejects a spoken target contradicted by provider truth. The integration test changes the simulator appointment time and recomputes the outer bundle hash; offline verification rejects the saved oracle result.
- Known limitations and deferred work: this Phase 6 runner uses a scripted transcript and scripted client playback acknowledgement. The WAV is a reproducible fixture, but the paired run does not stream it through STT or measure acoustic recognition. One clean scenario is not an inferential non-inferiority study. The margin, exclusions, and confirmatory sample remain for Phase 7 protocol freeze. Broader revision, workflow, acoustic, provider-visibility, speech-exposure, and fault-family coverage also remains. No new contract ambiguity requiring human decision was found.

## Delayed provider visibility continuation

- Scope: a distinct P3 scenario combines the hidden-commit response-loss fault with a provider that returns non-authoritative `UNKNOWN` for its first two status and resource reads. B3, P1, and P2 use the same named barrier and visibility setting. The runner preserves the scenario in the manifest and rejects B0-B2 for this variant because their delayed-visibility drivers are not implemented.
- Files changed: `research/scenario_dsl/models.py`, `research/scenario_dsl/catalog.py`, `research/runner/paired.py`, `research/runner/clean_paired.py`, `research/replay/verify_phase6.py`, `tests/unit/test_phase6_research.py`, `tests/integration/test_phase6_postgres_and_paired.py`, `README.md`, `docs/08_PHASE6_COVERAGE_MATRIX.md`, and this report. No migration or earlier fixture changed.
- Invariants: the first write has one durable effect despite the lost response; at least two reconciliation reads remain `UNKNOWN`; an authoritative `PRESENT` observation precedes the linked RESCHEDULE; the simulator truth has exactly `CREATE, RESCHEDULE`. The offline verifier checks the original operation's stored write and lookup attempts, then recomputes the independent oracle and metrics.
- Commands and tests: `python -m research.runner.paired --phase P3 --delayed-visibility-case` and `python -m research.replay.verify_phase6` passed on the saved bundle. Focused unit and live integration tests passed **24/24**. Ruff lint and mypy passed. The final full Python suite passed **102 tests, 0 failed, 0 skipped**, with four existing dependency/FastAPI deprecation warnings.
- Successful trace: `artifacts/phase-6-replays/7c6eee58-188d-439d-9448-2a659caee294.json` (hash `ac7cf476840c151558debe8e475a51f32d5af06db3882e5d70451f22d7484a48`) verified three arms of **one independent delayed-visibility scenario**. Each arm recorded four `UNKNOWN` worker steps across the two operations, then ended with one confirmed corrected appointment and no duplicate logical effect.
- Expected failure trace: the integration test changes the first stored non-authoritative status result to `PRESENT`, recomputes the outer bundle hash, and confirms that offline verification rejects the claimed delayed-visibility sequence.
- Known limitations and deferred work: this case adds one provider-visibility level but still uses a scripted transcript, one ticket, visibility after two reads, and one response-loss fault. The [coverage matrix](../docs/08_PHASE6_COVERAGE_MATRIX.md) names the still-missing live dimensions without treating labels as evidence. The broader secondary covering array, other workflow shapes, acoustic conditions, and fault families remain. No new contract ambiguity requiring human decision was found.

## Pre-commit provider delay continuation

- Scope: a distinct P2 case configures the simulator's `DELAY` fault at `BEFORE_COMMIT:1` and holds that named barrier while revision two is accepted. B3, P1, and P2 run the same hashed case and placement. The simulator now enforces that a configured delay actually reaches a held barrier before mutation proceeds. This uses the same named-barrier mechanism as the P2 timing experiment; it is one controlled pre-commit delay scenario, not an independent latency distribution.
- Files changed: `research/provider_simulator/main.py`, `research/scenario_dsl/models.py`, `research/scenario_dsl/catalog.py`, `research/runner/paired.py`, `research/replay/verify_phase6.py`, `tests/unit/test_phase6_research.py`, `tests/integration/test_phase6_postgres_and_paired.py`, `README.md`, `docs/08_PHASE6_COVERAGE_MATRIX.md`, and this report. No migration was added or altered, and no frozen fixture was edited.
- Invariants: the configured simulator fault targets the first pre-commit request; the barrier is reached and held; simulator truth has no commit while held; the correction is accepted before release; the first commit timestamp follows release; and the final independent truth sequence is exactly `CREATE, RESCHEDULE` with one corrected appointment. The offline verifier checks these facts plus the existing claim, metric, and bundle hashes.
- Commands and tests: `docker compose up -d --build --wait provider-simulator` returned healthy. `python -m research.runner.paired --phase P2 --provider-delay-case` and `python -m research.replay.verify_phase6` passed. The focused live integration test passed **1/1** and Phase 6 unit tests passed **24/24**. Ruff lint/format and mypy passed. The full Python suite passed **104 tests, 0 failed, 0 skipped** in 6m29s, with four existing dependency/FastAPI deprecation warnings.
- Successful trace: `artifacts/phase-6-replays/764beb0d-02b4-4c6d-8e8e-722a2119953e.json` (hash `b78d4d40a98781b2de1eb08bf970758c591a003fb3852616c1f74c75da77123d`) passed offline verification for three arms of **one independent scenario**. Every arm reached the held barrier with no provider commit, then completed the corrected appointment after release.
- Expected failure trace: the integration test inserts a fictitious pre-release commit into the saved delay evidence, recomputes the outer bundle hash, and confirms the offline verifier rejects the claim. A `DELAY` rule without its named held barrier is rejected by simulator configuration validation.
- Known limitations and deferred work: delay is controlled by an explicit named barrier, so this case does not estimate natural provider latency. The next section adds pre-commit provider refusal; conflicting changes, partial effects, Redis loss, broader revision and workflow shapes, and acoustic variation remain uncovered. B0-B2 still have only P3 live drivers. No new contract ambiguity requiring human decision was found; Phase 7 has not started.

## Pre-commit provider refusal continuation

- Scope: a distinct P2 case injects simulator `RETURN_5XX` on the first request before commit while the named pre-commit barrier holds the request for the correction. The B3, P1, and P2 arms use the same hashed case and fault placement. The worker treats the 503 response as `UNKNOWN`, performs status and resource reconciliation, and creates the corrected booking only after authoritative `ABSENT` evidence.
- Files changed: `research/scenario_dsl/models.py`, `research/scenario_dsl/catalog.py`, `research/runner/paired.py`, `research/replay/verify_phase6.py`, `tests/unit/test_phase6_research.py`, `tests/integration/test_phase6_postgres_and_paired.py`, `README.md`, `docs/08_PHASE6_COVERAGE_MATRIX.md`, and this report. No migration was added or altered, and no frozen fixture was edited.
- Invariants: the first provider write returns HTTP 503 and makes no simulator commit; the first operation has exactly one write and an authoritative `ABSENT` reconciliation result; that observation precedes the corrected CREATE request; and the simulator truth contains exactly one CREATE for the final intent. The offline verifier checks the configured fault, barrier snapshots, attempt records, time ordering, independent oracle, metrics, and bundle hashes.
- Commands and tests: `python -m research.runner.paired --phase P2 --provider-refusal-case` and `python -m research.replay.verify_phase6` passed. The focused unit and live integration tests passed **2/2**. Ruff lint/format and mypy passed after a formatting correction. The full Python suite passed **106 tests, 0 failed, 0 skipped** in 3m47s, with four existing dependency/FastAPI deprecation warnings.
- Successful trace: `artifacts/phase-6-replays/8248e1d3-ea8b-48a2-a045-466b5ece25db.json` (hash `f030929890b5fca6bf5ff9496d4c790885c2b350dbd745ba7bb88fca85ed5539`) passed offline verification for three arms of **one independent scenario**. Every arm recorded a first-write 503, an authoritative absence read, and one final corrected CREATE.
- Expected failure trace: the integration test changes the saved absence read to non-authoritative and recomputes the outer bundle hash. Offline verification rejects the claimed safe follow-up write. A provider refusal assigned to P3 is rejected by scenario validation.
- Known limitations and deferred work: one pre-commit refusal does not cover after-commit 5xx, conflicting concurrent changes, partial effects, Redis loss, or unavailable provider evidence. Acoustic input remains scripted and B0-B2 remain P3-only. No new contract ambiguity requiring human decision was found; Phase 7 has not started.

## Permanently unavailable provider evidence continuation

- Scope: a distinct P3 case combines hidden-commit response loss with status and resource endpoints that remain unavailable. B3, P1, and P2 receive the same hashed scenario and fault placement. The paired runner can now end at a durable handoff while preserving the independent oracle's correction-failure result. The runner version is `phase6-paired-runner-v4`.
- Files changed: `research/scenario_dsl/models.py`, `research/scenario_dsl/catalog.py`, `research/runner/paired.py`, new `research/runner/handoff_evidence.py`, `research/replay/verify_phase6.py`, `tests/unit/test_phase6_research.py`, `tests/integration/test_phase6_postgres_and_paired.py`, `tests/unit/test_phase5_local_voice.py`, `README.md`, `docs/08_PHASE6_COVERAGE_MATRIX.md`, and this report. No migration was added or altered, and no frozen experiment fixture was edited.
- Invariants: one original provider write and one hidden CREATE; eight non-authoritative UNKNOWN reconciliation observations with HTTP 503 from both read endpoints; no corrected operation or follow-up write; an OPEN review handoff with the UNKNOWN effect fact and original operation link; no claim, permit, audio segment, or playback. A historical-effect verification receipt remains UNKNOWN and its claim request is rejected with RFC 9457 problem details and a trace ID. Controller rows are mechanism evidence only; the oracle still reads external intent, independent simulator truth, and playback.
- Commands and tests: started Docker Desktop in the background, then `docker compose up -d --wait` returned required services healthy. `python -m research.runner.paired --phase P3 --unavailable-evidence-case` and `python -m research.replay.verify_phase6` passed. The Phase 6 unit tests plus focused PostgreSQL/live integration test passed **27/27**. Mypy passed on 84 source files and all three changed test modules; Ruff lint/format passed. The earlier refusal replay also reverified offline. The initial full run had **107 passed, 1 failed** because an older hallucinated-date unit test used October 3, 2026 at 3 PM and the live calendar had passed that time. That test now freezes its clock at October 1, 2026 to exercise model disagreement consistently; all five local voice unit tests passed after the fix. The final full Python suite passed **108 tests, 0 failed, 0 skipped** in 6m41s, with four existing dependency/FastAPI deprecation warnings. The completed source tree then generated a fresh replay, which passed offline verification. The earlier development replay was retained under `artifacts/phase-6-diagnostics/30ec976b-5d54-464e-a7c4-9d6e6cc71975.json`.
- Successful mechanism trace: `artifacts/phase-6-replays/7635e7e3-533e-4b68-b0eb-e6cea6543e05.json` (hash `160ddd4f65c9d6598ae636fef00bc8236eefbc5092763aa862a3d49ea0dbb20f`) verified three arms of **one independent scenario**. Every arm retained UNKNOWN, reached a durable handoff after eight reads, and withheld decisive speech. Correction success is **false** in all arms; the original 3 PM appointment remains in provider truth, and outcome latency is censored.
- Expected failure traces: the claim endpoint rejects the UNKNOWN receipt with HTTP 409 `receipt-not-applicable`. The integration test changes a saved read to authoritative ABSENT, changes the claim denial to HTTP 201, and adds a hidden second commit in three separate tampered bundles. Recomputing the outer hash does not make any of them pass offline verification.
- Known limitations and deferred work: one unavailable-evidence scenario does not cover stale evidence, provider recovery after handoff, conflicting concurrent changes, partial effects, Redis loss, or broader acoustic and workflow variation. The silent unresolved result has no successful-booking credit. B0-B2 still require additional live profiles. No new contract ambiguity requiring human decision was found; Phase 7 has not started.

## Provider version conflict after P5 continuation

- Scope: a new hashed scenario accepts the parameter correction after original verification at P5, then injects `CONFLICTING_CHANGE` before the second provider write commits. B3, P1, and P2 share the scenario and fault placement. A concurrent writer advances the original appointment from version 0 to 1; the linked RESCHEDULE still expects version 0 and receives HTTP 409. Separate durable barriers bind the correction to the original verification receipt and the fault to `BEFORE_COMMIT:2`. The runner version is `phase6-paired-runner-v5`.
- Files changed: `apps/durable_worker/phase2.py`, `research/scenario_dsl/models.py`, `research/scenario_dsl/catalog.py`, `research/barriers/schedule.py`, `research/runner/paired.py`, new `research/runner/conflict.py`, `research/runner/handoff_evidence.py`, new `research/replay/conflict_evidence.py`, `research/replay/verify_phase6.py`, `tests/unit/test_phase6_research.py`, `tests/integration/test_phase6_postgres_and_paired.py`, `tests/integration/test_phase2_postgres.py`, `README.md`, `docs/08_PHASE6_COVERAGE_MATRIX.md`, `acceptance/traceability.csv`, and this report.
- Migrations: none added or changed. No frozen experiment fixture was edited.
- Invariants: one original CREATE and one independent concurrent version change; one rejected reschedule write; authoritative ABSENT status evidence before durable handoff; no blind retry or overwrite; operation knowledge and handoff known facts preserve ABSENT while final intent resolution remains UNRESOLVED. The worker stores the observation, terminal operation state, and handoff in one PostgreSQL transaction. A VIOLATED receipt cannot authorize speech; no claims, permits, audio segments, or client playback are created. The independent oracle uses simulator truth rather than controller handoff state and reports correction failure with censored outcome latency.
- Worker correction: the first diagnostic run found that the existing conflict handoff retained UNKNOWN despite an authoritative ABSENT observation. The conflict branch now records ABSENT and distinguishes it from the unresolved final request. Crash tests at `BEFORE_LOOKUP`, `AFTER_LOOKUP`, and `AFTER_RECONCILIATION_RECORDED` verify recovery without another write or duplicate handoff.
- Commands and tests: `docker compose up -d --build --wait durable-worker` returned healthy. The focused Phase 6 unit, live conflict integration, and three worker crash tests passed **31/31**. Configured `.venv/Scripts/mypy.exe` passed on **86 source files**; Ruff lint and format checks passed on applications, packages, research, and tests (100 files formatted). The full `.venv/Scripts/python.exe -m pytest -q` passed **113 tests, 0 failed, 0 skipped** in 7m28s, with four existing dependency/FastAPI deprecation warnings. An exploratory mypy command that additionally included the entire test tree reported eight existing typing errors in three older integration test modules; tests are outside the configured mypy file set. After testing, `python -m research.runner.paired --phase P5 --provider-conflict-case` and the separate offline `python -m research.replay.verify_phase6` passed for all three executions of one independent scenario.
- Successful mechanism trace: `artifacts/phase-6-replays/406022d1-9177-4d61-9362-53b403e064d4.json` (hash `db8c3f89160aa0bb46736af2e9b1e8831ff679cfb4e2debe3aa6d303e8514757`) records original CREATE verification SATISFIED at version 0, P5 correction acceptance, the second-request barrier, preserved concurrent version 1, and one durable conflict handoff per arm. Every arm retains authoritative ABSENT for the rejected reschedule and emits no unsupported confirmation. Correction success remains **false**, rather than giving a handoff successful-booking credit. The earlier diagnostic run exposing the UNKNOWN defect is retained at `artifacts/phase-6-diagnostics/b2da0410-6e35-4bbf-bc05-0835cf8c70f6.json` and is excluded from final replay results.
- Expected failure traces: the claim endpoint rejects the VIOLATED receipt with HTTP 409 `receipt-not-applicable` and a trace ID. Three separately rehashed tampered bundles replace ABSENT with UNKNOWN, remove the concurrent version increment, or link the fault to the correction barrier; offline verification rejects each.
- Saved expected failure: P2 claim denial trace `07dffb24-a50a-49cc-a99e-87eb4c3dcb58` is linked to workflow `3d1d9f0f-a684-4ad8-adb3-b1dfeceb30a1` and rejected operation `1b7dbc7a-c21d-404d-9b78-c90217891185` in that bundle.
- Known limitations and deferred work at that checkpoint: the concurrent writer changes the resource version while retaining the original appointment time; it does not model every competing business change or another resource. User revision type remains PARAMETER_CORRECTION, so this fault does not cover a conflicting user-intent revision. Input and playback remain scripted; one paired scenario provides no effect-size estimate. Partial provider effects, Redis loss, stale evidence, broader revision/workflow/acoustic coverage, and B0-B2 parity were still open then. The closure below supersedes that backlog. Phase 7 has not started.

## Phase 6 closure — 2026-10-03

### Scope and exit criteria

- All six arms now have provider drivers at P0–P5, clean controls and isolated
  P6–P9 audio counterfactuals. B0/B1 use best-effort cancellation; B2 uses atomic
  reschedule or linked compensation; B3/P1/P2 use their recorded durable profiles.
- Five revision classes, read/cancel/reuse/replace semantics, two workflows with
  distinct tickets/resources, four provider visibility levels, two capabilities,
  generated/published/partial/full exposure and the declared fault families have
  live replay evidence. Named barriers replace timing sleeps.
- The secondary selection executes 20 of 70 valid candidate combinations and
  covers all 150 feasible pairs in its constrained domain. Acoustic/exposure/
  other fault levels are separately mandatory; this is not full-domain pairwise
  coverage or a Cartesian campaign.
- Actual Vosk, local Qwen and safe eSpeak output are captured in six acoustic
  fixtures. The accepted proposal comes from the measured model, never the oracle
  target. Raw/model/prompt/input hashes and timings are retained. One proposal is
  shared across paired arms to isolate protocol mechanisms.
- [Completion manifest](phase-6-completion/completion-0ce13a086fe0.json):
  **43 paired fixture checks + one auxiliary witness, 256 independently verified
  execution records**. Hash:
  `0ce13a086fe0452e5a3c77198c3f40a580624f07ddb4c33db59afa094bf42bff`.
  Counts describe harness fixtures/executions, not independent population draws.
  Original metric-v1 closure remains immutable; metric-v2 derivative records its
  parent hash and analysis source. Child source/image identities remain explicit.
- The P3 B3/P1/P2 paired exit criterion passed with identical placement. Offline
  verification regrades external final intent, simulator truth and playback,
  validates mechanism traces and recomputes primary/secondary metrics.

### Files changed and supported invariants

| Files | Invariant supported |
|---|---|
| `packages/domain/revision_policy.py`; `apps/durable_worker/phase2.py` | Pure revision decision; fresh resource evidence before reuse; PARTIAL/known absence remain distinct from UNKNOWN; linked cancellation/compensation; crash recovery |
| `apps/api_controller/phase1_service.py`; `phase3_verification_service.py` | A reused prior operation needs a fresh current-revision receipt and is superseded by later incompatible intent |
| `research/provider_simulator/store.py`; `scenario_dsl/models.py`, `catalog.py`, `covering.py` | Actual stale/partial faults; versioned revision/workflow/read fixtures; deterministic constrained coverage |
| `research/runner/paired.py`, `baselines.py`, `baseline_covering.py`, `baseline_audio.py`, `clean_paired.py`, `p8_paired.py`, `playout_paired.py` | Explicit arm mechanisms through shared provider/TTS interfaces; same fixtures and placement; no caller-facing unpermitted audio |
| `research/runner/redis_loss.py`, `acoustic.py`, `acoustic_source.py`, `completion.py` | Cache wipe/restart preserves PostgreSQL facts; actual cascade evidence; complete accounting and immutable child references |
| `research/replay/recovery_evidence.py`, `baseline_evidence.py`, `baseline_audio_evidence.py`, `verify_phase6.py`, `verify_clean_paired.py`, `verify_p8_paired.py`, `verify_playout_paired.py`, `phase4_p8.py` | Offline semantic verification, no fabricated claim/repair, scoped worker stepping, existing repair survives cache loss |
| `research/oracle/grade.py`, `p8_witness.py`; `analysis/completion_metrics.py` | Independent final-state truth; side-resource preservation; honest handoff safety separate from task/outcome credit; timestamp missingness and censoring |
| `tests/integration/test_phase6_completion.py`, `test_phase2_postgres.py`, `test_phase3_postgres.py`, `test_phase4_postgres.py`; `tests/unit/test_phase6_covering_selection.py`, `test_phase6_closed_replay.py` | Real PostgreSQL transition/crash/receipt tests; deterministic case coverage; semantic tamper rejection; test isolation from unrelated jobs |
| `.github/workflows/ci.yml`, `README.md`, `docs/06_SOURCE_CONFLICT_REPORT.md`, `docs/08_PHASE6_COVERAGE_MATRIX.md`, `acceptance/traceability.csv` | Redis gate available in CI; accurate scope, constraints, conflict decisions and traceability |

No migration was added in this closure. The Phase 6 migration set remains
`0008`–`0011`; no previous migration or source contract was altered.

### Commands and test results

- `docker compose up -d --build --wait api-controller durable-worker voice-worker provider-simulator`: required services healthy.
- Secondary live array: 20 cases × six arms = 120 verified executions.
- `python -m research.runner.completion`: mandatory and acoustic rows executed;
  successful child checkpoints reused only after offline verification.
- `python -m research.runner.completion --verify artifacts/phase-6-completion/completion-0ce13a086fe0.json`: all 256 execution records verified without services or new inference.
- Ruff format/lint passed; configured mypy passed **98 source files**.
- Focused completion integration/selection tests: **22 passed**.
- Final oracle and saved closure checks: **34 passed**; added semantic/model/handoff
  closure tests: **7 passed**.
- Full Python regression: **150 passed, 0 failed, 0 skipped** in 482.04 seconds
  (8m02s), with four existing dependency/FastAPI deprecation warnings. Results:
  [final test XML](phase-6-final-tests.xml). The first closure
  regression had 145 passed and two failed because single-resource unit fixtures
  lacked a resource key. Multi-resource key access is now conditional; both
  tests pass in the focused oracle run. Its XML is retained in
  `phase-6-diagnostics/closure-first-regression.xml`.
- Web ESLint, strict TypeScript and Vitest passed: **6 tests in 3 files**.
- Web Prettier format check passed. Final Python Ruff format check passed on
  129 files, Ruff lint passed, and configured mypy passed on 98 source files.
- Fresh disposable PostgreSQL: upgrade head → downgrade base → upgrade head
  passed; 38 public tables and head `0011_phase6_b3_audio` verified. Main data
  was preserved; the disposable database was removed. See
  [migration gate](phase-6-migration-gate.json).
- Earlier development failures (partial receipt expectation, reuse drain/receipt
  handling, read baseline stop handling, unrelated worker jobs, and baseline
  fixture-arm validation) were corrected and their failed run/ledger evidence
  retained. No frozen successful child was overwritten or silently substituted.

### Successful trace

[P8 six-arm replay](phase-6-completion/p8-paired-cd4a554e-fdef-4222-a065-ff0f391a068a.json),
P2 execution `481e3a3e-fb8f-4fad-ac66-9f2b176f893c`, workflow
`c1e30453-352e-46a8-8e7f-0b8d3275deae`: initial CREATE, acknowledged stale
500 ms/8000-frame span, correction accepted, reconciled RESCHEDULE, fresh permit,
explicit corrective text and full corrected acknowledgement. Independent
correction success, outcome coverage and repair completion are true; duplicate
effect and unsupported confirmation are false. Hash:
`ecef79cf94652b1cabf60cbd96cce6e94f365436145bfff63ae52cf565e9402c`.

The [recorded clean cascade](phase-6-completion/clean-paired-d9e7ea92-dc22-473c-a0f3-edf4e6d2b38b.json)
also succeeds under all six arms with the actual November 5, 3 PM model proposal.

### Expected failure trace

[Partial effect replay](phase-6-completion/d1ee5afc-e08c-418e-bdbf-09ffd2861c36.json),
P2 execution `e231b84e-e033-4f19-a7cf-1aec941bb35a`: simulator commits one
HELD/PARTIAL effect. Eight reconciliation reads retain PARTIAL, then create a
durable review handoff; no second write or decisive playback occurs. A VIOLATED
receipt cannot authorize speech: HTTP 409 `receipt-not-applicable`, trace
`b1ca2c88-8144-4f25-a1e1-05576626a0a0`. Booking success and outcome coverage are
false. Secondary safe-resolution v2 recognizes the honest durable handoff.

[Noisy input replay](phase-6-completion/clean-paired-975d37ac-8f28-4e4c-a9a5-a106a847781c.json)
loses the requested day during recognition; all six arms clarify, with zero
effects/claims and false task/outcome scores. This failure remains visible.

### Known limitations, conflicts and deferred work

- Five synthetic speech conditions still fail recognition. The harness exposes
  these failures safely; it does not establish acceptable voice accuracy. Model
  improvement and inspection of failures belong in the Phase 7 pilot.
- Audio-boundary checks use deterministic test TTS/client acknowledgements.
  Acoustic checks measure local recognition, proposal and non-decisive TTS.
  Neither establishes physical hearing/comprehension or natural speech quality.
- Retraction safely cancels the effect but withholds cancellation speech because
  the authoritative claim contract has no cancellation template. Conditional
  cancellation exposure is N/A (zero denominator), never a claimed perfect rate.
- Baseline audio is isolated counterfactual research evidence. Real calls and
  normal/null-arm workflows retain applicable permit checks.
- Latencies cover logical turn, accepted revision, dispatch, provider knowledge,
  verification, authorization, client playback and final resolution where the
  necessary timestamps exist. Missing/noncomparable observations are explicit;
  censored outcomes remain censored. No physical end-of-turn timestamp is inferred.
- P5 concurrent-version-conflict is a B3/P1/P2 verification ablation. B0–B2 lack
  the same proposed receipt boundary; their ordinary timing/fault drivers are
  exercised separately rather than given invented verification behavior.
- The old matrix's physical listener gate was corrected to authoritative optional
  RQ9. Historical completion-only safety rows remain immutable; v2 adds honest
  handoff credit without oracle substitution. The approved UUIDv4 SQL exception
  remains unchanged. No new ambiguity requiring a human decision remains.
- Phase 7's pilot, failure review, sample justification, non-inferiority margin,
  exclusions and global protocol freeze are deferred. Phase 8 population results,
  native-audio comparisons, phone transfer/dialer and application extensions have
  not been started. No paid API key is required to reproduce current local gates.

### Final disposition

Phase 6 is closed after the full regression and replay gates passed. The known
recognition failures are research outcomes retained in the harness, not skipped
tests or falsely credited bookings. Implementation stopped at Phase 6; no Phase
7 pilot, fixture freeze, new product feature or paid-provider setup was started.

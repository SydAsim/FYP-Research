# Research-readiness audit before Phase 8

Date: 2026-10-03. Verdict: **C — revise and version the protocol/design before Phase 8.**

Phase 7's execution, accounting and content-freeze gates pass. Those gates do not establish that the instrument validly measures every claimed research outcome. This audit found an arm-dependent repair grader, a partial-playback fixture that has not reached decisive words, a reachable repair-ablation leak, and a gap between the stated evidence-support endpoint and its implemented truth-only speech check. Repeating the current design 500 times would preserve these limitations.

The implementation and frozen pilot were kept read-only. Only this new audit report was created. No new scenario execution, dependency upgrade, system-arm modification, migration, fixture edit or Phase 8 campaign was performed. Proposed checks below have **not** been run.

## 1. Evidence inspected and verification performed

Read repository instructions, README, ordered UI/backend/data/API/evaluation/phased specifications, SQL/OpenAPI/event contracts, Phase 7 protocol, source implementing arms/runners/voice/claim/playback/repair/oracle/analysis/freeze, the frozen manifest, all child replay records, observation exports, all failure-review records, selected paired timelines, existing tests and historical reproduction evidence. The repository specifications extracted from the implementation pack govern this assessment.

Executed only existing offline verification and read-only data calculations, using Python `-B` to avoid bytecode writes:

```powershell
.\.venv\Scripts\python.exe -B -m research.pilot.runner --verify artifacts/phase-7-pilot/v1/pilot-c1cf3fdf4dda.json
.\.venv\Scripts\python.exe -B -m research.pilot.freeze artifacts/phase-7-pilot/v1/freeze-90901263019a.json --verify
```

Both passed. Independently iterating child execution rows reproduced the counts below. CSV contains 267 execution IDs matching the manifest; raw-count, paired-table and failure-review exports match their underlying manifest data. The freeze verifies the ZIP and the current 202-member executable inventory.

- Pilot hash: `c1cf3fdf4ddaa67417148191dae133896b347dce9db087db3cb997354de52a3e`.
- Freeze hash: `90901263019a6ebb1c4b4981b06279687618f9f2aeb00a52e69b45c46e160f4a`.
- Executable inventory hash: `537b5984f585dbf78bbe41c4ef1d85e091c5369ceb5222546ab962a41b339c09`.
- The saved historical test XML reports 158 tests, zero failures/errors/skips. Tests were **not rerun**: several create fixtures and execute experiments, contrary to this audit's scope.
- Historical clean reproduction records six independently reverified executions and matching binary metric rows. It demonstrates reproduction of this instrument, including its existing metric definitions; it is not an independent validation of those definitions.

## 2. What the pilot actually exercised

| Component | Main protocol cases | Separate actual acoustic versions | Evidence and limits |
|---|---|---|---|
| STT | P0–P5 and four scripted clean cases use supplied transcripts. P6–P9 use `ScriptedSTT` through an actual voice HTTP endpoint. | Six local capture conditions; Vosk transcribes speech conditions, with uncertainty handled as an unclear request. | [cascade.py][cascade], [voice main][voice-main], [acoustic capture][acoustic]. The main cases do not test recognition accuracy. |
| Intent interpretation | Supplied typed desired state; P6–P9 use `ScriptedTypedIntentLLM`. | Real local Qwen HTTP inference for the successful recorded condition. Five unsuccessful conditions have null raw model output. | [offline adapters][offline] grounds a date deterministically first; Qwen is instructed to copy that ISO date into schema-constrained JSON and is rejected if it disagrees. This is a restricted extraction/validation pipeline, not evidence of broad conversational reasoning. |
| TTS | P0–P5/clean task metrics use synthetic 500 ms acknowledgements, without rendering outcome speech. P6–P9 render real WAV bytes using `DeterministicToneTTS`. | Actual eSpeak generates synthetic input conditions and non-decisive progress/clarification audio whose hash is captured. The successful proposal then enters the same synthetic clean protocol runner. | A deterministic tone is **not intelligible spoken text**. Metadata describes a sentence; the WAV does not say it. Actual eSpeak outcome playback is not measured by this pilot. |
| Accepted revisions | Real validated controller requests and PostgreSQL transactions. | Shared measured proposal is submitted to each arm's real controller fixture. Clarification accepts no revision and writes no appointment. | [paired runner][paired], [clean runner][clean], [revision service][revision]. Scripted desired states are authoritative scenario inputs, not model discoveries. |
| Provider execution/faults | Real HTTP adapter, separate PostgreSQL provider simulator, append-only commits and explicit durable named barriers. Core arms use actual durable worker steps; B0–B2 use explicit provider drivers. | Same simulator after the shared model proposal, if READY. | A real simulator implementation, not a production booking provider. DROP_RESPONSE, unavailable/stale reads, partial effects, version conflict and Redis loss are controlled faults. |
| Playback | P0–P5/clean use runner-generated `PlaybackAck`. Core P6–P9 submit scripted STARTED/PROGRESS/INTERRUPTED/COMPLETED requests to the real controller. B0–B2 synthesize client request/response evidence in the harness. | No microphone-to-outcome playback chain is measured in the acoustic arm comparison. | [P6–P9 replay][audio-replay], [baseline audio][baseline-audio]. Both repair bundles have `livekit_sent=null`. No browser/device rendered samples are captured. |
| Claim authorization | Actual revision/resource-bound receipt and permit commands for P1/P2. Baseline paths bypass permits in research only. B3's P6–P9 audio path still checks fresh provider evidence and current revision. | P1/P2 issue real permits after a successful proposal; clarification issues none. | [claim service][claims], [B3 audio][b3], [audio service][audio]. P0–P5 B3 speech is a harness acknowledgement, not B3 scheduler publication. |
| Repair/recovery | P2 real PG obligation OPEN → REPAIR_AUTHORIZED → REPAIR_PLAYED in P8/P9, driven manually by the replay. Real worker reconciles provider state. | No repair case uses actual local acoustic inference. | The replay discovers the obligation and explicitly schedules its correction. No paired restart/disconnect occurs. Durable storage exists; unattended repair delivery/recovery is unproven. |
| Oracle | Independent external case + simulator commit history + scripted client acknowledgements; existing offline verifier recalculates grades. | Externally expected November 5, 3 PM compared with measured proposal's actual effect; clarification is retained as task failure. | [business/speech grade][grade], [P8 grade][p8-grade], [P9 grade][p9-grade]. Important construct-validity defects are documented below. |

**Supported scope:** deterministic protocol execution, provider ambiguity/reconciliation behavior, durable state changes, controlled audio lifecycle and reproducible synthetic exposure records. **Unsupported scope:** a complete live voice agent under these faults, natural dialogue competence, real audible repair effectiveness, human hearing/understanding, production provider/telephony reliability or measured voice latency. Existing Phase 5 voice acceptance is separate evidence and cannot be added to this paired pilot's sample.

## 3. Arm differences: declared switches versus runtime behavior

The frozen profile in [research/arms.py][arms] declares these cumulative mechanisms. Several fields are descriptive manifest labels, rather than independently enforced runtime switches. Runtime choices occur through separate drivers, the `claim_permits`/provider-idempotency branches and workflow `research_arm` checks.

| Arm | Declared mechanisms | Actual provider/correction behavior and functions | Speech/playback/repair behavior | Shared safeguards |
|---|---|---|---|---|
| B0 | All nine mechanism booleans false | `execute_baseline_p3`, `execute_covering`: direct provider calls, stop on ambiguous outcomes when safe retry proof is unavailable; visible faults allow best-effort cancel/create. | Synthetic tool-result speech; no permit; `run_baseline_audio` generates scripted playback observations for measurement. No repair. | Validated external inputs, real PG accepted revision, provider versions/constraints, normalized logs, conservative no-blind-retry harness checks. |
| B1 | Durable idempotency, reconciliation before retry | Same baseline drivers; authoritative status/postcondition reads, cancellation then creation after correction. | No permit or cross-layer repair; synthetic speech after successful verified path. | Same guards; eight-read budget in covering cases. |
| B2 | B1 + revision invalidation, staging, compensation | Separate driver implements reschedule when supported, cancel/create otherwise; compatible read reuses effect. | No permit; measured synthetic audio events do not mean B2 has a production playback scheduler. | Same accepted-intent/identity/provider guardrails. Staging flag does not establish identical crash-recovery machinery to B3. |
| B3 | B2 + playback tracking | `_execute_one`, `_drain` use the same actual durable operation/reconciliation worker as P1/P2. | P0–P5 synthesize final acknowledgement after recovery; P6–P9 use `_b3_audio`/`_b3_text` with fresh facts, current revision and no permit. Existing revision handler stops/cancels old segments; STARTED requires current revision. Corrected 4 PM update is acknowledged. No repair in the observed cases. | Stable operations, UNKNOWN, reconciliation, revision/resource checks, competent stop/cancel and final-state recovery. |
| P1 | B3 + claim permits and product-state invariants | Same core worker/recovery path as B3. | `_publish_current`, `_claim_audio`, `VoiceScheduler` use permits, current receipt, expiry/predicate/resource rechecks at publication/start. Revision acceptance omits repair when `research_arm=P1`. | Same core guards plus explicit persisted claim authority. Late acknowledgement path has an ablation leak (F2). |
| P2 | P1 + durable played-span repair | Same core worker/recovery path. | Same permits; PG repair obligation; explicit retraction prefix; full corrected acknowledgement marks repair played. Replay supplies `repair_obligation_id` to schedule it. | Same core guards; no evidence that ordinary live/restarted worker discovers and automatically delivers outstanding repair. |

Baseline implementation: [baselines.py][baselines] `execute_baseline_p3`; [baseline_covering.py][baseline-covering] `execute_covering`; [baseline_audio.py][baseline-audio] `run_baseline_audio`. Core: [paired.py][paired] `_execute_one`, `_drain`, `_publish_current`; [durable worker][worker]; [playback service][playback] `on_revision_accepted`, `record_playback`.

### Does shared code contaminate baselines?

**Observed runs:** B3's successful P0–P5/clean outcomes do not have permits; B3's P6–P9 segments have `research_unpermitted=true`, null receipt/permit/claim, and use the dedicated research path. P1/P2 have actual permits. Observed B3/P1 repair traces contain no RepairRequired event or repair obligation. Thus the zero primary rates alone do not show contamination, and the observed audio paths do distinguish permits.

**Shared restrictions:** B3 deliberately checks current revision and fresh provider state in `_b3_text` using the same deterministic predicate evaluator. All core audio STARTED commands check segment state/current revision, even without permits. This is competent established invalidation/playback handling and must remain in B3. It overlaps P1's safety outcomes without giving B3 a persisted permit. In P5, all core arms also invalidate the old receipt through the shared accepted-revision transaction. This substantially reduces opportunities for P1 to add outcome benefit.

There is no single permit gate across all six arms. The ordinary product path always has permits; research bypasses are explicit. Unsupported confirmation could still arise in a declared baseline when an unpermitted tool-result claim is false, a resource changes after B3's observation/publication but before playback, or old buffered playback continues after a correction. B3 STARTED lacks P1's fresh evidence/resource-version recheck; ordinary current-revision invalidation already blocks a simple old-revision start. **None of the pilot's primary ambiguity cases drives that stale-start/resource-change claim race.**

**Reachable unobserved leakage:** F2 below shows P1 can acquire repair via late acknowledgement. The `product_state_invariants` boolean is not separately consulted in executable decisions; core B3 shares orthogonal state/worker guards. Attribute empirical differences to the actual permit/repair paths, not an unexercised manifest flag.

## 4. Why the primary endpoints tie

### Raw paired results

| B3 versus comparison | Endpoint | Matched cases | Both success/event | B3 only | Comparison only | Both failure/no event |
|---|---|---:|---:|---:|---:|---:|
| P1 | Correction success | 35 | 29 | 0 | 0 | 6 |
| P2 | Correction success | 35 | 29 | 0 | 0 | 6 |
| P1 | Unsupported confirmation | 21 | 0 | 0 | 0 | 21 |
| P2 | Unsupported confirmation | 21 | 0 | 0 | 0 | 21 |

The correction result is expected from these drivers: B3/P1/P2 reconcile and transition the provider with the **same worker**, then the runner waits for the final effect before submitting any final claim. Repair changes subsequent communication, not the business final state, in the two exercised cases.

The six shared correction failures are four permanently unavailable cases (`pilot-secondary-07`, `-11`, `-16`, `-19`), one HELD partial effect and one concurrent version conflict. No arm can safely complete the declared final request within the available evidence/constraints. They remain failures; honest handoff has separate process-policy credit.

### Specific evidence

1. **Hidden-commit successful pair:** [P3 replay][p3-bundle], B3 execution `ba4374e1-6158-49d6-a82e-85d2ed3fd6f0`, P1 `698826be-e891-4098-bbd3-985045c679c7`, P2 `b484a242-259a-4c7f-b956-e6b23b221959`. All converge to November 23 at 4 PM. B3 has no receipt/permit; P1/P2 issue new revision-2 permits after `_drain`. No old claim is attempted while knowledge is UNKNOWN.
2. **Correction after verification:** [P5 replay][p5-bundle], B3 `09adbf8a-30c6-4d97-8860-8b4394976191`, P1 `204d70d9-d82d-467d-90ac-230746fea5cf`, P2 `16a2ef2b-c51e-4d8a-a891-eb9818d782f9`. Old receipts `26c20f2a-02ec-4f5f-839a-c1bfe7469c8a`, `3642aa1b-a171-4819-90dd-2fc3a79359cc`, `3a121a18-2730-4622-86c8-ae27555267f5` are invalidated. `_execute_one` does **not** try authorizing/publishing from them; it drains recovery and submits a fresh revision-2 claim. This reaches an interesting boundary without testing the proposed incremental protection.
3. **Partial/unavailable/conflict claim denials:** [partial replay][partial-bundle], P2 `93177b1a-f2d6-4453-ac54-f3e94f31edbd`, B3 `7c38772d-6144-4e98-819a-874f563fb0c6`, P1 `ea84ba8e-3719-4a3d-95ef-08148b424beb`; all withhold speech after unresolved recovery and send the same experiment claim probe that gets 409. B3 is probed through the proposed claim endpoint too, even though that endpoint is not its normal research speech path. These are common refusal/evidence controls, **not a B3-would-permit/P1-would-reject witness**. Conflict has the same limitation.
4. **P6/P7:** all core arms cancel generated/unplayed old audio and deliver current final text. The shared revision/playback handler already prevents the tested stale start. The replay does not try a delayed buffered STARTED request after correction.

In 21 primary ambiguity scenarios, each core arm exposes a final claim in 13 and none in eight (five completed retractions with cancellation speech withheld, three unavailable cases). B0 exposes none in that subset. Thus zero unsupported events partly reflects withholding and the scheduler's choice to wait. Useful coverage must accompany the safety rate. The pilot does not demonstrate P1 rejecting a stale/unsupported claim that competent B3 would permit.

## 5. The two paired repair timelines

All times below are UTC on 2026-10-03; appointment content is October 1 in Asia/Karachi. Provider CREATE produces 3 PM/version 0, RESCHEDULE produces 4 PM/version 1. These are sequential paired executions under one external fixture, not simultaneous callers. Audio publication is a real PG lifecycle event; playback is scripted client testimony.

### P8 partial exposure

Bundle: [p8-paired-35dd180f-8cad-4feb-80e0-5d7158aafb03.json][p8-bundle]. Hash `ab358401a3ae5d1ea33e84c944c06835cd41e8f7dca98c1e875a2f08dba3643a`.

| Evidence | B3 | P1 | P2 |
|---|---|---|---|
| Execution ID | `e3566cee-894b-4371-88cd-3bcbfd8a420b` | `b12ecb22-7356-4111-843c-302ba783432e` | `3efdff58-a8b6-4039-bc07-9ad722930def` |
| Accepted r1 | 17:59:21.209026 | 17:59:24.239251 | 17:59:28.435587 |
| CREATE truth | 17:59:21.449139 | 17:59:24.524537 | 17:59:28.646229 |
| r1 evidence/permit | Fresh facts; no receipt or permit | SATISFIED/version 0; permit `9dd728ae-ad0d-4bf9-a67e-35420a93ba9b` | SATISFIED/version 0; permit `ab7f9aee-ca83-4a8a-b2f3-eb43f75bbe2d` |
| Initial publication/start ACK | Published event 17:59:21.995116; start 17:59:22.087316 | Permit scheduling + audio release; start 17:59:25.404423 | Permit scheduling + audio release; start 17:59:29.311093 |
| Partial ACK | 17:59:22.136052 | 17:59:25.504254 | 17:59:29.387921 |
| Interrupted ACK | 17:59:22.228916 | 17:59:25.595142 | 17:59:29.515093 |
| Scripted correction / accepted r2 | 17:59:22.274294 / 17:59:22.654430 | 17:59:25.651364 / 17:59:26.154593 | 17:59:29.562946 / 17:59:30.027563 |
| Invalidation/repair | Segment STOPPED, no repair | Old receipt invalidated at accepted r2; no repair | Old receipt invalidated; repair `102a7b7c-4f5f-4c94-ae79-8d8bfbe53bad` OPEN at accepted r2 |
| RESCHEDULE truth | 17:59:23.074236 | 17:59:26.708300 | 17:59:30.433977 |
| r2 authority | Fresh 4 PM facts; no permit | SATISFIED/version 1; `6a3dcbbe-d335-4914-8d2a-8c40435c6c50` | SATISFIED/version 1; `ca59464f-952c-490d-970d-9a2c4eb2299e`; repair authorized 17:59:31.096967 |
| Corrected STARTED → COMPLETED ACK | 17:59:23.735124 → 17:59:23.802261; 2160 ms/34560 frames/12 words | 17:59:27.806450 → 17:59:28.030266; same span | 17:59:31.378445 → 17:59:31.556362; 3240 ms/51840 frames/18 words |
| Durable completion | None | None | REPAIR_PLAYED/RepairSatisfied at 17:59:31.585960 |

The initial metadata is “Your maintenance appointment is confirmed for 3:00 PM on 2026-10-01 (Asia/Karachi).” **Each partial ACK is 500 ms/8000 frames/two words: `Your maintenance`.** The equal-duration word proxy places “confirmed” at 720–900 ms and “3:00” at 1080–1260 ms. The acknowledged span therefore has not conveyed a decisive confirmation or the old time, even within the synthetic text representation. The WAV is a tone, so there is no actual spoken claim to hear.

B3/P1 acknowledge the complete statement “Your maintenance appointment has been moved to 4:00 PM on 2026-10-01 (Asia/Karachi).” P2 acknowledges that statement prefixed by “Correction: my earlier confirmation was outdated.” All are backed by the independently committed final appointment; P1/P2 also have version-1 revision-2 receipts. The original r1 permits remain recorded as PUBLISHED with null `invalidated_at`; accepted r2 invalidates the receipt and stops the segment. Historical publication is retained, not erased.

The P8 oracle finds partial/full spans and correct final state without reading `repair_played.state`. However, [grade_p8_witness][p8-grade] changes expected text by `research_arm` and explicitly requires `arm not in (B0,B1,B2,B3,P1)` for repair success. A baseline with identical correct explicit repair behavior still fails solely because of its label. Conversely, P1 with P2's explicit text fails the arm-dependent exact text match. Thus the result is not a valid arm-neutral repair-outcome comparison. The current grade is not simply checking a P2 DB record; **it is still partly predetermined by arm identity**.

### P9 full exposure before correction

Bundle: [p9-paired-8ec7c439-e7de-45e0-9b11-24b9b6c17d51.json][p9-bundle]. Hash `c9d01bd5058493cc0a432a93e767454676be52b16529aa8a7f24776421f1f10f`.

| Evidence | B3 | P1 | P2 |
|---|---|---|---|
| Execution ID | `40037cb6-1b47-4b27-81e0-abd2e45f784c` | `e604bba3-80a5-4191-a3c0-473b09f55829` | `9453e125-64e3-4c90-b374-e08b5032a998` |
| Accepted r1 | 17:58:57.189833 | 17:59:01.219404 | 17:59:07.340018 |
| CREATE truth | 17:58:57.443742 | 17:59:01.588776 | 17:59:07.588672 |
| r1 evidence/permit | Fresh facts; no receipt/permit | SATISFIED/version 0; `95c5bec9-0f59-4145-9570-9d024e717c03` | SATISFIED/version 0; `6d059ed1-e97d-4e10-8667-b2efda4953a0` |
| Old STARTED → COMPLETED ACK | 17:58:57.925692 → 17:58:57.975639 | 17:59:03.004300 → 17:59:03.169424 | 17:59:08.347395 → 17:59:08.449760 |
| Old acknowledged span | 1980 ms/31680 frames/11 words, full sentence | Same | Same |
| Scripted correction / accepted r2 | 17:58:58.076893 / 17:58:58.409790 | 17:59:03.334349 / 17:59:03.844972 | 17:59:08.579946 / 17:59:09.024375 |
| Invalidation/repair | Completed historical segment retained; no repair | Receipt invalidated at r2; no repair | Receipt invalidated; repair `f7ce5717-c395-4ed0-b3ee-10529128db2b` OPEN at r2 |
| RESCHEDULE truth | 17:58:58.976040 | 17:59:04.840801 | 17:59:09.632460 |
| r2 authority | Fresh 4 PM facts; no permit | SATISFIED/version 1; `fdc61518-1466-44fd-8f8e-e8676e90ec9e` | SATISFIED/version 1; `4ee7076f-8e42-456d-a964-b3b19cceeb0f`; repair authorized 17:59:10.993367 |
| Corrected STARTED → COMPLETED ACK | 17:59:00.360063 → 17:59:00.478710; 2160 ms/34560 frames/12 words | 17:59:06.485989 → 17:59:06.863900; same span | 17:59:11.388136 → 17:59:11.650720; 3240 ms/51840 frames/18 words |
| Durable completion | None | None | REPAIR_PLAYED/RepairSatisfied at 17:59:11.692228 |

All old audio finishes before correction; none is interrupted. The full metadata includes the 3 PM confirmation, valid when played and later outdated. All three acknowledge a correct 4 PM update; P2 adds the same explicit retraction prefix as P8.

[grade_playout][p9-grade] is arm-neutral for P9: it requires that explicit prefix, full old exposure, full corrected exposure and independent truth support; it does not require a DB obligation or P2 label. It would credit a baseline exhibiting the same observable text/span evidence. Its exact template requirement should nevertheless be preregistered as an **explicit retraction endpoint**, distinct from communicating the correct final appointment, which B3/P1 already do.

### What these two cases establish

P2 really records durable obligations, schedules an evidence-bound correction template and gets a full scripted ACK. It is not succeeding merely because a database row says complete. Yet P8's grade is arm-dependent; P8's span lacks decisive words; P9's difference is explicit wording rather than final-state correctness. Neither demonstrates benefit from **durability across restart**, loss of ACK, reconnect, human confusion or physical hearing. ACK timestamps are synthetic: for example P9 P2 acknowledges 3240 ms of output only 262.584 ms after STARTED, so these are logical progress records, not real-time audio durations.

## 6. Endpoint definitions and oracle independence

### Independence that is present

- Final target comes from the externally declared `ScenarioCase`/`CleanScenarioCase`, not the controller's last desired state. Recorded acoustic proposal can disagree and fail externally graded correctness.
- Business state is reconstructed from the separate simulator's append-only `after_facts` history, in sequence order. No controller receipt conclusion determines final business success.
- Client request IDs/spans/times feed the playout graders. Controller repair state is not a truth input. Existing tests alter repair state without changing grade.
- Actual controller/worker provider adapter uses normal status/resource observations. No `/truth` call or simulator truth-store import was found in their execution paths, and their Compose environments lack the simulator DB URL. The experiment harness reads truth to collect/grade evidence and coordinate faults.

**Isolation limit:** the simulator's `/internal/scenarios/{id}/truth` endpoint is reachable on the same network and has no separate oracle credential. Independence is implemented by code convention and separate DB/environment, not enforced inability to access truth. The assertion “controller cannot use privileged truth” is stronger than present evidence. A read-only import/endpoint audit supports “does not use it in these paths”; a future access-denial check/network or token boundary would support “cannot.”

### Speech grading gaps

1. [grade()][grade] checks whether the claimed time is CONFIRMED in truth at two supplied timestamps and whether revision is older than the external correction anchor. `permit_id` is not used; no available raw observation, freshness window, evidence resource-version binding or predicate entailment is an input. Truth matching is essential but **does not by itself prove the executing arm possessed applicable evidence**. A lucky true claim under hidden knowledge could receive support credit. Replay mechanism checks retain useful reads, but do not turn this general truth-only classifier into the stated applicable-evidence endpoint.
2. P0–P5/clean set `released_at=played_at=now` in a synthetic ACK, instead of capturing actual publication/start. P8/P9 set `released_at` to client STARTED time, not the recorded server publication. Thus the claimed release/play criterion is not consistently implemented as actual release-time grading.
3. Staleness is `ack.played_at >= correction_scripted_at` and `intent_revision < final_revision`. It uses the external scripted correction start, not durable accepted revision; these are different moments. There is no interval reconstruction for a segment spanning the correction, and compatible revisions are not semantically distinguished by this simple test.
4. P8 old progress and interruption precede the scripted correction; P9 full old completion precedes it. Neither becomes an unsupported/stale event under that definition. Repair means an earlier valid statement later needs updating, a distinct endpoint; it need not increase unsupported-at-play counts.
5. Any positive `played_ms` is treated as exposure of the full decisive claim. The actual word span need not have reached a decisive predicate. In P8 it has not. `needs_repair` likewise requires older OUTCOME/REPAIR plus any positive span, not semantic decisive content.
6. Final-state grade generally checks status/start/timezone and absence of other active appointments, with special cancellation/multiple-resource rules. It does not fully compare end time or every actor/ticket/resource predicate of the external desired appointment. This is adequate for the fixed equal-duration fixtures but is a gap before broader fixture diversity or claims of complete domain-intent correctness.

The three concepts must be specified separately in a new version: (a) false/evidence-unsupported claim at actual publication/exposure; (b) incompatible stale claim exposed after the chosen correction/acceptance anchor; (c) appropriate update/retraction after earlier valid exposure. Internal obligation persistence/completion is a separate mechanism endpoint. A baseline must receive the same outcome grade for identical externally observable behavior.

## 7. Sample accounting and retained failures

The 40 primary instances comprise 31 provider cases, four audio-boundary cases and five clean cases. One clean instance has five additional acoustic versions: **45 versions**. All versions have six arms except the concurrent conflict, which has only B3/P1/P2 by predeclared applicability.

`40 × 6 − 3 = 237` primary executions; `5 × 6 = 30` exploratory acoustic executions; total **267**. Each core arm has 45 total/40 primary; each earlier baseline has 44 total/39 primary. No duplicate execution IDs. All 45 attempt entries are VERIFIED, no failed attempts, infrastructure exclusions or reruns in this pilot ledger.

| Arm | Correction success | Clean success | Unsupported, all primary tasks | Useful outcome coverage | Recorded repair endpoint |
|---|---:|---:|---:|---:|---:|
| B0 | 15/34 | 5/5 | 0/39 | 15/39 | 0/2 |
| B1 | 29/34 | 5/5 | 0/39 | 30/39 | 0/2 |
| B2 | 29/34 | 5/5 | 0/39 | 30/39 | 0/2 |
| B3 | 29/35 | 5/5 | 0/40 | 30/40 | 0/2 |
| P1 | 29/35 | 5/5 | 0/40 | 30/40 | 0/2 |
| P2 | 29/35 | 5/5 | 0/40 | 30/40 | 2/2 |

Repair figures are reproduced **as recorded**, with the validity qualifications above. All arms have zero duplicate effects in these recorded primary cases. The 34 versus 35 correction denominators reflect the one conflict case's declared absence from B0–B2, not an outcome-based exclusion. Compare all arms only on matched applicable cases; do not contrast 29/34 with 29/35 as the same trial population.

Core correction pairs contain the 31 provider and four audio cases. Unsupported primary comparison uses only 21 RESPONSE_LOSS cases: `pilot-secondary-01` through `pilot-secondary-20`, plus `maintenance-read-preserves-booking-41`. The separate REDIS_LOSS hidden-commit case is not included by the implementation's exact RESPONSE_LOSS selector. This is an endpoint-eligibility detail to declare explicitly in the next manifest. Core clean NI contains four scripted clean tasks and the recorded-clean primary acoustic version. P8/P9 supply the two repair pairs; P6/P7 do not enter that denominator.

Five synthetic acoustic conditions fail safe date recognition/grounding and accept no intent/write/claim. They are 30 failed exploratory executions, retained in raw data/reviews, **not five additional independent scenarios**. The six conditions share one actual model result per version across arms, so they are not six independent model runs per arm. Recorded clean success is one captured successful Qwen response; other conditions have null model output, so “six LLM interpretations succeeded/failed” would be misleading. Primary clean 5/5 does not imply all actual acoustic conditions succeeded (one of six did).

All 112 reviews are present: 18 baseline limitation, 30 unavailable-provider/withheld, 15 cancellation speech unavailable, six partial-effect, three resource conflict, ten repair-ablation/coverage and 30 acoustic clarification reviews. They are mechanically generated classified records with raw evidence attached, not evidence of 112 individualized human adjudications. This audit examined the shared core failures and paired audio evidence rather than treating those labels as proof that failures are expected.

Refusals, UNKNOWN, partial effects, handoffs and unavailable outcomes remain in task denominators. Safe handoff is separate version-2 process-policy credit, never business success/useful decisive coverage. Existing provider latency rows retain right-censoring at the saved observation end. There were no missing playback records in the planned synthetic cases because the harness supplies them; this does not validate handling of real missing acknowledgements.

No repetitions inflate primary sample count. Nevertheless new dates, UUIDs, seeds and IDs do not establish stochastic independence: cases share scenario templates, single recordings, deterministic drivers and providers. `template_id` is set to each renamed scenario key in much of the plan, so it does **not preserve the original generator-template family** needed for robust family clustering. The current analysis reports nominal scenario-level binomial/McNemar quantities; it does not correct underlying template dependence merely by excluding variants.

## 8. Defects and unresolved evidence gaps

| ID | Severity/type | Evidence | Consequence and minimum proposed remedy |
|---|---|---|---|
| F1 | High: experimental validity defect | P8 grader lines 83–90, 124–130 branches on arm identity. | New arm-neutral observable repair metric; separate explicit retraction, correct final update and DB durability. Label-invariance and behavioral equivalence checks. Retain v1 grades unchanged. |
| F2 | High: reachable implementation/ablation defect, not observed in pilot | `on_revision_accepted` excludes B3/P1 at playback-service line 166; `record_playback` calls `_ensure_repair` unconditionally at line 334; `needs_repair` has no arm guard. | Late PROGRESS/COMPLETED for a started old P1 segment after accepted r2 can create a P2 obligation. For B3 its null claim conflicts with NOT NULL `stale_claim_id`, predicting a transaction failure rather than baseline playback handling. Proposed real PG three-arm late-ACK check, then consistent repair capability guard in a new version. No new execution was made to confirm the prediction. |
| F3 | High: endpoint/fixture mismatch | P8 span is two introductory words; tone output; grader treats any positive span as decisive. | Version fixture to exposure after actual decisive predicate; preserve before-predicate control. Define semantic exposure and use actual speech/alignment if claiming audible semantic effects. |
| F4 | High: oracle contract gap | Truth-only `grade` input, synthetic release times and pointwise exposure; no available-evidence check. | Freeze separate truth support and knowledge/evidence applicability; reconstruct actual release/play interval, revision anchor and semantic predicate span without requiring a P1 receipt representation for baselines. |
| F5 | Medium: inadequate incremental-mechanism exercise | No stale receipt/claim use after P5; core worker shared; P6/P7 merely cancel old audio before new scheduling. | Predeclare targeted ordinary races through competent arm interfaces. Record attempted claim, blocking mechanism and observable outcome; ties are allowed. |
| F6 | Medium: recovery evidence missing | P8/P9 no restart/disconnect; runner directly schedules repair. No outstanding-repair consumer located in durable worker; live agent calls scheduler without repair obligation. | Paired restart-after-obligation-before-delivery and reconnect checks. Distinguish durable persistence from automatic delivery; specify explicit recovery entry point and limits before claiming unattended recovery. |
| F7 | Medium: freeze metadata incomplete/heterogeneous | Main audio uses tone; frozen model summary lists local Vosk/Qwen/eSpeak. P6–P9 replay drain is 20 loop passes versus global frozen “30 transitions”; scheduler-controller HTTP uses 15 s versus runner's 40 s. | Enumerate effective budgets/adapters per path in new manifest. Source hashes pin the actual values, but current prose/global budget labels are incomplete. A loop pass may process several operations, so neither label is an exact global transition bound. |
| F8 | Medium: dependence/analysis readiness | Unique renamed template IDs, one reused recording; Phase 8 template `fixtures=[]`; survival/mixed model/confirmatory family execution not implemented. | Materialize new instances, retain generator family/speaker IDs, predeclare strata and comparison families/cluster estimands/missingness analysis before any main outcome. Needed analysis code must be added and frozen under the new protocol before campaign starts. |
| F9 | Limited isolation evidence | Controller code does not use truth, but truth API is reachable without an oracle-only credential. | State code-based independence honestly; propose an access-denial check and small non-RBAC isolation boundary if stronger separation is required. |

These are audit findings, not changes to v1's signed/content-hashed records. The Phase 7 report's “none found” describes the earlier review; this audit supplies additional contrary evidence. No current failed runtime test was manufactured. Historical passing tests do not cover F2's arm-specific late ACK path or establish F1's validity.

## 9. Assessment of the 500-instance allocation

The **100 clean / 200 ambiguity / 100 playout / 100 other provider-boundary** allocation is a reasonable provisional coverage allocation, not evidence of power or mechanism sensitivity. Retain it provisionally while fixing the instrument; freeze detailed cells only after exploratory checks. Increasing counts cannot repair a circular outcome or force a competent baseline to fail.

- **Primary:** P2 versus B3 correction success on eligible revision cases (potentially 400 if all non-clean cases qualify), and unsupported decisive confirmation on 200 declared ambiguity cases; exact paired McNemar with Holm over the two tests. P1 mechanism comparisons/B0–B2 comparisons are secondary or exploratory under explicit families. Repair is currently secondary; a changed primary claim requires an explicit new preregistration.
- **Repair exposure denominator:** 100 playout cases do not imply 100 repair opportunities. P6/P7 have none; P8/P9 only qualify if actual decisive content has been exposed. Predeclare allocation across queued/partial/full, ACK loss/restart/additional revisions and semantic spans. Report repair completion among qualifying exposures plus unconditional task-level safety/coverage so withholding cannot disappear from view.
- **Confidence limits:** at zero failures, two-sided exact 95% binomial upper bound is `1 - 0.025^(1/n)`: 16.11% at n=21; 8.81% at n=40; 3.62% at n=100; 1.83% at n=200; 0.918% at n=400; 0.735% at n=500. Use the denominator of the actual arm/stratum/eligible exposure, never 267 executions or 500 total for a smaller endpoint subset. These formulas assume independent comparable Bernoulli trials; shared templates can invalidate population interpretations.
- **NI:** observed clean paired difference is zero; n=5 gives conservative lower bound −52.18 percentage points, so the 5-point criterion is not met. Hypothetically 100 clean identical paired successes give −3.62 points under the frozen conservative formula, which could pass −5 points **under the sampling assumptions**. That is a mathematical possibility, not a forecast. A largely scripted clean set supports protocol utility, not live-recognition utility; specify the latter separately if desired.
- **Zero discordance:** pilot primary McNemar p=1 gives no superiority and does not establish equivalence. The nominal discordance upper bounds (10.00% at n35, 16.11% at n21) are uncertainty bounds, not predicted future discordances. Deterministic structurally identical paths can keep tying regardless of n.
- **Diversity:** independent inputs must change relevant constraints/fault schedules/resource states/dialogue semantics; shifting dates or replaying one sample does not produce population independence. Preserve underlying family IDs; use appropriate clustering/sensitivity analysis for synthetic families. Actual speech comparison needs distinct speakers/utterances and recorded model outcomes without inflating arm n from shared inference.
- **Timeouts/missingness:** planned failures/timeouts/handoffs remain task failures unless the external final state actually satisfies the endpoint; retain censoring windows. Missing ACK is unknown exposure/completion, not evidence of silence or successful repair. Report missingness, planned slots and reasons plus worst/best-case binary sensitivity bounds; do not convert unavailable timestamps to zero or restrict latency conclusions to favorable completed pairs. Predeclare event, censoring horizon and survival estimand.
- **If core arms tie:** report reproducible absolute performance/safety limits and no detected incremental primary benefit on these scenarios. RQ2 comparisons against earlier baselines may remain useful. Mechanism evidence can show current receipts prevent prohibited releases or obligations persist, and arm-neutral secondary behavior can show explicit retraction delivery. None demonstrates statistical primary superiority, general live-agent reliability, reduced human confusion or literature novelty.

## 10. Minimum next work proposed — not executed

**C rather than A or B:** revision is already necessary because F1/F4 change outcome validity and F2 changes a mechanism boundary. An exploratory audit alone cannot make v1's grader valid. Keep v1 intact; publish a small `research-readiness-exploratory-v1` plan and then freeze a new protocol/source/metric/fixture version before Phase 8. No requirement to redesign the full app or buy API keys.

First propose arm-blind grading with a precise externally observable definition: final correct statement, explicit retraction of previously exposed incompatible content, truth/evidence applicability at actual timestamps, completion ACK, and separate durable-mechanism telemetry. Unit properties should credit identical behavior regardless of labels/DB representation and distinguish partial intro from decisive words. Specify how missing evidence produces UNKNOWN and sensitivity bounds. Keep outcome grading independent of controller conclusions.

Smallest useful exploratory set: **six predeclared fixtures under B3/P1/P2 = 18 executions**; all remain outside pilot and future confirmatory n. Use the same scripts/evidence availability/budgets/interfaces and named barriers for each arm; do not suppress established B3 cancellation, current-revision checks or ordinary corrective statements. Do not predict a winner.

| Check | Purpose and placement | Evidence required |
|---|---|---|
| E1: correction after verification | Retain old evidence; accept r2; attempt the arm's normal old claim/outcome path before/after recovery. | Actual request and rejection/publication, current revision, old/new evidence predicates/version, first blocking mechanism, truth and playback. Determine whether P1 adds a protection beyond B3's ordinary current-revision check; a tie is valid. |
| E2: queued resource change before playback | Publish valid current audio, hold before STARTED; provider changes version at the same intent revision; release buffered start. | Publication time, independent provider commit, available ordinary observations, permit/freshness checks and actual ACKs. This targets P1's evidence-at-start check where simple revision invalidation alone cannot decide. No deliberately stale baseline bypass. |
| E3: partial decisive span with late ACK | Play through the confirmation/time, hold the final progress ACK until after accepted correction; then deliver it. | Aligned decisive span and frame/word progress, accepted revision order, B3 playback response, P1 no-repair ablation behavior, P2 obligation idempotency, correct final update. This tests F2; keep the original two-word span as an offline/control definition rather than count it as a misleading claim. |
| E4: restart before repair delivery | After qualifying exposure/r2 acceptance and persisted obligation, stop/restart the relevant worker using a named barrier. | Process identity/restart evidence, unchanged PG facts, standard recovery entry point, no duplicate provider effect/claim, independently supported correction and playback. Measure delivery, not merely row survival. |
| E5: missing completion ACK / reconnect | Allow corrected playback attempt, withhold completion ACK, disconnect/reconnect, then replay/complete with stable IDs. | Missing evidence status and pending obligation, no premature repair success, replay-safe ACKs, eventual observed behavior or honest unresolved result. No assumption that missing ACK means unheard speech. |
| E6: another revision during repair | After repair r2 publication/partial exposure, accept r3 before completion. | Receipt/resource binding per revision, cancelled/stopped r2 correction, ordered truth, new obligation/exposure without premature closure, appropriately supported final r3 statement/ACK. |

Admission to Phase 8 should require: (1) arm-neutral grader and semantic/timing definitions accepted and versioned; (2) F2's scoped repair behavior verified in real PG; (3) remaining recovery limits explicitly stated; (4) exploratory failures retained/investigated; (5) all 500 new inputs, applicability, comparison families, cluster provenance, budgets and analysis implementation frozen before first main execution. B3 should remain competent even if all results tie.

## 11. Research claims at present

| Dimension | Supported | Currently unsupported |
|---|---|---|
| Implementation correctness | Recorded PG revisions, actual simulator reconciliation, 267 accounted-for executions, verified freeze/replay, permit-bound proposed-arm scheduling, two recorded durable repair lifecycle transitions. | Universal crash/ACK/revision safety; ablation isolation at late ACK; unattended live/restart repair delivery; absence of all possible defects. |
| Experimental validity | Matched fault schedules, independent simulator business history, external intent, descriptive counts, retained failures, no repetition inflation. | Arm-neutral P8 repair comparison; proof of decisive partial semantic exposure; complete evidence-applicability metric; inference from shared-template n as population independence. |
| Potential novelty | A research instrument integrates these mechanisms and makes their state/evidence inspectable. P2 produces an explicit repair template and durable obligation in controlled runs. | Primary improvement over competent B3, reduction of misleading hearing/belief, durability advantage without a restart comparison, or novelty against literature from passing implementation tests. A literature comparison and valid controlled mechanism evidence remain separate requirements. |

## 12. Exact existing evidence to share for independent review

Share the **whole** [frozen pilot directory][pilot-directory], since its manifest refers to child bundles; sharing only the summary JSON is insufficient. Include the following existing files:

1. [Pilot manifest][pilot-manifest] and [attempt ledger][ledger].
2. [Freeze manifest][freeze-manifest] and [202-member frozen source archive][source-archive].
3. [Raw observations CSV][observations], [raw counts][counts], [paired discordance][discordance], [112 failure reviews][reviews], [sample justification][sample], [Phase 8 manifest template][template].
4. [P8 paired repair bundle][p8-bundle] and [P9 paired repair bundle][p9-bundle].
5. [P3 hidden-commit pair][p3-bundle], [P5 verified-before-correction pair][p5-bundle], [partial-effect failure][partial-bundle], [version-conflict failure][conflict-bundle], [P6 generated-audio pair][p6-bundle], [P7 published-unplayed pair][p7-bundle].
6. [Actual recorded-clean comparison][recorded-bundle] and the six acoustic versions in the whole directory; manifest embeds actual audio/transcript/model evidence.
7. [Clean reproduction gate][clean-gate] and [fresh six-arm reproduced bundle][reproduced].
8. [Historical test XML][tests-xml], [Phase 7 report][phase7-report], [protocol prose][protocol-doc]. Treat the audit's validity qualifications as accompanying those historical results.

The frozen source ZIP contains implementation and contracts, but excludes root instructions/docs and Python tests. Supply those review materials separately with the archive. Local model weights and Docker images are not inside the ZIP: their identities are recorded, and they are required for actual acoustic/container reruns. Offline verification itself requires no model inference or paid API.

[arms]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/arms.py>
[paired]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/runner/paired.py:437>
[clean]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/runner/clean_paired.py:45>
[baselines]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/runner/baselines.py:133>
[baseline-covering]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/runner/baseline_covering.py:41>
[baseline-audio]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/runner/baseline_audio.py:51>
[worker]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/durable_worker/phase2.py>
[revision]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/api_controller/phase1_service.py:443>
[claims]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/api_controller/phase3_claim_service.py:108>
[b3]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/api_controller/phase6_b3_audio.py:51>
[audio]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/api_controller/phase4_audio_service.py:102>
[playback]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/api_controller/phase4_playback_service.py:119>
[grade]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/oracle/grade.py:52>
[p8-grade]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/oracle/p8_witness.py:83>
[p9-grade]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/oracle/playout_witness.py:104>
[cascade]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/voice_worker/cascade.py>
[voice-main]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/voice_worker/main.py:181>
[offline]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/apps/voice_worker/offline_adapters.py:214>
[acoustic]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/runner/acoustic_source.py:158>
[audio-replay]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/replay/phase4_p8.py:113>
[pilot-directory]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1>
[pilot-manifest]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1/pilot-c1cf3fdf4dda.json>
[ledger]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1/ledger.json>
[freeze-manifest]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1/freeze-90901263019a.json>
[source-archive]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1/protocol-source-537b5984f585.zip>
[observations]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-observations.csv>
[counts]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-raw-counts.json>
[discordance]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-paired-discordance.json>
[reviews]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-failure-reviews.json>
[sample]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-sample-justification.json>
[template]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-final-manifest-template.json>
[p8-bundle]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1/p8-paired-35dd180f-8cad-4feb-80e0-5d7158aafb03.json>
[p9-bundle]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1/p9-paired-8ec7c439-e7de-45e0-9b11-24b9b6c17d51.json>
[p3-bundle]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1/703ecbee-0b3d-48da-b98b-efeb24737c91.json>
[p5-bundle]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1/3c40f693-5fe8-42ba-830f-8104ca7d8aa3.json>
[partial-bundle]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1/75c0ff0b-22d0-4320-a5f5-f5ff03c66c58.json>
[conflict-bundle]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1/6fb52a11-fb38-4f90-8070-059cd100a2f3.json>
[p6-bundle]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1/p6-paired-aec5d09d-b228-4593-8114-ce802d115615.json>
[p7-bundle]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1/p7-paired-3d032806-e2e1-41ce-85fe-2a95143128c8.json>
[recorded-bundle]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1/clean-paired-e7c913f1-39f1-4d56-8042-b07d9613ebf4.json>
[clean-gate]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1/phase7-clean-61dae8506afb/reproduction-gate.json>
[reproduced]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-pilot/v1/phase7-clean-61dae8506afb/evidence/reproduced.json>
[tests-xml]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-final-tests.xml>
[phase7-report]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-7-report.md>
[protocol-doc]: <C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/docs/09_PHASE7_PROTOCOL.md>

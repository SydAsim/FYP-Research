# Commit-Aware Voice Agent: professor meeting brief

Prepared for Syed Asim Bacha. Evidence cutoff: 21 October 2026, 18:56 Pakistan time (13:56 UTC). Study ongoing; pooled descriptions only, not a final comparative result.

## 1. The project in one sentence

I am investigating when revision-bound evidence and speech permissions, followed by durable correction obligations, improve the consistency between an agent's actions and its delivered confirmations beyond a competent baseline.

The application domain is property-maintenance appointment booking. The current main experiment isolates the transaction/communication protocol using typed intents, a deterministic provider simulator and scripted tone/playback evidence. It is not an end-to-end evaluation of a speech model or a human comprehension study.

## 2. The problem in ordinary language

Illustrative example, not a new experimental result:

1. A caller requests an appointment at 3 PM.
2. The external service commits that booking, but its response is lost.
3. The controller therefore does not know whether the booking happened.
4. The caller changes the request to 4 PM.
5. An earlier 3 PM confirmation may already be generated, buffered, partly played or completed.

The controller must reconcile the earlier booking without duplicating it, determine whether the new target can be achieved, and control which outcome claims are justified now. If incompatible content was already exposed, stopping future audio is insufficient: the system may still owe the caller an explicit correction, even after a worker restart or disconnect.

Three different things can diverge: what happened, what the controller can establish from its observations, and what the client has played. A correct final appointment does not prove that an earlier statement was supported when issued. Likewise, refusing unsupported speech does not by itself mean the business task succeeded.

## 3. How the implementation addresses it

The model proposes a candidate intent. Deterministic backend code validates and accepts a versioned intent in PostgreSQL. PostgreSQL stores correctness-relevant state; Redis is optional and disposable.

Independent dimensions are tracked together, rather than collapsed into a single success/failure flag:

| Dimension | Question |
|---|---|
| Accepted intent revision | What has the user most recently requested and the server accepted? |
| External operation/effect | Was the request sent, did an effect commit, or is the result still unknown? |
| Verification evidence | What do available ordinary provider observations establish, for which resource version and validity window? |
| Claim permission | Is this precise decisive statement authorized for this intent and evidence? |
| Playback | Was the segment generated, queued, published, started, partly played or completed? |
| Repair obligation | Is an explicit correction still owed; has it been discovered, delivered or escalated? |

A verification receipt is an evidence record, not ground truth. It names the intent revision, operation, claim predicates, resource version and validity. A claim permit is a deterministic authorization for a specific outcome statement. It is not a user-consent token and not a business commit. Applicability is checked at the relevant delivery gates; an old receipt cannot simply authorize any newer statement.

An ambiguous write remains UNKNOWN. Another write is not automatically sent because the first HTTP request timed out. Reconciliation uses the provider capabilities and observed effects; retries require the declared safety conditions. If no safe automatic resolution can be established, uncertainty/handoff is a legitimate outcome.

Durable repair records track an obligation to correct already exposed incompatible content. Persistence alone is not delivered correction; the experiment keeps the record and externally evidenced completion separate.

## 4. The arms and the fair baseline

An arm is a configuration of mechanisms in the same study, not a different language model. Each input is tested across the three main arms with fresh resource bindings, comparable capabilities, faults and budgets, in the saved serial order.

| Main arm | Mechanisms and role |
|---|---|
| B3: competent baseline | Durable idempotency, reconciliation before retry, revision invalidation, transaction staging, compensation, playback tracking and ordinary corrective statements. Its ordinary evidence checks remain enabled. It can refuse a stale or unsupported claim. |
| P1: prevention mechanism | B3 plus explicit product-state invariants and revision/resource-bound claim permits. Tests additional prevention at the evidence-to-speech boundary. |
| P2: prevention plus repair | P1 plus durable played-span repair obligations, including persistence/discovery and controlled delivery or escalation. Tests correction after incompatible content was exposed. |

B0, B1 and B2 are earlier mechanism ablations retained in the project: B0 ordinary best-effort tool agent; B1 adds durable idempotency/reconciliation; B2 adds revision invalidation, staging and compensation. They are not part of this 1,500-execution main campaign. The name P1 for a main arm must not be confused with similarly named timing-barrier labels in older implementation documents.

Research question: when do P1/P2 add protection beyond B3's existing checks? The experiment must allow B3 to succeed, refuse unsupported speech and deliver an ordinary correction. No mechanism receives an observable outcome grade merely because of its arm label or internal record.

## 5. Study design and what a case means

500 distinct context inputs x 3 main arms = 1,500 original executions. These are not 1,500 independent scenarios, speakers or real calls.

| Stratum | Planned inputs | Purpose |
|---|---:|---|
| CLEAN | 300 | Normal useful completion; check that safety controls do not obtain apparent safety by never confirming anything. |
| HIDDEN_COMMIT | 100 | Effects that may commit while acknowledgements/status/resource observations are lost, delayed, reordered or unavailable. |
| PLAYOUT | 60 | Corrections near verification/publication/playback, delayed ACKs, version changes, restarts and reconnect/another-revision boundaries. |
| OTHER_BOUNDARY | 40 | Pre-dispatch corrections, provider errors, partial effects and other state/recovery boundaries. |

The fixed recipe support has 50 recipes. Inputs are context draws conditional on that support, with paired arms; they are not 500 sampled real callers. Named barriers control fault timing. Every original keeps its identity and full 600-second observation window anchored to the final external request, including after a normal driver return or a recognized refusal. This catches late effects rather than stopping observation at the first apparent success.

The independent oracle reads the simulator's append-only truth log and externally scripted target. It does not treat a controller receipt or the model's belief as ground truth. Stored grades separate correct business state, forbidden effects, support at publication/playback, exposure, supported final update, explicit retraction and repair telemetry. Missing relevant evidence stays UNKNOWN.

The two co-primary endpoints are correction success on the 200 correction inputs and unsupported decisive exposure on the 100 hidden-commit inputs. P2 versus B3 is the primary comparison. The accepted analysis retains paired input dependence, correction-stratum standardization, conservative uncertainty/missingness bounds and multiplicity handling. A separate clean useful-task tolerance is 5 percentage points. The final analysis also includes the accepted clustered/censored timing analyses. No interim significance test, bootstrap or arm ranking was run for this brief.

## 6. Verified progress: operational completion is not research accuracy

At the cutoff: 1,096 BACKED_UP, one RUNNING and 403 PLANNED (73.1% backed up). The active execution was sequence 1,097/P2. There were 366 inputs represented, 365 complete three-arm sets and one B3-only set. Backed-up arm counts were B3 366 / P1 365 / P2 365.

The campaign and watchdog were active with no pause. The absolute stop is 26 October 2026, 05:00 Pakistan time. An earlier cutoff stops new admissions while retaining the observation window of an active execution. Completion is currently projected around 25 October if pace holds; final verification/analysis and writing follow collection.

AWS runs the controlled instrument on Linux/EC2 with Docker and isolated PostgreSQL resources, a hash-chained SQLite research ledger, immutable exports and version-pinned S3 backups. Checkpointing resumes the same execution/deadline without replay. Source/freeze checks, resource/cost/storage guards and independent stop timers control admissions. The runner does not require an active coding-agent chat.

The backing-up percentage is evidence-retention progress, not a booking or model success rate. This task did not estimate AWS uptime, cloud-service reliability or actual billed spending. A conservative policy forecast is not an AWS invoice.

## 7. Latest pooled recorded outcomes

All 1,096 saved grades were readable and matched their applicable sealed export/history commitments; their backup receipts matched the master snapshot's pinned references. There were no verification failures, recorded collection errors or recorded oracle failures in this extraction. This reused existing archive verification; it did not freshly download and reverify every complete archive or S3 object.

These are execution-level counts pooled across arms. They are not model leaderboard scores, final weighted primary estimates, independently sampled caller rates or evidence of an arm's superiority.

| Stored endpoint | TRUE | FALSE | UNKNOWN | Eligible completed executions |
|---|---:|---:|---:|---:|
| Final business state correct | 994 | 102 | 0 | 1,096 |
| Correction success | 340 | 102 | 0 | 442 |
| Clean useful-task success | 654 | 0 | 0 | 654 |
| Correct supported final update | 889 | 199 | 8 | 1,096 |
| Forbidden effect | 0 | 1,096 | 0 | 1,096 |
| Unsupported decisive exposure | 4 | 1,045 | 47 | 1,096 |
| Incompatible stale exposure | 0 | 1,049 | 47 | 1,096 |
| Corrective delivery after challenge | 70 | 0 | 0 | 70 |
| Complete corrective communication | 23 | 35 | 12 | 70 |

Useful shorthand: 90.7% correct final business state, 76.9% correction success, 100% observed clean useful success, and 81.1% correct supported final update. State the denominator and the ongoing pooled status each time. Zero observed forbidden effects does not prove zero risk; the 47 unknown exposure records cannot be counted as safe.

All 70 eligible completed recovery-challenge executions recorded an ordinary supported corrective update; only 23 recorded complete corrective communication, with 35 FALSE and 12 UNKNOWN. The stricter endpoint requires withdrawal when necessary, so a later correct appointment statement does not automatically satisfy it. These counts alone do not prove P2's durability advantage or identify the cause of each deficit.

Raw driver statuses are 991 COMPLETED and 105 FAILED. Of the latter, 101 have a recorded narrowly recognized EXPECTED_EVIDENCE_REFUSAL classification; the other four retain historical failure/timing classifications. These raw statuses are preserved, not converted to successful bookings. A refusal can be appropriate evidence-based behavior while leaving the business or speech task unsuccessful. No claim of zero historical infrastructure/control defects is supported.

The 4 recorded unsupported-exposure outcomes are sequences 59, 507, 849 and 931. They are retained, not excluded or regraded. The 47 exposure UNKNOWN outcomes and incomplete campaign block a broad safety conclusion.

The accepted protocol keeps formal paired arm comparison for the final analysis; this meeting snapshot does not provide a B3/P1/P2 win ranking. Even perfect clean performance and passing implementation checks do not establish novelty or primary superiority.

## 8. Potential contribution and what already exists

The following primary sources establish that important ingredients and related evaluation problems are already known:

- AWS documents idempotent API/retry design, including changed intent: [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).
- LiveKit documents interruption handling and conversation-history truncation: [Turns overview](https://docs.livekit.io/agents/logic/turns/). Its wording about heard content is a framework-level playback/history model, not a human comprehension measure for this study.
- Twilio documents playback mark and clear messages: [Media Streams WebSocket messages](https://www.twilio.com/docs/voice/media-streams/websocket-messages). A mark can follow normal completion or buffer clearing; it must be interpreted with the protocol history.
- Realistic full-duplex grounded voice evaluation already exists: [tau-Voice, March 2026](https://arxiv.org/abs/2603.13686). The present synthetic protocol percentages are not comparable to that benchmark's model scores.
- A recent survey explicitly discusses grounded outcomes, recovery and timing: [Evaluating Real-Time Voice Agents: From Component Quality to Grounded Outcomes, September 2026](https://arxiv.org/abs/2609.30798). It is relevant literature to review, not a claim of full coverage by this brief.

Do not tell a professor that industry lacks idempotency, interruption support, durable workflows, tool verification or voice-agent benchmarks. Public documentation also cannot establish the absence of a mechanism from every vendor's private implementation.

The proposed research contribution is narrower: an explicit cross-layer contract connecting accepted intent, ordinary provider evidence, resource version, authorized outcome claim and measured protocol exposure; durable obligation to correct already exposed incompatible content; and a controlled, independent-oracle comparison measuring the incremental effect over a competent baseline. Which parts are novel requires a focused systematic literature comparison, not an absence inference from this short search.

Defensible wording: "I am evaluating whether an explicit revision- and evidence-bound claim/repair protocol offers incremental protection over an already careful agent integration, and under which commit/playback/recovery conditions it does so."

The known shared revision-only claim-selection limitation remains disclosed. A committed cancel/create replacement chain can coexist with a selected reschedule claim that ordinary evidence cannot support; then correct business state and refusal of confirmation can occur together. The studied behavior was not silently improved during experiment-control amendments. Refusal-classification fixes changed continuation handling, not application claim selection or retrospective grades.

This is an empirical reliability study, not a new foundation model, a proof of global exactly-once behavior, a real-call safety certification or a completed paper. If the main arms tie, the appropriate result is no demonstrated incremental primary benefit within this tested scope, accompanied by the retained mechanism and limitation evidence.

## 9. Suggested 60-90 second explanation

"My final-year project studies consistency between an AI agent's external actions and the confirmations it delivers. For example, an appointment can be committed even when the API response is lost, while the user changes the requested time and an earlier confirmation is already buffered or partly played. I built a PostgreSQL-backed protocol that records accepted revisions, reconciles ambiguous effects before retrying, authorizes decisive claims using applicable evidence, and persists correction obligations when incompatible content has already been exposed.

I am comparing a competent baseline with two mechanism configurations: claim permits, and claim permits plus durable repair. The fixed study has 500 inputs and 1,500 serial original executions, with independent simulator truth and full observation windows. At today's verified snapshot, 1,096 executions are backed up; pooled final business correctness is 90.7%, but the study also records unsupported exposures, unknown evidence and incomplete corrective communication. The experiment uses scripted protocol audio, so I am not claiming real-call speech reliability or superiority yet. I would welcome your guidance on literature positioning, rigorous analysis and a small research software task where I could contribute."

## 10. Questions to rehearse

**Are B3, P1 and P2 models?** No. They are mechanism configurations; the main campaign uses typed intents and scripted protocol playback to isolate backend/communication behavior.

**Why not just interrupt speech?** That can stop future output; it does not undo an external commit, establish the latest truth, or ensure a correction is delivered after earlier incompatible content was exposed.

**Why does correct business state sometimes have no confirmation?** The independent oracle may know a simulator effect occurred while ordinary observations available to the application do not establish the selected claim. A receipt is only as strong as its available evidence and applicability.

**Does the baseline already verify?** Yes. B3 retains established safeguards and ordinary corrective statements, including its evidence-based refusal path. The question is incremental protection, not beating an intentionally careless baseline.

**Is your system 90.7% reliable?** That is one pooled interim business-state endpoint on the current synthetic input subset. It is not overall end-to-end voice reliability, an arm-specific result or a population guarantee.

**Does a playback ACK mean the person understood?** No. All current main evidence is SCRIPTED_TONE_SEMANTIC_PROXY. Human comprehension, real acoustic alignment and real microphone/model error rates are not measured here.

**What if all arms tie?** Report the tie and the tested limits. A working mechanism or extra internal record is not automatically an observable advantage, novelty or publishability.

**What are the main limitations?** Fixed recipe support; synthetic intent/playback; finite windows; missingness/UNKNOWN; shared-host/time dependence; shared claim selection; several versioned experiment-control amendments; final paired analysis still pending.

**How did you develop it?** Explain your own design, implementation and debugging responsibilities accurately, including AI-assisted development where applicable. Be able to trace a retained failure and its evidence rather than reciting terms.

**What can you contribute to the group?** Python/API development, experiment automation, data validation, fault/recovery tests, trace analysis, evidence packaging and reproducible documentation. Ask for a small scoped initial task and agree a realistic weekly commitment.

## 11. What to take to the meeting

Updated CV; this brief; the arm/stratum tables; a retained event sequence; the verified pooled summary with its cutoff; and a repository or sanitized code sample you can actually share. Do not invent a public release link, journal acceptance, peer-review status or publication. No email or external sharing was performed in preparing this brief.

## Evidence provenance

- Local authority: `research/arms.py`, accepted Phase 8 review/freeze documents, v11 runtime report and retained independent grades.
- Verified outcome derivative: `pooled-outcomes.json`; canonical SHA-256 `52c9adb4d0c52a8dd3f51e0be4009dea1d00e2a2bfc81c7247cb5a344b5a74f7`.
- The extractor checked all 1,500 saved identities/order in one consistent master snapshot and all completed original receipt/export commitments. It read saved outcomes only: no scenarios, regrading, pause release, source changes, archival downloads or study changes.
- The pooled field for recorded refusal classification reads the existing `classification` key correctly; this derivative-field correction does not recompute a refusal or change any original result.

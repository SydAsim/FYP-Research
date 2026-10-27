# Commit-Aware Agents: Linking Transactional Evidence to Outcome Claims and Durable Correction

**Syed Asim Bacha**

Department of Computer Science, Islamia College Peshawar, Pakistan

syedasimbacha5@gmail.com

*Work-in-progress draft for scope review | 24 October 2026 | Independent undergraduate research*

## Abstract

Tool-using agents can reach a correct business state while delivering an unsupported confirmation, or withhold confirmation because the available evidence does not justify the selected claim. We study this separation under changing requests, ambiguous external commits and delayed playback. The proposed protocol binds outcome claims to accepted intent revisions and provider resource versions, and persists correction obligations for incompatible content already exposed. A controlled study compares a competent baseline with claim-permit and permit-plus-repair configurations on 500 inputs, yielding 1,500 planned executions. At an interim cutoff, 1,318 executions have verified stored grades: 1,198 have correct final business state, 1,068 have a correct supported final update, and 31 of 93 eligible recovery-challenge executions meet the stricter complete-correction endpoint. These pooled descriptions establish neither comparative superiority nor real-speech reliability. Typed intents and scripted tone/playback traces isolate protocol behavior. Final paired analysis remains pending; applicability to software-update agents is a transfer hypothesis.

**Keywords:** tool-using agents; commit ambiguity; evidence-bound claims; durable repair; protocol evaluation

## 1. Problem and research question

An agent may book an appointment successfully even when the provider response is lost. If the user then changes the requested time, retrying the first request can duplicate effects, while cancelling local audio cannot undo an external commit. A previously generated confirmation can also become stale before publication or after partial playback. The system must distinguish what happened, what its observations establish, and what content the client exposed.

This study asks: **when do explicit claim permissions and durable correction obligations add observable protection beyond a competent baseline's existing checks?** Correct final state alone cannot answer this question. A later correct statement also need not retract an earlier incompatible statement. Conversely, an evidence-based refusal may be appropriate while leaving the requested business or communication task unsuccessful.

The work investigates a cross-layer contract and a controlled measurement instrument. Idempotent API design already addresses retries, side effects and changed intent [1]. Tool-agent benchmarks evaluate policy compliance and final database state [2]; grounded full-duplex voice evaluation also exists [3]. LiveKit provides interruption and conversation-history handling [4]. These foundations motivate testing the incremental effect of the proposed revision/evidence/claim/repair composition. A systematic comparison remains necessary to establish its novelty.

## 2. Contract and implemented system

The application manages property-maintenance appointments. A model proposal becomes authoritative only when deterministic code accepts an intent revision in PostgreSQL. PostgreSQL stores correctness-relevant records; Redis is optional and disposable. Orthogonal dimensions track intent, external effect, evidence, claim permission, playback and repair instead of collapsing them into one linear success state.

After a possibly sent request times out, its effect remains UNKNOWN until reconciliation establishes whether retry is safe. A materially changed request receives a linked new logical operation. The proposed speech path requires an applicable, deterministically authorized claim; model prose and tool-return text cannot directly authorize decisive outcome speech. The main experiment supplies typed intents, so it does not measure proposal-model or speech-recognition accuracy.

<!-- PAGE_BREAK -->

## 2.1. Evidence, permission and correction

A verification receipt records the workflow, operation, accepted intent revision, claim predicates, observed resource version, source and validity interval. Its result is SATISFIED, VIOLATED or UNKNOWN. A claim permit authorizes a specific statement using applicable evidence; it is neither a business commit nor ground truth. Applicability is rechecked at the configured publication/playback gates. New revisions invalidate incompatible unplayed claims.

Generation, queuing, publication, playback start, partial playback, completion and interruption are separate events. If incompatible decisive content was already exposed, suppressing future output is insufficient. The repair configuration persists an obligation, supports recovery/discovery after interruption, and records delivery or escalation. Obligation creation and eventual externally evidenced correction are graded separately. Missing completion acknowledgements do not establish silence or successful delivery.

Table 1. Main configurations. Differences are mechanisms, not different language models.

| Arm | Retained safeguards and incremental mechanism |
| --- | --- |
| B3: competent baseline | Durable idempotency, reconciliation before retry, revision invalidation, staging, compensation, playback tracking and ordinary corrective statements. Its ordinary evidence checks can refuse unsupported claims. |
| P1: claim prevention | B3 safeguards plus explicit product-state invariants and revision/resource-bound claim permits. |
| P2: prevention and repair | P1 plus durable played-span repair obligations and their discovery/delivery path. |

B3 receives full outcome credit for an ordinary supported corrective statement. It does not need P1/P2 receipt objects to justify a claim. Earlier B0-B2 ablations exist in the project, but they are outside this three-arm main campaign.

## 3. Fixed study design and independent measurement

The declared sampling frame combines 50 fixed simulator recipes with generated appointment context. Within each stratum, recipes are drawn uniformly with replacement and context draws follow the recipe constraints. The input draw is the sampling unit; arms are paired within input. The fixed allocation is 300 CLEAN, 100 HIDDEN_COMMIT, 60 PLAYOUT and 40 OTHER_BOUNDARY inputs. Every input receives B3, P1 and P2 with the same provider capabilities, fault specification and budgets, giving 1,500 original executions. These are not 1,500 independent scenarios or sampled real callers.

Inputs and arm order are saved before execution. The main schedule is serial, using fresh resource bindings and named fault barriers rather than approximate race sleeps. Each original retains a 600-second observation horizon after its final externally issued request, including normal returns and recognized refusals. Missing anchors, gaps, timeouts, late effects and unresolved records remain explicit. Checkpoint recovery preserves execution identity and deadline without replaying commands.

Business truth comes from the simulator's append-only effect log and the externally scripted final target, independently of the controller's receipt or belief. Claim support uses ordinary observations available at the recorded event time; publication, decisive exposure and acknowledgement receipt times remain distinct. An arm-independent grader separates business correctness, support, incompatible exposure, final update, explicit withdrawal and repair telemetry. Missing relevant evidence is UNKNOWN.

The two co-primary endpoints are correction success on 200 correction inputs and unsupported decisive exposure on 100 hidden-commit inputs. P2 versus B3 is primary. The clean useful-task tolerance is five percentage points. Thirty-three predeclared inputs test recovery challenges. Their fixed denominators credit ordinary baseline updates and do not condition the main delivery comparison on post-treatment exposure.

<!-- PAGE_BREAK -->

## 4. Verified interim observations

The evidence cutoff is **24 October 2026, 01:25 Pakistan time** (23 October, 20:25 UTC). Of 1,500 originals, 1,318 are BACKED_UP, one is running and 181 are unstarted. The completed prefix represents 440 inputs: 439 complete three-arm sets and one P1-only set. Completed arm counts are B3 439, P1 440 and P2 439. Completion is evidence-retention progress, not a business-success rate.

A bounded read-only extractor checked every completed grade against its applicable sealed export or retained manifest commitment, checked master-bound backup receipts, and verified all 1,500 saved identities/order. All 1,318 grades were available, with no extraction-verification, recorded collection or recorded oracle failures. This reused earlier archive verification; it did not freshly revalidate every full S3 archive or rerun the oracle. The snapshot and source commitments accompany this draft.

Table 2. Pooled stored grades across arms; descriptive and incomplete. Every row states its eligible completed-execution denominator. TRUE is adverse for unsupported exposure and forbidden effects. Structural N/A is excluded only from that endpoint's eligible count.

| Stored endpoint | TRUE | FALSE | UNKNOWN | Eligible n |
| --- | ---: | ---: | ---: | ---: |
| Final business state correct | 1198 | 120 | 0 | 1318 |
| Correction success | 424 | 120 | 0 | 544 |
| Clean useful-task success | 774 | 0 | 0 | 774 |
| Correct supported final update | 1068 | 242 | 8 | 1318 |
| Unsupported decisive exposure: all strata | 4 | 1261 | 53 | 1318 |
| Unsupported decisive exposure: hidden commit | 0 | 259 | 0 | 259 |
| Forbidden effect | 0 | 1318 | 0 | 1318 |
| Supported update after recovery challenge | 93 | 0 | 0 | 93 |
| Complete corrective communication | 31 | 48 | 14 | 93 |

Within this completed pooled subset, final business correctness is 90.9%, whereas correct supported final update is 81.0%. These are different marginals, not a computed count of their overlap. Among 93 eligible challenge executions, all record a supported update, but only 31 meet complete corrective communication; 48 are FALSE and 14 UNKNOWN. The stricter endpoint also requires explicit withdrawal when necessary and grants success when none is required. A later update and complete correction therefore cannot be treated as interchangeable endpoints.

The four recorded unsupported-exposure outcomes occur in PLAYOUT, at sequences 59, 507, 849 and 931; they remain included. The 53 UNKNOWN exposure records are not counted as safe. Zero recorded forbidden effects, or zero adverse hidden-commit exposures in this interim subset, does not prove zero risk. No arm ranking, significance test, resampling or adaptive design change was performed for this draft.

## 4.1. Retained failure trace: correct state, unsupported selected claim

Original sequence 145 provides a concrete example. The initial booking committed before its deliberately dropped response. Reconciliation then cancelled it and created a corrected appointment because in-place rescheduling was unsupported. Recorded provider observations were authoritative HTTP-200 CREATE/CANCEL/CREATE facts. Yet the frozen B3 synthesis path selected RESCHEDULED_APPOINTMENT because the accepted revision exceeded one. That predicate was VIOLATED, so the backend refused the non-retryable speech request.

Its preserved grades report correct final business state and correction success, no forbidden effect, and no correct final update. This demonstrates a separation of endpoints, not superiority of a proposed arm. P1/P2 and later-revision repair share this revision-only claim-selection limitation. Runner amendments recognize narrowly evidenced refusals for collection/continuation; they do not improve that studied behavior or replace original grades.

<!-- PAGE_BREAK -->

## 5. Pending analysis and validity limits

Final analysis retains all planned eligible originals, including failures and missing records. It estimates standardized paired risk differences over the declared recipe/context mixture. Correction-stratum weights are 0.5/0.3/0.2 for hidden commit/playout/other boundary. Conservative paired bounds and worst/best missingness bounds are retained; the two co-primary claims use Bonferroni allocation, with Holm adjustment for the declared secondary family. P1-B3 and P2-P1 comparisons examine mechanism increments. No final effect estimate or noninferiority claim is available yet.

The accepted timing plan keeps all arm rows together in an input-cluster bootstrap, plus censored lognormal accelerated-failure-time analysis with arm and stratum terms. Missing anchors and collection gaps are not ordinary administrative censoring. Fit failures and sensitivity to omitting each of 20 saved order blocks must be reported. Conditional recipe independence does not remove shared-host, temporal or operational-version dependence.

All 1,318 inspected voice-evidence records are labelled SCRIPTED_TONE_SEMANTIC_PROXY. Typed requests and scripted playback support protocol-state, evidence-applicability and acknowledgement comparisons, not intelligible-word exposure, human understanding, speech-model quality or real-call usability. Client acknowledgements are not proof that a person heard or understood a message. The fixed explicit-withdrawal matcher is not an open-language semantic evaluator. Real-speech transfer would require independent alignment/playback evidence and a separately reviewed protocol.

The shared claim-selection limitation may constrain outcome coverage in every arm. Final interpretation must concern these frozen implementations rather than idealized mechanisms. Raw statuses remain 1,188 COMPLETED and 130 FAILED; 126 failures have recorded EXPECTED_EVIDENCE_REFUSAL classifications, while four retain historical failure/timing records. A recognized refusal is not a successful booking. Versioned experiment-control amendments, pauses and unsuccessful operational attempts are retained; this is not an uninterrupted endurance run or a guarantee of error-free infrastructure.

## 6. Relevance to agentic software updates

The evidence-binding question may transfer to software-update agents: a requested target revision could include a package/lockfile or artifact digest; applicable observations could include tests, deployment generation and health evidence; a consequential claim could state that a release or rollback is complete. A superseded target or delayed observation could invalidate such a claim after an external action. This mapping motivates discussion of provenance and autonomous release decisions, but the current study has no repository-update, security-patch, canary or deployment benchmark. Its fit to AgSU is therefore a scope question for the organizers, not an established evaluation result.

## 7. Conclusion

This work-in-progress presents an implemented commit/evidence/claim/repair contract and an ongoing controlled study. The verified pooled observations show why final state, supported confirmation and complete correction must be reported separately. Whether explicit permits and durable repair add protection beyond B3 remains a final-analysis question. A tie or bounded negative result will be reported within the declared synthetic scope.

**AI-assistance disclosure (draft).** OpenAI Codex assisted software development, experiment tooling and manuscript preparation. Human author review and approval of this draft remain required before submission; the author retains responsibility for the work. No AI system is listed as an author.

## References

[1] Featonby M. Making retries safe with idempotent APIs. Amazon Builders' Library. https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/ (accessed 24 October 2026).

[2] Yao S, Shinn N, Razavi P, Narasimhan K. tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains. 2024. arXiv:2406.12045. https://doi.org/10.48550/arXiv.2406.12045.

[3] Ray S, Dhandhania K, Barres V, Narasimhan K. tau-Voice: Benchmarking Full-Duplex Voice Agents on Real-World Domains. 2026. arXiv:2603.13686. https://doi.org/10.48550/arXiv.2603.13686.

[4] LiveKit. Turns overview. LiveKit Agents documentation. https://docs.livekit.io/agents/logic/turns/ (accessed 24 October 2026).

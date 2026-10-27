# Commit-Aware Agents: Separating Business Correctness, Evidence-Bound Claims, and Corrective Delivery

**Syed Asim Bacha**

Department of Computer Science, Islamia College Peshawar, Pakistan

syedasimbacha5@gmail.com

*Full research manuscript for review | 25 October 2026 | Independent undergraduate research*

## Abstract

An agent can change an external resource correctly while lacking evidence for its confirmation; a later correct update can also leave an earlier incompatible statement unwithdrawn. We investigate these distinctions in a maintenance-booking system with changing requests, ambiguous commits, and delayed playback. A competent baseline, B3, includes durable idempotency, reconciliation, revision invalidation, staging, compensation, playback tracking, and ordinary corrective updates. P1 adds explicit claim permits and product-state invariants; P2 additionally persists played-content repair obligations. A fixed synthetic study runs 500 paired inputs across the three arms, retaining all 1,500 originals and their 600-second observation windows. Each arm achieves 455/500 correct final business states and 155/200 successful corrections, with identical paired business outcomes. No incremental benefit is demonstrated on the two co-primary endpoints. In 33 predeclared recovery inputs, every arm delivers an ordinary supported update; complete corrective communication is TRUE in 33/33 P2 inputs, versus 26 FALSE and seven UNKNOWN for each comparator. This secondary result is bounded by a fixed withdrawal-template grader and scripted tone/playback acknowledgements. The study contributes an implemented protocol and auditable endpoint separation, rather than evidence of general voice-agent superiority or human-belief repair.

**Keywords:** tool-using agents; transaction uncertainty; claim authorization; durable repair; protocol evaluation

## 1. Introduction

Suppose an agent requests an appointment at 12:15. The provider commits, but the response disappears. The user then requests 14:15. Retrying the first operation can duplicate effects; stopping audio cannot undo a booking; and changing the database does not retract a confirmation that has already reached playback. These events cross distinct boundaries: accepted intent, external effect, available evidence, publication, playback, and correction.

Idempotent APIs already address retry safety and changing intent [1]. Transactional agent runtimes and revision-recovery systems address related effect and validity problems [2-5]. The question here is incremental: **when do evidence-bound claim permission and durable corrective delivery provide observable protection beyond a competent baseline's existing safeguards?**

The experiment separates business correctness from communication correctness. A backend refusal can be appropriate even if the requested speech outcome is unsuccessful. Conversely, normal driver completion does not establish the correct business state. An ordinary corrected statement is credited in every arm; the baseline is not required to possess the proposed receipt objects.

This paper makes three bounded contributions: an implemented revision/evidence/claim/repair contract; a paired, fixed-frame evaluation with separately observable endpoints and preserved UNKNOWNs; and a completed result showing a primary business-outcome tie alongside a narrower distinction in explicit corrective communication. These are implementation and measurement contributions. They are not a new transaction primitive, a proof of universal safety, or a claim that existing systems lack correction mechanisms.

<!-- PAGE_BREAK -->

## 2. Related work and contribution boundary

**Transactional effects and uncertain completion.** Safe idempotent API design distinguishes duplicate requests from changed intent [1]. Atomix gates settlement using progress-aware transactions and effect classification [2]. Cordon stages external effects within a task-scoped boundary with lineage and authority checks [3]. These are direct antecedents: irreversible-effect gating and recovery are not new here. Our empirical question concerns the relationship between resource evidence and the lifecycle of an outcome statement, including correction after previously exposed content.

**Revisions and recoverability.** Revisable by Design formalizes concurrent intervention and action reversibility [4]. REVISE preserves validity-established work while recomputing affected workflow regions [5]. DART studies admissible recovery boundaries after downstream commitment [6]. These works prevent a broad novelty claim about handling revisions, retaining progress, or recognizing irreversible consequences. Our study evaluates a specific booking implementation, rather than comparing their algorithms or proving a stronger recovery guarantee.

**Verification and receipts.** Verified Tool Calls combines postcondition verification, idempotency, and verify-before-retry behavior [7]. Tool Receipts links response claims to execution evidence [8]. Consequently, neither verification before retry nor evidence-backed claims is asserted as original in isolation. The proposed composition additionally treats accepted intent revision, resource version, exposure, and persistent corrective obligations as separately recorded concerns.

**Playback and dialogue repair.** Incremental speech-generation research already addresses self-monitoring and revision during output [9]. PACE aligns model-facing context with client playback and distinguishes physical playback evidence from semantic commitment and comprehension [10]. Our protocol also distinguishes generated and exposed output, but evaluates truth/evidence applicability and explicit withdrawal after changing booking targets. It does not reproduce PACE's live speech-model evaluation or establish superiority over it.

**Evaluation.** Tau-bench evaluates tool-agent-user interaction using final database state [11]; tau-Voice extends grounded evaluation to full-duplex audio [12]. Our typed-intent, scripted-tone path isolates protocol behavior. Its results cannot be numerically compared with their model success rates. It measures neither speech recognition nor a language model's ability to choose an intent or formulate a correction.

These comparisons are a targeted primary-source review, not an exhaustive systematic review. The strongest candidate contribution is the integrated, auditable evaluation of business state, available evidence, exposure, and explicit corrective delivery against an already protected baseline. The study does not establish priority for that entire combination. External novelty assessment remains a peer-review question, especially given the close transactional and playback literature.

## 3. System and correctness model

The application manages property-maintenance appointments. A model proposal has no authority to create business records directly. Deterministic acceptance establishes a new intent revision in PostgreSQL, which is the durable correctness authority. Redis is disposable. The experiment injects typed requests and therefore bypasses recognition and proposal-model uncertainty.

The operation is represented by orthogonal dimensions rather than a single linear success state. A request can have a committed external effect, UNKNOWN local knowledge, an invalidated claim, and an outstanding repair obligation simultaneously. External simulator truth is distinct from the observations available to the application.

<!-- PAGE_BREAK -->

## 3.1. Evidence-bound permission

After a possibly sent operation times out, the effect remains UNKNOWN until reconciliation establishes whether a retry is safe. A materially changed request receives a linked logical operation. A verification receipt records the accepted revision, operation, claim predicates, resource version, evidence provenance, and validity interval, with SATISFIED, VIOLATED, or UNKNOWN results. A permit authorizes a particular claim using applicable evidence; it does not establish that an external transaction committed.

Applicability is checked at the configured publication/playback gates. A newer accepted revision can invalidate an unplayed claim. Provider changes can invalidate resource-version evidence even when an appointment-time phrase remains true. Model prose and tool-return text do not independently authorize decisive outcome speech. B3 uses its ordinary evidence checks and can also refuse an unsupported statement.

## 3.2. Exposure and durable repair

Generation, publication, playback start, progress, completion, and interruption are separate events. If incompatible decisive content has already been exposed, suppressing a future segment does not withdraw it. P2 persists an obligation, attempts an applicable corrective statement, and retains its delivery state. Duplicate or delayed acknowledgements must be processed without losing already recorded effects.

Figure 1. Independent dimensions of the implemented contract. Rows may coexist; this is not a sequence of mutually exclusive states. The experiment observes scripted exposure, not a person's understanding.

<!-- CONTRACT_FIGURE -->

Table 1. Explicit main-study profiles. Incremental switches are read from the frozen arm configuration; ordinary supported baseline updates receive full outcome credit.

| Arm | Safeguards and incremental mechanism |
| --- | --- |
| B3 | Durable idempotency; reconcile before retry; revision invalidation; staging; compensation; playback tracking; ordinary corrective statements and evidence checks. |
| P1 | B3 plus explicit claim permits and product-state invariants. |
| P2 | P1 plus durable repair of previously played incompatible content. |

## 3.3. Observable endpoints

The independent grader reads scripted accepted targets, simulator truth, ordinary observations, output segments, and client testimony. It does not use an arm label, receipt verdict, permit identifier, or internal obligation state to decide observable success. Internal repair persistence/completion is reported separately as mechanism telemetry.

The endpoints distinguish final business state; claim truth and supporting evidence at publication/playback; incompatible stale exposure; a correct supported final update; explicit withdrawal; and persistence/completion of repair. Missing relevant evidence or playback acknowledgements remains UNKNOWN. Introductory words do not establish decisive confirmation. All main-study audio evidence is labelled SCRIPTED_TONE_SEMANTIC_PROXY: word-index acknowledgements are logical proxies, without verified acoustic word alignment or human listening.

<!-- PAGE_BREAK -->

## 4. Study design and analysis

## 4.1. Frame, allocation, and execution

The frame combines 50 fixed simulator recipe families with generated appointment contexts. Recipes are sampled within strata with replacement under their context constraints. The target estimand is an arm difference over this declared recipe/context mixture, not a production population of callers, providers, or arbitrary agents. The input draw is the sampling unit; its three arm outcomes form a paired cluster. Repeated recipe families do not become independent domains.

Table 2. Fixed allocation. Each input receives all three arms, yielding 500 complete comparison sets and 1,500 original executions.

| Stratum | Inputs | Original executions | Correction weight |
| --- | ---: | ---: | ---: |
| CLEAN | 300 | 900 | Not applicable |
| HIDDEN_COMMIT | 100 | 300 | 0.50 |
| PLAYOUT | 60 | 180 | 0.30 |
| OTHER_BOUNDARY | 40 | 120 | 0.20 |

The saved input identities and serial order are retained. Comparable provider capabilities, faults, evidence availability, and budgets apply across arms. Named barriers control intended event order. Each original retains a 600-second collection horizon anchored to the saved final-request deadline, including recognized refusals. Checkpoint recovery preserves identity and deadline without replaying commands. Calibration and diagnostic runs are separate from main outcomes.

All 1,500 originals reached BACKED_UP. The ledger contains one admission, export, and backup transition per original; all export transitions follow their saved observation deadlines. This verifies window accounting, not perfect event capture. Failures, timeouts, refusals, and UNKNOWN values are retained. The campaign had pauses and versioned experiment-control amendments; it was not an uninterrupted reliability endurance run.

## 4.2. Prespecified comparisons and missingness

The co-primary P2-B3 comparisons are correction success on 200 non-clean inputs and unsupported decisive exposure on 100 hidden-commit inputs. Correction risk differences standardize saturated arm-by-stratum means using weights 0.50/0.30/0.20. Conservative paired component bounds allocate error across strata and the two co-primary quantities; each reported co-primary interval is 97.5%. Clean-task usefulness has an accepted five-percentage-point tolerance with a one-sided 95% bound. Secondary P1-B3 and P2-P1 contrasts examine incremental mechanisms.

The 33 recovery inputs are designated before analysis; eligibility does not depend on an arm creating its own repair obligation. Ordinary supported updates and complete corrective communication are distinct. Planned-denominator best/worst assignments retain missing outcomes. The ten-comparison Holm family reports diagnostic paired tests, not permission to reinterpret UNKNOWNs as successful prevention. Twenty fixed temporal-block omission summaries assess the primary correction contrast.

## 4.3. Timing

The accepted timing computation uses a 600-second restricted horizon, 2,000 stratified paired input bootstrap draws (seed 8042051), and a right-censored lognormal accelerated-failure-time model with arm and stratum terms. Its 1,000 bootstrap draws (seed 8042052) resample input IDs with all three arms together. This is time to a supported scripted-ACK completion, not complete corrective communication or human call latency. Shared-host dependence, censoring validity, and model form remain assumptions. The analysis retains its restricted claim-permission flags; computation alone does not validate them.

<!-- PAGE_BREAK -->

## 5. Results: business state and supported claims

Table 3. Final stored grades. Fractions use all planned inputs eligible for that endpoint. TRUE is adverse for unsupported exposure and forbidden effects.

| Endpoint | B3 | P1 | P2 |
| --- | ---: | ---: | ---: |
| Correct final business state | 455/500 | 455/500 | 455/500 |
| Clean task success | 300/300 | 300/300 | 300/300 |
| Correction success | 155/200 | 155/200 | 155/200 |
| Correct supported final update: TRUE | 408/500 | 408/500 | 408/500 |
| Correct supported final update: UNKNOWN | 0/500 | 4/500 | 4/500 |
| Forbidden effect recorded | 0/500 | 0/500 | 0/500 |

Business correctness is 91% for every arm, with correction outcomes identical input by input: 73/100 hidden commit, 56/60 playout, and 26/40 other boundary. The weighted correction difference is zero; its conservative 97.5% interval is [-8.79, +8.79] percentage points (pp). The hidden-commit adverse-exposure comparison is 0/100 per arm, with difference interval [-4.95, +4.95] pp. These results demonstrate no incremental benefit on the co-primary endpoints; they do not prove universal equivalence or zero risk.

All 300 clean inputs succeed per arm. The P2-B3 one-sided 95% lower bound is -1.22 pp, above the accepted -5 pp tolerance under the frozen conditional rule. Every primary correction block-omission estimate remains zero. Neither result establishes independence or stationarity for timing or secondary endpoints.

Table 4. Unsupported exposed claims across all 500 inputs per arm. No UNKNOWN is counted as safe.

| Stored grade | B3 | P1 | P2 |
| --- | ---: | ---: | ---: |
| TRUE | 4 | 0 | 0 |
| FALSE | 481 | 481 | 481 |
| UNKNOWN | 15 | 19 | 19 |

The four B3 TRUE outcomes occur in the version-change-before-start playout recipe. Their P1/P2 counterparts are UNKNOWN. Thus the observed 4-versus-0 TRUE count does not establish that permits eliminated exposure. None of the four belongs to the hidden-commit primary denominator. Incompatible stale exposure has zero TRUEs but 15 UNKNOWNs for B3 and 19 each for P1/P2. Content can become outdated after a later accepted request even when it was compatible when originally played.

## 5.1. Driver status is not the outcome

The raw statuses are 1,359 COMPLETED and 141 FAILED, with 47 failures per arm. All 141 FAILED records nevertheless have correct final business state, and none records a supported final update. Conversely, 135 COMPLETED records have incorrect final business state. The paired business result is therefore not a renamed driver success rate. Original failures and grades remain unchanged. Available compact records do not justify calling every historical exception an expected refusal; such a classification requires its original evidence and response context.

<!-- PAGE_BREAK -->

## 6. Corrective communication and timing

All three arms deliver an ordinary supported corrected update in each of the 33 designated recovery inputs. Complete corrective communication is TRUE for all 33 P2 inputs; B3 and P1 each have 26 FALSE and seven UNKNOWN. A claim that the baseline never corrects the appointment would contradict these results.

Figure 2. Complete corrective communication in the 33 planned recovery inputs per arm. FALSE and UNKNOWN remain distinct; the endpoint includes the fixed explicit-withdrawal criterion. Ordinary supported updates succeed in 33/33 for every arm.

<!-- COMMUNICATION_FIGURE -->

The recovery families comprise full playback before correction (9 inputs), delayed decisive acknowledgement (7), partial decisive-time playback (7), reconnect with another revision (7), and restart before repair (3). P2 is TRUE throughout. Comparator FALSEs occur in the first, second, fourth, and fifth families; the partial-time family supplies all seven comparator UNKNOWNs.

For P2-B3 and P2-P1, 26 known pairs favor P2, none favors the comparator, and seven pairs are missing. The exact McNemar diagnostic p-value is 2.9802e-8; the ten-family Holm diagnostic value is 2.9802e-7. These complete-pair diagnostics are not missingness-free confirmatory claims. Assigning all possible binary values to the seven baseline UNKNOWNs yields an empirical planned-denominator difference range of +78.79 to +100 pp. That range is an identification bound, not a confidence interval.

P2 telemetry records 40 obligations across the 33 inputs, all REPAIR_PLAYED. Additional obligations occur after another revision. This supports retained obligation/playback-state accounting. It does not independently prove unattended discovery: the sampled repair trace includes experiment-invoked worker processes. Observable communication grades do not use those internal obligation states.

**Measurement qualification.** The frozen withdrawal matcher requires a supported, fully acknowledged update beginning with "Correction: my earlier confirmation was outdated." It is arm-label neutral but template-specific. The positive result partly reflects the intended output behavior and its matching instrument. It does not establish semantically superior natural-language repair, restored human belief, or benefit over an alternative ordinary phrasing.

Table 5. Conditional restricted-mean scripted completion-time differences. Positive values mean longer recorded time; intervals are paired input-bootstrap 95% intervals.

| Comparison | Difference (seconds) | Interval (seconds) |
| --- | ---: | ---: |
| P2-B3 | +0.2593 | +0.2241 to +0.2996 |
| P1-B3 | +0.2251 | +0.2041 to +0.2472 |
| P2-P1 | +0.0342 | +0.000073 to +0.07192 |

The timing set contains 1,224 completion events and 276 censored rows, without missing or zero times. All 1,000 AFT bootstrap fits converge. Conditional time ratios versus B3 are 1.2258 for P1 (interval 1.2044-1.2451) and 1.2265 for P2 (1.2034-1.2506). Lognormal form and independent censoring are unproven; convergence does not resolve either assumption. No faster-agent claim follows.

<!-- PAGE_BREAK -->

## 7. Trace interpretation and validity

**A correct transaction with a refused statement.** Sequence 145 begins with a committed booking and a deliberately lost response. Reconciliation cancels the first appointment and creates the corrected one because in-place rescheduling is unavailable. The synthesis path nevertheless selects RESCHEDULED_APPOINTMENT from the accepted revision number. That claim's predicate is VIOLATED, so B3 refuses the speech request with HTTP 409. Its raw FAILED status coexists with correct business/correction grades and an unsuccessful final-update outcome. P1/P2 share this revision-only claim-selection limitation; it was preserved, not silently repaired by a collector change.

**Evidence can expire without changing every word's truth.** Sequence 59, B3, records a provider resource change before playback. The original grade has TRUE truth at publication/playback but FALSE evidence at playback, with unsupported exposure TRUE and final business state FALSE. An appointment-time component can remain true while its resource/evidence binding is inapplicable. The trace illustrates why a scalar success label is insufficient; it is not a formal proof of completeness of the oracle.

**Another revision during repair.** Sequence 82, P2, retains an initial confirmation, an interrupted revision-two repair, a revision-three corrective statement, and delayed earlier testimony. Two obligations end REPAIR_PLAYED, with correct final state, update, and withdrawal grades. This is a concrete recorded repair path. Its explicitly invoked workers preclude presenting it alone as autonomous recovery evidence.

## 7.1. Threats to validity

**Construct validity.** Typed intents and tones isolate protocol state. Word-index ACKs do not verify intelligible audio, attention, or understanding. Missing terminal testimony remains UNKNOWN. The exact-prefix withdrawal test is narrower than general semantic retraction and may favor the particular repair template by construction. The complete communication difference must be read alongside equal ordinary-update performance. Repair telemetry is a mechanism observation, not an independent delivery oracle.

**Implementation validity.** The shared claim-selection limitation can withhold useful confirmations in all arms. Outcomes concern these implementations, not ideal mechanisms. Preventive permits and product-state invariants change together in P1, so their individual effects are not identified. P2 differs by the repair package, including its output behavior, rather than storage persistence alone. The study cannot attribute the secondary difference solely to durability.

**Statistical validity.** Five hundred context draws arise from 50 fixed families, not 1,500 independent tasks. Shared serial infrastructure, temporal drift, and operational interruptions weaken independence assumptions. The block sensitivity addresses the primary contrast only. The helper outputs retain confirmatory/model claim guards as false; this paper reports conditional bounds and diagnostic tests rather than overriding those restrictions.

Four raw timing records retain INFRASTRUCTURE_FAILURE labels (sequences 1, 2, 145, 616). A separate accepted view reuses only the previously approved first-two label sidecars, with identical numeric durations and outcomes; two infrastructure labels remain in that view. No new sidecar or retrospective regrade was applied. These histories do not establish independent administrative censoring. Restricted-horizon and AFT estimates therefore require qualified interpretation.

**Operational and external validity.** Nine admission-controller binding segments document amendments and pauses. A binding is a provenance reference, not per-process binary attestation. Hash verification and post-deadline exports establish integrity/accounting, not complete capture of every late event or deployment reliability. No natural callers, speech-model comparison, payment workflow, or software-update benchmark was evaluated. Generalization beyond the declared simulator frame remains untested.

<!-- PAGE_BREAK -->

## 8. Reproducibility, implications, and conclusion

All 1,500 originals, including unsuccessful outcomes, remain in the analysis. Identity/export/backup joins and 196,037 chained notices were checked; 3,450 frozen final-inventory file hashes still match after analysis. Operational provenance identifies each original's applicable controller binding. These checks do not imply that every original ran the final controller version.

The retained local result package contains the full 1,500-row CSV, compact original records, frozen-method outputs, verification records, reproduction commands, and three bounded trace examples. It does not contain all raw archives or the entire pinned runtime. The final returned evidence bundle has SHA-256 1d67c5adc39fc6ef6f9cfcaa32a910532be8a9faf824383946d5c2ed10426341. A separate companion evidence map records exact source/output hashes. No public archival DOI or anonymously accessible full artifact is claimed.

The principal result is an observed tie in business correctness beyond a strong baseline. The secondary result distinguishes an ordinary supported update from the implemented explicit-withdrawal criterion. This suggests a useful reporting discipline: distinguish effects, knowledge, exposure, and correction, and preserve refusal and missingness rather than equating either with success. It does not establish a breakthrough, general superiority, or durable repair's isolated causal effect. For software-update agents, artifact versions and deployment evidence offer a conceptual analogue; this study supplies no empirical software-update result. The completed study supports a bounded systems/measurement paper with a negative primary finding and a qualified secondary finding.

## References

[1] M. Featonby. Making retries safe with idempotent APIs. Amazon Builders' Library. https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/ (accessed 25 October 2026).

[2] B. Mohammadi, N. Potamitis, L. Klein, A. Arora, and L. Bindschaedler. Atomix: Timely, Transactional Tool Use for Reliable Agentic Workflows. arXiv:2602.14849v2, 2026. https://arxiv.org/abs/2602.14849v2

[3] Z. Chen, H. Liu, D. Xu, D. Dong, J. Li, B. Pu, and J. Zhai. Cordon: Semantic Transactions for Tool-Using LLM Agents. arXiv:2606.17573v1, 2026. https://arxiv.org/abs/2606.17573v1

[4] Z. Zhai, M. Li, and X. Wang. Revisable by Design: A Theory of Streaming LLM Agent Execution. arXiv:2604.23283v1, 2026. https://arxiv.org/abs/2604.23283v1

[5] R. Qi, X. Wu, P. Liu, J. Chen, and Y. Liu. REVISE: Validity-Guided Recovery for Online Revisions in Agent Workflows. arXiv:2609.00643v1, 2026. https://arxiv.org/abs/2609.00643v1

[6] K. Yang, P. Li, Z. Wu, K. Xu, H. Huang, and X. Huang. DART: Semantic Recoverability for Structured Tool Agents. arXiv:2605.23311v1, 2026. https://arxiv.org/abs/2605.23311v1

[7] I. K. Mansoor, A. Phadke, and P. Rana. Verified Tool Calls Improve LLM Agent Reliability Under Non-Atomic Failures. arXiv:2608.02645v1, 2026. https://arxiv.org/abs/2608.02645v1

[8] A. Basu. Tool Receipts, Not Zero-Knowledge Proofs: Practical Hallucination Detection for AI Agents. arXiv:2603.10060v1, 2026. https://arxiv.org/abs/2603.10060v1

[9] G. Skantze and A. Hjalmarsson. Towards Incremental Speech Generation in Dialogue Systems. Proceedings of SIGDIAL, pp. 1-8, 2010. https://aclanthology.org/W10-4301/

[10] S. Wang, Z. Zhang, L. Wang, and J. Ma. PACE: A Playback-Aligned Context Engine for LLM-Based Full-Duplex Voice Dialogue. arXiv:2608.07631v1, 2026. https://arxiv.org/abs/2608.07631v1

[11] S. Yao, N. Shinn, P. Razavi, and K. Narasimhan. Tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains. arXiv:2406.12045, 2024. https://arxiv.org/abs/2406.12045

[12] S. Ray, K. Dhandhania, V. Barres, and K. Narasimhan. Tau-Voice: Benchmarking Full-Duplex Voice Agents on Real-World Domains. arXiv:2603.13686, 2026. https://arxiv.org/abs/2603.13686

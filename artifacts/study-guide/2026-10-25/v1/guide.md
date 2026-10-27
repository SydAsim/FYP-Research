# PART I - Understand the idea before the mathematics

## 1. How to use this book

This is a learning companion to Syed Asim Bacha's eight-page full manuscript, dated 25 October 2026. It is written for a Software Engineering student preparing to explain the project to professors. The research manuscript and original grades are preserved. This book explains them; it does not create a new experiment, a new analysis, or an accepted publication.

The reading order is: follow the fictional booking story; learn the components; understand the experiment and numbers; read the original manuscript with its paragraph-by-paragraph explanations; then practise the difficult questions. You do not need to memorize every decimal before you understand the problem. Start by being able to explain what happened, what the agent knew, and what it was justified in saying.

For close reading, every one of the manuscript's 52 prose blocks is reproduced exactly and followed by an explanation, difficult-word definitions, an analogy, and a caution. All five tables and both figure captions are covered. Common connecting words such as 'the' are not assigned separate dictionary entries; the technical words and the meaning of each argument receive the detail. References are explained individually later, with their primary-source links.

There are three kinds of material in this guide. **Recorded result** means a fact from the retained study. **Teaching example** means an invented scenario used to explain a concept. **Possible future work** means something not established by this study. The realistic images are AI-generated fictional illustrations. They depict no actual participant, author, experiment, deployment screen, or AWS facility. The deterministic diagrams explain concepts; they are not replacement executable contracts.

## 2. The title, phrase by phrase

**Commit-Aware Agents.** An agent is software that coordinates actions toward a request. A commit is an action becoming durable at a system boundary, such as the appointment provider saving a booking. Commit-aware means the system represents the possibility that the provider has committed even when the controller has not received confirmation. It does not mean that a language model has magical awareness of an external database.

**Separating Business Correctness.** Business correctness asks whether the final requested appointment exists in the right state. A successful HTTP response or a polite voice message is not the definition. The independent simulator truth and accepted target are used to check it.

**Evidence-Bound Claims.** A claim is a statement such as 'your appointment is confirmed'. Evidence-bound means the statement must be supported by observations applicable to this operation, accepted request version, resource version, and time. A correct guess is not equivalent to justified knowledge.

**Corrective Delivery.** When a previously exposed statement becomes incompatible with the accepted target, a later message may need to identify it as outdated and provide a supported update. Delivery concerns recorded output events, not merely composing an apology. In this experiment, its observable basis is scripted playback acknowledgement rather than human understanding.

**The one-sentence project explanation:** I studied how to keep an agent's external actions, available evidence, spoken outcome claims, and recorded corrections consistent when requests change and tool outcomes are uncertain.

## 3. The story: Ali changes a maintenance appointment

<!-- STORY_IMAGE -->

**Fictional teaching story.** Ali is a resident reporting a leaking kitchen tap. He asks for a maintenance visit at 12:15. These names and conversations are explanatory inventions, not recordings from the campaign. The photo panels show a human setting; the main research itself used typed requests and scripted tones.

**Scene A - The request becomes accepted.** A recognizer or model could propose 'create an appointment at 12:15'. The backend validates the request and records accepted revision 1 in PostgreSQL. The important boundary is acceptance by deterministic server code. A partially recognized sentence is not automatically an accepted booking instruction.

**Scene B - The provider commits, but its reply disappears.** The worker sends a create request with a stable logical operation identity. The provider saves the appointment. Before the controller receives the reply, a simulated fault drops it. The controller times out. From the provider's truth, the appointment exists. From the controller's observations, the outcome may still be UNKNOWN. Both descriptions can be correct because they describe different knowledge boundaries.

**Scene C - Ali changes his mind.** Ali now asks for 14:15. The server accepts revision 2. It must determine what happened to revision 1 before issuing unsafe replacement writes. If it simply assumes the first request failed, a second create may leave two appointments. If it simply says 'cancelled', that may be unsupported. Revision 2 is a new desired target; it does not erase history.

**Scene D - Reconcile before retry.** The application asks an appropriate provider status/resource interface what actually exists. If it finds the first appointment, it plans the correction using supported capabilities. An in-place reschedule and cancel-then-create are distinct operation histories. If it cannot establish the state, it may retain UNKNOWN or hand off. 'Try again' is not automatically the safe answer.

**Scene E - Check what the agent may say.** A claim such as 'your appointment was rescheduled' has a predicate. If the provider actually cancelled one booking and created another, a claim that assumes an in-place reschedule may fail verification. The final appointment can be right while that selected claim is wrong. A permit is a scoped permission for supported wording, not proof that all possible confirmation statements are interchangeable.

**Scene F - The old message was already partly played.** Suppose the earlier 12:15 confirmation reached decisive content before the correction was accepted. Stopping the rest avoids more exposure, but it cannot make the earlier words unplayed. A supported update to 14:15 and an explicit withdrawal address different parts of the problem. P2 records repair work durably. If a client disconnects, that obligation should not exist only in a browser variable.

**Scene G - Observe and grade.** The research runner follows a planned scenario and retains the full observation window. An independent oracle checks provider truth and ordinary observations. A backup records an unsuccessful result just as faithfully as a successful one. There is no instruction to rerun the case until it succeeds.

## 4. Three facts that must not be merged

| Question | Possible answer in the story | What it does not establish |
| --- | --- | --- |
| What actually happened? | The provider saved the booking. | The controller necessarily knows it. |
| What does available evidence justify? | The reply was lost; support may be UNKNOWN. | Nothing happened at the provider. |
| What reached recorded playback? | A decisive time phrase was acknowledged. | A human attended to or understood it. |

Imagine a teacher sees a sealed envelope on a desk. The answer sheet inside may contain the correct solution, but the teacher has not read it. Truth and available evidence differ. The independent oracle in our simulator can inspect the truth log under the research protocol. The application must act on the observations actually available at its decision time. Giving the application the oracle's hidden knowledge would destroy the intended test.

The fourth question is what remains owed. A correct final database state does not tell us whether a previous message needs withdrawal. Conversely, a clear apology does not repair a duplicated external appointment. This is why the paper keeps several endpoints.

# PART II - How the system works

## 5. The components and their jobs

<!-- ARCHITECTURE -->

The **browser interface** is where a person would view a call and dashboard. The repository's product stack includes Next.js, React, TypeScript, Tailwind, TanStack Query, and Zod. These technologies organize presentation, client state and input validation. They do not make the browser an authority for external business success.

The **voice worker** connects media and candidate intents to the deterministic backend. In a cascaded voice design, STT converts speech to text, an intent component proposes structure, and TTS creates speech. A native speech-to-speech adapter is another possible interface. Neither path is the independently varied treatment in the main campaign. The study supplied typed intents and scripted tone/playback behavior to isolate the protocol.

The **API controller** validates commands, accepts revisions, coordinates application handlers, and returns queries. FastAPI is the HTTP framework; Pydantic validates structured input. Controllers should not bury the core domain decision inside an HTTP route. The domain logic needs to remain inspectable and testable apart from the transport.

The **durable worker** performs queued work using PostgreSQL-backed records and leases. Leasing is temporary ownership of a job, so multiple workers do not casually act on the same row. It dispatches, reconciles, verifies, and coordinates recovery. A network request must not keep an unrelated database transaction locked for a whole voice conversation.

The **provider adapter/simulator** represents the external appointment service. The simulator supports controlled capabilities and faults, including a commit followed by a missing reply. Its append-only truth log enables independent checking. It is synthetic, but the application still runs real code and database transactions.

The **speech scheduler and client testimony** track whether output was generated, queued, published, started, progressed, interrupted, or completed. The **research runner and oracle** are a separate measurement layer. They control scenarios and observe records without treating the application's confidence as ground truth.

## 6. Why PostgreSQL and why not Redis alone?

PostgreSQL stores durable accepted intent, logical operation identities, evidence, claim permissions, and repair records. Transactions let related local changes succeed or roll back together. Constraints help reject invalid duplicates or inconsistent combinations. A successful local transaction still cannot atomically control an unrelated opaque provider's network commit. That external boundary is why reconciliation remains necessary.

Redis is useful for short-lived caching or hints. A cache can be lost or rebuilt. Losing it must not erase an accepted revision, validate a stale statement, or remove the only copy of an obligation. The design principle is not 'Redis is bad'; it is that correctness must not depend on an ephemeral sole copy.

Think of a sticky note and a signed office register. The sticky note can remind you to look at the register. It cannot replace the durable authoritative entry. An appointment provider has its own register, so the local register must distinguish observed provider facts from assumptions.

## 7. IDs, revisions, resource versions, hashes, and time

These are five different identifiers. An **input ID** identifies the scenario/context draw. An **execution ID** identifies that input under a particular arm and attempt. An **operation ID** identifies a logical external action. An **intent revision** identifies an accepted version of the user's request. A **resource version** identifies a particular state of a provider resource. A hash identifies exact content bytes or a specified normalized object. None substitutes for all the others.

If a create request is retried as the same logical action, keep its logical identity as required by the provider contract. If the user materially changes the request, create the linked new operation rather than reusing an idempotency key with a different meaning. Evidence about resource version 4 does not silently become evidence about version 5.

Wall-clock time answers 'what UTC instant was this?'. Monotonic time measures elapsed time within a boot without acting like an editable calendar. The guarded runner retains paired readings and boot identity so a bad clock measurement does not silently reset study deadlines. A fresh paired sample brackets the wall read with monotonic readings to quantify sampling uncertainty. A timing guard protects operation, but it is not the same as the scientific latency estimator.

## 8. Read a receipt like a carefully scoped certificate

| Field | Easy question |
| --- | --- |
| Workflow/operation | Which task and which external action? |
| Intent revision | Which accepted request version? |
| Claim predicates | Exactly what statement was checked? |
| Resource version | Which observed provider state? |
| Evidence source | Which authoritative observation supports it? |
| Validity interval | When is that observation applicable? |
| Verdict | SATISFIED, VIOLATED, or UNKNOWN? |

SATISFIED means the checked predicates are supported under the verifier's rules. VIOLATED means relevant evidence contradicts the predicate. UNKNOWN means sufficient support or contradiction has not been established. The three states must not be collapsed into a binary success flag that turns lack of knowledge into known failure.

A claim permit is more like permission to issue a specific certificate than an extra copy of the booking. It binds wording/claim type to applicable evidence. A later revision or resource change can make a formerly valid authorization unusable. A model writing 'confirmed' cannot create that authorization by being fluent.

B3 can use its ordinary observations to decide whether a claim is supported. Our oracle does not insist that it use the proposed arms' receipt object. That matters for fairness: externally equivalent behavior should receive the same outcome grade.

## 9. One failure can contain several outcomes

The verified slot-145 diagnosis is the clearest example. An initial create committed before its deliberately dropped reply. Recovery cancelled it and created the corrected appointment because in-place rescheduling was unsupported. The selected claim still used RESCHEDULED_APPOINTMENT because the accepted revision exceeded one. The verifier correctly rejected that predicate, producing the specific HTTP 409 refusal wrapping b3-evidence. The exception propagated through the driver and retained its FAILED status.

This includes two different limitations. The **studied application** selected a claim type too coarsely from revision number. That behavior was preserved across arms, not quietly fixed to improve a result. The **experiment control** initially failed to recognize a narrow, evidence-supported refusal outcome. Classifier amendments allowed full collection, grading and backup of that unsuccessful speech outcome without treating unrelated errors as harmless. Original records were not replaced.

The lesson is not '409 is fine'. Endpoint, method, request, response schema, non-retryable code, scenario conditions, revision, operation, and recorded evidence determine whether a refusal is the expected research outcome. Genuine defects, unknown responses, failed backups, or integrity failures must pause admissions. Retrying a non-retryable speech refusal would change what the scenario measures.

# PART III - The experiment, AWS, and evidence

## 10. What exactly ran?

The main study had **500 inputs**, each executed under **B3, P1 and P2**, giving **1,500 original executions**. All originals used their saved identities and order. The independent sampling unit for the accepted conditional analysis is the context input draw, keeping all three arm rows paired. The inputs come from 50 fixed recipe families. They are not 1,500 independent natural conversations, and repeated variants are not new independent domains.

The main arms are implementation profiles. B3 includes durable idempotency, reconcile-before-retry, revision invalidation, staging, compensation and playback tracking. P1 adds claim permits plus product-state invariants. P2 adds the durable played-content repair package. Earlier B0-B2 profiles exist in the project but are outside this main comparison. The timing phases named P1-P9 in older experimental documents refer to event boundaries, not the P1/P2 arm names. Always specify which naming system you mean.

No new language model was trained. No Gemini/OpenAI model ranking was estimated. The local simulator/scripted path avoided paid model or speech calls in the campaign. This improves control over protocol faults, while excluding claims about recognition errors, accents, background noise, natural language flexibility, and human understanding.

## 11. The four strata and what they teach

**CLEAN - 300 inputs.** Ordinary tasks check that the protections do not make useful work needlessly fail. All three arms succeeded on all 300. This is a sample result, not a promise that every real clean call succeeds.

**HIDDEN_COMMIT - 100 inputs.** A provider can commit while its acknowledgement is unavailable. These cases stress knowledge versus effect and recovery after a change. They contribute half of the planned correction mixture. A timeout alone must not authorize a duplicate write.

**PLAYOUT - 60 inputs.** These focus on output timing, delayed testimony, version changes, or content that reaches a decisive span. Generated audio and recorded playback are deliberately separated. They contribute 30% of the correction mixture.

**OTHER_BOUNDARY - 40 inputs.** These cover the remaining declared boundary recipes. They are part of the fixed design, not an improvised category for surprising failures after analysis. They contribute 20% of the correction mixture.

**The 33 recovery inputs** are a predeclared subset across relevant challenges: full playback before correction (9), late decisive ACK (7), partial decisive-time playback (7), reconnect with another revision (7), and restart before repair (3). Keeping eligibility fixed avoids comparing P2 only on the repair records it chose to create.

## 12. Named barriers and budgets

A named barrier is an explicit handshake with a precise point in the workflow. For example, the provider can record a commit while withholding its acknowledgement, then signal that it reached the named point. The script accepts the correction and releases the next step. An approximate sleep such as 'wait half a second and hope the commit happened' gives less reliable event ordering.

Budgets are limits on actions and observation, not interchangeable units. The reviewed configuration permits reconciliation up to **eight attempts** and drain up to **30 passes**. Neither means eight seconds or 30 seconds. The observation window is **600 seconds**. A retry budget governs how many qualified tries are allowed; a timeout governs how long a request waits; an absolute deadline governs when the campaign must stop admitting/running according to its policy.

Intentionally injected faults are the study's treatment conditions. A simulator's planned lost reply is not the same as an accidental network outage between the runner and its evidence storage. A deliberate application refusal is not automatically a technical defect. However, an unexpected error cannot be ignored just because later driver commands return normally.

## 13. Why AWS was used

<!-- INFRA_IMAGE -->

The practical need was a long-running, reproducible experiment that could continue without keeping a laptop and a Codex conversation active all day. The local machine had finite RAM and disk headroom. A retained Linux host gave the standalone runner a consistent place to run, with dedicated research resources and independently checked limits. AWS was infrastructure for the experiment, not evidence of its novelty or a source of artificial intelligence in the tested arms.

The retained deployment records identify an EC2 m7i-flex.large host in ap-southeast-2. This guide reads historical local records only. It does not assert a fresh host state, instance price, current bill, or available credit balance. The host was last verified stopped during closeout. No AWS operation is needed to read this guide or the completed local analysis.

**EC2** provided the Linux computer. **EBS** retained its root filesystem and working records. **S3 versioned objects** retained backup archives with exact version references. **SSM** provided managed control-plane command/status access. **CloudShell** later provided an authenticated cloud-side environment for bounded evidence extraction when the local network route was unreliable. **System services and watchdog/independent timers** kept the experiment separate from an interactive chat and provided bounds on failed preparation or stalled operation.

These choices do not mean cloud is intrinsically required by the research question. Another suitably isolated, qualified machine could run the software. They also do not imply every AWS service in an architecture diagram was used. No paid speech service or model subscription should be inferred from the existence of the EC2 host.

## 14. Why the campaign took time

The observation windows alone impose a substantial serial lower bound: 1,500 x 600 seconds = 900,000 seconds = 250 hours = 10 days and 10 hours. That excludes setup, scenario commands, evidence export, backup/readback, safety checks, pauses, diagnosis, deployment and transfer time. It is not a claim that every application operation took ten minutes. The collector kept watching after the driver returned to preserve late effects.

Parallel execution was not assumed safe simply because IDs differed. Shared fault controls, provider bindings, workers, global cache operations, and collection queries can interfere. The accepted main schedule remained serial. Additional CPUs cannot remove a fixed full observation window; they shorten elapsed time only when overlapping executions are scientifically and operationally isolated and qualified.

The difference between the planning forecast and actual elapsed campaign history matters. Pauses and instrument defects added overhead. Completion is recorded at the final saved backup, not inferred from an earlier estimate. The final original's backup timestamp was 25 October 2026 at 10:09:34.327454 UTC. That is a historical evidence timestamp, not a new cloud measurement.

## 15. The standalone runner and durable ledger

The runner keeps saved slots binding input, arm, attempt and execution identity. It admits one original only after the relevant source, authority, cost, resource, time and evidence gates pass. During collection, checkpoints preserve the same identity and original deadline. A pause blocks new admissions; it must not silently replay a business command or replace a failed result.

The research ledger is a durable operational record. A slot progresses through admission, collection, export, grade/retention steps and backup under the implemented rules. Do not confuse it with the appointment provider's database. Its value is explaining which execution occurred, under which controller binding, with which deadline and original archive.

The watchdog checks guards separately from the main driver. A watchdog can itself encounter bugs or connectivity failures, so the history includes versioned corrections and retained failed attempts. A pause is not automatically equivalent to stopped compute. Independent shutdown controls and explicit state verification provide the bounded operational stop procedure. None is a proof that infrastructure can never fail.

The final accepted operational policy reached a US$76 admission guard and US$77 total ceiling, with 80-GiB backup caps and a 26 October 2026 12:00 UTC absolute stop. These are historical authorization limits, not a fresh actual-spend figure or permission to start resources today. Cost forecasts, delayed billing, evidence retention and root-disk charges are different accounting concerns.

## 16. Backups, hashes, and why extraction is not rerunning cases

Each original has exact archive/export bindings and pinned backup versions. Hash checking detects a file differing from its committed bytes. Independent readback verifies that the retained backup can be read and matches the expected material. Source inventories bind files to versions; they do not prove those files contain no bug.

The final evidence download extracted compact verified results from already executed originals. A progress line 'VERIFIED 1128/1500' counted evidence records processed, not new experiments. The first extraction process stopped, recovery retained that attempt, and a packaging problem arose because old and modern cached records used different schemas. A package-only correction used the already saved records, with no network requests or research replays. The returned final bundle contained all 1,500 records.

Its verified SHA-256 is 1d67c5adc39fc6ef6f9cfcaa32a910532be8a9faf824383946d5c2ed10426341. The bundle was 823,115 bytes. Small compact results do not mean all original archives are that small. The full raw evidence remains separately retained and version-pinned. Reusing verified data avoids both unnecessary network loops and accidental replacement of originals.

# PART IV - Statistics without mystery

## 17. Percentages, denominators, and percentage points

Business correctness is 455/500 = 0.91 = 91% per arm. Correction success is 155/200 = 77.5%, because only the 200 non-clean inputs are eligible for that endpoint. Clean success is 300/300. Supported final update is 408/500 = 81.6%. These percentages answer different questions; none is the fraction of AWS commands that succeeded.

The correction weights reproduce the planned mixture: 0.50 x 0.73 + 0.30 x (56/60) + 0.20 x 0.65 = 0.775. Compare arms by subtracting their corresponding weighted means. Here that difference is zero because their input-level correction outcomes match.

Percentage points are absolute differences in percentages. A change from 80% to 85% is +5 percentage points, although its relative increase is 5/80 = 6.25%. The paper's clean tolerance is five percentage points, not five percent of whatever baseline success happened to be. Mixing these units would change the question.

## 18. Why pairing matters

Imagine 500 cards. Each card holds one input's three results: B3, P1 and P2. A fair comparison looks within cards before summarizing across cards. One arm should not get easier appointment contexts or weaker faults. Paired analysis uses this matching rather than treating the three rows as unrelated people.

For a binary success endpoint, each B3/P2 card is both succeed, both fail, P2-only success, or B3-only success. The observed correction data contain 155 both-success cards and 45 both-failure cards, with zero discordant cards. That is stronger evidence of an observed tie than merely finding two equal totals which might hide different successful cases.

It still does not prove universal equivalence. There can be untested conditions, sampling variability, shared-host effects, or implementation limitations common to both. The 50 fixed families also limit the population to which any interval can reasonably transfer.

## 19. Confidence intervals and an observed tie

The conservative 97.5% correction-difference interval is -8.79 to +8.79 percentage points. Zero lies inside. The hidden-commit adverse-exposure difference interval is -4.95 to +4.95 points. A positive difference for a success endpoint favors P2; a positive difference for an adverse endpoint is worse. Always name the endpoint and subtraction direction.

A frequentist confidence procedure has a long-run coverage property under its assumptions. It is not a direct statement that this fixed interval has a 97.5% probability of containing a random true parameter. For a meeting, a practical phrasing is: 'These are uncertainty bounds calculated under the declared frame and dependence assumptions; they do not demonstrate an improvement.'

Zero observed differences do not justify reporting an interval [0,0]. The implemented conservative method accounts for unobserved possibilities rather than interpreting zero empirical variance as perfect certainty. The paper retains the helper's restricted claim flags, so the calculation is not presented as a blanket confirmatory endorsement.

## 20. Co-primary allocation, Holm, and p-values

If many questions are tested, chance alone can produce apparently striking results. The study therefore specified two main comparisons and allocated error across them. The stated 97.5% individual bounds correspond to the accepted two-comparison Bonferroni allocation. The secondary diagnostic family contains ten comparisons with Holm adjustment. No new favorite endpoint was promoted to primary after the result became known.

For complete corrective communication, 26 known pairs favor P2 and none favor the comparator. The frozen exact McNemar diagnostic p-value is 2.9802e-8; the Holm diagnostic value is 2.9802e-7. Their small size describes the known-pair imbalance under the diagnostic null and assumptions. Seven pairs are missing, the template is narrow, and shared dependence remains a concern.

A p-value is not the probability that P2 is better, the chance the paper will be accepted, or proof of industrial value. An effect size with its denominator, missingness, measurement definition and assumptions is more informative than a dramatic decimal alone. This study's secondary p-value cannot erase the primary tie.

## 21. Missingness and the 78.79-to-100 range

For the 33 designated inputs, P2 has 33 known complete-communication successes. Each comparator has zero known successes, 26 known failures, and seven unknowns. If all seven unknowns were successes, the comparator would have seven of 33, so the difference is (33-7)/33 = 78.79 percentage points. If they were all failures, the difference is 33/33 = 100 points.

This is a range of empirical differences compatible with the missing binary values in this sample. It is not a confidence interval accounting for repeated samples. Nor does it prove people understand P2 better. The exact-prefix endpoint remains the outcome being bounded.

Structural N/A is different. A clean input is not eligible for a correction endpoint merely because its result is convenient. UNKNOWN is not removed from a planned denominator just to improve a rate. The separate unsupported-exposure table illustrates the danger: four baseline adverse grades have proposed-arm UNKNOWN counterparts, so '4 versus 0' does not identify definite prevention.

## 22. Clean-case usefulness

Protections can be too restrictive. A system that refuses every request might avoid unsupported claims while being useless. The clean-case condition therefore checks ordinary task completion against an accepted loss tolerance. P2 and B3 each have 300/300 clean successes; the one-sided 95% lower difference bound is -1.22 percentage points, above -5 points.

The cautious conclusion is that the accepted descriptive/conditional clean criterion is met in this frame. It is not a guarantee that the proposed mechanisms never harm usability. No real-call duration, satisfaction, accent performance, or human burden was measured by this clean endpoint.

Likewise, 'no forbidden effect recorded in 500 inputs per arm' is not 'forbidden effects are impossible'. You can only report the tested denominator and the evidence rule. Refusing everything is also not how B3 or the proposed arms achieved their business results: 455 final business targets were correct per arm.

## 23. Censoring, restricted timing, and AFT

An event is the supported scripted completion whose time the endpoint tracks. If it is not established within the observation basis, the exact event time is censored. That is not the same as knowing the event never occurs. The accepted restricted calculation uses a 600-second horizon rather than pretending we watched forever. Its results must retain the saved timing and missingness rules.

There are 1,224 event rows (408 per arm) and 276 censored rows. The paired restricted-mean differences are +0.2593 seconds for P2-B3, +0.2251 for P1-B3, and +0.0342 for P2-P1. Positive means longer measured time. These are not new call recordings and are not a measurement of how quickly a human updates their belief.

An accelerated-failure-time model relates time multiplicatively to arm and stratum. The lognormal version models the logarithm of positive time with a normal-shaped error distribution. The P2/B3 estimated time ratio is about 1.2265 under that model. That means roughly a 1.2265 multiplier, not an extra 1.2265 seconds. Model form and independent censoring remain unproven; optimization convergence does not certify them.

## 24. Bootstrap, dependence, and the limits of robustness checks

The timing bootstrap repeatedly samples input cards within the declared strata. Each selected card brings all its arm results. Two thousand draws support the paired timing intervals; a separate thousand input-cluster draws support AFT uncertainty. Seeds 8042051 and 8042052 make these computational draws reproducible. They do not make the underlying observations independent.

AFT converged on all 1,000 bootstrap draws; no failed fit was dropped. The 20 fixed temporal-block omission summaries all retain a zero primary correction difference. Those are useful checks, but they answer limited questions. They do not validate every secondary endpoint, reveal all missing late effects, or prove timing stability across deployment versions.

The raw timing history retains four infrastructure labels at sequences 1, 2, 145, and 616. Only the already accepted first-two label sidecars are used in a separate timing view. No numeric duration or business outcome was changed. Historical labeling and outcome-dependent stopping still limit an independent-censoring interpretation.

## 25. Read the findings in one minute

<!-- BUSINESS_CHART -->

**What is strong:** all 1,500 originals are accounted for; the three arms are paired; ordinary baseline updates receive credit; failures and UNKNOWNs remain; primary business outcomes tie input by input; source and backup provenance is retained.

**What is narrow:** complete communication recognizes a fixed explicit-withdrawal phrase on supported fully acknowledged output. Its P2 result is positive, but it bundles repair storage, delivery logic and wording. It is not an isolated durability experiment or a human-belief experiment.

**What is absent:** a new trained model, natural-call evaluation, proof of zero risk, direct comparisons against the cited external runtimes, and evidence of general industry-first novelty. These exclusions do not make the study worthless. They define a systems/measurement result that can be reviewed honestly.

**What to tell a professor:** 'I built and evaluated a protocol that separates what an agent did, what evidence supports, what was exposed, and what correction remains owed. Our competent baseline matched the proposed arms on final business outcomes. The repair configuration differed on a limited explicit-withdrawal endpoint, which we report with its template and scripted-playback limitations.'

## 26. How the build phases fit together

| Phase | What it supplied | What it does not establish by itself |
| --- | --- | --- |
| 0 | Repository scaffold and local boot | Research correctness or a successful campaign |
| 1 | Durable local appointment transactions | Atomic control of an unrelated external provider |
| 2 | External operations, ambiguity and reconciliation | Permission to speak every possible outcome claim |
| 3 | Revision/resource-bound verification and claim permission | Proof that generated output reached playback |
| 4 | Playback scheduling, measurement and repair machinery | Human understanding or uninterrupted service uptime |
| 5 | Voice-path integration work | Natural-speech evaluation in the main study |
| 6 | Explicit research-arm drivers and comparison paths | A completed frozen main campaign |
| 7 | Pilot, audit and versioned study preparation | Main-study superiority from pilot debugging |
| 8 | Reviewed study design, qualification, campaign and final analysis | Guaranteed publication or universal safety |
| 9 | Optional transfer/extension studies in the original plan | A required missing analysis step after Phase 8 |

This is a teaching overview of the development history, not a replacement for the versioned phase reports. In particular, final statistical analysis belongs to the completed Phase 8 closeout. 'Phase 9' is not a reason to imply the 1,500 original results are still waiting to be analyzed. Optional transfer studies would need a separate question, protocol and authorization.

## 27. A simple mathematical reading of the timing model

An AFT model can be written conceptually as log(T) = baseline + arm terms + stratum terms + error, where T is a positive event time. 'Log' is a mathematical transformation and 'exp' reverses it. Exponentiating an arm coefficient gives its estimated time multiplier. An estimated multiplier above 1 means longer modelled time, not greater accuracy.

This shorthand explains the accepted arm-plus-stratum model, not a new fit. Its coefficients are identified by a reference arm/stratum rather than adding redundant parameters for every label plus an unconstrained intercept. Censored observations contribute information about not yet observing the event, under the model's assumptions, instead of being deleted as inconvenient failures.

There is no reason for a time ratio of 1.2265 to equal an additive difference of 0.2593 seconds. The model and restricted paired mean summarize different aspects of timing under different assumptions. Neither measures the time for a human to understand a correction. If a professor asks about the gap, explain the estimands rather than claiming the values are contradictory.

# PART V - Read the full manuscript closely

Every original prose block appears below in gray. Read it, then read the explanation. The separate appendix reproduces all eight original pages. Table values remain the original values.

## Original manuscript page 1

**Original heading: Abstract**

### 01. Abstract: the entire study in one paragraph

> An agent can change an external resource correctly while lacking evidence for its confirmation; a later correct update can also leave an earlier incompatible statement unwithdrawn. We investigate these distinctions in a maintenance-booking system with changing requests, ambiguous commits, and delayed playback. A competent baseline, B3, includes durable idempotency, reconciliation, revision invalidation, staging, compensation, playback tracking, and ordinary corrective updates. P1 adds explicit claim permits and product-state invariants; P2 additionally persists played-content repair obligations. A fixed synthetic study runs 500 paired inputs across the three arms, retaining all 1,500 originals and their 600-second observation windows. Each arm achieves 455/500 correct final business states and 155/200 successful corrections, with identical paired business outcomes. No incremental benefit is demonstrated on the two co-primary endpoints. In 33 predeclared recovery inputs, every arm delivers an ordinary supported update; complete corrective communication is TRUE in 33/33 P2 inputs, versus 26 FALSE and seven UNKNOWN for each comparator. This secondary result is bounded by a fixed withdrawal-template grader and scripted tone/playback acknowledgements. The study contributes an implemented protocol and auditable endpoint separation, rather than evidence of general voice-agent superiority or human-belief repair.

**Plain-English reading:** The opening sentence separates doing the job from having enough proof to announce it. The next sentence adds a second problem: giving new information may leave an older statement uncorrected. The paragraph then names the three implementations and the size of the completed comparison. Its business result is a tie. Its narrower communication result concerns explicit withdrawal. The final sentences tell you the test's boundaries: a fixed wording rule and scripted playback. Read the abstract as problem, proposed mechanisms, method, result, then limitation. It does not promise a better language model.

**Difficult words:** Abstract = compressed overview; competent baseline = a comparison system with meaningful existing protections; paired = the same input tested under each arm; explicit withdrawal = clearly identifying an earlier statement as outdated.

**A teaching example:** A clerk can correctly move your appointment while never telling you. Another clerk can tell you the new time without saying the earlier time no longer applies. These are different accomplishments.

**Keep the claim accurate:** Do not compress this abstract into 'P2 is 100% accurate'. Its 33/33 communication result has a special denominator and a narrow instrument.

**Original heading: 1. Introduction**

### 02. Introduction: why a missing reply is dangerous

> Suppose an agent requests an appointment at 12:15. The provider commits, but the response disappears. The user then requests 14:15. Retrying the first operation can duplicate effects; stopping audio cannot undo a booking; and changing the database does not retract a confirmation that has already reached playback. These events cross distinct boundaries: accepted intent, external effect, available evidence, publication, playback, and correction.

**Plain-English reading:** The booking service can save the 12:15 appointment and then lose the reply. The controller sees a timeout, not a reliable statement that nothing happened. Meanwhile, the resident changes the desired time to 14:15. Repeating the first create request might add another booking. Muting audio prevents additional output but cannot remove an external booking or make previously played words disappear. This paragraph introduces six separate boundaries because each answers a different question.

**Difficult words:** Commit = make an external change durable; external effect = a booking or cancellation outside the controller; accepted intent = the request the server has formally accepted; playback = output reaching the client media path.

**A teaching example:** A restaurant places your takeaway order, but your app loses internet before the receipt arrives. Pressing order again is not automatically safe.

**Keep the claim accurate:** The times are an explanatory example. They are not a transcript of a real resident or one universal campaign case.

### 03. Introduction: the incremental research question

> Idempotent APIs already address retry safety and changing intent [1]. Transactional agent runtimes and revision-recovery systems address related effect and validity problems [2-5]. The question here is incremental: **when do evidence-bound claim permission and durable corrective delivery provide observable protection beyond a competent baseline's existing safeguards?**

**Plain-English reading:** The first sentence credits established API ideas. The second acknowledges earlier research on transactions and revisions. The bold question asks what the additional mechanisms achieve once these strong protections already exist. 'Incremental' means the extra effect beyond the comparator. This prevents winning simply by comparing a careful implementation with an obviously unsafe one.

**Difficult words:** API = the agreed request/response interface; idempotent = repeats of the same logical request do not create extra effects; transactional runtime = software coordinating effects and settlement; incremental benefit = improvement attributable to an added package under this comparison.

**A teaching example:** To evaluate a new seat belt, compare with a functioning existing seat belt rather than a car with none.

**Keep the claim accurate:** This study does not run Atomix or Cordon as experimental arms. Related-work discussion is not a head-to-head benchmark.

### 04. Introduction: a refusal can protect truth and still leave a task unfinished

> The experiment separates business correctness from communication correctness. A backend refusal can be appropriate even if the requested speech outcome is unsuccessful. Conversely, normal driver completion does not establish the correct business state. An ordinary corrected statement is credited in every arm; the baseline is not required to possess the proposed receipt objects.

**Plain-English reading:** A business outcome asks what exists at the provider. A communication outcome asks what was justified and delivered. If evidence is insufficient, refusing a decisive confirmation may be the right action. It still means the desired confirmation was not delivered. Likewise, a driver returning normally is only a process fact. The baseline can justify claims from its ordinary observations; requiring it to generate P1's special receipt objects would bias the measurement.

**Difficult words:** Backend = server-side application; refusal = an application deliberately rejecting a request; driver = the research program issuing the scenario; outcome credit = the grader's assessment of externally observable success.

**A teaching example:** An honest receptionist says 'I cannot confirm yet' after a payment timeout. Honesty is valuable, but it is not the same as completing the confirmation task.

**Keep the claim accurate:** Never label every refusal as a successful business outcome or every HTTP error as an infrastructure outage.

### 05. Introduction: what the paper contributes

> This paper makes three bounded contributions: an implemented revision/evidence/claim/repair contract; a paired, fixed-frame evaluation with separately observable endpoints and preserved UNKNOWNs; and a completed result showing a primary business-outcome tie alongside a narrower distinction in explicit corrective communication. These are implementation and measurement contributions. They are not a new transaction primitive, a proof of universal safety, or a claim that existing systems lack correction mechanisms.

**Plain-English reading:** There are three claimed outputs: a working contract, a comparison instrument, and results from that instrument. 'Bounded' means the claim has an explicitly stated scope. The business comparison did not distinguish the arms; the communication measure did in a limited subset. A negative primary result remains a result when the comparator and methods are meaningful. None of this invents database transactions or proves the system correct under every possible schedule.

**Difficult words:** Protocol = agreed rules across components; instrument = software used to create and measure experiments; primary outcome = a main endpoint selected in the plan; negative finding = no demonstrated benefit on the question tested.

**A teaching example:** Building a calibrated thermometer and learning that two rooms have the same temperature can be valuable even without discovering a hotter room.

**Keep the claim accurate:** A new combination is not automatically novel. Its scientific value must be judged against prior work and the quality of evidence.

## Original manuscript page 2

**Original heading: 2. Related work and contribution boundary**

### 06. Related work: transaction boundaries

> **Transactional effects and uncertain completion.** Safe idempotent API design distinguishes duplicate requests from changed intent [1]. Atomix gates settlement using progress-aware transactions and effect classification [2]. Cordon stages external effects within a task-scoped boundary with lineage and authority checks [3]. These are direct antecedents: irreversible-effect gating and recovery are not new here. Our empirical question concerns the relationship between resource evidence and the lifecycle of an outcome statement, including correction after previously exposed content.

**Plain-English reading:** This paragraph recognizes known work on retry safety and on deciding when effects should settle. Its purpose is positioning, not importing those papers' performance claims. Our focus is a particular outcome statement and its exposure history. We did not implement each cited runtime and compare its results with ours.

**Difficult words:** Settlement = deciding which effects are final; lineage = a record of what an output depends on; authority = permission to cause a consequence; antecedent = relevant earlier work.

**A teaching example:** An office approval process can govern when a letter is sent. Our question additionally tracks whether an already delivered message needs a correction.

**Keep the claim accurate:** The reference guide later summarizes these papers briefly. Do not claim that all of their mechanisms are absent from our comparator or present in our code.

### 07. Related work: changing instructions and recovery

> **Revisions and recoverability.** Revisable by Design formalizes concurrent intervention and action reversibility [4]. REVISE preserves validity-established work while recomputing affected workflow regions [5]. DART studies admissible recovery boundaries after downstream commitment [6]. These works prevent a broad novelty claim about handling revisions, retaining progress, or recognizing irreversible consequences. Our study evaluates a specific booking implementation, rather than comparing their algorithms or proving a stronger recovery guarantee.

**Plain-English reading:** A request can change while work is running. Prior research already studies preserving useful progress and recovering consistently. The cited papers concern different recovery formulations. Our experiments test the frozen booking implementation, not a universal replacement for those systems.

**Difficult words:** Reversibility = whether an action can be undone; admissible = allowed by the correctness conditions; downstream = work depending on an earlier result; recovery boundary = the point from which work can safely continue.

**A teaching example:** If a draft shopping list changes, unused notes can be edited. If a package has already shipped, editing the notes cannot undo shipment.

**Keep the claim accurate:** The existence of our revision counter is not evidence that we invented online revision handling.

### 08. Related work: observations and receipts

> **Verification and receipts.** Verified Tool Calls combines postcondition verification, idempotency, and verify-before-retry behavior [7]. Tool Receipts links response claims to execution evidence [8]. Consequently, neither verification before retry nor evidence-backed claims is asserted as original in isolation. The proposed composition additionally treats accepted intent revision, resource version, exposure, and persistent corrective obligations as separately recorded concerns.

**Plain-English reading:** Verification before retry and receipts for claims are established approaches. This study combines them with revision, resource-version, exposure, and repair records. The important conceptual separation is between observing an action, storing an observation, and authorizing a statement about it.

**Difficult words:** Postcondition = a condition that should hold after an action; receipt = structured evidence about a check; provenance = where evidence came from; predicate = a statement that can be checked as satisfied, violated, or unknown.

**A teaching example:** A delivery scan is evidence. It is not automatically permission to tell the customer that a different package arrived.

**Keep the claim accurate:** Our receipt is not a cryptographic proof of the provider's entire internal history.

### 09. Related work: generated output versus played output

> **Playback and dialogue repair.** Incremental speech-generation research already addresses self-monitoring and revision during output [9]. PACE aligns model-facing context with client playback and distinguishes physical playback evidence from semantic commitment and comprehension [10]. Our protocol also distinguishes generated and exposed output, but evaluates truth/evidence applicability and explicit withdrawal after changing booking targets. It does not reproduce PACE's live speech-model evaluation or establish superiority over it.

**Plain-English reading:** Speech can be produced ahead of what the client has played. Existing dialogue work studies this gap and repair. Here the measured question is whether booking-related words have applicable support and whether outdated content is explicitly withdrawn. We do not claim that our tone-based setup is equivalent to another paper's live speech evaluation.

**Difficult words:** Incremental generation = producing a response in pieces; model-facing context = information available to a model; playback boundary = the recorded progress point of output; semantic = concerning meaning.

**A teaching example:** A video player may download a whole scene while the viewer has watched only its first seconds. Downloaded and watched are different facts.

**Keep the claim accurate:** An ACK is client testimony about progress. It cannot establish attention or understanding.

### 10. Related work: what kind of benchmark this is

> **Evaluation.** Tau-bench evaluates tool-agent-user interaction using final database state [11]; tau-Voice extends grounded evaluation to full-duplex audio [12]. Our typed-intent, scripted-tone path isolates protocol behavior. Its results cannot be numerically compared with their model success rates. It measures neither speech recognition nor a language model's ability to choose an intent or formulate a correction.

**Plain-English reading:** A benchmark is a shared testing setup. The cited benchmark family examines tool interaction and grounded voice tasks. Our experiment deliberately bypasses recognition and intent generation to study deterministic protocol behavior. Its 91% business rate cannot be ranked against a different benchmark's model success rate.

**Difficult words:** Grounded task = one whose result is checked against an environment; typed intent = structured request supplied directly; leaderboard = a ranked comparison under a common protocol.

**A teaching example:** A brake test on a controlled track and a driving test in city traffic measure related but different abilities.

**Keep the claim accurate:** Do not advertise the study as a Gemini-versus-GPT comparison. Those are not its arms.

### 11. Related work: why novelty stays qualified

> These comparisons are a targeted primary-source review, not an exhaustive systematic review. The strongest candidate contribution is the integrated, auditable evaluation of business state, available evidence, exposure, and explicit corrective delivery against an already protected baseline. The study does not establish priority for that entire combination. External novelty assessment remains a peer-review question, especially given the close transactional and playback literature.

**Plain-English reading:** The author checked selected relevant original sources. That is not an exhaustive search of all publications. The plausible contribution is the evaluated combination and endpoint separation. Whether it is sufficiently original is a review question, not something established by its number of test cases.

**Difficult words:** Primary source = the authors' paper or official description; systematic review = a defined search and screening process; priority = being the first to establish something.

**A teaching example:** Knowing several nearby buildings does not prove there is no similar building elsewhere in the city.

**Keep the claim accurate:** Avoid 'nobody in industry does this' and 'world first'. Neither follows from the current evidence.

**Original heading: 3. System and correctness model**

### 12. System: where authority comes from

> The application manages property-maintenance appointments. A model proposal has no authority to create business records directly. Deterministic acceptance establishes a new intent revision in PostgreSQL, which is the durable correctness authority. Redis is disposable. The experiment injects typed requests and therefore bypasses recognition and proposal-model uncertainty.

**Plain-English reading:** A model may suggest a request, but server rules decide whether to accept it. PostgreSQL saves the accepted revision and correctness-relevant records. Redis can accelerate disposable operations but cannot be the only place that remembers an obligation or accepted request. Typed inputs remove one source of variability from the main experiment.

**Difficult words:** PostgreSQL = durable relational database; Redis = optional in-memory cache; deterministic = the same relevant inputs and rules lead to the same decision; revision = numbered accepted version of intent.

**A teaching example:** A receptionist's rough note is a proposal. An approved entry in the appointment register is the accepted record.

**Keep the claim accurate:** A durable local record does not give the application omniscient knowledge of an opaque external provider.

### 13. System: orthogonal state dimensions

> The operation is represented by orthogonal dimensions rather than a single linear success state. A request can have a committed external effect, UNKNOWN local knowledge, an invalidated claim, and an outstanding repair obligation simultaneously. External simulator truth is distinct from the observations available to the application.

**Plain-English reading:** A single SUCCESS or FAILED label loses information. The provider may have committed, the controller may not know, old speech may be invalid, and a repair may still be owed. All four can be true together. Orthogonal means these questions have separate axes rather than being squeezed into a single line of states.

**Difficult words:** Orthogonal = represented separately; product state = the combination of several state dimensions; local knowledge = what observations justify, not everything that is true.

**A teaching example:** A parcel can be delivered, its tracking page delayed, its notification unsent, and its customer complaint unresolved at the same time.

**Keep the claim accurate:** The dimension chart is a conceptual map. It is not the exact list of executable transition rules.

## Original manuscript page 3

**Original heading: 3.1. Evidence-bound permission**

### 14. System: UNKNOWN, reconciliation, receipt, and permit

> After a possibly sent operation times out, the effect remains UNKNOWN until reconciliation establishes whether a retry is safe. A materially changed request receives a linked logical operation. A verification receipt records the accepted revision, operation, claim predicates, resource version, evidence provenance, and validity interval, with SATISFIED, VIOLATED, or UNKNOWN results. A permit authorizes a particular claim using applicable evidence; it does not establish that an external transaction committed.

**Plain-English reading:** Timeout is a statement about waiting, not proof of no external effect. Reconciliation checks provider status or resources before another write. Repeating one logical operation keeps its identity; changing the actual request needs a linked new one. The receipt names which operation, revision, predicates, version, source, and validity period it concerns. A permit is then a scoped authorization to say something, not a second booking commit.

**Difficult words:** UNKNOWN = insufficient knowledge; reconciliation = matching observations with possible effects; validity interval = the period during which evidence is applicable; SATISFIED/VIOLATED/UNKNOWN = three-valued verification.

**A teaching example:** A dated inspection certificate for apartment A cannot certify apartment B after renovation. Its identity, version, and date matter.

**Keep the claim accurate:** A satisfied receipt can later become inapplicable. Stored evidence is not eternally current.

### 15. System: why a publication check is not enough

> Applicability is checked at the configured publication/playback gates. A newer accepted revision can invalidate an unplayed claim. Provider changes can invalidate resource-version evidence even when an appointment-time phrase remains true. Model prose and tool-return text do not independently authorize decisive outcome speech. B3 uses its ordinary evidence checks and can also refuse an unsupported statement.

**Plain-English reading:** The world can change between generation, publication, and playback. A new accepted request or changed provider version can invalidate previously usable support. The statement's particular words and predicate matter: 'exists at 14:15' and 'was rescheduled in place' are not identical claims. B3 is also allowed to check evidence and refuse.

**Difficult words:** Applicable = relevant and valid for this claim now; publication = releasing a segment into the output path; decisive = conveying a consequential outcome, such as confirmation or a specific appointment time.

**A teaching example:** A boarding gate announcement drafted five minutes ago may need checking again before it plays.

**Keep the claim accurate:** Our experiment does not establish that permits defeat every possible publication/playback race.

**Original heading: 3.2. Exposure and durable repair**

### 16. System: preventing future output versus repairing past exposure

> Generation, publication, playback start, progress, completion, and interruption are separate events. If incompatible decisive content has already been exposed, suppressing a future segment does not withdraw it. P2 persists an obligation, attempts an applicable corrective statement, and retains its delivery state. Duplicate or delayed acknowledgements must be processed without losing already recorded effects.

**Plain-English reading:** Deleting a queued segment can prevent future exposure. Once decisive content has reached playback, preventing later output alone cannot address the already exposed statement. P2 therefore records a repair obligation. A delayed ACK can reveal exposure after a correction was accepted, so handlers need to maintain the correct obligation history across event orderings.

**Difficult words:** Obligation = stored work that remains owed; duplicate ACK = repeated report of an event; delayed ACK = a report received after the event time; durable = surviving a process restart.

**A teaching example:** If the receptionist already said the wrong room number, muting the telephone afterward does not correct that number. Another supported statement is required.

**Keep the claim accurate:** Surviving storage is only one part of delivery. A consumer must discover the obligation and successfully deliver or escalate it.

### 17. Figure 1: how to read independent dimensions

> Figure 1. Independent dimensions of the implemented contract. Rows may coexist; this is not a sequence of mutually exclusive states. The experiment observes scripted exposure, not a person's understanding.

**Plain-English reading:** Read each row as a separate question: what was accepted, what happened, what is known, what may be said, what reached playback, and what remains owed. Do not read down the rows as a compulsory sequence from Intent to Repair. A repair row can remain pending after the business effect is complete.

**Difficult words:** Coexist = be true at the same time; conceptual figure = explanatory diagram; mutually exclusive = unable to be true together.

**A teaching example:** A dashboard can show fuel, speed, engine temperature, and a warning simultaneously. It is not one combined status with only four values.

**Keep the claim accurate:** Scripted exposure is a measurement proxy, not a claim about a real listener's mental state.

<!-- DIMENSIONS -->

### 18. Table 1: what the arm names mean

> Table 1. Explicit main-study profiles. Incremental switches are read from the frozen arm configuration; ordinary supported baseline updates receive full outcome credit.

**Plain-English reading:** B3 is the protected baseline. P1 adds both permits and explicit product-state invariants. P2 adds the played-content repair package. Their names are configuration labels, not names of three language models. A correct ordinary baseline update receives the same observable credit as an equivalent proposed-arm update.

**Difficult words:** Arm = experimental configuration; ablation = removing a component to examine its increment; frozen = version-pinned for the comparison.

**A teaching example:** Compare three versions of the same booking office: established safeguards, extra authorization checks, then authorization plus a persistent correction desk.

**Keep the claim accurate:** Because P1 adds two switches together, the design cannot isolate which one caused a difference.

| Arm | Safeguards and incremental mechanism |
| --- | --- |
| B3 | Durable idempotency; reconcile before retry; revision invalidation; staging; compensation; playback tracking; ordinary corrective statements and evidence checks. |
| P1 | B3 plus explicit claim permits and product-state invariants. |
| P2 | P1 plus durable repair of previously played incompatible content. |

**Original heading: 3.3. Observable endpoints**

### 19. Measurement: the grader must not trust the system's own confidence

> The independent grader reads scripted accepted targets, simulator truth, ordinary observations, output segments, and client testimony. It does not use an arm label, receipt verdict, permit identifier, or internal obligation state to decide observable success. Internal repair persistence/completion is reported separately as mechanism telemetry.

**Plain-English reading:** The grader uses the external script, provider truth, ordinary observations, generated segments, and client reports. It does not award success because an arm's receipt says SATISFIED or because its repair row says done. This reduces self-grading. Internal obligation data is useful for mechanism inspection but is not substituted for externally supported communication.

**Difficult words:** Oracle = independent outcome checker; controller belief = what the application thinks; telemetry = internal diagnostic records; label neutrality = not changing a grade because the arm name changes.

**A teaching example:** A driving examiner observes the car's path rather than accepting the dashboard's 'excellent driving' message.

**Keep the claim accurate:** Independent implementation does not mean infallible. The grader can contain bugs or narrow semantic assumptions.

### 20. Measurement: separate questions, separate answers

> The endpoints distinguish final business state; claim truth and supporting evidence at publication/playback; incompatible stale exposure; a correct supported final update; explicit withdrawal; and persistence/completion of repair. Missing relevant evidence or playback acknowledgements remains UNKNOWN. Introductory words do not establish decisive confirmation. All main-study audio evidence is labelled SCRIPTED_TONE_SEMANTIC_PROXY: word-index acknowledgements are logical proxies, without verified acoustic word alignment or human listening.

**Plain-English reading:** The endpoint list prevents one good result from hiding a different failure. Correct database state, true wording, applicable evidence, exposure, final update, and explicit withdrawal are distinct. The start of 'Your maintenance ...' is not sufficient evidence that a confirmation or time was exposed. The study uses logical word positions and tones, so its evidence does not establish acoustic intelligibility.

**Difficult words:** Endpoint = the exact result being measured; N/A = not applicable by design; UNKNOWN = applicable but insufficient evidence; alignment = mapping a word to an audio position.

**A teaching example:** Hearing the introduction 'Your train ...' does not tell you whether 'is cancelled' was played next.

**Keep the claim accurate:** An acknowledgement without suitable word/audio alignment cannot prove which real spoken words a person heard.

## Original manuscript page 4

**Original heading: 4. Study design and analysis**

**Original heading: 4.1. Frame, allocation, and execution**

### 21. Design: 500 draws from 50 recipe families

> The frame combines 50 fixed simulator recipe families with generated appointment contexts. Recipes are sampled within strata with replacement under their context constraints. The target estimand is an arm difference over this declared recipe/context mixture, not a production population of callers, providers, or arbitrary agents. The input draw is the sampling unit; its three arm outcomes form a paired cluster. Repeated recipe families do not become independent domains.

**Plain-English reading:** A recipe defines a kind of event ordering and fault. Context fills in appointment details under its constraints. Drawing with replacement means the same family can recur. Every sampled input is tested under each arm, keeping those three rows together. The estimand is the average arm difference for this declared synthetic mixture, not for every conceivable customer call.

**Difficult words:** Sampling frame = eligible source of test inputs; stratum = planned group of scenarios; estimand = the precise quantity the study aims to estimate; cluster = observations kept together because they belong to one unit.

**A teaching example:** Testing ten meal recipes with different ingredient amounts gives many preparations, but not hundreds of independent cuisines.

**Keep the claim accurate:** Independent context draws are an assumption. A shared host and repeated families can create additional dependence.

### 22. Table 2: count inputs and executions correctly

> Table 2. Fixed allocation. Each input receives all three arms, yielding 500 complete comparison sets and 1,500 original executions.

**Plain-English reading:** There are 300 clean inputs, 100 hidden-commit inputs, 60 playout inputs, and 40 other-boundary inputs. Each gets three executions. Thus 500 inputs produce 1,500 rows, not 1,500 independent scenarios. The correction weights are 100/200, 60/200, and 40/200 after excluding the 300 clean inputs from that correction endpoint.

**Difficult words:** Allocation = the planned number assigned to each stratum; denominator = the total eligible units for a fraction; correction weight = a stratum's contribution to the planned correction mixture.

**A teaching example:** Five hundred exam questions answered by three students produce 1,500 answers, but still only 500 distinct questions in the comparison.

**Keep the claim accurate:** The 33 recovery inputs are a designated subset, not an extra 33 inputs added to the 500.

| Stratum | Inputs | Original executions | Correction weight |
| --- | ---: | ---: | ---: |
| CLEAN | 300 | 900 | Not applicable |
| HIDDEN_COMMIT | 100 | 300 | 0.50 |
| PLAYOUT | 60 | 180 | 0.30 |
| OTHER_BOUNDARY | 40 | 120 | 0.20 |

### 23. Design: controlled faults and full observation

> The saved input identities and serial order are retained. Comparable provider capabilities, faults, evidence availability, and budgets apply across arms. Named barriers control intended event order. Each original retains a 600-second collection horizon anchored to the saved final-request deadline, including recognized refusals. Checkpoint recovery preserves identity and deadline without replaying commands. Calibration and diagnostic runs are separate from main outcomes.

**Plain-English reading:** The serial schedule and identities are saved. Each arm receives comparable conditions. Named barriers pause at a specific event boundary instead of hoping a sleep catches the right race. The collector keeps observing for the full saved 600-second horizon after the final request, even when the driver returns or refuses. After interruption it resumes collection for the same execution and deadline, rather than issuing the business commands again.

**Difficult words:** Barrier = an explicit wait/release point; horizon = observation period; checkpoint = saved progress; replay = issuing commands again; serial = one original execution admitted at a time.

**A teaching example:** A crash test triggers the obstacle at the marked sensor line, rather than guessing when the car reaches it with a stopwatch.

**Keep the claim accurate:** A full window does not guarantee every asynchronous event was captured. Collection gaps require separate treatment.

### 24. Design: BACKED_UP is an evidence status

> All 1,500 originals reached BACKED_UP. The ledger contains one admission, export, and backup transition per original; all export transitions follow their saved observation deadlines. This verifies window accounting, not perfect event capture. Failures, timeouts, refusals, and UNKNOWN values are retained. The campaign had pauses and versioned experiment-control amendments; it was not an uninterrupted reliability endurance run.

**Plain-English reading:** All planned executions have saved original records and verified backup transitions. There is one admission per identity, followed by export after the saved deadline and backup. That establishes accounting and preservation. It does not certify a successful booking or a successful confirmation. Pauses and instrument amendments remain part of the history.

**Difficult words:** Admission = allowing the next planned execution to start; export = saving a portable record; BACKED_UP = ledger state indicating retained verified evidence; amendment = explicitly versioned change.

**A teaching example:** A hospital archive can contain a complete record of an unsuccessful treatment. Archive completeness and treatment success are different facts.

**Keep the claim accurate:** This is a document-storage analogy only; the application itself contains no medical workflow.

**Original heading: 4.2. Prespecified comparisons and missingness**

### 25. Analysis: two primary endpoints and a clean-case tolerance

> The co-primary P2-B3 comparisons are correction success on 200 non-clean inputs and unsupported decisive exposure on 100 hidden-commit inputs. Correction risk differences standardize saturated arm-by-stratum means using weights 0.50/0.30/0.20. Conservative paired component bounds allocate error across strata and the two co-primary quantities; each reported co-primary interval is 97.5%. Clean-task usefulness has an accepted five-percentage-point tolerance with a one-sided 95% bound. Secondary P1-B3 and P2-P1 contrasts examine incremental mechanisms.

**Plain-English reading:** The primary comparison is P2 minus B3. Correction success uses the 200 non-clean inputs; hidden-commit exposure uses the 100 hidden-commit inputs. A weighted mean preserves the planned recipe mix. Conservative paired bounds retain uncertainty despite zero observed discordances. The analysis allocates error across the two primary questions. Clean cases check whether added protection loses too much ordinary usefulness, with a five-percentage-point tolerance.

**Difficult words:** Risk difference = success proportion in one arm minus that in another; saturated cell means = estimate a separate arm-by-stratum mean; co-primary = one of two main planned outcomes; noninferiority margin = largest tolerated loss.

**A teaching example:** If the intended workload is half hidden commit, its result receives half the correction weight even if one later selects an interesting trace.

**Keep the claim accurate:** The stored claim guards remain restricted. A computed bound is not blanket authorization for a confirmatory claim.

### 26. Analysis: prevent selection bias in recovery evaluation

> The 33 recovery inputs are designated before analysis; eligibility does not depend on an arm creating its own repair obligation. Ordinary supported updates and complete corrective communication are distinct. Planned-denominator best/worst assignments retain missing outcomes. The ten-comparison Holm family reports diagnostic paired tests, not permission to reinterpret UNKNOWNs as successful prevention. Twenty fixed temporal-block omission summaries assess the primary correction contrast.

**Plain-English reading:** The study chooses the 33 recovery opportunities before looking at which arm created repair rows. Otherwise P2 could be evaluated on an easy subset that B3 never entered. Missingness bounds ask how the result changes under every allowed assignment of unknown binary outcomes. Holm addresses the declared family of ten diagnostics. Omitting fixed time blocks checks whether the primary tie depends on one part of the execution order.

**Difficult words:** Post-treatment selection = selecting units using a variable affected by the arm; missingness bound = range consistent with unknown outcomes; Holm = multiple-test adjustment; sensitivity check = test how interpretation depends on a choice or assumption.

**A teaching example:** Compare delivery services on the same planned packages, not just the packages each service chose to mark as needing attention.

**Keep the claim accurate:** A sensitivity check addresses the assumption it varies, not every possible source of bias.

**Original heading: 4.3. Timing**

### 27. Analysis: timing and the bootstrap

> The accepted timing computation uses a 600-second restricted horizon, 2,000 stratified paired input bootstrap draws (seed 8042051), and a right-censored lognormal accelerated-failure-time model with arm and stratum terms. Its 1,000 bootstrap draws (seed 8042052) resample input IDs with all three arms together. This is time to a supported scripted-ACK completion, not complete corrective communication or human call latency. Shared-host dependence, censoring validity, and model form remain assumptions. The analysis retains its restricted claim-permission flags; computation alone does not validate them.

**Plain-English reading:** The timing calculation resamples input IDs, keeping each input's B3/P1/P2 results together. Two thousand draws give the paired timing interval; a separate thousand draws assess uncertainty in an AFT model. A fixed seed makes the computational random draws repeatable. The endpoint is completion of a supported scripted ACK, not the time until a customer understands the corrected appointment.

**Difficult words:** Bootstrap = repeatedly resampling observed units; censored = the event time is only partly known; AFT = a model describing multiplicative changes in time; lognormal = logarithm of time follows a normal-shaped distribution; seed = reproducible random-number starting value.

**A teaching example:** Keep three test versions of the same case on one index card and resample cards, not individual results torn from their cases.

**Keep the claim accurate:** Shared-host dependence and informative censoring can invalidate an otherwise neatly calculated interval.

## Original manuscript page 5

**Original heading: 5. Results: business state and supported claims**

### 28. Table 3: know whether TRUE is good or bad

> Table 3. Final stored grades. Fractions use all planned inputs eligible for that endpoint. TRUE is adverse for unsupported exposure and forbidden effects.

**Plain-English reading:** Final business correctness and supported updates are favorable when TRUE. Forbidden effects and unsupported exposure are adverse when TRUE. Every table fraction uses that endpoint's eligible denominator. Different rows are different questions; you cannot subtract their counts to infer overlap unless the paired row-level relationship was actually checked.

**Difficult words:** Favorable endpoint = higher is desirable; adverse endpoint = higher indicates harm; marginal count = total for one outcome without the joint relationship to another outcome.

**A teaching example:** A school can report 90 students passing maths and 80 passing English. That alone does not tell you exactly how many passed both.

**Keep the claim accurate:** The separate raw-status cross-tab is available because that overlap was checked from row-level data.

| Endpoint | B3 | P1 | P2 |
| --- | ---: | ---: | ---: |
| Correct final business state | 455/500 | 455/500 | 455/500 |
| Clean task success | 300/300 | 300/300 | 300/300 |
| Correction success | 155/200 | 155/200 | 155/200 |
| Correct supported final update: TRUE | 408/500 | 408/500 | 408/500 |
| Correct supported final update: UNKNOWN | 0/500 | 4/500 | 4/500 |
| Forbidden effect recorded | 0/500 | 0/500 | 0/500 |

### 29. Results: the main business comparison tied

> Business correctness is 91% for every arm, with correction outcomes identical input by input: 73/100 hidden commit, 56/60 playout, and 26/40 other boundary. The weighted correction difference is zero; its conservative 97.5% interval is [-8.79, +8.79] percentage points (pp). The hidden-commit adverse-exposure comparison is 0/100 per arm, with difference interval [-4.95, +4.95] pp. These results demonstrate no incremental benefit on the co-primary endpoints; they do not prove universal equivalence or zero risk.

**Plain-English reading:** Each arm finishes 455 of 500 business targets correctly. Removing the 300 clean successes leaves 155 of 200 successful corrections. Hidden commit contributes 73 successes, playout 56, and other boundary 26. The paired correction difference is exactly zero in the observed sample. The conservative interval still allows effects in either direction in the declared frame under its assumptions. Zero events in the hidden-commit adverse endpoint is not proof that the risk is impossible.

**Difficult words:** Percentage point = absolute difference between percentages; conservative = deliberately avoiding overly narrow uncertainty; discordance = a paired case where arms differ.

**A teaching example:** If two thermometers give the same readings in your test rooms, that supports a tie there. It does not prove they will always agree everywhere.

**Keep the claim accurate:** Do not call the zero difference a proof that the mechanisms are useless. The study's frame and implementation limit the conclusion.

### 30. Results: clean usefulness and block sensitivity

> All 300 clean inputs succeed per arm. The P2-B3 one-sided 95% lower bound is -1.22 pp, above the accepted -5 pp tolerance under the frozen conditional rule. Every primary correction block-omission estimate remains zero. Neither result establishes independence or stationarity for timing or secondary endpoints.

**Plain-English reading:** Every arm succeeds on all 300 clean inputs. The one-sided lower bound says the estimated clean difference is compatible with at most a limited loss under the accepted rule; it is above the allowed negative five-point margin. Removing any one of twenty temporal blocks leaves the primary correction difference at zero. That stability concerns this endpoint, not all aspects of the system.

**Difficult words:** One-sided bound = uncertainty focused on one direction; lower bound = lower end of the permitted range; stationarity = behavior remaining stable over time.

**A teaching example:** A protection feature should not stop normal customers from completing ordinary work. Clean inputs provide that usefulness check.

**Keep the claim accurate:** Three hundred clean successes do not prove production success is exactly 100%.

### 31. Table 4: UNKNOWN stays visible

> Table 4. Unsupported exposed claims across all 500 inputs per arm. No UNKNOWN is counted as safe.

**Plain-English reading:** B3 has four recorded unsupported exposures, 481 negative grades, and 15 unknowns. P1 and P2 have zero recorded positive grades, the same 481 negative grades, and 19 unknowns. The table deliberately makes unknown testimony visible. The apparent four-event advantage disappears as a certain prevention claim when you inspect the paired unknown results.

**Difficult words:** FALSE for an adverse endpoint = no adverse event established under the grading rule; UNKNOWN = relevant evidence insufficient; paired counterpart = the same input under another arm.

**A teaching example:** A security camera that misses the doorway cannot certify that nobody entered. Missing footage is not a clean negative observation.

**Keep the claim accurate:** Never report this as 'B3 made four errors and P2 proved zero risk'.

| Stored grade | B3 | P1 | P2 |
| --- | ---: | ---: | ---: |
| TRUE | 4 | 0 | 0 |
| FALSE | 481 | 481 | 481 |
| UNKNOWN | 15 | 19 | 19 |

### 32. Results: the four exposure cases do not identify prevention

> The four B3 TRUE outcomes occur in the version-change-before-start playout recipe. Their P1/P2 counterparts are UNKNOWN. Thus the observed 4-versus-0 TRUE count does not establish that permits eliminated exposure. None of the four belongs to the hidden-commit primary denominator. Incompatible stale exposure has zero TRUEs but 15 UNKNOWNs for B3 and 19 each for P1/P2. Content can become outdated after a later accepted request even when it was compatible when originally played.

**Plain-English reading:** All four B3 positive exposure grades come from a playout recipe where the provider version changes before playback. Their proposed-arm counterparts lack enough evidence for a definite exposure grade. These cases are not in the hidden-commit primary group. Previously valid content can also become outdated after a later revision; that is distinct from content being stale at its original playback time.

**Difficult words:** Resource version = identifier of a particular state of an appointment; stale = no longer applicable to the currently accepted situation; counterpart UNKNOWN = no conclusive paired answer.

**A teaching example:** A timetable statement can be correct when announced and later need withdrawing after the train is rescheduled.

**Keep the claim accurate:** An earlier statement needing correction does not necessarily mean it was false when first spoken.

**Original heading: 5.1. Driver status is not the outcome**

### 33. Results: FAILED and COMPLETED are process labels

> The raw statuses are 1,359 COMPLETED and 141 FAILED, with 47 failures per arm. All 141 FAILED records nevertheless have correct final business state, and none records a supported final update. Conversely, 135 COMPLETED records have incorrect final business state. The paired business result is therefore not a renamed driver success rate. Original failures and grades remain unchanged. Available compact records do not justify calling every historical exception an expected refusal; such a classification requires its original evidence and response context.

**Plain-English reading:** There are 141 raw driver failures and 1,359 normal completions. Every failed driver record has correct final business state but no supported final update. Another 135 normal completions have incorrect business state. The original record and the independent grades therefore tell different stories. Do not rewrite the raw statuses to make a nicer success percentage.

**Difficult words:** Raw = original retained value; cross-tabulation = counting combinations of two variables; exception = a program signalling a problem; infrastructure failure = a technical malfunction, not automatically any rejected application request.

**A teaching example:** An ATM can dispense cash then fail to print the receipt. A smooth screen animation can also complete while a requested transfer is not achieved. Observe both facts.

**Keep the claim accurate:** The compact evidence does not establish that every one of the 141 failures had the same refusal cause.

## Original manuscript page 6

**Original heading: 6. Corrective communication and timing**

### 34. Recovery results: an update is not the full correction criterion

> All three arms deliver an ordinary supported corrected update in each of the 33 designated recovery inputs. Complete corrective communication is TRUE for all 33 P2 inputs; B3 and P1 each have 26 FALSE and seven UNKNOWN. A claim that the baseline never corrects the appointment would contradict these results.

**Plain-English reading:** Every arm delivers a supported corrected update in the 33 planned challenges. P2 additionally receives complete communication credit in all 33. Each comparator has 26 definite failures and seven unknowns for that stricter endpoint. The result is about the implemented withdrawal criterion, not baseline inability to update the appointment.

**Difficult words:** Ordinary update = supported current information; complete corrective communication = the declared update-plus-withdrawal requirement when applicable; comparator = arm used as a reference.

**A teaching example:** 'Your appointment is now at 14:15' gives a new time. 'My earlier confirmation was outdated; your appointment is at 14:15' explicitly addresses the previous message as well.

**Keep the claim accurate:** These sentences are teaching examples. The grader's actual accepted prefix is documented separately.

### 35. Figure 2: explain all three colors

> Figure 2. Complete corrective communication in the 33 planned recovery inputs per arm. FALSE and UNKNOWN remain distinct; the endpoint includes the fixed explicit-withdrawal criterion. Ordinary supported updates succeed in 33/33 for every arm.

**Plain-English reading:** The P2 bar contains 33 known successes. The B3 and P1 bars contain 26 known failures plus seven unknowns. The gray and amber parts must not be merged as 33 proven failures. Separately, ordinary update performance is 33/33 for every arm. The graphic depicts a specific secondary endpoint and its missingness.

**Difficult words:** Stacked bar = colored parts making up one planned total; denominator = 33 eligible inputs per arm; descriptive plot = a picture of recorded counts, not a causal proof.

**A teaching example:** An attendance chart should distinguish absent students from students whose attendance sheet was lost.

**Keep the claim accurate:** The bars do not show real people hearing or understanding a correction.

<!-- COMMUNICATION_CHART -->

### 36. Recovery results: the five challenge families

> The recovery families comprise full playback before correction (9 inputs), delayed decisive acknowledgement (7), partial decisive-time playback (7), reconnect with another revision (7), and restart before repair (3). P2 is TRUE throughout. Comparator FALSEs occur in the first, second, fourth, and fifth families; the partial-time family supplies all seven comparator UNKNOWNs.

**Plain-English reading:** The 33 inputs are divided 9+7+7+7+3. The challenges vary whether output finished, a decisive ACK arrived late, time words were partly played, another revision arrived after reconnect, or a worker restarted before repair. The seven partial-time cases are exactly where comparator communication grades are unknown. This locates missingness instead of hiding it in a total.

**Difficult words:** Reconnect = client session returns after disconnection; decisive-time playback = content reaches a consequential time phrase; restart-before-repair = worker is restarted between recorded obligation and delivery.

**A teaching example:** Five different fire drills can test different procedures even when they all end at the same assembly point.

**Keep the claim accurate:** Having a restart recipe does not, by itself, prove unattended production recovery. The actual consumer path and orchestration matter.

### 37. Recovery analysis: tiny p-values and seven unknowns

> For P2-B3 and P2-P1, 26 known pairs favor P2, none favors the comparator, and seven pairs are missing. The exact McNemar diagnostic p-value is 2.9802e-8; the ten-family Holm diagnostic value is 2.9802e-7. These complete-pair diagnostics are not missingness-free confirmatory claims. Assigning all possible binary values to the seven baseline UNKNOWNs yields an empirical planned-denominator difference range of +78.79 to +100 pp. That range is an identification bound, not a confidence interval.

**Plain-English reading:** Among known pairs, 26 favor P2 and none favor the baseline. McNemar examines this imbalance; Holm adjusts within the planned diagnostic family. Seven pairs remain missing. If all seven unknown baseline results were successes, P2's advantage is 26/33. If all were failures, it is 33/33. That yields 78.79 to 100 percentage points as a sample identification range, not a confidence interval for a wider population.

**Difficult words:** p-value = probability of data at least as incompatible with a specified null model, assuming that model and its conditions; identification bound = possible range given missing outcomes; diagnostic = exploratory/qualified interpretation.

**A teaching example:** You can count what every missing answer might do without pretending to know which answer it actually contained.

**Keep the claim accurate:** A tiny p-value is not the probability our theory is true and does not repair a narrow endpoint or violated assumptions.

### 38. Recovery telemetry: 40 obligations across 33 inputs

> P2 telemetry records 40 obligations across the 33 inputs, all REPAIR_PLAYED. Additional obligations occur after another revision. This supports retained obligation/playback-state accounting. It does not independently prove unattended discovery: the sampled repair trace includes experiment-invoked worker processes. Observable communication grades do not use those internal obligation states.

**Plain-English reading:** One input can create more than one obligation when another revision arrives. Thus 40 obligations across 33 inputs is consistent. All end REPAIR_PLAYED in the retained internal telemetry. That describes obligation state, not independent proof of every service being continuously available. The sampled trace explicitly invokes repair workers from the experiment.

**Difficult words:** Telemetry = diagnostic state emitted by components; REPAIR_PLAYED = internal terminal delivery state; unattended discovery = a service finding pending work without a manual/driver call to deliver that particular repair.

**A teaching example:** A to-do list can have two tasks for one customer. Marking them complete is informative, but it is not independent proof that an autonomous clerk found them.

**Keep the claim accurate:** Do not say 'P2 autonomously recovers every crash' from this telemetry.

### 39. Measurement: the fixed phrase is a serious limitation

> **Measurement qualification.** The frozen withdrawal matcher requires a supported, fully acknowledged update beginning with "Correction: my earlier confirmation was outdated." It is arm-label neutral but template-specific. The positive result partly reflects the intended output behavior and its matching instrument. It does not establish semantically superior natural-language repair, restored human belief, or benefit over an alternative ordinary phrasing.

**Plain-English reading:** The withdrawal matcher accepts a particular prefix on a supported, fully acknowledged final update. It does not understand arbitrary equivalent language. P2 intentionally produces the matching type of correction, so the finding includes a message-format component. A different baseline phrase might satisfy a human while receiving no explicit-withdrawal credit here. The independent, label-neutral instrument still has a limited construct.

**Difficult words:** Construct = the underlying concept a measure intends to represent; template-specific = tied to prescribed wording; semantic equivalence = different wording with the same meaning; human belief repair = a listener revising their understanding.

**A teaching example:** A spelling checker that accepts one correct synonym but rejects another has a real rule, but does not measure all ways of expressing the idea.

**Keep the claim accurate:** This is why we cannot attribute the secondary finding solely to durable storage or claim better human understanding.

### 40. Table 5: plus means slower in this endpoint

> Table 5. Conditional restricted-mean scripted completion-time differences. Positive values mean longer recorded time; intervals are paired input-bootstrap 95% intervals.

**Plain-English reading:** The P2-B3 difference is about 0.2593 seconds; P1-B3 is 0.2251 seconds; P2-P1 is 0.0342 seconds. Positive means the proposed arm takes longer on the recorded timing measure. The intervals come from paired input resampling. These values concern supported scripted completion and a restricted horizon, not customers' conversation experience.

**Difficult words:** Restricted mean = timing summary capped at a chosen horizon; paired bootstrap interval = uncertainty computed while preserving each case's comparison; second = the unit here, unlike retry attempts or drain passes.

**A teaching example:** An extra document check can slightly delay issuing a receipt even while it protects the claims made on that receipt.

**Keep the claim accurate:** Do not market a latency improvement; the recorded differences point the other way.

| Comparison | Difference (seconds) | Interval (seconds) |
| --- | ---: | ---: |
| P2-B3 | +0.2593 | +0.2241 to +0.2996 |
| P1-B3 | +0.2251 | +0.2041 to +0.2472 |
| P2-P1 | +0.0342 | +0.000073 to +0.07192 |

### 41. Timing: event observations, censoring, and model convergence

> The timing set contains 1,224 completion events and 276 censored rows, without missing or zero times. All 1,000 AFT bootstrap fits converge. Conditional time ratios versus B3 are 1.2258 for P1 (interval 1.2044-1.2451) and 1.2265 for P2 (1.2034-1.2506). Lognormal form and independent censoring are unproven; convergence does not resolve either assumption. No faster-agent claim follows.

**Plain-English reading:** There are 408 supported completions per arm, totaling 1,224 events. The other 276 records are censored. The AFT model's time ratio of about 1.226 means a multiplicative time factor under that model, not 1.226 seconds. All bootstrap fits converged, so none was silently discarded. But solving an optimization problem does not establish that lognormal timing or independent censoring is true.

**Difficult words:** Event = observed endpoint completion; censored row = exact completion time not established within the observation basis; time ratio = multiplicative factor; convergence = optimizer meets its stopping conditions.

**A teaching example:** A calculator can correctly fit a straight line to a curved relationship. Numerical success does not prove the chosen shape is right.

**Keep the claim accurate:** Keep missing-event and historical infrastructure labels visible. Do not reinterpret all censoring as harmless waiting.

## Original manuscript page 7

**Original heading: 7. Trace interpretation and validity**

### 42. Trace 145: right booking, wrong claim predicate

> **A correct transaction with a refused statement.** Sequence 145 begins with a committed booking and a deliberately lost response. Reconciliation cancels the first appointment and creates the corrected one because in-place rescheduling is unavailable. The synthesis path nevertheless selects RESCHEDULED_APPOINTMENT from the accepted revision number. That claim's predicate is VIOLATED, so B3 refuses the speech request with HTTP 409. Its raw FAILED status coexists with correct business/correction grades and an unsuccessful final-update outcome. P1/P2 share this revision-only claim-selection limitation; it was preserved, not silently repaired by a collector change.

**Plain-English reading:** The provider committed the first booking before losing its reply. Recovery established the old effect, cancelled it, and created the corrected booking. It did not perform an in-place reschedule. The frozen selection logic nevertheless asked to say RESCHEDULED_APPOINTMENT because the revision number exceeded one. The verifier rejected that predicate. This combines a studied application limitation with a collector-classification problem that was separately amended.

**Difficult words:** Predicate mismatch = requested statement asserts a fact unsupported by actual operations; synthesis input = structured facts/claim type supplied to output generation; classifier = instrument code deciding whether a refusal is expected or a technical stop.

**A teaching example:** A shop refunds an old purchase and creates a new order. Saying 'we edited your original order' may misdescribe what actually happened.

**Keep the claim accurate:** The application claim-selection behavior was not silently improved midway. The original FAILED status and grades remain.

### 43. Trace 59: factual phrase versus applicable evidence

> **Evidence can expire without changing every word's truth.** Sequence 59, B3, records a provider resource change before playback. The original grade has TRUE truth at publication/playback but FALSE evidence at playback, with unsupported exposure TRUE and final business state FALSE. An appointment-time component can remain true while its resource/evidence binding is inapplicable. The trace illustrates why a scalar success label is insufficient; it is not a formal proof of completeness of the oracle.

**Plain-English reading:** The appointment-time phrase can be true while its supporting observation refers to an old resource version. The retained grade therefore separates truth from evidence at playback. Final business state is also separately false in this input. One sentence of confirmation can contain a correct time component without satisfying the full evidence contract.

**Difficult words:** Version binding = evidence identifies exactly which resource state it concerns; scalar = a single value; oracle completeness = ability to correctly handle every relevant condition.

**A teaching example:** A document says a machine was safe at inspection version 4. The machine is still on the same floor at version 5, but that unchanged detail does not renew the inspection.

**Keep the claim accurate:** This illustration does not imply all true statements require this particular application's receipt format.

### 44. Trace 82: correction can itself become outdated

> **Another revision during repair.** Sequence 82, P2, retains an initial confirmation, an interrupted revision-two repair, a revision-three corrective statement, and delayed earlier testimony. Two obligations end REPAIR_PLAYED, with correct final state, update, and withdrawal grades. This is a concrete recorded repair path. Its explicitly invoked workers preclude presenting it alone as autonomous recovery evidence.

**Plain-English reading:** The trace includes an initial confirmation, a revision-two repair that is interrupted, and a later revision-three correction. Delayed earlier testimony is retained rather than discarded because it is inconvenient. Two obligations end played, while final state, supported update, and withdrawal receive favorable grades. The control explicitly invokes workers, so this trace demonstrates a recorded path rather than autonomous service discovery.

**Difficult words:** Revision three = the third accepted target; terminal state = final recorded state of a particular record; orchestration = controlling which process runs when.

**A teaching example:** You begin apologizing for a 12:15 booking with a new 14:15 time, but the customer asks for tomorrow at 15:15 before the apology finishes. The repair must follow the newest accepted target.

**Keep the claim accurate:** The illustrative time story is a teaching aid. The original export is the authority for the exact retained sequence.

**Original heading: 7.1. Threats to validity**

### 45. Validity: are we measuring the thing we care about?

> **Construct validity.** Typed intents and tones isolate protocol state. Word-index ACKs do not verify intelligible audio, attention, or understanding. Missing terminal testimony remains UNKNOWN. The exact-prefix withdrawal test is narrower than general semantic retraction and may favor the particular repair template by construction. The complete communication difference must be read alongside equal ordinary-update performance. Repair telemetry is a mechanism observation, not an independent delivery oracle.

**Plain-English reading:** Construct validity asks whether the instrument represents the intended concept. Tones and ACK indexes can test protocol behavior but not attention or intelligible-word exposure. The fixed wording criterion captures one implemented form of explicit correction. Internal telemetry cannot replace the independent output measure. Equal ordinary-update results keep the positive finding in context.

**Difficult words:** Validity = how well an inference is supported; proxy = substitute measurement; testimony = a reported observation; construct validity = fit between a measure and its intended concept.

**A teaching example:** Counting opened textbooks measures access to books, not necessarily comprehension of their content.

**Keep the claim accurate:** Do not convert a protocol proxy into a claim about human psychology.

### 46. Validity: what did each arm actually change?

> **Implementation validity.** The shared claim-selection limitation can withhold useful confirmations in all arms. Outcomes concern these implementations, not ideal mechanisms. Preventive permits and product-state invariants change together in P1, so their individual effects are not identified. P2 differs by the repair package, including its output behavior, rather than storage persistence alone. The study cannot attribute the secondary difference solely to durability.

**Plain-English reading:** The shared claim-selection limitation can affect every arm. P1 changes permits and product-state rules together. P2 changes a repair package that includes what is said and how obligations are stored. Therefore an arm difference identifies the effect of that implemented package under the study, not the isolated effect of one storage mechanism. Frozen implementations may behave differently from idealized mechanisms.

**Difficult words:** Confounding within a package = multiple changing components prevent isolating one; causal attribution = assigning a change in outcome to a particular cause; idealized = assuming a perfectly implemented concept.

**A teaching example:** If a new teaching course changes both textbook and instructor, better marks cannot be attributed to the textbook alone.

**Keep the claim accurate:** Answering 'durability alone caused 33/33' would exceed this design.

### 47. Validity: independence is an assumption

> **Statistical validity.** Five hundred context draws arise from 50 fixed families, not 1,500 independent tasks. Shared serial infrastructure, temporal drift, and operational interruptions weaken independence assumptions. The block sensitivity addresses the primary contrast only. The helper outputs retain confirmatory/model claim guards as false; this paper reports conditional bounds and diagnostic tests rather than overriding those restrictions.

**Plain-English reading:** The 1,500 rows belong to 500 paired inputs drawn from 50 fixed families. Host load and time can influence several rows. Operational interruptions can introduce additional dependence. The temporal omission check preserves the primary tie but is not a full proof of independent timing errors. Original analysis flags remain restricted rather than being changed after a pleasing result.

**Difficult words:** Temporal drift = conditions changing with time; independence = one unit's uncertainty not influencing another's after the model's conditions; confirmatory = supporting a planned inference under satisfied assumptions.

**A teaching example:** Students taking an exam in a hot room may share a room effect. More answers do not remove that dependence.

**Keep the claim accurate:** Do not call 1,500 rows an effective sample size of 1,500 independent cases.

### 48. Validity: preserve timing history rather than rewriting it

> Four raw timing records retain INFRASTRUCTURE_FAILURE labels (sequences 1, 2, 145, 616). A separate accepted view reuses only the previously approved first-two label sidecars, with identical numeric durations and outcomes; two infrastructure labels remain in that view. No new sidecar or retrospective regrade was applied. These histories do not establish independent administrative censoring. Restricted-horizon and AFT estimates therefore require qualified interpretation.

**Plain-English reading:** Four original records retain infrastructure-failure censor labels. Two previously accepted sidecars create a separate timing view with label-only changes; numeric outcomes and durations remain identical. This task did not create another sidecar or regrade old cases. A historical label does not establish whether censoring is statistically independent of the outcome.

**Difficult words:** Sidecar = separate amendment metadata stored beside an original; retrospective regrading = changing a past outcome after seeing evidence/results; administrative censoring = observation stopping for reasons appropriately independent under the analysis assumptions.

**A teaching example:** Add an explanatory note next to an old lab entry rather than erasing the original ink.

**Keep the claim accurate:** A separate view must remain traceable to the original, including limitations its relabeling does not solve.

### 49. Validity: provenance is not a universal deployment guarantee

> **Operational and external validity.** Nine admission-controller binding segments document amendments and pauses. A binding is a provenance reference, not per-process binary attestation. Hash verification and post-deadline exports establish integrity/accounting, not complete capture of every late event or deployment reliability. No natural callers, speech-model comparison, payment workflow, or software-update benchmark was evaluated. Generalization beyond the declared simulator frame remains untested.

**Plain-English reading:** Nine controller-binding segments preserve the history of different operational versions. Their records connect identities, admission, exports, and backups. They are not hardware-level attestations of every running binary. Hashes support unchanged bytes and post-deadline exports support accounting; neither guarantees complete observation. The study has no evidence about real callers, speech-model rankings, payments, or software-update agents.

**Difficult words:** Binding = recorded association between identities/versions; attestation = independent evidence about what actually ran; external validity = transfer of results beyond the tested setting.

**A teaching example:** A signed travel itinerary records intended flights. It is not, by itself, proof of every minute of the passenger's journey.

**Keep the claim accurate:** Use the term 'controlled protocol evaluation', not 'production-certified voice system'.

## Original manuscript page 8

**Original heading: 8. Reproducibility, implications, and conclusion**

### 50. Reproducibility: what was checked

> All 1,500 originals, including unsuccessful outcomes, remain in the analysis. Identity/export/backup joins and 196,037 chained notices were checked; 3,450 frozen final-inventory file hashes still match after analysis. Operational provenance identifies each original's applicable controller binding. These checks do not imply that every original ran the final controller version.

**Plain-English reading:** The analysis retains all originals. The ledger joins original identities to export and backup records. Its chained notices support traceability. The final source inventory still matches after local analysis. However, earlier originals were admitted under earlier controller bindings, so the paper does not pretend the entire campaign used the last operational binary.

**Difficult words:** Hash = content fingerprint; chained notice = event record linked by hashes to earlier notices; inventory = list of files and fingerprints; provenance = the history showing where a result came from.

**A teaching example:** Keep every version of a laboratory procedure and record which version applied to which sample.

**Keep the claim accurate:** A hash proves byte identity with a trusted commitment, not that the content's scientific claim is true.

### 51. Reproducibility: results package versus full archive collection

> The retained local result package contains the full 1,500-row CSV, compact original records, frozen-method outputs, verification records, reproduction commands, and three bounded trace examples. It does not contain all raw archives or the entire pinned runtime. The final returned evidence bundle has SHA-256 1d67c5adc39fc6ef6f9cfcaa32a910532be8a9faf824383946d5c2ed10426341. A separate companion evidence map records exact source/output hashes. No public archival DOI or anonymously accessible full artifact is claimed.

**Plain-English reading:** The compact local package contains the CSV, compact records, calculations, checks, instructions, and selected trace examples. It is not every large raw archive or a bundled computer environment. The long SHA-256 identifies the returned evidence bundle. A companion map links claims to files. The manuscript does not invent a public DOI or imply a private local file is a public research deposit.

**Difficult words:** SHA-256 = a standard 256-bit cryptographic content fingerprint; CSV = table stored as comma-separated text; runtime = interpreter and dependencies; DOI = persistent identifier assigned through an appropriate registration route.

**A teaching example:** A book's index helps locate material, but is not the full library it indexes.

**Keep the claim accurate:** Publishing an artifact would require an intentional release and appropriate checks; it has not occurred merely because a PDF exists.

### 52. Conclusion: the strongest honest story

> The principal result is an observed tie in business correctness beyond a strong baseline. The secondary result distinguishes an ordinary supported update from the implemented explicit-withdrawal criterion. This suggests a useful reporting discipline: distinguish effects, knowledge, exposure, and correction, and preserve refusal and missingness rather than equating either with success. It does not establish a breakthrough, general superiority, or durable repair's isolated causal effect. For software-update agents, artifact versions and deployment evidence offer a conceptual analogue; this study supplies no empirical software-update result. The completed study supports a bounded systems/measurement paper with a negative primary finding and a qualified secondary finding.

**Plain-English reading:** The business endpoint ties beyond the competent baseline. The secondary result distinguishes ordinary current information from the fixed explicit-withdrawal criterion. This supports a reporting discipline that keeps effect, knowledge, exposure, and correction separate. It does not establish a breakthrough or durability's isolated benefit. Software updates are a possible analogy only; no update benchmark was run. The contribution is a bounded systems/measurement study, including a negative primary finding.

**Difficult words:** Implication = a lesson supported by a result; transfer hypothesis = a proposed extension to a new setting; negative primary finding = planned main comparison does not demonstrate an advantage.

**A teaching example:** A careful experiment can show that the established safety measures already handle a problem well, while revealing a narrower communication gap worth studying.

**Keep the claim accurate:** The study's completion and a useful manuscript do not guarantee novelty, acceptance, or a publication venue.

# PART VI - The twelve referenced works explained

These works are not twelve language models installed in our system. Some are algorithms, runtimes, theories or benchmarks; one is an engineering article. The following concise summaries explain their role. They do not reproduce the papers, claim their code was run, or compare their rates with ours. The close-reading chapter and the appendix retain the manuscript's references.

## 1. Featonby - Making retries safe with idempotent APIs

**What kind of work is it?** Engineering article, not a language model.

**Simple explanation:** The article explains why retrying a request can repeat an unwanted side effect. Caller-provided identifiers distinguish another attempt at the same logical request from a new intent. Late requests and changed parameters require explicit API semantics. This is practical distributed-systems guidance, not an AI architecture we trained.

**Connection to our paper:** Our baseline already has durable operation identity and reconciliation. We apply known ideas; our results do not invent them. The article is not an experimental arm, and our AWS hosting decision is a separate issue.

**Read the primary source:** https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/

## 2. Atomix - Timely, Transactional Tool Use for Reliable Agentic Workflows

**What kind of work is it?** Transactional runtime research; arXiv preprint version v2.

**Simple explanation:** Atomix coordinates settlement of tool effects. It records resource reads/effects, seals a transaction's footprint, and uses progress information to determine when earlier conflicting work can no longer arrive. Effect classes determine what can be buffered, compensated or gated before release. It is a runtime for workflows, not the name of a foundation language model.

**Connection to our paper:** Our question emphasizes the evidence and exposure history of an outcome statement, including later correction. We did not run Atomix against B3/P1/P2. Gating irreversible effects is established prior work, not our first-ever invention.

**Read the primary source:** https://arxiv.org/html/2602.14849v2

## 3. Cordon - Semantic Transactions for Tool-Using LLM Agents

**What kind of work is it?** Task-scoped transactional runtime; cited as an arXiv preprint.

**Simple explanation:** Cordon treats a task as a validation and commit boundary. Its design tracks result lineage, reversible local changes, staged outward effects, delegated authority and recovery metadata. It validates the composed flow rather than approving isolated calls without their dependencies. 'Semantic transaction' here names a runtime abstraction, not a newly trained neural model.

**Connection to our paper:** It is close prior work for composed effect/authority boundaries. Our study evaluates a particular booking claim/repair contract and does not establish that Cordon lacks an equivalent capability or performs worse.

**Read the primary source:** https://arxiv.org/html/2606.17573v1

## 4. Revisable by Design - A Theory of Streaming LLM Agent Execution

**What kind of work is it?** Theory and revision-recovery algorithm; arXiv preprint.

**Simple explanation:** The paper studies users intervening while an agent is executing. Its action taxonomy distinguishes idempotent, reversible, compensable and irreversible actions. It explains how the action space constrains what revision can achieve and proposes a rollback-based recovery algorithm. The 'model' includes a formal execution model, which is different from an LLM's learned weights.

**Connection to our paper:** It prevents us from claiming that concurrent revisions or irreversible consequences are new ideas. Our experiment concerns frozen booking implementations and measured communication endpoints, not a stronger theorem about revisability.

**Read the primary source:** https://arxiv.org/abs/2604.23283v1

## 5. REVISE - Validity-Guided Recovery for Online Revisions in Agent Workflows

**What kind of work is it?** Validity-guided workflow runtime; arXiv preprint.

**Simple explanation:** REVISE uses recorded data/control dependencies to determine which workflow work a changed instruction invalidates. It preserves work whose validity is established, recomputes affected regions, and revalidates before commit. Incomplete provenance causes more conservative recovery. Its reported applications include LangGraph/LLMCompiler and Qwen3-14B; that is their evaluation setup, not our campaign's model.

**Connection to our paper:** Our protocol also respects accepted revisions, but our study does not measure selective recomputation savings or compare algorithms directly. A revision counter alone is not a novelty claim.

**Read the primary source:** https://arxiv.org/html/2609.00643v1

## 6. DART - Semantic Recoverability for Structured Tool Agents

**What kind of work is it?** Recovery-boundary framework; arXiv preprint.

**Simple explanation:** DART asks when restoring a local checkpoint remains meaningful after downstream work has already committed. It identifies admissible restore boundaries under dependency and effect constraints rather than assuming that mechanically restoring bytes is enough. The framework can block a restore that would invalidate committed work. It is not an interchangeable model API.

**Connection to our paper:** This reinforces the distinction between local recovery and external consequences. Our study measures booking/evidence/playback behavior and cannot claim to replace DART or outperform its evaluated recovery cases.

**Read the primary source:** https://arxiv.org/abs/2605.23311v1

## 7. Verified Tool Calls Improve LLM Agent Reliability Under Non-Atomic Failures

**What kind of work is it?** Verification-aware tool wrapper; arXiv preprint.

**Simple explanation:** The work examines tool behavior such as a timeout after dispatch, delayed visibility, and partial updates. Its wrapper combines postcondition checking, verification before retry, and idempotency keys. The key idea is strengthening interaction semantics without requiring a new underlying language model.

**Connection to our paper:** Those protections belong in a competent baseline, which is why our B3 includes related safeguards. Our incremental comparison concerns claim/repair packages beyond that baseline. We did not reproduce this paper's model/task results as part of the 1,500 originals.

**Read the primary source:** https://arxiv.org/abs/2608.02645v1

## 8. Tool Receipts, Not Zero-Knowledge Proofs

**What kind of work is it?** Claim/evidence verification framework; arXiv preprint.

**Simple explanation:** The paper links response claims to recorded tool executions and classifies their epistemic source. Its described runtime creates signed tool receipts and checks statements against them. A receipt is practical evidence about execution; it is not a zero-knowledge proof that every inference is correct. The framework and its benchmark are different objects from a trained base model.

**Connection to our paper:** Our receipt objects additionally participate in the implemented revision/resource/claim contract. Receipt-based verification itself is not our invention. We make no direct detection-rate comparison against this paper.

**Read the primary source:** https://arxiv.org/html/2603.10060v1

## 9. Skantze and Hjalmarsson - Towards Incremental Speech Generation in Dialogue Systems

**What kind of work is it?** SIGDIAL 2010 speech-generation research.

**Simple explanation:** This work considers producing speech incrementally while interpretation and response planning continue. Self-monitoring and revision matter because later input can change what should be said. It is a dialogue-system generation approach, not a contemporary foundation-model API.

**Connection to our paper:** It establishes that incremental output and correction have a long research history. Our focus is the connection to external booking evidence and the measured withdrawal endpoint. Our tones do not reproduce a human speech-generation evaluation.

**Read the primary source:** https://aclanthology.org/W10-4301/

## 10. PACE - A Playback-Aligned Context Engine for LLM-Based Full-Duplex Voice Dialogue

**What kind of work is it?** Playback/context middleware and benchmark; arXiv preprint.

**Simple explanation:** PACE addresses divergence between generated output, client playback and model-facing context. It records playback progress and repairs context after interruption, with an actual audio-only path through a black-box realtime voice model. It distinguishes playback evidence from attention/comprehension and discusses conditions needed for semantic alignment.

**Connection to our paper:** It is close prior work, not a competitor we tested. Our outcome is booking claim support and corrective communication under scripted proxies. PACE's own configuration labels, including P1, are unrelated to our P1 arm.

**Read the primary source:** https://arxiv.org/html/2608.07631v1

## 11. Tau-bench - Tool-Agent-User Interaction in Real-World Domains

**What kind of work is it?** Interactive evaluation benchmark; 2024 paper.

**Simple explanation:** Tau-bench supplies tool interfaces, domain policies and simulated users to evaluate interactive agents. It checks final database state against annotated goals and examines repeated-run reliability through pass^k. A benchmark is a test environment and scoring protocol, not a foundation model.

**Connection to our paper:** Its final-state approach is relevant background, but our instrument separately reports evidence/exposure/correction. Our 91% cannot be compared to its success rates because tasks, input paths, models and conditions differ. We did not claim a new leaderboard record.

**Read the primary source:** https://arxiv.org/abs/2406.12045

## 12. Tau-Voice - Full-Duplex Voice Agents on Real-World Domains

**What kind of work is it?** Grounded voice-agent benchmark; arXiv preprint.

**Simple explanation:** Tau-Voice evaluates full-duplex voice interaction on grounded tasks, including realistic audio conditions and verifiable task completion. It connects voice interaction quality with tool-based goals. It is a benchmark for evaluating agents, not the name of a single voice model.

**Connection to our paper:** Our typed-input/tone path does not measure accent robustness, recognition, natural conversation or its voice capability gap. The two studies motivate related questions but do not share a denominator. A future real-speech evaluation would need its own reviewed protocol.

**Read the primary source:** https://arxiv.org/abs/2603.13686

# PART VII - Difficult professor questions and defensible answers

These are practice answers, not permission to claim expertise or work you did not perform. Read the short answer first. The follow-up explains the boundary a professor may test. Adapt personal-contribution statements to your actual work.

## Motivation

### Q01. What problem are you solving in one minute?

**Answer:** I study the gap between external actions, evidence, and outcome messages when a request changes during execution. A booking can commit even when its reply is lost, and a previous confirmation can already have reached playback. The protocol separates reconciliation, claim authorization and corrective delivery.

**If challenged further:** Use the 12:15-to-14:15 teaching example, then distinguish provider truth, application knowledge and client testimony. Do not start with a technology shopping list.

### Q02. Is this an AI paper or ordinary distributed-systems engineering?

**Answer:** It is a systems/protocol evaluation in an agent application. Much of the foundation is distributed systems. The studied boundary concerns consequential agent claims and exposed output. The main experiment bypasses model uncertainty, so it is not a new-model capability paper.

**If challenged further:** That narrower identity is more defensible than calling every component an AI innovation. The relevance is how the surrounding system constrains model-proposed actions and statements.

### Q03. Why can a correct booking lack a justified confirmation?

**Answer:** The oracle can know from simulator truth that the booking exists while the application lacks the applicable observations needed to support its selected statement. Also, the statement might assert the wrong operation predicate, as in cancel/create versus in-place reschedule.

**If challenged further:** Correctness of a world state, truth of a phrase, and justification at the decision time are different questions. A correct guess does not create evidence.

## Novelty

### Q04. What exactly is new?

**Answer:** The candidate contribution is the implemented composition and auditable evaluation separating business state, evidence, exposure and explicit correction against a protected baseline. I do not claim to invent idempotency, receipts, revision handling, playback alignment or repair.

**If challenged further:** Novelty is not established by the case count. The paper's targeted related-work review identifies close antecedents, and external priority remains open to scientific review.

### Q05. Is this a breakthrough?

**Answer:** No breakthrough is demonstrated. The primary business comparison tied. A narrower secondary distinction appears in explicit corrective communication, with substantial template and scripted-playback limitations.

**If challenged further:** Presenting a careful negative result and a qualified secondary finding is more credible than overstating what the data can establish.

### Q06. Why not just use an existing transactional runtime?

**Answer:** Existing runtimes are important antecedents. Our study asks about one booking/evidence/playback contract, including correction after exposure. It does not demonstrate superiority over external runtimes or prove they cannot implement similar rules.

**If challenged further:** A head-to-head integration would be a different study. Do not invent missing capabilities in another paper to manufacture a novelty gap.

### Q07. Did you compare against a deliberately weak baseline?

**Answer:** B3 already has durable idempotency, reconcile-before-retry, revision invalidation, staging, compensation and playback tracking. It can refuse unsupported statements and provide ordinary corrective updates. All arms received ordinary-update credit on the same observable basis.

**If challenged further:** The identical business outcomes and 33/33 ordinary recovery updates are evidence that the baseline was not simply prevented from succeeding by the grader.

## Mechanism

### Q08. What does a claim permit guarantee?

**Answer:** It authorizes a particular statement using evidence bound to the operation, accepted revision, resource version and validity conditions. It is not a commit receipt from an omniscient provider or a universal proof that all later speech is safe.

**If challenged further:** Explain the configured publication/playback rechecks. A validity rule is meaningful only under its assumptions about observations, event timing and trusted components.

### Q09. Why not let the LLM decide whether to confirm?

**Answer:** The model can propose wording or intent, but fluency does not establish provider facts. Deterministic backend checks authorize decisive claims. This gives inspectable rules at a correctness boundary instead of allowing unconstrained prose to mutate state or certify outcomes.

**If challenged further:** It does not mean deterministic code is always correct. Its predicates, evidence binding and implementation still require qualification.

### Q10. What is UNKNOWN, precisely?

**Answer:** It means the current observations do not establish the relevant outcome. A timeout after a request may have been sent is not proof of failure. Reconciliation is needed before a retry can be justified.

**If challenged further:** Distinguish operation knowledge from an outcome grade that is UNKNOWN because playback evidence is missing. Both preserve uncertainty, but they describe different layers.

### Q11. Why does idempotency not solve the whole problem?

**Answer:** It helps avoid extra effects from repeated attempts at one logical request. It does not by itself accept a new request revision, establish current resource evidence, stop stale output or withdraw content already exposed.

**If challenged further:** A changed intent is not always the same logical request. Reusing one key for different meaning can violate the provider's contract.

### Q12. Why is compensation not the same as rollback?

**Answer:** Compensation is another action intended to address a previous external effect. It can fail and does not erase the fact that the earlier action occurred. A local database rollback cannot undo an already committed opaque-provider action.

**If challenged further:** For speech, later correction cannot make words unplayed. The system can record and address consequences, not reverse the listener's history.

### Q13. Does a repair row prove the user was corrected?

**Answer:** No. Internal persistence is mechanism evidence. A delivered, supported update and explicit withdrawal require the relevant external output evidence under the instrument. Our ACKs remain scripted proxies, not proof of understanding.

**If challenged further:** Forty REPAIR_PLAYED obligations across 33 inputs are useful telemetry, but the independent communication outcome does not read that internal state as its oracle.

### Q14. Did you prove unattended restart recovery?

**Answer:** The main retained telemetry alone does not prove it. The sampled P2 trace contains experiment-invoked repair workers. I can describe that recorded path and the separate qualification history, but not generalize it to an always-running autonomous consumer.

**If challenged further:** A strong unattended claim would require evidence of the documented consumer discovering pending obligations without a driver manually delivering each repair.

## Design

### Q15. What are your independent units?

**Answer:** The accepted conditional sampling unit is an input/context draw from the fixed recipe frame. Its three arm results form a paired cluster. There are 500 inputs, not 1,500 independent scenarios, and only 50 fixed recipe families.

**If challenged further:** Shared host, temporal effects and repeated families limit the independence assumption. The intervals are conditional on the declared frame and dependence assumptions.

### Q16. Why 500 inputs, including 300 clean ones?

**Answer:** The allocation was selected before the campaign to balance usefulness precision with the fault strata under practical runtime limits. The final allocation is 300 clean and 200 non-clean, split 100/60/40. It was not changed after seeing which arm won.

**If challenged further:** Do not invent an unverified power percentage. The observed clean bound is -1.22 points against the five-point tolerance; prospective design justification is in the retained v4 package.

### Q17. Why only three arms in the main campaign?

**Answer:** The main question concerns increments beyond a competent integration. B3 provides that reference, P1 adds prevention-related rules, and P2 adds the repair package. Earlier B0-B2 profiles are outside this fixed main design.

**If challenged further:** Increasing the number of arms later would change the protocol, execution count and multiple-comparison questions. We did not add them after inspecting results.

### Q18. Are permits and durability individually identified?

**Answer:** No. P1 adds claim permits and product-state invariants together. P2 adds a repair package including output behavior and persistence. The comparison identifies implementation-package differences in this frame, not each switch's isolated effect.

**If challenged further:** This is a central qualification of the positive secondary finding. Say 'P2's package met the criterion', not 'durable storage alone caused the improvement'.

### Q19. How did you make the arms comparable?

**Answer:** Each input has the same planned provider capabilities, fault conditions, evidence opportunities and budgets across its arms, with separate resource bindings and saved order. Named barriers control the intended event order.

**If challenged further:** Comparable conditions do not eliminate every shared-host or temporal influence. The provenance and limitations remain necessary.

### Q20. Why not run all cases in parallel?

**Answer:** Isolation must cover services, provider resources, faults, worker restarts, global caches and collection queries. Different IDs alone do not prove isolation. The accepted main schedule is serial; unqualified overlap could confound the scientific comparison.

**If challenged further:** Parallelism could reduce elapsed time only after bounded qualification. It cannot simply remove each original's 600-second observation horizon.

## Measurement

### Q21. Is your independent oracle truly independent?

**Answer:** It reads simulator truth and externally scripted accepted targets, and assesses support from ordinary observations. Observable grades do not depend on arm labels, permit IDs, receipt verdicts or obligation states. Independence means separation from controller belief, not freedom from bugs.

**If challenged further:** The exact-prefix limitation is an example of a narrow instrument even when the code is label-neutral. Independent implementation still needs audit.

### Q22. Did you measure actual spoken words?

**Answer:** The main study uses typed intents and SCRIPTED_TONE_SEMANTIC_PROXY evidence with logical word-index ACKs. It tests protocol behavior. It does not establish intelligible speech exposure or human comprehension.

**If challenged further:** A future real-speech study needs suitable acoustic alignment, playback evidence, recognition conditions and a separately reviewed protocol. We did not silently claim that transfer here.

### Q23. Is the explicit-withdrawal metric tautological?

**Answer:** It is template-specific and partly tracks the behavior P2 was designed to produce. That limits its interpretation. The design credits ordinary updates separately and retains a fixed eligible subset, but does not establish general semantic equivalence or human-belief repair.

**If challenged further:** Acknowledge this directly. The result demonstrates the implemented criterion, not an independent discovery that a particular phrase universally improves understanding.

### Q24. Why are seven comparator outcomes UNKNOWN rather than failures?

**Answer:** The partial-time cases do not provide enough relevant testimony for a conclusive complete-communication grade under the frozen instrument. We preserve UNKNOWN and show planned-denominator bounds rather than silently assigning a convenient value.

**If challenged further:** Known failure, unknown evidence and structural inapplicability are different. The all-33 comparison must retain that distinction.

## Results

### Q25. What is the main result?

**Answer:** All three arms have 455/500 correct final business states and 155/200 successful corrections, matching input by input. The two co-primary comparisons do not demonstrate added protection from P2 over B3 in this frame.

**If challenged further:** This is an observed tie, not proof of universal equivalence. Report the correction and hidden-commit uncertainty bounds when discussing generalization.

### Q26. What is the strongest positive finding?

**Answer:** Every arm supplies an ordinary supported update in the 33 designated recovery inputs. P2 also satisfies complete corrective communication in 33/33; each comparator has 26 FALSE and seven UNKNOWN. The finding is narrow because of template and scripted-playback measurement.

**If challenged further:** Include the ordinary-update tie whenever explaining the stricter difference. Otherwise the audience may falsely believe the baseline never corrected the appointment.

### Q27. Why not say P2 eliminated the four unsupported exposures?

**Answer:** The four B3 positive exposure cases have P1/P2 UNKNOWN counterparts. Zero positive grades with more unknowns is not evidence of definite silence or successful prevention. They are playout cases, not the hidden-commit primary denominator.

**If challenged further:** Show the complete table: B3 4 TRUE/481 FALSE/15 UNKNOWN; P1/P2 0/481/19. The paired uncertainty is material.

### Q28. How can 141 FAILED runs all have correct business state?

**Answer:** Raw status records what the driver did, while the independent oracle checks the final provider state. A refusal or exception can occur after the business action succeeds. Conversely, 135 raw COMPLETED records have incorrect final state.

**If challenged further:** Do not generalize that every failure was harmless. The original exception and evidence determine whether it is expected, and the raw FAILED label remains preserved.

### Q29. Why do we still have 45 failed corrections per arm?

**Answer:** The retained instrument reports 45 FALSE correction outcomes per arm in this fixed frame. They remain in the denominator. The summary alone does not identify one universal cause for every such outcome.

**If challenged further:** Use a specific verified trace if asked for a mechanism. Do not attribute all failures to the shared claim-selection limitation: that limitation can leave business success intact while affecting communication.

## Statistics

### Q30. Does zero observed difference mean the mechanisms are identical?

**Answer:** No. Their recorded business outcomes match on these paired inputs. Conservative bounds remain -8.79 to +8.79 points for weighted correction and -4.95 to +4.95 for hidden-commit adverse exposure. Untested settings or shared limitations can conceal differences.

**If challenged further:** An absence of observed discordance is not a theorem of equivalence. The estimand is the declared fixed-frame mixture.

### Q31. What does the tiny p-value mean?

**Answer:** It describes the 26-versus-zero known-pair communication imbalance under the diagnostic test's null and assumptions. It is not a probability of our theory being true, and it does not solve missingness, measurement scope or dependence.

**If challenged further:** Report exact McNemar 2.9802e-8 and Holm diagnostic 2.9802e-7 only with the seven missing pairs and fixed-prefix limitation.

### Q32. Is +78.79 to +100 a confidence interval?

**Answer:** No. It is an empirical identification range over all assignments to the seven unknown comparator outcomes among 33 planned inputs. It does not include sampling uncertainty as a confidence interval would.

**If challenged further:** Compute its endpoints on the board: (33-7)/33 and (33-0)/33. Keep its outcome definition explicit.

### Q33. Why a paired bootstrap instead of resampling all 1,500 rows?

**Answer:** The three outcomes for one input belong together. Resampling input IDs preserves that matching. Independently drawing rows would break the case comparison and could understate dependence.

**If challenged further:** Input clustering does not automatically handle all host/time dependence. The report retains that unresolved assumption.

### Q34. Did the model prove a latency improvement?

**Answer:** No. Recorded restricted timing differences are positive, so the proposed arms are slower on that scripted completion measure. P2-B3 is approximately +0.2593 seconds. The AFT interpretation is conditional on unproven model/censoring assumptions.

**If challenged further:** Do not confuse time to a supported scripted ACK with human call latency or complete corrective communication.

### Q35. All bootstrap fits converged; why still qualify the analysis?

**Answer:** Convergence means the optimizer found a solution meeting its stopping rule. It does not establish lognormal form, independent censoring, unbiased measurement or independent inputs. All 1,000 fits were retained because none failed.

**If challenged further:** Explain numerical validity separately from scientific model validity. A well-solved wrong model can still mislead.

### Q36. Does the clean-case test prove the system is useful?

**Answer:** It meets the accepted descriptive/conditional clean tolerance in this frame: all arms succeed on 300 clean inputs, with lower difference bound -1.22 points above -5. It does not measure natural-call usability or satisfaction.

**If challenged further:** A usefulness gate helps prevent celebrating a system that refuses everything. It is not a substitute for real-user evaluation.

## Integrity

### Q37. Did operational fixes invalidate the experiment?

**Answer:** They create a provenance and validity issue that must be disclosed. Versioned instrument corrections, original failures, binding segments and unsuccessful attempts are preserved. Application behavior, fixtures, grading and study windows were not silently improved as outcomes accumulated.

**If challenged further:** Do not claim all 1,500 originals ran one final controller binary. The per-original binding history is available and interpretation remains qualified.

### Q38. Did you rerun failed cases until they passed?

**Answer:** No original was replayed or replaced in the retained main analysis. Calibration and diagnostic attempts have separate identities. Original raw failures, grades, timestamps and backup references remain traceable.

**If challenged further:** A recovery that resumes collecting the same original deadline differs from rerunning its driver commands. Evidence extraction also differs from a research replay.

### Q39. What does a SHA-256 prove?

**Answer:** It supports byte identity against a trusted recorded commitment. It can reveal altered content. It does not establish that the file's original claims are true or that the code is bug-free.

**If challenged further:** The trust comes from the entire provenance chain, the original commitments, independently verified copies and scientific checks, not merely printing a long hexadecimal string.

### Q40. Why a full 600 seconds after a refusal?

**Answer:** Late provider effects, ACKs or recovery events can occur after a driver returns. The accepted window is retained even for unsuccessful outcomes. Stopping early on a refusal could systematically miss later events.

**If challenged further:** Export after the saved deadline supports accounting, but does not prove perfect event capture. Missing anchors and collection gaps remain explicit issues.

## Infrastructure

### Q41. Why AWS instead of your laptop?

**Answer:** The long serial observation schedule needed an independently runnable environment with controlled resources and backups. The laptop had finite available RAM/disk and should not need an active chat. AWS hosted the runner; it did not provide the measured intelligence.

**If challenged further:** Another qualified isolated host could serve the same purpose. Cloud hosting is an operational choice, not the novelty claim.

### Q42. How much did it cost?

**Answer:** I must distinguish actual billed spend from the accepted budget and conservative forecast. The final accepted policy used a US$76 admission guard and US$77 ceiling. This guide does not refresh billing and cannot honestly turn either limit into actual expenditure.

**If challenged further:** Evidence storage and retained disks can continue to cost money after compute stops. A new financial statement requires bounded read-only billing evidence under the accepted accounting method.

### Q43. Why did it stop several times?

**Answer:** The retained history includes instrument and operational defects, guard trips and connectivity problems. These were diagnosed and versioned rather than bypassed. The campaign therefore is not evidence of an uninterrupted fault-free deployment.

**If challenged further:** Discuss one demonstrated incident accurately, such as the slot-145 classifier path or the clock-sampling correction. Do not blame the watchdog for every exception.

### Q44. Can Codex be closed while the experiment runs?

**Answer:** The qualified standalone service was designed to run on its host without an active conversation, with ledger checkpoints and independent guards. This statement concerns the deployed orchestration, not a promise that every extraction shell survives browser/session expiry.

**If challenged further:** The CloudShell extraction interruption illustrates why a background process and an independently durable service are not the same thing.

## Authorship

### Q45. What did you personally do, and how was AI used?

**Answer:** The project used substantial AI assistance for implementation, experiment tooling and drafting. I should describe my actual decisions and contributions honestly, distinguish them from generated work, and demonstrate the parts I understand. I must not claim to have hand-written every line.

**If challenged further:** Adapt this answer to your real work. Before submission, independently review code, results and literature; follow the venue's disclosure rules. A memorized answer is not a substitute for understanding.

### Q46. Can you explain the code without the assistant?

**Answer:** I should be able to walk through one accepted revision, one external operation, one verification, one refusal and one repair trace, then show how the oracle grades it. If I cannot explain a component yet, I should say so and study it.

**If challenged further:** Practise tracing input ID to arm/execution ID, operation/evidence, saved deadline, outcome row and backup binding. Do not claim mastery that the meeting would immediately contradict.

## Scope

### Q47. Can this be a software-update paper for AgSU?

**Answer:** Artifact versions, deployment evidence and claims of successful rollout form a plausible analogy. However, our evaluation is booking workflows, not software updates. Venue fit is for the organizers to judge; I would request a scope review rather than claim an update benchmark we did not run.

**If challenged further:** A scope invitation is not paper acceptance or a registration waiver. The full review manuscript still needs the chosen venue's format and declarations.

### Q48. What would be the next scientific study?

**Answer:** Only stronger claims require a new study: natural speech with verified alignment, human understanding, broader providers, independent repair consumers, or isolating persistence from wording. None is retroactively added to this finished campaign.

**If challenged further:** The current paper can report the primary tie without optional extensions. Future work must have its own design, authority and resources rather than changing the frozen denominator.

### Q49. What is the strongest criticism of your positive finding?

**Answer:** The withdrawal rule accepts a fixed phrase, and P2 is designed to produce that form. Therefore the result can partly reflect the instrument/output template match. It does not independently establish human benefit or durability's isolated causal value.

**If challenged further:** Name the criticism yourself and explain why the paper reports ordinary-update success separately, retains UNKNOWNs, and restricts its conclusion.

### Q50. Why is the project still worth discussing if the main result tied?

**Answer:** A strong baseline handling the tested business conditions is informative. The instrument also demonstrates why state, evidence, exposure and correction should be reported separately. A useful systems study can include a negative primary result without a superiority claim.

**If challenged further:** Publication value depends on clarity, relevance, originality and methodological credibility. Case count, cloud spending or effort alone cannot guarantee acceptance.

# PART VIII - Practise explaining, not memorizing

## A 30-second introduction

My project studies how an agent should act and speak when a user's request changes and an external operation may already have committed without a reply. I built and evaluated a protocol separating accepted intent, provider effects, evidence, claim permission and corrective delivery. Across 500 inputs and three configurations, business outcomes tied. A narrower explicit-correction endpoint differed, but it uses scripted playback and a fixed wording rule, so I keep that conclusion limited.

## A two-minute explanation

Imagine booking a maintenance visit. The provider saves it but its reply is lost. Then the resident changes the requested time. Retrying blindly can create an extra booking, and stopping audio does not undo the first effect or withdraw words already played.

The system therefore records accepted request revisions and durable operation identities in PostgreSQL. It reconciles uncertainty before retrying. Proposed-arm permits bind a particular outcome statement to applicable observations, revision and resource version. The repair configuration additionally persists work owed when incompatible decisive content has reached recorded playback.

The comparison uses a competent baseline with idempotency, reconciliation, invalidation, staging, compensation and playback tracking. Five hundred fixed-frame synthetic inputs each receive B3, P1 and P2, producing 1,500 retained originals with full observation windows. An independent oracle reads simulator truth and ordinary observations; it does not grade an arm by trusting its own receipt verdict.

All arms have 455/500 correct final states and matching correction outcomes. All three deliver ordinary supported updates in the 33 designated recovery inputs. P2 also meets the explicit-withdrawal criterion in 33/33, while each comparator has 26 FALSE and seven UNKNOWN. That secondary result is template-specific, uses scripted tone/ACK evidence, and cannot isolate durability alone. The contribution is an auditable systems study with a negative primary finding and a qualified communication distinction.

## A five-minute meeting structure

**Minute 1 - Problem and example.** Draw customer, controller and provider. Place the missing acknowledgement after the provider's commit. Ask what the controller actually knows. Add the customer's correction. Explain why another write or a confident statement needs justification.

**Minute 2 - Protocol.** Draw separate rows for intent, effect, evidence, claim, playback and repair. Show a receipt tied to a revision/resource version. Distinguish suppressing unplayed content from addressing content that already reached the decisive span. Mention PostgreSQL authority and optional disposable Redis.

**Minute 3 - Experiment.** Show 500 input cards, each with three arm boxes. State the 300/100/60/40 allocation, independent oracle, named barriers, saved serial order, and full 600-second windows. Explain that typed inputs/scripted tones isolate protocol behavior rather than voice-model quality.

**Minute 4 - Results.** Show the primary tie before the secondary finding. Use all denominators and preserve UNKNOWN. Say that the four baseline exposure positives have unknown proposed-arm counterparts. Do not turn that into proved prevention. Timing is slightly longer in the recorded metric and has qualified censoring/dependence assumptions.

**Minute 5 - Contribution and limits.** Name close prior work without claiming you tested those systems. Explain the exact-prefix limitation and shared revision-only claim-selection problem. Ask for feedback on scientific framing and venue scope. Present the completed manuscript as a review draft, not an accepted publication or breakthrough.

## What to show if asked for evidence

Start with the final report and 1,500-row outcome CSV. Then use the provenance index to identify the relevant original, admission binding, export and pinned backup. Choose one verified trace for a concrete mechanism: sequence 145 for the claim-selection/refusal issue; sequence 59 for truth versus resource-bound evidence; sequence 82 for another revision during repair. The full raw archive collection is not embedded in this learning guide.

The exact local analysis source and environment are pinned in the retained reproduction notes. Explain the distinction between reproducing a calculation from existing data and rerunning the original business scenario. Do not start a new live system in a meeting merely to look confident; it could require resources, protocol authority and controlled conditions.

## How to answer when you do not know

Use a precise boundary: 'I can explain this path from the retained trace, but I have not independently checked that other implementation detail yet.' Or: 'Our experiment does not measure human comprehension, so I cannot answer that from these data.' These are stronger answers than inventing a mechanism, claiming a number from memory, or treating another paper's advertised result as your own.

If asked to identify your own contribution, discuss actual work and decisions truthfully. The project used substantial AI assistance for implementation, experiment tooling and writing. Reviewing and understanding it is necessary; a long document is not a substitute for that understanding. Follow the chosen venue's disclosure policy before submission.

## A small self-check before emailing the professor

Can you explain UNKNOWN without calling it failure? Can you count 500 inputs versus 1,500 executions? Can you describe what B3 already protects? Can you calculate 455/500 and 155/200? Can you explain why a correct booking may have refused speech? Can you state why 33/33 does not prove human understanding or durability's isolated effect? Can you locate one original and its evidence binding? If any answer is unclear, revisit that chapter before presenting.

## Final memory card

**One question:** What additional protection do permits/repair provide beyond a competent baseline in this declared frame?

**Three layers:** external effect, applicable evidence, recorded communication.

**Four denominators:** 500 inputs per arm; 200 correction inputs; 100 hidden-commit exposure inputs; 33 designated recovery inputs.

**Three important results:** 455/500 business correctness in every arm; 33/33 ordinary updates in every recovery arm; complete communication P2 33 TRUE, B3/P1 26 FALSE and seven UNKNOWN each.

**One major caution:** exact-prefix/scripted-ACK success is not general semantic or human-belief repair.

**One honest contribution:** an implemented protocol and auditable endpoint separation, including a primary tie. Publication and novelty remain review questions.

# Evidence and illustration notes

This book was assembled from the preserved eight-page manuscript, final Phase 8 report and machine-readable analysis outputs, frozen arm/oracle sources, retained slot-145 diagnosis, and historical local deployment records. It performs no new statistical inference, no oracle regrading, no case replay, and no AWS operation. Earlier README descriptions of a campaign that had not started are historical; final closeout records establish the completed state described here.

All twelve numbered reference links point to primary author/publisher sources. Their individual summaries are concise paraphrases, not reproductions of the papers. Some are preprints; an arXiv identifier does not itself establish peer-review acceptance. Detailed numeric performance claims about those external systems are intentionally not compared with this study's rates.

The two realistic composite illustrations were generated with the built-in image tool specifically for this private learning guide. They show fictional people and facilities. They are not pictures of Syed, participants, the real provider, AWS's actual interior, the actual research dashboard, or scientific evidence. The exact prompts and local image fingerprints are retained with the guide's source package. All technical diagrams and outcome charts are deterministic teaching drawings.

The final appendix reproduces the original eight-page manuscript in the same PDF, including its own original page numbers 1-8. The book's preceding close-reading notes reference those manuscript page numbers. The original standalone manuscript and source files remain unchanged. This makes one complete downloadable learning PDF while preserving the original research text for comparison.

# PART IX - Technical words in everyday English

Use this dictionary when a word interrupts your reading. Definitions explain this project's usage. Exact executable constraints remain in the frozen contracts/source.

**Ablation.** A comparison that removes an implemented component/package to inspect its increment. Our P1/P2 comparison removes P2's repair package, not only its database persistence.

**Accepted intent.** A validated request version formally recorded by the backend. A model proposal or partial transcript has not necessarily crossed this boundary.

**ACK / acknowledgement.** A report that something was received or progressed. Provider acknowledgement and client playback acknowledgement are different events with different meanings.

**ACID.** Atomicity, consistency, isolation and durability: properties of local database transactions. They do not automatically extend across an unrelated opaque provider.

**Admission.** Allowing the next saved execution to start after relevant authority, evidence, source, budget, resource and deadline guards pass.

**AFT.** Accelerated-failure-time model: describes event time multiplicatively. Our accepted fit uses a lognormal form with arm and stratum terms, under qualified assumptions.

**Agent.** Software coordinating actions toward a request. In the main campaign, structured intents bypassed the language model's proposal ability.

**Alignment.** A mapping between content such as a word and its audio/time position. Scripted indexes do not establish accurate alignment of intelligible speech.

**API.** Application programming interface: agreed commands, inputs, outputs and error semantics between components.

**Append-only truth log.** Provider simulator history that adds committed facts without silently replacing old ones. It lets the independent oracle reconstruct what occurred.

**Arm.** An explicit experimental configuration, here B3, P1 or P2. It is not a model brand, a participant, or a fault timing phase.

**Artifact.** A retained research output such as source, data, manifest, trace or report. A local artifact is not automatically publicly accessible.

**Attempt.** A specific planned attempt identity. Main originals remain attempt 1; separately labelled diagnostic reads/runs do not replace them.

**Authority.** Recorded permission and policy binding for an action. In the protocol it can concern claims; operationally it concerns reviewed deployment/launch limits.

**BACKED_UP.** A research ledger retention state. It says evidence reached the verified backup step, not that the appointment or communication succeeded.

**Baseline.** The comparison system. A competent baseline includes meaningful known safeguards so a proposed feature is not rewarded for beating an artificially weak system.

**Barrier.** Named wait/release event at a specific workflow boundary. More precise for race tests than hoping a fixed sleep produces the intended ordering.

**Binding.** A recorded association between identities, versions or evidence. Its strength depends on what actually generated and verified the association.

**Bootstrap.** A computational method that resamples observed units. Our timing analysis keeps an input's three arms together; resampling cannot manufacture independence.

**Budget.** An explicit limit, possibly monetary, time-based, storage-based or action-count based. Always state its unit.

**B3.** Competent baseline with idempotency, reconciliation, revision invalidation, staging, compensation and playback tracking, plus ordinary evidence checks and corrective statements.

**Candidate.** A proposed version awaiting the relevant review. A candidate's existence does not itself authorize freeze, deployment or research execution.

**Censoring.** The exact event time is not established within the observation basis. Censoring is not proof the event is impossible or never happens.

**Claim.** A consequential assertion, such as a booking confirmation or cancellation. Its exact predicate matters; 'created again' and 'rescheduled in place' are not identical.

**Claim permit.** Scoped deterministic permission for a specific claim using applicable evidence. It is not an external provider commit or universal proof of truth.

**Clean case.** An input in the planned ordinary-work stratum, used to assess useful task completion without the non-clean fault challenge.

**Cluster.** Observations treated together because they share a unit. Here an input carries B3/P1/P2 results; there can also be unmodeled family/host/time dependence.

**Co-primary.** One of the two prespecified main comparison questions. Secondary findings were not retroactively promoted because they looked more favorable.

**Collector.** Instrument code retaining observations through the saved deadline, including after a driver return or recognized refusal.

**Commit.** Durable external/local state change at a defined boundary. In this title it primarily means transactional effect, not merely a Git source-code commit.

**Compensation.** An additional action intended to address a prior external effect. It can fail and does not erase history.

**Complete corrective communication.** The declared supported-update plus explicit-withdrawal criterion when relevant, evaluated on fixed eligible recovery inputs. Its wording matcher is narrow.

**Confidence interval.** Range produced by a procedure with a claimed repeated-sampling coverage property under assumptions. It is not automatically a probability that a fixed parameter lies inside this particular interval.

**Confirmatory.** An interpretation based on planned questions and satisfied inferential requirements. The retained helper claim guards remain restricted.

**Construct validity.** Whether a measure captures the intended underlying idea. A fixed prefix may measure a message format more narrowly than general belief repair.

**Context draw.** One generated appointment context from the declared fixed recipe frame. It is the conditional sampling unit, not a naturally sampled caller.

**Controller.** Application process validating commands and coordinating accepted domain decisions. Its belief is not the independent provider truth.

**Convergence.** An optimizer satisfying its numerical stopping conditions. It does not validate the model form or causal interpretation.

**Correction success.** Frozen endpoint checking successful correction to the accepted final target. Eligible for the 200 non-clean inputs, not all 500.

**Cross-tab.** Counts of combinations of two recorded variables, such as raw FAILED versus correct final business state.

**Decisive content.** Words conveying an outcome or relevant time rather than introductory filler. Scripted word-index evidence is the study's proxy.

**Dependency.** Something a piece of work relies on. It can mean data/control lineage in a workflow or a software package needed by a runtime; distinguish them.

**Deterministic.** Defined code rules decide from relevant inputs, instead of relying on unconstrained model prose to authorize consequences.

**Diagnostic p-value.** A test output interpreted with its specific null, missingness and dependence limitations. It is not a probability the paper is correct.

**Discordant pair.** A matched input on which two arms differ in the binary outcome. The observed business correction comparison has no discordant pairs.

**DOI.** Persistent scholarly identifier assigned through an appropriate registration route. A local PDF or ordinary web URL does not create one.

**Drain pass.** One iteration of the reviewed drain process. The limit is 30 passes, not 30 seconds.

**Driver.** The program issuing the scenario's actions. Raw driver completion differs from independent business or speech success.

**Durable.** Stored so the relevant fact/work survives process interruption under the system's persistence assumptions. It does not alone guarantee a consumer executes it.

**EBS.** AWS block storage for a host filesystem. A stopped instance can retain its disk and evidence, with ongoing storage costs.

**EC2.** AWS virtual-machine service used as a Linux execution host in this project, not the proposed agent mechanism.

**Endpoint.** Either an HTTP address or a measured research outcome. A professor may mean either; clarify from context.

**Estimand.** The exact quantity of interest: here arm differences over the declared fixed simulator recipe/context mixture.

**Evidence.** Available observations supporting a particular claim at a particular time. Evidence can be missing, stale or bound to the wrong version.

**Execution ID.** Saved identity of one input-arm-attempt original. Continuing collection must preserve it rather than create a replacement outcome.

**Explicit withdrawal.** Identifying a previously exposed statement as outdated/withdrawn, not merely giving a new time. Our grader recognizes a fixed prefix.

**Exposure.** Content reaching the relevant recorded playback boundary under the instrument. It does not prove attention or comprehension.

**External validity.** How far a result transfers beyond the tested setting. Natural callers and different provider ecosystems remain untested.

**Fault injection.** Deliberately causing a planned error/timing condition, such as dropping a reply after commit. Distinct from an accidental infrastructure failure.

**Fixture.** A versioned scenario/configuration input defining conditions and expected protocol structure. It is preserved after freeze rather than edited to fit a result.

**Freeze.** Version/hash binding of an accepted research package. Freezing is not the same as launching it or claiming code is bug-free.

**Full-duplex.** Listening and output can overlap. Support for a full-duplex product path does not mean the main campaign evaluated natural full-duplex speech.

**Git commit.** A source-history snapshot identity. Different from a provider transaction commit, although both concern recorded state at different boundaries.

**Grading.** Applying the frozen outcome instrument. This guide reads existing grades; it does not rerun the oracle or change outcomes.

**Hash / SHA-256.** A content fingerprint. Matching a trusted hash supports identical bytes, not scientific truth or absence of bugs.

**Hidden commit.** A provider effect occurs but its acknowledgement is unavailable to the controller. The world can be settled while local knowledge remains UNKNOWN.

**Holm adjustment.** A multiple-comparison procedure for the declared diagnostic family. Adjustment does not fix a biased endpoint or missing evidence.

**Horizon.** Observation limit used by the study, here 600 seconds per original under the accepted saved deadline rules.

**HTTP 409.** Conflict response status. Its meaning requires exact endpoint/request/problem details and evidence; status alone is not a refusal classifier.

**Idempotency.** Repeating the same logical operation under the provider contract does not add extra effects. Changed intent needs separate semantics.

**Identification bound.** Range consistent with observed and unknown outcomes in the sample. It is not a confidence interval for sampling uncertainty.

**Invariant.** A property that should remain true across allowed transitions, such as preserving accepted intent and not using stale evidence to authorize a claim.

**IANA time zone.** Named regional time zone retained with appointments, such as Asia/Karachi, distinct from a bare UTC offset.

**Lease.** Temporary ownership of queued work, used to coordinate workers. A lease needs crash/recovery handling; it is not permanent completion.

**Ledger.** Durable operational record of identities, progress, notices and retention. Different from the provider's truth log and the application's business database.

**Lineage.** Recorded relationship showing which earlier data or work an output depends on.

**LLM.** Large language model. It may propose language or actions, but the main study did not compare its learned capability.

**Lognormal.** Distributional form where the logarithm of positive time has a normal-shaped distribution. It is an assumption in the accepted AFT model.

**Manifest.** Inventory binding files/objects, identities and hashes. Its usefulness depends on trusted original commitments and verification.

**McNemar test.** Paired binary-outcome test focusing on discordant directions. The reported communication calculation is diagnostic and has seven missing pairs.

**Model.** May mean a learned LLM, a mathematical timing model, or a conceptual execution model. The cited papers do not all propose neural models.

**Monotonic clock.** A clock for elapsed time within a boot, distinguished from calendar wall time. Boot identity and paired measurement remain important.

**N/A.** Structurally not eligible for an endpoint. Different from UNKNOWN, where the question applies but sufficient evidence is unavailable.

**Native audio.** Model interface handling speech directly. Optional adapters do not turn the main typed/scripted study into a native-audio model comparison.

**Noninferiority margin.** Largest accepted loss relative to the comparator for a defined endpoint. Here five percentage points for clean usefulness under the planned rule.

**Observation.** A recorded piece of provider/client evidence at a time. It may differ from what actually happened in the external system.

**Operation ID.** Identity of a logical external action. It is not the same as a new execution ID, accepted revision or provider resource version.

**Oracle.** Independent grader using simulator truth, scripted targets and relevant observations, rather than accepting controller confidence as ground truth.

**Orthogonal dimensions.** Separate state axes that can coexist, such as effect committed, evidence unknown and repair pending.

**Outbox.** A durable record of work/effects awaiting publication or dispatch. Recording an item is different from proving it was externally delivered.

**P1 / P2.** Our main study's prevention-related and prevention-plus-repair profiles. Other papers and older timing diagrams can use these labels differently.

**Paired analysis.** Comparison preserving the same input's outcomes across arms, rather than treating all rows as independent unrelated observations.

**Percentage point.** Absolute difference between percentages. From 80% to 85% is five points, not a five-percent relative increase.

**Pinned version.** An exact retained source/dependency/object version. It prevents silently reading a newer object under an old name.

**Playback.** Output reaching the client's recorded media progress. Generated/queued/published/completed are separate lifecycle events.

**Postcondition.** Condition that should hold after an action, checked independently where possible before assuming success or retry safety.

**PostgreSQL.** Durable relational database used for correctness-relevant application records. The simulator also has isolated provider-side persistence.

**Predicate.** Precisely stated condition a claim asserts, such as creation, cancellation or in-place rescheduling. Similar wording can imply different facts.

**Primary outcome.** Main endpoint selected by the design before inspecting results. A more exciting secondary endpoint cannot simply replace it.

**Protocol.** Rules governing how components coordinate knowledge, authority, effects, output and recovery.

**Provenance.** Traceable origin and history of data/code/results, including source bindings, exports, hashes, notices and backups.

**Proxy.** Observable substitute for a concept. Logical word ACKs proxy exposure without establishing real intelligible speech or comprehension.

**Publication.** In this protocol, releasing output into a media/message path. In academic discussion, publishing a paper means something different.

**Raw status.** Original driver label such as FAILED or COMPLETED, retained separately from independent outcome grades.

**Receipt.** Structured verification record scoped to operation, revision, predicate, resource version, source and validity. It can be SATISFIED, VIOLATED or UNKNOWN.

**Recipe.** Fixed family of scenario/fault conditions. Context variation gives new inputs without making a new independent research domain.

**Reconciliation.** Checking authoritative status/resource evidence after ambiguity to determine possible effects and whether retry is safe. The reviewed limit is eight attempts.

**Redis.** Optional disposable cache/hint store, never the only retained copy of a correctness-relevant fact in this contract.

**Refusal.** Application-level rejection of a requested action/claim. Only narrowly recognized evidence-supported cases qualify for expected-outcome handling.

**Repair obligation.** Persistent record of corrective work owed for incompatible exposed content. Its creation, discovery, delivery and escalation are distinct concerns.

**Replay.** Issuing scenario commands again. This differs from resuming evidence collection or downloading an already executed original's record.

**Resource version.** Specific provider resource state to which observations/claims can be bound. Same appointment ID or same time phrase does not guarantee same version.

**Restricted mean.** Timing summary evaluated up to an accepted horizon rather than assuming indefinite follow-up. Here interpreted under the frozen scripted-completion rules.

**Retraction.** Explicitly withdrawing or identifying earlier content as outdated. The implemented matcher is narrower than open-language semantic retraction.

**Revision.** Numbered accepted version of a request. More than one revision does not prove that the provider performed an in-place reschedule.

**Risk difference.** Difference in outcome proportions between arms in a defined population/frame and subtraction direction.

**S3.** AWS object storage used with versioned evidence backups. Knowing an object key without its required version/hash can be insufficient.

**SATISFIED / VIOLATED / UNKNOWN.** Verification's three knowledge verdicts: supported, contradicted, or not sufficiently established under the rules.

**Seed.** Starting value for repeatable computational random draws. It improves reproducibility, not the truth of an independence assumption.

**Semantic.** Concerning meaning. Semantic correctness is broader than literal string matching; the study's correction matcher has a documented wording restriction.

**Serial.** One original execution admitted at a time in the saved order. It simplifies some isolation concerns but introduces shared-time/host limitations.

**Sidecar.** Separate explanatory/amendment metadata preserving an original rather than overwriting it. Only the previously accepted first-two timing sidecars were reused.

**Simulator.** Controlled external provider implementation with fault injection and independent truth logging. Synthetic does not mean the application code/database effects were imaginary.

**SSM / CloudShell.** AWS managed control and interactive shell facilities used operationally. They are distinct from an always-running campaign service and from research-arm behavior.

**STT / TTS.** Speech-to-text and text-to-speech. The main campaign bypassed these natural-speech uncertainties through typed intents/scripted audio.

**Staging.** Holding a planned effect/output before its release condition. A queued or staged acknowledgement does not prove an external effect occurred.

**Stale.** No longer applicable to the accepted intent or relevant resource state. A statement can become outdated after having been valid earlier.

**Stratum.** A prespecified scenario group: CLEAN, HIDDEN_COMMIT, PLAYOUT or OTHER_BOUNDARY.

**Synthetic.** Constructed under controlled rules rather than sampled from natural human calls. Conclusions must respect that frame.

**Telemetry.** Internal state/log information useful for understanding a mechanism. It must not automatically replace independent outcome evidence.

**Timeout.** Waiting limit reached. It does not by itself prove whether an external action committed.

**Trace.** Time-ordered retained evidence about one execution's requests, observations, output, grades and operational context.

**Truth versus knowledge.** What occurred in the provider versus what the application's applicable observations justify. The oracle's privileged truth is not silently given to the arm.

**UNKNOWN.** Insufficient relevant evidence, not a convenient success/failure value. Applies to different layers with their own definitions.

**UTC.** Common timestamp reference retained for ordering/accounting; original appointment time-zone identity is also retained where applicable.

**Validity interval.** Time window within which evidence/authorization applies, subject to its other identity and version conditions.

**Version drift.** Actual source/dependencies differ from expected pinned material. A safe runner pauses rather than silently blessing the difference.

**Watchdog.** Independent guard-checking process. A pause and stopped compute are different states; separate shutdown controls and verification matter.

# APPENDIX - The preserved original manuscript

The following eight pages reproduce the complete original research manuscript, including its tables, figures and references. Its original printed page numbers restart at 1. Use the PDF's Appendix bookmark to return here. This book does not change the original file, its grades, or its source commitments.

Before you present: explain the main result in your own words, identify one verified trace, name the strongest measurement limitation, and state what your evidence cannot answer. The goal is understanding and accurate scientific discussion.

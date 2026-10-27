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

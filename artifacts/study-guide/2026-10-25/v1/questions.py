"""Meeting practice: qualified answers, not a script for claiming unearned expertise."""

from __future__ import annotations

QUESTIONS: list[tuple[str, str, str, str]] = [
    (
        "Motivation",
        "What problem are you solving in one minute?",
        "I study the gap between external actions, evidence, and outcome messages when a "
        "request changes during execution. A booking can commit even when its reply is lost, "
        "and a previous confirmation can already have reached playback. The protocol separates "
        "reconciliation, claim authorization and corrective delivery.",
        "Use the 12:15-to-14:15 teaching example, then distinguish provider truth, application "
        "knowledge and client testimony. Do not start with a technology shopping list.",
    ),
    (
        "Motivation",
        "Is this an AI paper or ordinary distributed-systems engineering?",
        "It is a systems/protocol evaluation in an agent application. Much of the foundation "
        "is distributed systems. The studied boundary concerns consequential agent claims and "
        "exposed output. The main experiment bypasses model uncertainty, so it is not a "
        "new-model capability paper.",
        "That narrower identity is more defensible than calling every component an AI "
        "innovation. The relevance is how the surrounding system constrains model-proposed "
        "actions and statements.",
    ),
    (
        "Motivation",
        "Why can a correct booking lack a justified confirmation?",
        "The oracle can know from simulator truth that the booking exists while the "
        "application lacks the applicable observations needed to support its selected "
        "statement. Also, the statement might assert the wrong operation predicate, as in "
        "cancel/create versus in-place reschedule.",
        "Correctness of a world state, truth of a phrase, and justification at the decision "
        "time are different questions. A correct guess does not create evidence.",
    ),
    (
        "Novelty",
        "What exactly is new?",
        "The candidate contribution is the implemented composition and auditable evaluation "
        "separating business state, evidence, exposure and explicit correction against a "
        "protected baseline. I do not claim to invent idempotency, receipts, revision "
        "handling, playback alignment or repair.",
        "Novelty is not established by the case count. The paper's targeted related-work "
        "review identifies close antecedents, and external priority remains open to scientific "
        "review.",
    ),
    (
        "Novelty",
        "Is this a breakthrough?",
        "No breakthrough is demonstrated. The primary business comparison tied. A narrower "
        "secondary distinction appears in explicit corrective communication, with substantial "
        "template and scripted-playback limitations.",
        "Presenting a careful negative result and a qualified secondary finding is more "
        "credible than overstating what the data can establish.",
    ),
    (
        "Novelty",
        "Why not just use an existing transactional runtime?",
        "Existing runtimes are important antecedents. Our study asks about one "
        "booking/evidence/playback contract, including correction after exposure. It does not "
        "demonstrate superiority over external runtimes or prove they cannot implement similar "
        "rules.",
        "A head-to-head integration would be a different study. Do not invent missing "
        "capabilities in another paper to manufacture a novelty gap.",
    ),
    (
        "Novelty",
        "Did you compare against a deliberately weak baseline?",
        "B3 already has durable idempotency, reconcile-before-retry, revision invalidation, "
        "staging, compensation and playback tracking. It can refuse unsupported statements and "
        "provide ordinary corrective updates. All arms received ordinary-update credit on the "
        "same observable basis.",
        "The identical business outcomes and 33/33 ordinary recovery updates are evidence that "
        "the baseline was not simply prevented from succeeding by the grader.",
    ),
    (
        "Mechanism",
        "What does a claim permit guarantee?",
        "It authorizes a particular statement using evidence bound to the operation, accepted "
        "revision, resource version and validity conditions. It is not a commit receipt from "
        "an omniscient provider or a universal proof that all later speech is safe.",
        "Explain the configured publication/playback rechecks. A validity rule is meaningful "
        "only under its assumptions about observations, event timing and trusted components.",
    ),
    (
        "Mechanism",
        "Why not let the LLM decide whether to confirm?",
        "The model can propose wording or intent, but fluency does not establish provider "
        "facts. Deterministic backend checks authorize decisive claims. This gives inspectable "
        "rules at a correctness boundary instead of allowing unconstrained prose to mutate "
        "state or certify outcomes.",
        "It does not mean deterministic code is always correct. Its predicates, evidence "
        "binding and implementation still require qualification.",
    ),
    (
        "Mechanism",
        "What is UNKNOWN, precisely?",
        "It means the current observations do not establish the relevant outcome. A timeout "
        "after a request may have been sent is not proof of failure. Reconciliation is needed "
        "before a retry can be justified.",
        "Distinguish operation knowledge from an outcome grade that is UNKNOWN because "
        "playback evidence is missing. Both preserve uncertainty, but they describe different "
        "layers.",
    ),
    (
        "Mechanism",
        "Why does idempotency not solve the whole problem?",
        "It helps avoid extra effects from repeated attempts at one logical request. It does "
        "not by itself accept a new request revision, establish current resource evidence, "
        "stop stale output or withdraw content already exposed.",
        "A changed intent is not always the same logical request. Reusing one key for "
        "different meaning can violate the provider's contract.",
    ),
    (
        "Mechanism",
        "Why is compensation not the same as rollback?",
        "Compensation is another action intended to address a previous external effect. It can "
        "fail and does not erase the fact that the earlier action occurred. A local database "
        "rollback cannot undo an already committed opaque-provider action.",
        "For speech, later correction cannot make words unplayed. The system can record and "
        "address consequences, not reverse the listener's history.",
    ),
    (
        "Mechanism",
        "Does a repair row prove the user was corrected?",
        "No. Internal persistence is mechanism evidence. A delivered, supported update and "
        "explicit withdrawal require the relevant external output evidence under the "
        "instrument. Our ACKs remain scripted proxies, not proof of understanding.",
        "Forty REPAIR_PLAYED obligations across 33 inputs are useful telemetry, but the "
        "independent communication outcome does not read that internal state as its oracle.",
    ),
    (
        "Mechanism",
        "Did you prove unattended restart recovery?",
        "The main retained telemetry alone does not prove it. The sampled P2 trace contains "
        "experiment-invoked repair workers. I can describe that recorded path and the separate "
        "qualification history, but not generalize it to an always-running autonomous "
        "consumer.",
        "A strong unattended claim would require evidence of the documented consumer "
        "discovering pending obligations without a driver manually delivering each repair.",
    ),
    (
        "Design",
        "What are your independent units?",
        "The accepted conditional sampling unit is an input/context draw from the fixed recipe "
        "frame. Its three arm results form a paired cluster. There are 500 inputs, not 1,500 "
        "independent scenarios, and only 50 fixed recipe families.",
        "Shared host, temporal effects and repeated families limit the independence "
        "assumption. The intervals are conditional on the declared frame and dependence "
        "assumptions.",
    ),
    (
        "Design",
        "Why 500 inputs, including 300 clean ones?",
        "The allocation was selected before the campaign to balance usefulness precision with "
        "the fault strata under practical runtime limits. The final allocation is 300 clean "
        "and 200 non-clean, split 100/60/40. It was not changed after seeing which arm won.",
        "Do not invent an unverified power percentage. The observed clean bound is -1.22 "
        "points against the five-point tolerance; prospective design justification is in the "
        "retained v4 package.",
    ),
    (
        "Design",
        "Why only three arms in the main campaign?",
        "The main question concerns increments beyond a competent integration. B3 provides "
        "that reference, P1 adds prevention-related rules, and P2 adds the repair package. "
        "Earlier B0-B2 profiles are outside this fixed main design.",
        "Increasing the number of arms later would change the protocol, execution count and "
        "multiple-comparison questions. We did not add them after inspecting results.",
    ),
    (
        "Design",
        "Are permits and durability individually identified?",
        "No. P1 adds claim permits and product-state invariants together. P2 adds a repair "
        "package including output behavior and persistence. The comparison identifies "
        "implementation-package differences in this frame, not each switch's isolated effect.",
        "This is a central qualification of the positive secondary finding. Say 'P2's package "
        "met the criterion', not 'durable storage alone caused the improvement'.",
    ),
    (
        "Design",
        "How did you make the arms comparable?",
        "Each input has the same planned provider capabilities, fault conditions, evidence "
        "opportunities and budgets across its arms, with separate resource bindings and saved "
        "order. Named barriers control the intended event order.",
        "Comparable conditions do not eliminate every shared-host or temporal influence. The "
        "provenance and limitations remain necessary.",
    ),
    (
        "Design",
        "Why not run all cases in parallel?",
        "Isolation must cover services, provider resources, faults, worker restarts, global "
        "caches and collection queries. Different IDs alone do not prove isolation. The "
        "accepted main schedule is serial; unqualified overlap could confound the scientific "
        "comparison.",
        "Parallelism could reduce elapsed time only after bounded qualification. It cannot "
        "simply remove each original's 600-second observation horizon.",
    ),
    (
        "Measurement",
        "Is your independent oracle truly independent?",
        "It reads simulator truth and externally scripted accepted targets, and assesses "
        "support from ordinary observations. Observable grades do not depend on arm labels, "
        "permit IDs, receipt verdicts or obligation states. Independence means separation from "
        "controller belief, not freedom from bugs.",
        "The exact-prefix limitation is an example of a narrow instrument even when the code "
        "is label-neutral. Independent implementation still needs audit.",
    ),
    (
        "Measurement",
        "Did you measure actual spoken words?",
        "The main study uses typed intents and SCRIPTED_TONE_SEMANTIC_PROXY evidence with "
        "logical word-index ACKs. It tests protocol behavior. It does not establish "
        "intelligible speech exposure or human comprehension.",
        "A future real-speech study needs suitable acoustic alignment, playback evidence, "
        "recognition conditions and a separately reviewed protocol. We did not silently claim "
        "that transfer here.",
    ),
    (
        "Measurement",
        "Is the explicit-withdrawal metric tautological?",
        "It is template-specific and partly tracks the behavior P2 was designed to produce. "
        "That limits its interpretation. The design credits ordinary updates separately and "
        "retains a fixed eligible subset, but does not establish general semantic equivalence "
        "or human-belief repair.",
        "Acknowledge this directly. The result demonstrates the implemented criterion, not an "
        "independent discovery that a particular phrase universally improves understanding.",
    ),
    (
        "Measurement",
        "Why are seven comparator outcomes UNKNOWN rather than failures?",
        "The partial-time cases do not provide enough relevant testimony for a conclusive "
        "complete-communication grade under the frozen instrument. We preserve UNKNOWN and "
        "show planned-denominator bounds rather than silently assigning a convenient value.",
        "Known failure, unknown evidence and structural inapplicability are different. The "
        "all-33 comparison must retain that distinction.",
    ),
    (
        "Results",
        "What is the main result?",
        "All three arms have 455/500 correct final business states and 155/200 successful "
        "corrections, matching input by input. The two co-primary comparisons do not "
        "demonstrate added protection from P2 over B3 in this frame.",
        "This is an observed tie, not proof of universal equivalence. Report the correction "
        "and hidden-commit uncertainty bounds when discussing generalization.",
    ),
    (
        "Results",
        "What is the strongest positive finding?",
        "Every arm supplies an ordinary supported update in the 33 designated recovery inputs. "
        "P2 also satisfies complete corrective communication in 33/33; each comparator has 26 "
        "FALSE and seven UNKNOWN. The finding is narrow because of template and "
        "scripted-playback measurement.",
        "Include the ordinary-update tie whenever explaining the stricter difference. "
        "Otherwise the audience may falsely believe the baseline never corrected the "
        "appointment.",
    ),
    (
        "Results",
        "Why not say P2 eliminated the four unsupported exposures?",
        "The four B3 positive exposure cases have P1/P2 UNKNOWN counterparts. Zero positive "
        "grades with more unknowns is not evidence of definite silence or successful "
        "prevention. They are playout cases, not the hidden-commit primary denominator.",
        "Show the complete table: B3 4 TRUE/481 FALSE/15 UNKNOWN; P1/P2 0/481/19. The paired "
        "uncertainty is material.",
    ),
    (
        "Results",
        "How can 141 FAILED runs all have correct business state?",
        "Raw status records what the driver did, while the independent oracle checks the final "
        "provider state. A refusal or exception can occur after the business action succeeds. "
        "Conversely, 135 raw COMPLETED records have incorrect final state.",
        "Do not generalize that every failure was harmless. The original exception and "
        "evidence determine whether it is expected, and the raw FAILED label remains "
        "preserved.",
    ),
    (
        "Results",
        "Why do we still have 45 failed corrections per arm?",
        "The retained instrument reports 45 FALSE correction outcomes per arm in this fixed "
        "frame. They remain in the denominator. The summary alone does not identify one "
        "universal cause for every such outcome.",
        "Use a specific verified trace if asked for a mechanism. Do not attribute all failures "
        "to the shared claim-selection limitation: that limitation can leave business success "
        "intact while affecting communication.",
    ),
    (
        "Statistics",
        "Does zero observed difference mean the mechanisms are identical?",
        "No. Their recorded business outcomes match on these paired inputs. Conservative "
        "bounds remain -8.79 to +8.79 points for weighted correction and -4.95 to +4.95 for "
        "hidden-commit adverse exposure. Untested settings or shared limitations can conceal "
        "differences.",
        "An absence of observed discordance is not a theorem of equivalence. The estimand is "
        "the declared fixed-frame mixture.",
    ),
    (
        "Statistics",
        "What does the tiny p-value mean?",
        "It describes the 26-versus-zero known-pair communication imbalance under the "
        "diagnostic test's null and assumptions. It is not a probability of our theory being "
        "true, and it does not solve missingness, measurement scope or dependence.",
        "Report exact McNemar 2.9802e-8 and Holm diagnostic 2.9802e-7 only with the seven "
        "missing pairs and fixed-prefix limitation.",
    ),
    (
        "Statistics",
        "Is +78.79 to +100 a confidence interval?",
        "No. It is an empirical identification range over all assignments to the seven unknown "
        "comparator outcomes among 33 planned inputs. It does not include sampling uncertainty "
        "as a confidence interval would.",
        "Compute its endpoints on the board: (33-7)/33 and (33-0)/33. Keep its outcome "
        "definition explicit.",
    ),
    (
        "Statistics",
        "Why a paired bootstrap instead of resampling all 1,500 rows?",
        "The three outcomes for one input belong together. Resampling input IDs preserves that "
        "matching. Independently drawing rows would break the case comparison and could "
        "understate dependence.",
        "Input clustering does not automatically handle all host/time dependence. The report "
        "retains that unresolved assumption.",
    ),
    (
        "Statistics",
        "Did the model prove a latency improvement?",
        "No. Recorded restricted timing differences are positive, so the proposed arms are "
        "slower on that scripted completion measure. P2-B3 is approximately +0.2593 seconds. "
        "The AFT interpretation is conditional on unproven model/censoring assumptions.",
        "Do not confuse time to a supported scripted ACK with human call latency or complete "
        "corrective communication.",
    ),
    (
        "Statistics",
        "All bootstrap fits converged; why still qualify the analysis?",
        "Convergence means the optimizer found a solution meeting its stopping rule. It does "
        "not establish lognormal form, independent censoring, unbiased measurement or "
        "independent inputs. All 1,000 fits were retained because none failed.",
        "Explain numerical validity separately from scientific model validity. A well-solved "
        "wrong model can still mislead.",
    ),
    (
        "Statistics",
        "Does the clean-case test prove the system is useful?",
        "It meets the accepted descriptive/conditional clean tolerance in this frame: all arms "
        "succeed on 300 clean inputs, with lower difference bound -1.22 points above -5. It "
        "does not measure natural-call usability or satisfaction.",
        "A usefulness gate helps prevent celebrating a system that refuses everything. It is "
        "not a substitute for real-user evaluation.",
    ),
    (
        "Integrity",
        "Did operational fixes invalidate the experiment?",
        "They create a provenance and validity issue that must be disclosed. Versioned "
        "instrument corrections, original failures, binding segments and unsuccessful attempts "
        "are preserved. Application behavior, fixtures, grading and study windows were not "
        "silently improved as outcomes accumulated.",
        "Do not claim all 1,500 originals ran one final controller binary. The per-original "
        "binding history is available and interpretation remains qualified.",
    ),
    (
        "Integrity",
        "Did you rerun failed cases until they passed?",
        "No original was replayed or replaced in the retained main analysis. Calibration and "
        "diagnostic attempts have separate identities. Original raw failures, grades, "
        "timestamps and backup references remain traceable.",
        "A recovery that resumes collecting the same original deadline differs from rerunning "
        "its driver commands. Evidence extraction also differs from a research replay.",
    ),
    (
        "Integrity",
        "What does a SHA-256 prove?",
        "It supports byte identity against a trusted recorded commitment. It can reveal "
        "altered content. It does not establish that the file's original claims are true or "
        "that the code is bug-free.",
        "The trust comes from the entire provenance chain, the original commitments, "
        "independently verified copies and scientific checks, not merely printing a long "
        "hexadecimal string.",
    ),
    (
        "Integrity",
        "Why a full 600 seconds after a refusal?",
        "Late provider effects, ACKs or recovery events can occur after a driver returns. The "
        "accepted window is retained even for unsuccessful outcomes. Stopping early on a "
        "refusal could systematically miss later events.",
        "Export after the saved deadline supports accounting, but does not prove perfect event "
        "capture. Missing anchors and collection gaps remain explicit issues.",
    ),
    (
        "Infrastructure",
        "Why AWS instead of your laptop?",
        "The long serial observation schedule needed an independently runnable environment "
        "with controlled resources and backups. The laptop had finite available RAM/disk and "
        "should not need an active chat. AWS hosted the runner; it did not provide the "
        "measured intelligence.",
        "Another qualified isolated host could serve the same purpose. Cloud hosting is an "
        "operational choice, not the novelty claim.",
    ),
    (
        "Infrastructure",
        "How much did it cost?",
        "I must distinguish actual billed spend from the accepted budget and conservative "
        "forecast. The final accepted policy used a US$76 admission guard and US$77 ceiling. "
        "This guide does not refresh billing and cannot honestly turn either limit into actual "
        "expenditure.",
        "Evidence storage and retained disks can continue to cost money after compute stops. A "
        "new financial statement requires bounded read-only billing evidence under the "
        "accepted accounting method.",
    ),
    (
        "Infrastructure",
        "Why did it stop several times?",
        "The retained history includes instrument and operational defects, guard trips and "
        "connectivity problems. These were diagnosed and versioned rather than bypassed. The "
        "campaign therefore is not evidence of an uninterrupted fault-free deployment.",
        "Discuss one demonstrated incident accurately, such as the slot-145 classifier path or "
        "the clock-sampling correction. Do not blame the watchdog for every exception.",
    ),
    (
        "Infrastructure",
        "Can Codex be closed while the experiment runs?",
        "The qualified standalone service was designed to run on its host without an active "
        "conversation, with ledger checkpoints and independent guards. This statement concerns "
        "the deployed orchestration, not a promise that every extraction shell survives "
        "browser/session expiry.",
        "The CloudShell extraction interruption illustrates why a background process and an "
        "independently durable service are not the same thing.",
    ),
    (
        "Authorship",
        "What did you personally do, and how was AI used?",
        "The project used substantial AI assistance for implementation, experiment tooling and "
        "drafting. I should describe my actual decisions and contributions honestly, "
        "distinguish them from generated work, and demonstrate the parts I understand. I must "
        "not claim to have hand-written every line.",
        "Adapt this answer to your real work. Before submission, independently review code, "
        "results and literature; follow the venue's disclosure rules. A memorized answer is "
        "not a substitute for understanding.",
    ),
    (
        "Authorship",
        "Can you explain the code without the assistant?",
        "I should be able to walk through one accepted revision, one external operation, one "
        "verification, one refusal and one repair trace, then show how the oracle grades it. "
        "If I cannot explain a component yet, I should say so and study it.",
        "Practise tracing input ID to arm/execution ID, operation/evidence, saved deadline, "
        "outcome row and backup binding. Do not claim mastery that the meeting would "
        "immediately contradict.",
    ),
    (
        "Scope",
        "Can this be a software-update paper for AgSU?",
        "Artifact versions, deployment evidence and claims of successful rollout form a "
        "plausible analogy. However, our evaluation is booking workflows, not software "
        "updates. Venue fit is for the organizers to judge; I would request a scope review "
        "rather than claim an update benchmark we did not run.",
        "A scope invitation is not paper acceptance or a registration waiver. The full review "
        "manuscript still needs the chosen venue's format and declarations.",
    ),
    (
        "Scope",
        "What would be the next scientific study?",
        "Only stronger claims require a new study: natural speech with verified alignment, "
        "human understanding, broader providers, independent repair consumers, or isolating "
        "persistence from wording. None is retroactively added to this finished campaign.",
        "The current paper can report the primary tie without optional extensions. Future work "
        "must have its own design, authority and resources rather than changing the frozen "
        "denominator.",
    ),
    (
        "Scope",
        "What is the strongest criticism of your positive finding?",
        "The withdrawal rule accepts a fixed phrase, and P2 is designed to produce that form. "
        "Therefore the result can partly reflect the instrument/output template match. It does "
        "not independently establish human benefit or durability's isolated causal value.",
        "Name the criticism yourself and explain why the paper reports ordinary-update success "
        "separately, retains UNKNOWNs, and restricts its conclusion.",
    ),
    (
        "Scope",
        "Why is the project still worth discussing if the main result tied?",
        "A strong baseline handling the tested business conditions is informative. The "
        "instrument also demonstrates why state, evidence, exposure and correction should be "
        "reported separately. A useful systems study can include a negative primary result "
        "without a superiority claim.",
        "Publication value depends on clarity, relevance, originality and methodological "
        "credibility. Case count, cloud spending or effort alone cannot guarantee acceptance.",
    ),
]

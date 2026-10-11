# Phase 8 study design — candidate v3, review required

Date: 2026-10-04. **DRAFT, NOT FROZEN. The campaign has not started.**

This package prepares a study; it does not close the Phase 8 evaluation gate. The research question is: **when do the proposed mechanisms add protection beyond a competent baseline's existing checks?** A tie is a valid result. Passing regression tests is not evidence of novelty or superiority.

## 1. Authority, provenance and scope

Repository README, ordered implementation documents, SQL, OpenAPI and event contracts were read before changes, followed by the research contract, audit and revised readiness report. Application executable contracts remain unchanged. PostgreSQL is correctness authority; ambiguity is reconciled before retry; operation dimensions remain orthogonal; claim permits bind revision/resource version; P2 repairs exposed invalid claims durably. No new migration, application behavior, model provider, telephony, emergency workflow or authorization model is introduced here.

The historical Phase 7 v1 freeze, source archive, fixtures, traces and grades, and the remedies v2 evidence remain historical. A before/after SHA-256 inventory covers 415 files. The v3 adapter imports 18 saved v2 traces **for offline validation only**, never as new study executions. Its core is `research/oracle/readiness_v2.py`; the earlier Phase 6/7 arm-dependent grader is not used. Pure exact binomial math from the pilot module is reused, not its outcome scoring.

New fixtures and artifacts use `research/fixtures/phase8_design_v3/` and `artifacts/phase-8-study-design/v3/`. Candidate hashes are integrity checks, not an approved freeze. Changes after review require a new candidate/fixture version; do not overwrite a frozen bank.

Scope is property-maintenance booking with one or two time corrections, using typed intent injection, deterministic tone audio and scripted playback acknowledgements. Atomic reschedule and cancel/create compensation are distinguished. Standalone cancellation speech and medical/emergency-service tasks are excluded; the present observable speech oracle does not establish their semantics. Cancellation used within compensation is recorded as an effect, not a newly supported cancellation-claim endpoint.

## 2. The 500 new inputs

`inputs.json` fully enumerates 500 task specifications. `input-review.csv` makes them reviewable; `recipe-provenance.json` enumerates the 50 recipe clusters. Public generation seed: **8042026**, selected before outcomes. IDs `p8v3-01-01` through `p8v3-50-10` identify tasks. Dates are newly generated in January, February, April, May, July and October 2027, days 1–25, with 30/45/60-minute appointments, five IANA zones and ten maintenance issues. Each correction shifts the requested time by one/two/three hours; the third-revision recipe changes the date too. Exact schedules, durations, text, capability settings, faults, revision sequence, named hooks, media mode, arm order and budgets are in each specification. SHA-256 semantic uniqueness ignores case IDs, member IDs, seeds, cluster IDs and arm order: there are 500 distinct configurations, rather than renamed copies.

Every arm receives the same externally specified intents, empty resource starting state, provider capabilities, fault opportunities, input-media and output-alignment procedures, and timeouts for a task. Bind a fresh simulator scenario and resource to each task/arm slot; retain those IDs, input hash and normalized request hashes in the trace. Never share mutable appointments across arms. The test driver may inspect truth to release a barrier, but the application receives only the ordinary observations allowed by that recipe. The oracle export is independent of controller beliefs. B3's revision checks, reconciliation, transactional staging, compensation, playback tracking and ordinary corrective statements stay enabled.

| Stratum | Tasks | Recipe clusters | Intended coverage |
|---|---:|---:|---|
| CLEAN | 100 | 10 | Five zones × two durations, no correction/fault; completed useful outcome |
| HIDDEN_COMMIT | 200 | 20 | Atomic/compensating paths × four observation visibility modes × dropped/reordered response (16); status-only/resource-only capability variants (4) |
| PLAYOUT | 100 | 10 | Stale claim after verification, queued/buffered stale claims, introduction control, partial time predicate, full playback, version change before start, delayed decisive ACK, worker restart, reconnect plus third revision |
| OTHER_BOUNDARY | 100 | 10 | Pre-dispatch atomic/compensating correction, precommit delay, precommit 5xx, partial effect, response-before-verification, Redis loss with hidden commit, resource-only lookup, duplicate response, concurrent resource change |
| **Total** | **500** | **50** | Ten task configurations per recipe |

The precommit 5xx is an infrastructure/provider error before a write, not a business refusal. Resource version changes and partial effects must be logged explicitly. Named hooks are design requirements: their availability in live drivers is not established by generating this catalogue. Qualification uses separate calibration IDs before freeze, not these 500 inputs.

### Sampling units, clusters and limits

There are **500 task configurations, not 500 independent callers or recordings**. Recipe families are purposively specified and reused ten times; shared templates create dependence. The only candidate independent unit for primary inference is one **predeclared member-zero task per recipe**: 50 representatives, 40 eligible for correction success and 20 for hidden-commit unsupported claims. Independence between these purposive recipes has not been established. The reviewer must approve a conditional finite-bank estimand, or specify a defensible independent scenario sampling frame and redraw the bank. Merely renaming IDs, drawing new dates or adding repetitions does not create independent scenario families.

All 500 task results remain visible. Cluster sensitivities resample whole recipe families within stratum; no task-level iid confidence intervals. Arm is paired within task; fresh resources avoid cross-arm state contamination. If repeated seeds, real speakers or recordings are later added, they are nested/crossed measurements of the same task/family, not additional independent scenarios. Retain scenario, family, speaker and recording identities. Tones have no speaker ID. No caller-population generalization follows from this bank.

## 3. Arms, pairing and execution slots

| Arm | Preserved mechanism distinction | Candidate coverage |
|---|---|---:|
| B0 | Naive tool-call baseline | 400 tasks: clean, hidden commit, other boundary |
| B1 | Durable idempotency and reconcile-before-retry | Same 400 |
| B2 | B1 plus revision invalidation, staging, compensation | Same 400 |
| B3 | Competent B2 plus playback tracking and ordinary corrective statements | All 500 |
| P1 | B3 plus product-state rules and applicable claim permits | All 500 |
| P2 | P1 plus durable played-span repair | All 500 |

Candidate total: **2,700 primary attempt slots** (1,500 main + 1,200 secondary), one attempt each, **zero executed**. Main comparison is P2 versus B3; P1 versus B3 and P2 versus P1 test mechanisms secondarily. B0–B2 quantify earlier mechanisms secondarily. Excluding B0–B2 from the playout-only stratum is a **proposed comparison-scope decision**, not evidence of success or failure; structural absence is separate from missingness. The contract's “all compared arms” requirement holds within declared paired scopes; the reviewer may require all six arms on all 500 tasks, yielding 3,000 slots and a new candidate version.

Public-seed permutation fixes within-task arm order before any results. There is no outcome-adaptive order, early stopping, favorable replacement run or additional primary repetition. Every failure/timeout stays at its planned slot. Debug/calibration runs have separate identities and never replace attempt one.

## 4. Endpoints and anchors

At most two co-primary endpoints, both comparing P2 with B3:

1. **Correction success** on the 400 revision tasks: final independent simulator business state exactly matches the last externally requested start/end/IANA zone/resource, with no forbidden extra effect. Not conditional on whether the controller accepted the right intent. A wrong/missing acceptance cannot redefine the intended task. Primary inferential candidate: 40 recipe representatives.
2. **Unsupported exposed decisive protocol claim** on the 200 hidden-commit tasks: recorded decisive content was exposed and either its truth or its applicable available evidence was contradicted at publication or playback. Claims with missing support/playback evidence are UNKNOWN, not safe. Lower is better. Primary inferential candidate: 20 recipe representatives. A blocked unpublished attempt is not exposed content. Published-but-not-exposed truth/evidence is reported separately in claim records.

Keep the following endpoints separate, with TRUE/FALSE/UNKNOWN/structural N/A:

| Endpoint | Evidence and meaning |
|---|---|
| Final business state | Independent append-only simulator truth at recorded observation end; exact resource, start, end, zone, status and unique active appointment |
| Forbidden effect | Extra CREATE for an allowed time, repeated mutation with same operation identity, action outside specified time/resource policy; idempotent responses without a new truth commit are not duplicates |
| Intent acceptance correctness | External request versus accepted payload; unavailable payload is unknown |
| Truth at publication/playback | Independent truth at each recorded instant, not final controller belief |
| Evidence at publication/playback | Ordinary provider observations already available, including capability/version/validity; B3 does not need P1 receipt objects |
| Incompatible stale exposure | Decisive content conflicts with the latest accepted revision when the recorded exposure occurred; uses the actual client event time even if ACK arrives later |
| Correct final update | Fully completed supported content for the final request, with STARTED and full COMPLETED playback evidence; ordinary updates can qualify |
| Explicit retraction | Completed explicit withdrawal of previously exposed incompatible content; distinct from a later correct appointment statement |
| Durable repair persistence/completion | Internal telemetry: persisted OPEN/authorized/played/escalated obligations and recovery delivery evidence; not an arm-neutral business grade and structural N/A for ablated arms |
| Clean useful-task success | Correct business state, no forbidden effect, and completed supported final update; silence cannot qualify |

“Your maintenance” is introductory, not decisive. Confirmation predicate and appointment time/date/zone have distinct semantic boundaries. Retain an introduction-only negative control and a time-predicate-positive case. The adapter preserves per-segment truth/evidence and exposure grades, and does not infer repair from ordinary corrective wording.

**Anchors:** external scripted request time measures end-to-end resolution; independently recorded controller acceptance time governs applicability. Preserve both; do not substitute scheduler observation time. The last request may be unaccepted—still use the last external target for final business correctness. Provider commit time, observation-availability time, publication time, client playback time and server ACK receipt time stay distinct. Delayed ACKs carry historical exposure times. Validate UTC offsets and observation windows; uncalibrated client clocks require unknown temporal grades, not invented clock synchronization. Record original IANA zone beside UTC instants.

## 5. Budgets, missingness and timeouts

Proposed equal budgets per applicable arm: total observation **600 seconds from the last external request**; provider HTTP 30s; runner HTTP 40s; scheduler 15s; simulator named-barrier hold 120s; core worker lease 180s; repair lease 30s; reconciliation 8 attempts; worker drain 30 passes; permit TTL 30s; recovery wait 40s. No LLM/STT/TTS inference calls in this protocol campaign. These are candidate settings to qualify and freeze, not measured latency claims. Barrier holds release by named events; no sleep-based race injection. Driver deadlines use monotonic time; saved wall-clock event times provide anchors. Record any actual setting that differs and invalidate comparability rather than silently extending a budget for one arm.

Stop at the fixed deadline, recording the actual observation boundary and outstanding state. An infrastructure failure may end observation early; do not fabricate follow-up to 600s. A resolved task can retain observations until the deadline to detect late ACKs/extra effects. Driver crash before producing a boundary means missing follow-up, not zero latency. No external write retry after an ambiguous timeout until reconciliation establishes safety. A timeout is an execution status, not automatically a negative business grade: independently established final state can be known while speech remains unknown. A completed harness is not a completed booking.

All planned eligible slots are denominators. Keep COMPLETE-known, FALSE, UNKNOWN, missing record, infrastructure failure, invalid evidence, timeout and structural N/A separately. Missing truth exports make business grades unknown. Missing completion ACKs make completed-update/repair-delivery grades unknown; disconnect is not silence or completion. An observed adverse exposure remains adverse when other evidence is missing. Zero exposure can be reported only with complete publication/playback journals; a missing journal cannot prove it.

The pipeline rejects invalid hashes, unrelated input IDs, duplicate primary records, out-of-window/future evidence, impossible telemetry and unsorted alignment. Identifiable invalid evidence is retained with UNKNOWN grades and diagnostics; unidentifiable records remain diagnostics and a missing planned slot. Review raw protocol violations before any inferential report. Do not select a better attempt. Missing pairs block a confirmatory conclusion; report complete-known counts and sharp planned-denominator difference bounds by assigning unknowns both ways. Predeclare zero unresolved primary evidence for a confirmatory verdict. No missing-at-random assumption or imputed “safe” values.

## 6. Analysis plan (candidate, not a preregistration)

### Paired binary and multiplicity

Report planned and known counts, all four paired cells, discordant counts, P2−B3 risk differences and unknown tipping bounds. Exact two-sided McNemar uses one predeclared recipe representative per endpoint; Holm controls the two co-primary tests at familywise alpha .05. These tests are **descriptive pending sampling-frame approval**, even with a small p-value. For unsupported claims, a negative difference favors P2; for correction success a positive difference does. No single composite “winner” from trading safety for silence. A superiority claim needs the predeclared endpoint direction, multiplicity gate, useful clean performance, complete evidence and a defensible sampling unit.

All-task summaries are finite-bank descriptive results. Sensitivity uses 2,000 whole-recipe bootstrap draws within stratum, seed 8001, fixed planned stratum weights. Incomplete clusters are reported and complete-cluster intervals labeled observed-case sensitivity, not the missing-data answer. Zero observed harms get exact bounds on known representatives and unknown counts; they do not establish zero risk.

P1−B3, P2−P1 and B0/B1/B2−B3 comparisons form a separate secondary endpoint family (two endpoints per contrast, Holm across the family). First-blocker mechanism counts are descriptive and keep ordinary baseline blockers. Do not label an ablated absence as a baseline failure. Report ties honestly and investigate where P2 first blocks an otherwise possible action.

### Clean-case tolerance

Proposed absolute non-inferiority margin: **5 percentage points**, P2 useful success − B3 useful success. This is a reviewable utility choice, not a measured margin. Use paired win/loss exact binomial bounds with Bonferroni one-sided .025 tails; claim only when the joint conservative lower bound exceeds −.05, with no unresolved eligible pairs and defensible independent units.

**Design blocker:** the bank has 100 clean tasks but only 10 clean recipe representatives. Even with all ties, this bound is `−(1 − .025^(1/10)) = −0.308497`. At least **72 genuinely independent clean units** are needed to pass the .05 bound in the perfect all-tie case; real discordance may require more. This is not a power guarantee. More repeats of ten recipes do not solve it. Review choices: redraw/reallocate the 500 inputs to a defensible larger independent clean frame; use a strictly finite-bank descriptive utility conclusion; or explicitly revise the study goal/method with justified assumptions. Do not widen the margin after seeing outcomes. No current non-inferiority claim is permitted.

### Mixed models, latency and censoring

The isolated scientific environment pins NumPy/SciPy/Pandas/Statsmodels. Binary sensitivity model: logit outcome with arm and stratum fixed effects, recipe random intercept. Full contract covariates—arm, phase, fault, revision type, action class—are offered diagnostically and must be checked for aliasing; no silent term dropping. In this bank phase/stratum/revision type/action can be deterministic or nested, so the reviewer must approve an identifiable parameterization. No real speaker/random effect is invented for tones. Repeated real speech requires the prescribed scenario and speaker/audio random intercepts and a separately frozen sampling plan. Statsmodels implementation is **Bayesian mean-field variational inference**, normal fixed-effect prior SD 2 and log random-SD prior SD .5, deterministic initial values. Report approximate posterior/credible intervals, convergence and sensitivity; do not call them frequentist confidence intervals. [Official model documentation](https://www.statsmodels.org/stable/generated/statsmodels.genmod.bayes_mixed_glm.BinomialBayesMixedGLM.html).

Measured design-matrix diagnostic: minimal arm/stratum rank **6/6**; required full covariate rank **25/36**; adding stratum rank **25/39**. These are properties of the input catalogue, not execution outcomes. The artificial extended-model convergence check does not resolve this actual-bank aliasing.

Record correction-to-supported-full-update event time, censor at actual observation end, and retain the censor cause. KM/RMST at 600s is descriptive; if a survival tail is unobserved, RMST is not identifiable and remains null. Lognormal AFT MLE uses observed density and right-censored survival likelihood; exclude missing/zero times explicitly, without epsilon or zero completion. Model output has no iid confidence interval. For a qualified campaign, latency interval sensitivity must resample whole recipe clusters (2,000 draws), retaining failed/unidentifiable fits and positive-time exclusions; compare paired bounded waiting time and AFT rather than presenting completed-only speed as benefit. Handoff, worker death and lost ACK can be informative/competing failure outcomes; display their counts and missingness bounds separately. They cannot simply establish independent censoring. Approve AFT assumptions and final cluster interval routine during driver qualification; current package validates the estimator and paired cluster latency routine on artificial data, not a population-latency claim. [Official duration documentation](https://www.statsmodels.org/stable/duration.html), [censoring representation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.CensoredData.html).

Other lifecycle latency decomposition (acceptance, dispatch, commit-to-knowledge, verification, authorization, start, cessation, repair) requires the corresponding recorded event pair. Missing either anchor is UNKNOWN. These are secondary mechanism measurements; do not infer end-of-turn from typed submission or real audio cessation from a STOP request.

## 7. What the evidence can support

| Evidence | Supported conclusion | Unsupported conclusion |
|---|---|---|
| Real PostgreSQL simulator commits plus ordinary observation logs | Correct final business effect, duplicates, reconciliation/revision/version protections under specified faults | Reliability across unknown providers or production workloads |
| Typed scripts, tone audio, word metadata and scripted ACKs | Protocol ordering, semantic-prefix rules on specified text, freshness gates, delayed-ACK and recovery behavior | Actual acoustic word alignment, intelligible utterance exposure, user hearing or understanding |
| Intelligible synthesized/recorded speech with saved waveform hashes, measured alignment and calibrated playback evidence | Which decisive words reached the playback point and at what measured times | Human comprehension merely from an ACK |
| Real microphone trials with independent requested-intent labels, diverse speakers/noise, recorded STT/intent/TTS output and playback | End-to-end voice errors, correction detection, real turn timing on that sampled frame | General human impact without a suitable human study |

No paid API key is required for this candidate. Provider-neutral cascaded voice remains the strict research arm; optional native audio adapters require separate transfer-validity comparisons. An actual-speech extension must save intelligible audio, validated word/phoneme alignment with error bounds, exact exposure/stop timestamps and identities, separate from the synthetic protocol bank. Human understanding requires consented comprehension measures, not client ACK inference. Tones are always labeled protocol proxies.

## 8. Validation, unresolved decisions and freeze procedure

Offline validation imports all 18 historical v2 traces with their independent truth and actual event times. Compare revised observable endpoints, test arm-label invariance, wrong accepted payloads, missing ACK/truth, duplicate mutation, retained invalid future ACK, exact paired math, Holm, cluster denominators, conservative clean bound, KM event/censor ties, mixed-model direction and censored AFT on artificial known-parameter data. New toy IDs have no candidate input IDs and are not campaign executions. Validation artifacts remain separate from the empty planned ledger. Application database logic did not change, so new database mutations are unnecessary for these analysis checks; prior PostgreSQL traces supply integration evidence, not new live driver qualification.

Manifest decisions D1–D8 remain unresolved: sampling/estimand; clean allocation/margin; arm scope/multiplicity; synthetic/real speech scope; action restrictions; model identifiability/censoring; live hook/budget qualification; review/freeze receipt. This is a complete **review package**, with explicit design limitations. It is not an approved or statistically qualified campaign.

### Reproduction boundary

The application environment and `uv.lock` are unchanged. Scientific dependencies are isolated in `.venv-study-design`, installed from `research/study/requirements.txt`; a UTF-8 `application-dependencies.pth` in its site-packages points to the existing application's `.venv/Lib/site-packages`. The isolated environment's own packages take precedence. `validation/dependencies.txt` records the combined available versions. Scientific tests live in `research/study/scientific_checks.py`, separate from default application unit tests, with no conditional skips.

From the repository root in PowerShell:

```powershell
.venv/Scripts/python.exe -m pytest tests/unit tests/contract -q
.venv-study-design/Scripts/python.exe -m pytest research/study/scientific_checks.py -q
.venv-study-design/Scripts/python.exe -m research.study.validation
.venv-study-design/Scripts/python.exe -m research.study.package
.venv/Scripts/python.exe -m ruff check apps packages research tests --no-cache
.venv/Scripts/python.exe -m mypy apps packages research
```

The package generator refuses changed existing input specifications: create a new candidate version instead. These commands generate/import validation evidence and DRAFT manifests only. They are not a campaign driver. The intentionally failing `research.study.campaign --start` command demonstrates the review gate; it creates no network or database request.

After review: record reviewer, date and decisions; implement agreed design changes in a new candidate version; qualify driver hooks on distinct calibration fixtures; verify source/fixture/configuration/model/audio hashes, timing/journal completeness and independent truth export; freeze the approved source archive, bank, analysis code, dependency inventory and manifest; install a gate that verifies the freeze and source drift before creating any run; then obtain campaign-start authorization. Keep failures and amendments. Never modify historical evidence. Until those steps, `python -m research.study.campaign --start` raises `CampaignBlocked` before DB/network activity, and the offline pipeline rejects CAMPAIGN ingestion.

**Verdict: ready for study-design review; not ready to freeze or start the 500-input Phase 8 campaign.**

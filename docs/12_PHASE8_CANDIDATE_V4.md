# Phase 8 candidate v4 — decisions before freeze

Status: candidate, not reviewed or frozen. The main campaign is unstarted.

## Sampling frame and estimand

The population is a declared finite support of 50 simulator protocol recipes,
combined with the context generator in `research/study_v4/design.py`. Within each
stratum, draw the recipe uniformly with replacement and independently draw a
maintenance issue, appointment date, time and applicable correction offset.
Dates, zones and durations restricted by a recipe remain conditional on that
recipe. The seed fixes reproducibility, not an observed outcome selection rule.
There are 500 semantically distinct new inputs; calibration uses separate dates,
IDs and an independent seed. The input draw is the sampling unit. Arms are paired
within input, executed in randomized order, with fresh resource bindings.

Recipe names are fixed support labels, not 50 sampled families. Shared processes,
host and temporal batches can produce dependence: report batch sensitivity and
order diagnostics; do not extrapolate to unseen recipes, callers or workloads.
Legacy member/representative fields only satisfy the v3 record wire schema and
are ignored by v4 inference. No speaker or recording clusters exist in tone tests.

The estimand is the standardized arm risk difference over this declared mixture,
conditional on the simulator, protocol client and application version. It is not
a population estimate of human understanding or real-call safety.

## Allocation and arms

| Stratum | Inputs | Probability within its recipe support |
| --- | ---: | --- |
| CLEAN | 300 | Uniform |
| HIDDEN_COMMIT | 100 | Uniform |
| PLAYOUT | 60 | Uniform |
| OTHER_BOUNDARY | 40 | Uniform |

B3, P1 and P2 receive all 500 inputs: 1,500 main slots, none executed. This candidate
answers incremental protection over the competent baseline. B0–B2 remain
historical ablations and require a separately reviewed extension if required in
the final full Phase 8 deliverable. It does not claim the six-arm campaign is done.

Clean noninferiority retains the absolute 5 percentage point tolerance. A
conservative paired bound subtracts the upper exact loss-probability bound from
the lower exact win-probability bound, with 0.025 in each tail. Exact enumeration
at n=300 gives approximately 80.39% power at equal risks and 5% discordance.
The complete grid is `analysis-design.json`; these are assumptions, not estimates
from the small pilot. Higher discordance or a true loss reduces power. Do not
change the margin or allocation after observing main outcomes. The all-ties bound
still expresses finite precision; zero observed events never proves zero risk.
The two contract co-primary endpoints are maintained. Clean tolerance is a
separate acceptance gate; multiplicity decisions require reviewer acceptance.

## Outcomes and identifiable analysis

Co-primary: (1) correct final business state without forbidden effects on the 200
correction inputs, standardized using stratum weights 0.5/0.3/0.2; (2) unsupported
decisive exposure on the 100 hidden-commit inputs. P2 versus B3 is primary; P1
versus B3 and P2 versus P1 are mechanism comparisons, not extra unadjusted primary
claims. Use Bonferroni for the two co-primary claims (.025 per comparison bound);
report paired exact stratum tests as diagnostics,
risk differences and conservative intervals. Weighted correction inference uses
simultaneous component binomial bounds, not a pooled exact McNemar test. Hidden
exposure uses paired win/loss bounds on its single stratum. Holm is reserved for
the explicitly declared secondary comparison family. Missingness remains in planned
denominators with worst/best possible paired differences; no complete-case claim
of noninferiority when those bounds fail it. A failed attempt is never replaced
by a successful rerun in primary analysis.

Use the saturated marginal arm × eligible-stratum cell-mean model (nine
parameters for correction; three each for hidden exposure and clean success).
Structural N/A cells are excluded before fitting. Coefficients are cell means
and differences of means; pair
covariance at the input level. Do not fit aliased phase, fault, revision and action
coefficients. Conditional recipe summaries and batch sensitivities are descriptive;
a new repeated-recording study requires a different sampling and covariance model.

Key secondary: supported final corrective delivery after an externally scheduled
recovery challenge, within the observation horizon. Give an ordinary B3 update
the same credit as a P2 repair segment. Separately measure supported update plus
explicit withdrawal of previously exposed incompatible content, and persistence,
discovery, retries and completion of durable obligations. Obligation creation is
not an observable advantage. The predeclared recovery subset includes partial,
full, delayed-ACK, restart and another-revision recipes. Report every challenge
even if a safeguard prevents the stale exposure. Do not condition the principal
comparison on an arm's post-treatment exposure.

`complete_corrective_communication` uses the fixed challenge denominator: it
requires a supported delivered update and withdrawal when needed, granting
success when no withdrawal is necessary. The conditional withdrawal-plus-update
endpoint is descriptive and explicitly N/A when there was nothing to withdraw.

The current fixed spoken template matcher recognizes the project's explicit
withdrawal wording; it is not an open-language semantic assessor. Missing support,
alignment or playback completion remains UNKNOWN. A journal export ending before
the 600-second administrative horizon cannot establish absence of later exposure
or delivery. A recorded unsafe event survives other missingness. Protocol ACKs
are not evidence of hearing or comprehension.

## Calibration acceptance rules (separate from outcomes)

Calibration covers every fixed recipe once across all three arms (150 planned
slots). Every original attempt, timeout, refusal and debugging rerun is retained.
Qualify only if raw evidence proves the named preconditions, fault effect and
causal ordering, including exact revision and resource binding. A driver status
COMPLETED alone does not qualify a hook. A safe refusal can qualify a fault while
leaving business correction unsuccessful or unknown. Export provider raw events
and independent simulator truth. B3 ordinary checks and corrective statements
remain enabled. Main cases cannot be executed by the calibration driver.

The unsupported `DUPLICATE/AFTER_RESPONSE` recipe has been replaced in this new
fixture version by duplicate request delivery before commit. Qualification needs
the provider's idempotent replay evidence and a single truth effect. A named
reordered response requires the recorded acceptance before barrier release and
response receipt; its label alone is insufficient.

Budgets to qualify: provider HTTP 30s, scheduler HTTP 15s, driver HTTP 40s,
provider barrier 120s, core job lease 180s, repair lease 30s, reconciliation
8 attempts, driver drain 30 passes, permit TTL 30s, recovery observation 40s,
main administrative observation 600s. Source/configuration checks are distinguished
from exercised boundary evidence. Unexercised budgets are blockers, not certified
from constants. Qualification experiments must use dedicated calibration IDs and
isolated databases. No 500-case driver is enabled by this candidate.

## Evidence limits and review

### Execution and secondary analysis decisions

Input execution order is shuffled using seed 8042043, saved in
`execution-order.json`. Twenty fixed blocks of 25 inputs support order/load
diagnostics; blocks are not sampled recipe families. Compare the standardized
estimate after omitting each block. Shared-host dependence requires review;
calling these blocks clusters does not establish their independence.

There are 33 predeclared recovery-challenge inputs. At 10% discordance, a normal
precision illustration is about ±10.8pp; this is not a power guarantee. Baseline
ordinary response opportunities remain available after restart; P2 additionally
uses native durable discovery. These fixtures do not establish an unattended
comparative delivery advantage over a deployed baseline responder.

The secondary family has ten comparisons: P1−B3 and P2−P1 on the two co-primary
and two delivery endpoints, plus P2−B3 on the two delivery endpoints. Apply Holm
across that family. Conditional withdrawal and obligation telemetry are descriptive.
Its paired exact tests address stratum-wise exchangeability as diagnostics; they
do not test the weak weighted-average null. Interpret average effects using the
standardized paired bounds. Missing family p-values leave the adjustment unresolved.

The response-reorder recipe is a single held ACK crossing revision acceptance;
it does not permute two provider responses. The reserved Redis flush is a
companion-cache negative control: this application does not consume that cache.
It cannot qualify an application Redis outage. Review must accept these scopes.

At the maximum 600s per slot, sequential observation alone could take 250 hours.
Scheduling, early-terminal evidence rules and storage must be frozen before
launch. Early exports cannot establish absence through the full horizon. Later
exports are capped at the final externally scripted request plus 600s, with late
information excluded from grades and uncapped evidence retained. Shared-process
restart faults prevent assuming unrestricted parallel execution is comparable.

Scripted text/tone playback can support transactional protocol, applicability,
ACK ingestion and recovery claims. It cannot support acoustic intelligibility,
ASR quality, turn-taking, human exposure or comprehension conclusions. Those need
intelligible recordings, independent alignment, real playback capture, speaker
sampling and a separately reviewed speech protocol.

Review must accept the conditional frame, three-arm scope, margin and nuisance
assumptions, multiplicity, recovery opportunities, complete observation window,
qualified hooks and budgets, and remaining operational limitations. This document
records proposals rather than a review receipt. See the separate v4 readiness
report for observed qualification results. Historical v1/v2/v3 artifacts stay
unchanged and their before/after hashes are checked.

# Timing analysis compatibility — review amendment

The earlier execution-plan v1 proposed descriptive-only timing. That proposal
does **not** satisfy `docs/04_TEST_EVALUATION_AND_TRACEABILITY.md` section 7 and
the Phase 8 build prompt. This package supersedes that proposal explicitly; it
does not silently remove the required clustered latency intervals or censored
resolution analysis. Application behaviour and the v4 outcome definitions stay
unchanged. Review must accept this analysis amendment before protocol freezing.

## Sampling and dependence units

The independently drawn **context input** is the sampling unit, conditional on
v4's fixed recipe support. Retain all three arm records for an input together in
each bootstrap draw. Draw inputs within each predeclared stratum, keeping realized
stratum counts and weights. Recipe labels are fixed support categories, not sampled
families; the legacy `cluster_id` and member-zero fields do not define v4 inferential
clusters. Diagnostic reruns are excluded from original-attempt estimates and remain
in the ledger. Future repeated audio/model versions would be nested within the
same input; this campaign introduces neither those repetitions nor speech clusters.

Serial execution prevents intentional overlap, but does not prove independence
from host load, cache warmth, background activity or time. Keep saved input/arm
order, host measurements and the existing twenty fixed blocks of 25 inputs. The
existing v4 block-omission risk-difference analysis remains a descriptive sensitivity
check, **not** proof that blocks are independent. Inspect time/order/load and stratum
timing diagnostics. If material dependence remains, qualify the input-bootstrap
intervals as conditional and report that limitation; do not promote timing results
to a population claim. A block bootstrap would require a separately accepted
dependence assumption and review amendment, rather than calling twenty blocks
independent automatically. It is not an added default analysis in this package.

Unqualified concurrent execution is excluded. Overlap would share CPU, storage and
collection contention even with separate databases and ports; different execution
IDs would not remove that dependence. A future concurrency schedule must record
lanes and overlap intervals and re-review both performance estimand and dependence
analysis. No faster concurrent-runtime estimate is treated as qualified here.

## Retained latency and censored analysis

`research/execution_setup/timing.py` integrates the existing revised oracle's
resolution times with:

- Stratified paired input-cluster percentile intervals, 2,000 draws, fixed seed
  8042051, for P2−B3, P1−B3 and P2−P1. The all-input mixture uses allocation weights
  .60/.20/.12/.08; the same function can report a declared stratum separately.
- Mean time to **recorded supported completion**, restricted at the unchanged
  600-second administrative horizon. No recorded completion through a complete
  window is administrative censoring, not an invented success, business failure,
  silence or human comprehension result. This restricted protocol-time estimand
  is explicitly proposed to avoid treating timeout durations as completed events.
- Completed-pair timing summaries labelled as selected-subset descriptions; they
  do not replace the planned-input estimate. Missing anchors, missing paired records
  and early interrupted collection produce missingness bounds over [0,600] and
  an unresolved primary timing interval, rather than a complete-case replacement.
- The existing identifiable right-censored lognormal AFT model,
  `1 + C(arm) + C(stratum)`, with input-ID clusters substituted for legacy recipe
  clusters in its bootstrap, 1,000 draws, seed 8042052. Keep every nonconverged,
  rank-deficient or otherwise failed draw. Report convergence, exclusions, censor
  reasons and assumptions; failed-fit sensitivity is required before interpreting
  conditional successful-draw intervals. No unclustered Hessian interval is used.

These are secondary timing estimates with nominal 95% intervals, not new
confirmatory superiority tests or extra endpoints. The two binary co-primary
comparisons, clean-case 5pp tolerance, planned-denominator missingness rules and
ten-comparison Holm family remain as defined in v4. AFT assumes its parametric
time distribution and suitable administrative censoring; an infrastructure outage
or missing ACK evidence is not automatically independent censoring. Missing times
are excluded transparently from model fits and block any unconditional timing claim.

The collector records script issuance **before** transmitting a revision and
keeps acceptance as a separate durable server event. The tiny crash gap between
recording issuance intent and sending HTTP remains uncertain; acceptance is never
invented. Original deadlines survive process restart. Playback receipt times are
replaced with actual durable server ACK timestamps when available; the instrument's
scripted client event times remain the protocol completion-time basis. This is not
acoustic alignment or a measurement of a listener understanding speech.

## Validation scope

Offline validation demonstrates paired grouping despite identical recipe labels,
stable results under row reordering, censor/missing separation, rerun exclusion,
main-evidence rejection, identifiable AFT fitting and retained input-cluster draws.
Live calibration exports exercise the revised v4 observable oracle using real
PostgreSQL and the independent simulator truth log. Two live qualification cases
cannot estimate study effects or validate all distribution/dependence assumptions.

**Review action:** accept the retained required analyses, restricted protocol-time
interpretation, conditional independence assumption and stated failure/missingness
handling. No descriptive-only waiver is presumed.

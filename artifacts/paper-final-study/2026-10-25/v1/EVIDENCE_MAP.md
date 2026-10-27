# Manuscript claim-to-evidence map

This companion is part of the review package, not a new protocol freeze or
analysis. Paths are relative to the repository unless noted otherwise. Exact
fingerprints are recorded in manuscript-verification.json.

| Manuscript claim | Retained source | Interpretation constraint |
| --- | --- | --- |
| 500 inputs, 1,500 originals, allocation, raw statuses | artifacts/phase-8-final-analysis/v1/analysis/summary.json; analysis/original-results.csv | Raw driver completion differs from business/speech success. |
| All originals backed up; exports after deadlines; 196,037 notices; nine bindings | artifacts/phase-8-final-analysis/v1/final-validation.json; analysis/operational-provenance.csv; analysis/operational-segments.json | Integrity/accounting does not establish complete capture or per-process binary attestation. |
| 455/500 business, 300/300 clean, 155/200 correction, 408 supported updates | artifacts/phase-8-final-analysis/v1/analysis/summary.json | Preserve all FALSE, UNKNOWN and N/A counts. |
| Co-primary 97.5% bounds and clean lower bound | artifacts/phase-8-final-analysis/v1/analysis/outcomes.json: primary_bounds, clean_noninferiority | Claim flags remain false; conditional intervals do not prove equivalence. |
| 33 recovery inputs; 26 known P2-only successes; seven missing pairs; Holm diagnostics | Same outcomes.json: recovery_secondary, secondary_family | Missingness bounds are not confidence intervals; diagnostic p-values are not a missingness-free superiority result. |
| 40 recorded repair obligations | artifacts/phase-8-final-analysis/v1/presentation/descriptive-facts.json | Mechanism telemetry; sampled workers were experiment-invoked. |
| 4/0/0 TRUE exposure with 15/19/19 UNKNOWN | analysis/summary.json; presentation/descriptive-facts.json | The four paired comparator results are UNKNOWN, not evidence of silence. |
| Timing values and input-cluster uncertainty | analysis/latency.json; analysis/aft.json; analysis/aft-bootstrap.json | Scripted-ACK completion; censoring and shared-host assumptions unresolved. |
| First-two historical sidecars only; no new sidecar | dataset/accepted-timing-rows.json; accepted-existing-sidecars/; analysis/summary.json | Raw sequence 1,2,145,616 labels preserved. Numeric outcomes unchanged. |
| Competent baseline / incremental switches | E:/p8v12/source/research/arms.py | P1 changes two switches together; P2 is a repair package, not an isolated persistence intervention. |
| Label-independent observable grader and exact-prefix withdrawal | E:/p8v12/source/research/oracle/readiness_v2.py: grade_observable | Does not read permit IDs/receipt verdicts; exact wording is not open-language semantic equivalence. |
| Shared revision-only claim-selection limitation / sequence 145 | artifacts/phase-8-continuation/classifier-145-v2/REPORT.md; bundle-provenance-closed.json; underlying retained slot-145 evidence | Experiment-control classifier correction did not repair studied application behavior. |
| Sequence 59 and 82 examples | artifacts/phase-8-final-analysis/v1/examples/0059-B3.export.json; 0082-P2.export.json; examples/verification.json | Illustrations, not new selected analysis denominators or unattended-recovery proof. |
| Sampling frame and fixed design | artifacts/phase-8-study-design/v4/candidate.json; frozen-cases.json in final-analysis/v1 | Fixed families/context generator; not a random production workload or caller sample. |
| Prior manuscript unchanged | artifacts/paper-draft-agsu/2026-10-24/v1/edits/comment1/verification.json | Earlier interim 1,318-row descriptions are historical, not reused as final results. |

## Literature verification

The twelve numbered references were checked against primary publisher/author
pages on 25 October 2026. Full-text HTML was inspected for Atomix, Cordon, REVISE,
Tool Receipts and PACE; the other comparisons use verified bibliographic/abstract
records. Claims about prior work are brief paraphrases. No comparative numerical
performance claim is made against these papers. Related-work coverage is targeted,
not exhaustive. The source URLs are included in the manuscript and readiness note.

The current workshop web fetch failed; its retained 24-October CFP is used only
as dated venue background. No current submission acceptance, publication status,
attendance exemption, discount or fee waiver is inferred.

## Package boundaries

Only manuscript source, typesetting helper, review notes and local verification
records are created here. The PDF is under output/pdf/commit-aware-agents-full-v1/.
No original grade, fixture, oracle, analysis method, runtime, cloud resource or
historical paper was modified. manuscript-verification.json validates existing
analysis-file hashes and the recorded post-edit hashes of the earlier WIP.

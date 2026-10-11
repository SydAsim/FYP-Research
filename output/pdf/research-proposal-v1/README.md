# Research proposal package

Documentation and evidence review dated 4 October 2026. This package does not freeze the study or authorize campaign execution.

## Start here

- [Complete proposal PDF](research-proposal.pdf) and [editable Markdown](research-proposal.md).
- [One-page overview PDF](plain-english-overview.pdf) and [Markdown](plain-english-overview.md).
- [Supervisor discussion checklist](supervisor-checklist.md).
- [Evidence index and all 18 exploratory trace links](evidence-index.md).
- [Verified bibliography](bibliography.md).
- [Unresolved factual gaps](factual-gaps.md).

The proposal distinguishes implementation phases, correction timing points and experimental arms. It explains the architecture, invariants, retained results, candidate sampling/analysis, measurement limits and decisions before a future freeze.

## Diagrams

`diagrams/` contains 23 readable panels across the 12 requested topics. Each has editable Mermaid (`.mmd`), vector SVG (`.svg`) and PNG (`.png`). All panels appear in both the Markdown and PDF. The split panels keep long processes legible at normal page size.

## Evidence and review boundaries

- Current candidate: v4; 500 new inputs and 1,500 paired-arm execution slots proposed, all unstarted.
- No review receipt or freeze hash exists. No accepted 100-input replacement was found.
- Original evidence: 450 historical files retain their hashes. All 282 final candidate source files retain their hashes.
- Revised exploratory business correctness ties at 5/6 across B3/P1/P2. Selected permit/repair differences do not establish general superiority.
- Synthetic tone/scripted ACK evidence supports temporal protocol findings. It does not establish human hearing, comprehension or autonomous comparative delivery.

Primary-source references are portable web links. Evidence links point to real absolute locations in this workspace. Sharing this documentation archive alone does not include the original repository, large evidence archives or uploaded PDFs; recipients need those sources to inspect the local links. The documents explicitly disclose this access requirement.

## Quality records

[Preservation check](documentation-preservation-check.json) records the read-only hash and campaign-status checks. [Source fingerprints](source-fingerprints.json) identify 47 key claim sources. [Quality check](quality-check.json) records PDF pagination, outline, text bounds, local-link existence and diagram geometry. Visual review covers every rendered page and the one-page overview; these checks validate presentation, not research hypotheses.

`build_proposal.py`, `render_package.py` and `validate_package.py` are documentation utilities retained for reproducibility. They are workspace-specific and read project evidence. The rendering tool uses ReportLab, Poppler, Mermaid CLI and an existing Chrome browser. They are not application changes or experiment drivers.

## Factual verdict

Selected local durability, reconciliation, permit and repair mechanisms are implemented and demonstrated. The incremental population benefit and a novel contribution remain hypotheses. Next, review the scope, estimands, clean tolerance, analysis promises and isolated observation schedule, then approve and record a new freeze before separately authorizing evaluation.

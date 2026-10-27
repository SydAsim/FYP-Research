# Package-only correction v3

The returned trace establishes that retrieval reached1500 with372 recovery GETs
and22198827558 recovery bytes. Packaging then raised KeyError('fixture_hash')
before all-results.json was written. This is an evidence helper defect, not a
failure of a research execution. Preserve both old scripts and both attempts.

Files: cloud_package_final_v3.py, five-control output, verification.json,
REPORT.md and HANDOFF.md. No application, analysis, grader or fixture changes.

Correction: the old735 compact records omit fixture_hash. Require those735
objects to equal their hash-bound cached originals exactly. Check their five
recorded identity fields and pinned archive/version bindings. Bind their fixtures
through the existing authenticated extraction-control identities, without adding
fields or changing bytes. New736–1500 records still require their fixture_hash.
Missing modern fields, altered caches, ordering/identity/receipt drift and partial
records must fail. Existing prepare_dataset.py later checks every frozen case.

Five fixed offline controls, maximum60seconds, before handoff: reproduce the
exact KeyError using the actual cached schema; package the full mixed schema
without altering any record; reject altered cached data; reject missing/wrong
modern fixture hashes; reject missing/duplicate originals and existing output
collisions without overwriting historical evidence. Synthetic new records are
temporary filesystem controls, not research executions or oracle outputs.

Package-only mode contains no AWS client or network operation. Reuse all765
downloaded records and735 cached originals. Validate old request bindings,
attempt/completion metadata, exact expected packaging failure and preserved
hashes. Keep original extraction deadline and192MiB total staging,2MiB failure
reserve,48MiB payload and32MiB bundle limits. Add a60-second packaging bound.
Never rerun extractors, retry GETs, clear failure records or overwrite outputs.
Return the four-member final bundle with separately embedded recovery/packaging
provenance. Original statuses, grades and failure records remain unchanged.

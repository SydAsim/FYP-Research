# Phase 8 candidate v3 — review index

**DRAFT. No approved freeze. No campaign executions.**

Read `docs/11_PHASE8_STUDY_DESIGN.md` first. This package proposes 500 new task configurations in 50 recipe clusters and 2,700 paired arm slots. It preserves the original evidence and validates the revised observable oracle independently of arm names.

## Review artifacts

| File | Purpose |
|---|---|
| `manifest.json` | Allocation, seed, equal budgets, eight unresolved decisions, null review/freeze fields |
| `input-review.csv` | Human-readable list of all 500 task configurations |
| `inputs.json` | Full input specifications, transcripts, provider faults and named hooks |
| `recipe-provenance.json` | 50 explicit shared recipe clusters |
| `planned-slots.json` | 2,700 slots; every status NOT_STARTED, every execution ID null |
| `analysis-not-started.json` | Empty planned-denominator report; not outcomes or observed failures |
| `validation/historical-import.json` | Offline import of 18 existing v2 traces, validation only |
| `validation/artificial-models.json` | Known artificial parameters, mixed/AFT fits, 40 cluster-bootstrap draws |
| `validation/design-matrix.json` | Covariate rank checks, no outcomes |
| `validation/successful-import.json` | One successful offline validation trace |
| `validation/expected-invalid-ack.json` | Deliberately invalid future ACK retained as UNKNOWN with diagnostic |
| `validation/expected-campaign-block.txt` | Expected refusal to start before review |
| `validation/unit-contract-tests.txt`, `scientific-tests.txt`, `ruff.txt`, `mypy.txt` | Validation logs |
| `historical-hashes-before.json`, `historical-hashes-after.json`, `historical-integrity.json` | Historical evidence SHA-256 checks |
| `source-candidate.zip`, `source-candidate-inventory.json` | Separate unapproved source snapshot; excludes secret `.env` |

## Decisions that prevent a freeze

1. Establish the sampling frame/estimand. Fifty purposive recipes are not proof of 500 independent scenarios.
2. Resolve clean utility assessment. Ten clean recipe units cannot establish the proposed five-percentage-point tolerance under the specified conservative bound, even with perfect ties.
3. Approve arm scope, primary endpoints, secondary family and multiplicity. Extending B0–B2 to all tasks changes the ledger to 3,000 slots.
4. Choose protocol-only conclusions or a separately preregistered real speech extension.
5. Approve booking/time-correction scope; cancellation claim semantics need a separate version.
6. Approve identifiable model covariates and censoring assumptions. Full bank design has rank 25 for 36 columns.
7. Qualify the live hooks and budgets on separate calibration inputs. Offline estimator validation does not establish live driver completeness.
8. Record explicit review decisions and a new immutable approved freeze. This candidate remains unfrozen.

**Ready for design review; not ready to freeze or run the campaign.**

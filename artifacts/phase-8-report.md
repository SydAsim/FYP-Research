# Phase 8 study-design preparation report

Date: 2026-10-04. **Review package complete. Campaign not started; Phase 8 evaluation not complete.**

## Scope implemented

Prepared candidate v3 using the revised observable instrument. Enumerated **500 new task configurations**, **50 recipe clusters**, and **2,700 primary execution slots**, all NOT_STARTED with null execution IDs. Proposed 100 clean / 200 hidden-commit / 100 playout / 100 other-boundary inputs. B3/P1/P2 share all 500 inputs; B0/B1/B2 share 400 inputs in their proposed secondary paired scope. The package specifies independent-unit assumptions, strata, arm profiles/order, endpoints, missingness, observation budgets, paired/cluster analysis, clean useful-task tolerance and synthetic-versus-real-speech limitations.

Integrated a strict offline evidence adapter with the revised arm-neutral oracle and planned-denominator analysis. Available baseline observations can support claims without P1/P2 receipts. Business state, forbidden effects, intent acceptance, publication/playback truth and evidence, stale exposure, final updates, explicit retraction and internal repair telemetry remain separate. Missing ACKs/records do not establish silence or completion. Invalid but identifiable evidence becomes UNKNOWN with retained diagnostics. Primary attempt one cannot be replaced by a favorable repetition.

Scientific dependencies use a separate environment; application dependencies and `uv.lock` are unchanged. No application controller/worker/provider behavior was changed. No new live experiment, model/API call, database mutation or migration was performed. **No paid API keys are needed for this preparation.**

## Files created

| Files | Invariant / role |
|---|---|
| `docs/11_PHASE8_STUDY_DESIGN.md` | Reviewable proposed research design, evidence limits and freeze blockers |
| `research/study/models.py`, `inputs.py` | Strict external intent/evidence contracts, 500 semantic specifications and cluster provenance |
| `research/study/oracle.py` | Revised independent observable grading; no arm-based business grading or receipt-only baseline requirement |
| `research/study/pipeline.py` | Exact fixture binding, retained invalid evidence, validation/campaign separation |
| `research/study/analysis.py` | Planned denominators, primary-attempt selection, exact pairing, missingness bounds, Holm, clustered sensitivities, KM/RMST |
| `research/study/statistical_models.py`, `requirements.txt` | Isolated Bayesian mixed model and right-censored AFT, rank/convergence checks, whole-cluster AFT bootstrap |
| `research/study/package.py`, `campaign.py` | DRAFT manifest, empty slot ledger and blocked start/ingestion |
| `research/study/validation.py`, `scientific_checks.py` | Offline historical integration and artificial known-parameter scientific checks |
| `research/study/integrity.py`, `__init__.py` | Historical hash verification and separate unapproved source candidate |
| `tests/unit/test_phase8_study.py` | Semantic uniqueness, equivalence, missingness, planned-unit math, blocked campaign and evidence checks |
| `research/fixtures/phase8_design_v3/inputs.json` | Separate candidate fixture version; historical fixtures unchanged |
| `artifacts/phase-8-study-design/v3/` | Full review catalogue, provenance, 2,700-slot ledger, diagnostics, logs and source snapshot |

**Migrations added: none.** Git currently reports the repository baseline as untracked; this report describes the scoped files created, not a committed diff.

## Validation evidence

| Check | Result |
|---|---|
| Default application unit + contract suite | **103 passed, 0 failed, 0 skipped**; four existing dependency/lifecycle deprecation warnings |
| Separate scientific checks | **5 passed, 0 failed, 0 skipped** |
| Revised oracle offline integration | **18/18** saved v2 PostgreSQL traces imported, **0** errors, **18/18** observable endpoint matches |
| Artificial scientific validation | 720 toy measurements, 30 recipe clusters, unrelated toy identities; not campaign executions |
| Artificial binary mixed model | Converged; P2 logit coefficient 1.370 against injected 1.300, approximate Bayesian VB output explicitly labeled |
| Artificial right-censored AFT | Converged; P2 log-time coefficient 0.292 against injected 0.350; 498 events / 720 observations |
| Artificial AFT recipe bootstrap | **40/40** fits converged, 0 failed; separate from the proposed 2,000 campaign sensitivity draws |
| Proposed bank covariate matrix | Minimal rank **6/6**; required full model **25/36**; extended with stratum **25/39** — review blocker, not silently fixed |
| Ruff | All checks passed on `apps packages research tests`, with `--no-cache` |
| Configured strict mypy | No issues in **130 source files** |
| Historical preservation | **415/415** before/after SHA-256 entries identical, 0 changed |
| Campaign guard | Expected `CampaignBlocked` before network/DB access; campaign ingestion also rejected |
| Campaign ledger | **0/2,700 executed**; all slots NOT_STARTED |

Relevant integration is offline ingestion of previously recorded independent simulator truth and ordinary provider/playback evidence. This does not demonstrate new live driver coverage for the proposed bank. Fresh PostgreSQL transaction tests were not necessary: application/database logic was not edited. No new statistical performance claim follows from these validation checks.

### Commands executed

From the repository root, PowerShell:

```powershell
.venv-study-design/Scripts/python.exe -m pip install -r research/study/requirements.txt
.venv/Scripts/python.exe -m pytest tests/unit tests/contract -q
.venv-study-design/Scripts/python.exe -m pytest research/study/scientific_checks.py -q
.venv-study-design/Scripts/python.exe -m research.study.package
.venv-study-design/Scripts/python.exe -m research.study.validation
.venv-study-design/Scripts/python.exe -m research.study.campaign --start
.venv/Scripts/python.exe -m ruff check apps packages research tests --no-cache
.venv/Scripts/python.exe -m mypy apps packages research
.venv-study-design/Scripts/python.exe -m pip freeze
.venv-study-design/Scripts/python.exe -m research.study.integrity
```

Ruff formatting/fixes were scoped to new study files only. The campaign start command intentionally failed and is retained in `validation/expected-campaign-block.txt`. Study setup linked the existing main application packages into the isolated environment with a UTF-8 `.pth`; scientific packages take precedence, and their combined inventory is saved.

Preparation diagnostics included a Windows default-encoding failure when writing the Japanese workspace path (fixed with UTF-8), a historical importer that initially included the directory's manifest as a trace (restricted to the 18 E1–E6 files), strict-type errors and long-line lint errors. These are preparation/debug failures, not failed campaign attempts. Their causes and fixes are documented here; `format-precheck.txt` and `ruff-before-final-fix.txt` retain lint diagnostics. The final validation gates above pass.

### Successful and expected failure traces

- Successful offline trace: [successful-import.json](phase-8-study-design/v3/validation/successful-import.json), derived from historical E1/B3. Exact independent final state and supported completed update; no import error. The original is unchanged.
- Expected evidence failure: [expected-invalid-ack.json](phase-8-study-design/v3/validation/expected-invalid-ack.json), explicitly mutated to contain a future ACK. Raw invalid record and diagnostic retained, correction outcome UNKNOWN, no invented completion.
- Expected start refusal: [expected-campaign-block.txt](phase-8-study-design/v3/validation/expected-campaign-block.txt).

All three are validation artifacts, not new Phase 8 application executions.

## Known limitations and review decisions

1. **Sampling:** 500 distinct configurations do not establish 500 independent scenarios. The proposed 50 purposive recipe clusters/member-zero representatives need an approved finite-bank estimand or a defensible new sampling frame. Repetitions cannot resolve this.
2. **Clean tolerance:** proposed absolute five-percentage-point non-inferiority margin is a utility choice awaiting review. Ten independent candidate clean units cannot pass the conservative bound even with perfect ties: best-case lower bound **−30.85 percentage points**. At least **72 truly independent clean units** are needed in that perfect case, with no guarantee when discordance exists. Redraw/reallocate or narrow the conclusion; do not relax the margin after outcomes.
3. **Comparisons/multiplicity:** review the P2–B3 co-primary family, secondary contrasts and B0–B2 exclusion from playout-only scope. All-six-arm coverage would require 3,000 slots/new candidate version.
4. **Speech:** all candidate inputs are typed/tone/scripted-ACK protocol proxies. They support protocol protection tests, not actual spoken-content exposure, human understanding, end-to-end microphone accuracy or production latency. Real speech requires intelligible hashed audio, measured alignment, calibrated playback evidence and a separate approved sampling plan.
5. **Domain:** standalone cancellation claims are outside this instrument's validated speech semantics. Compensating cancellation effects remain recorded.
6. **Models:** full covariates are rank deficient. Approve an identifiable parameterization and Bayesian/frequentist reporting scope. Informative censoring/terminal handoff/lost ACK limit KM/AFT inference; completed-pair latency is explicitly selection conditional. Missing time is never zero.
7. **Drivers:** proposed named hooks, observation-window completeness and equal budgets need live qualification on separate calibration inputs. Estimator validation and 18 historical imports are insufficient to claim every proposed recipe can run unattended.
8. **Freeze:** no reviewer receipt, approved fixture/source/analysis/dependency freeze or qualified campaign runner has been created. The candidate archive is explicitly unapproved.

No conflict with executable application contracts required choosing alternative application behavior. Research design choices above are pending, particularly independence, clean margin/allocation, comparison scope and model parameterization. Historical reports were not relabeled as revised campaign measurements.

## Deferred work and readiness verdict

Review the candidate; resolve D1–D8; create a new version for agreed sampling/design changes; qualify live drivers on separate inputs; freeze approved source, bank, grading/analysis, dependencies and configurations; install/verify the freeze integrity gate. Actual speech evidence needs its own declared extension. The 500-case campaign and Phase 8 conclusions remain deferred.

**Ready for study-design review. Not ready to freeze or start the Phase 8 campaign. Zero campaign executions.**

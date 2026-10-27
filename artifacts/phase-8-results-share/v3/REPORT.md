# Phase 8 interim pooled results — incomplete study

Snapshot: 2026-10-18T14:15:35.076287+00:00 (18 October 2026, 19:15 Pakistan time).
735/1500 originals BACKED_UP; 245 distinct inputs; 245 complete B3/P1/P2 sets.
All 735 saved grades were available in this snapshot; verification failures: 0.

These are original execution counts, not independent callers. Each input has three paired arm executions. This review reads stored grades only; it does not rerun an oracle, modify an outcome, apply a historical timing sidecar, fit a model, resample, rank arms or change scheduling.

## Observed pooled outcomes

| Recorded endpoint | TRUE / eligible executions | Descriptive percentage |
|---|---:|---:|
| Correct final business state | 672/735 | 91.4% |
| Correction success (correction executions only) | 234/297 | 78.8% |
| Clean useful-task success (clean executions only) | 438/438 | 100.0% |
| Correct final supported update | 597/735 | 81.2% |

Other stored categories remain explicit:

- **forbidden_effect**: FALSE=735.
- **unsupported_exposed_claim**: FALSE=708, TRUE=2, UNKNOWN=25.
- **incompatible_stale_exposure**: FALSE=710, UNKNOWN=25.
- **correct_final_update**: FALSE=134, TRUE=597, UNKNOWN=4.
- **corrective_delivery_after_challenge**: NOT_APPLICABLE=681, TRUE=54.
- **complete_corrective_communication**: FALSE=28, NOT_APPLICABLE=681, TRUE=18, UNKNOWN=8.
- **explicit_retraction**: FALSE=30, NOT_APPLICABLE=679, TRUE=18, UNKNOWN=8.

Raw status (separate from business/speech grades): {"COMPLETED": 660, "FAILED": 75}.
Stored timing censor reasons, unchanged: {"INFRASTRUCTURE_FAILURE": 4, "NO_SUPPORTED_COMPLETION": 134, "None": 597}.

## What this supports

Observed input coverage is 146/300 CLEAN, 51/100 HIDDEN_COMMIT, 31/60 PLAYOUT and 17/40 OTHER_BOUNDARY. Pooled percentages reflect this incomplete mixture, not the final frozen weighted co-primary effects. All 245 observed inputs have three recorded original arm grades; that is not 735 independent inputs.

Clean operation looks encouraging in the observed subset, and no forbidden effect was recorded. Faulted runs show substantial limits: incorrect final business states, missing supported final updates, two recorded unsupported decisive exposures and unresolved exposure grades. A backed-up execution is evidence retained, not a passed research outcome.

The corrective-delivery challenge distinguishes an ordinary final update from full corrective communication: receiving a corrected statement does not establish explicit withdrawal of previously invalid content. TRUE/FALSE/UNKNOWN are retained separately. Internal repair records alone do not earn external delivery credit.

The data are useful for a research report because failures and limits are visible. They do not yet demonstrate that P1/P2 outperform the competent baseline, that the study will meet its confirmatory gates, or that a paper is publishable. No adverse result is excluded, and no favorable stopping rule is introduced. The complete frozen comparison and missingness analyses remain for the final study.

The known shared revision-only claim-selection limitation remains part of the frozen studied applications. This descriptive review does not repair that behavior or attribute each adverse grade to it. The pooled family locators show where to conduct the final mechanism review; they do not, by themselves, establish the cause of each adverse outcome. Raw FAILED driver statuses, stored infrastructure censor labels and accepted separate timing sidecars remain distinct and unchanged.

## Integrity and scope

Downloaded compressed results SHA-256: `99a105636e344f811325e71bbd0865f25c54d86f54267f97c811cf2567d89c48` (157249 bytes).
Uncompressed JSON SHA-256: `1a669f90ef6ceea07adca474249ed25d06baae99aac3bd800da5ceba3f2d01b7`.
Every included export matched its sealed slot-ledger hash or the retained exact-145 manifest commitment. Every backup receipt matched the consistent master snapshot and its pinned version reference. This task reused prior archive qualification; it did **not** download or freshly verify every full archive or S3 object. The result is a verified compact derivative, not a replacement evidence archive.
Saved voice-evidence labels: {"SCRIPTED_TONE_SEMANTIC_PROXY": 735}. These are scripted tone/ACK semantic protocol proxies; they do not establish intelligible real speech, human hearing or comprehension.
0 executions recorded collection errors; 0 recorded oracle failures. Missing stored evidence would remain unavailable, never be filled with success or silence.

The earlier v2 diagnostic extractor failed its transfer-size bound before publishing a result. That script, request, response and failure are preserved. The narrower v3 transfer completed with finite bounded requests. No application, frozen code, campaign ledger, pause, timing, grade or research scenario was changed.

## Files

- `execution-results.csv`: one row per backed-up original, identities, saved endpoint values and export SHA-256.
- `saved-results.json.gz` / `saved-results.json`: compact derivative with pinned references, pooled counts, original timing categories and snapshot commitments.
- `verification.json`, `download-manifest.json` and request/response files: retained transfer and verification evidence.
- `descriptive-diagnostics.json`: pooled family counts and adverse/failure record locators for later review; no rankings.

Recommendation: retain the unchanged campaign and finish its planned observation/backup sequence while guards pass. Interpret final paired effects, clean tolerance and unknown bounds only under the frozen analysis; do not repair a studied arm or tune the experiment based on this interim view.

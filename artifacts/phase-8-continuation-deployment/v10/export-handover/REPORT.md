# Exact145 export handover — resolved; readiness blocked

## Result

All 145 originals were verified and materialized as `run/exports/0001/export.json` through `0145/export.json`. The unchanged frozen closed145 validator passed. The continuation was **not launched**: live readiness failed at `host_checks-final.py:78`, `CAMPAIGN_PROJECTED_DISK_HEADROOM_STOP`.

The host `i-057344e5372faf62f` is **STOPPED**, independently read back in [safe-stop-state2-result.json](safe-stop-state2-result.json). Its owned preparation guard was disabled and read back only after stopped-state verification. The absolute AWS guard remains the previously verified 25 October guard. No evidence or root storage was deleted.

Boundary remains **145 BACKED_UP / 1,355 PLANNED / zero active**. Next remains **146 / P2 / attempt1 / 01a11705-11f1-772d-8190-c43552871801**. Canonical all-row hash is `5e5be74f430a190c9f6ee70198b711fbb3851aa30d123da11d9f778dca9075bd`. Original durable pause hash remains `28ea1aec440408f1d9e467ece07e54c39485d14c29434dc79b35b9460919d519`. All original export bytes, raw statuses, grades, receipt references and pending order were preserved.

## Frozen authority and external-only difference

- Reused package: `bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c`.
- Reused archive: `212269264d45ac8bd6637c2ca0ca5e09c951d354cb445c9bf7a16c6ba2d0ba37`.
- Verified all **3,441** installed inventory files and frozen signed authority. No archive upload, source bootstrap, application change or refreeze.
- External `core.py` verifies retained archive/member commitments or frozen closed120 member commitments plus original pinned receipts, checks every export identity, rejects conflicts and performs atomic no-replace exact-byte publication.
- External `handover.py` records one resumable deadline, stage cap and checkpoints; verifies every one of 145 records before adoption; measures the unchanged frozen metadata copier; retains compact per-record provenance in restart-history. There is no driver invocation or result reconstruction.
- External payload hashes are in [final-code-binding.json](final-code-binding.json); provenance SHA-256 is `e575ee7413017464fa86c0f7e8806aabbbd3a9f07d58250c15bde2cbb49f48fd`.
- **0 pinned archive GETs** were necessary. Required records were found in exact retained local archives/histories. Every chosen export was bound to its original receipt, archive or frozen member commitment, and execution identity. This does not infer original cloud-archive bytes from an export alone.

## Measured storage before adoption

| Measurement | Value |
|---|---:|
| Raw export view | 200,673,073 bytes |
| Stage logical bytes | 958,673,196 |
| Stage unique allocated bytes | 761,659,392 |
| Baseline compressed metadata | 37,241,986 |
| Metadata with compact provenance | 37,304,507 |
| Positive measured compressed increment | 62,521 |
| Increment over accepted historical reference used in full1500 projection | 110,424 per archive |
| Future cloud + 1-GiB reservation | 78.929602 GiB |
| Future dedicated local backup + 1-GiB reservation | 79.186318 GiB |
| Current logical working run | 934,182,099 bytes |
| Required live free disk | 145,670,462,448 bytes (135.666190 GiB) |
| Actual preserved free disk sample | 142,678,020,096 bytes (132.879261 GiB) |
| Shortfall | 2,992,442,352 bytes (2.786929 GiB) |

Measured tar membership proves the top-level export view is excluded from the frozen master copier, while its compact provenance is included. Original archives remain the outcome recovery source. Raw history was not copied into restart-history again. Hard links were counted logically and allocated blocks measured independently; their archival cost was not assumed to be zero. Both gzip measurement archives are retained, labelled measurements rather than PRELAUNCH/COMPLETE receipts. Conservative full1500 growth, existing all-version inventory, measured duplicate local archives and future independent readback copies remain included. The 80-GiB cloud/local caps passed this measurement; the independent **working-disk headroom gate failed**.

## Checks and deployment progression

- Fixed pinned-Linux offline set: **8 passed in 0.044 seconds**; one history-commitment addendum **passed in 0.009 seconds**. No research scenarios, pilot, application stacks or observation windows. Completed qualification was reused.
- Latest Linux-target strict type check passed for the two external source files. Initial missing-SDK/platform and variable-type check failures are retained.
- Read-only effects inspection verified exact retained pause and identity boundary; old campaign was inactive. The autostarted owned v9 watchdog was inspected and quiesced. Both units had zero PID/inactive before handover.
- Installed-source/frozen-authority verification passed.
- Handover passed in **56.329 seconds**, including all145/frozen validator, measurement and exact-byte adoption.
- Metadata binding advanced to v10 while preserving v9 config, readiness and proofs in `restart-history/v9-before-v10`. A new paired **boot** anchor passed the unchanged clock guard; it did not reset the original elapsed history or stop deadline. This anchor belongs to the now-stopped boot and cannot be blindly reused after another boot.
- Live checker reached the disk gate after its source/dependency/image/permissions/port and all145 local-archive/pinned-S3 checks. It did not emit a PASS readiness record. Its original full traceback is retained in [live-checks-status3-result.json](live-checks-status3-result.json).
- Two small failure-preservation attempts also failed (wrong notice column; 4-MiB record bound). Neither wrote ledger/pause or a preservation file. The corrected compact record preserved consistent rows, notice hash/count, measurements and inactive units. All unsuccessful commands and responses remain retained.
- No new PRELAUNCH, genuine readiness, launch receipt or COMPLETE backup was created. No pause release or admission occurred. No later deployment gate was claimed to pass.

## Preservation and feasibility

Host preservation record: `/var/lib/p8-continuation-v10/deployment/export-handover-failed-readiness-preservation.json`, SHA-256 `d119142e3ea764b2d5e96e9e347fb773aad52aee79f447f0ec354d0c496613a9`. Its small returned diagnostic fields are retained in [preserve-failed-readiness-compact-status1-result.json](preserve-failed-readiness-compact-status1-result.json). Original pinned S3 backups and local outcome copies were not overwritten. This record is retained on the stopped root and its returned measurements locally; it is not a new independently backed-up campaign receipt.

Refreshed arithmetic at 2026-10-12T20:05:58.297231+00:00 preserves the accepted accounting and **262.316422 hours remaining + 2.5 hours preparation/shutdown + 24 hours uncertainty**. Conservative completion forecast **US$66.0275**, uncertainty forecast **US$69.5253**, full-deadline forecast **US$72.2201**. Uncertainty completion is 2026-10-24T20:54:57.416056+00:00, before the unchanged absolute stop/cutoff. The fresh preboot FREE-plan credit read was US$107.81. These forecasts include elapsed stopped/running history, full 80-GiB storage allowance and reviewed reserves; they are **not actual billed spending**. No assumptions were lowered to pass. Time/cost remain feasible; live disk capacity does not meet its reviewed gate.

## Minimum next requirement

Resolve the demonstrated **2.79-GiB minimum working-disk headroom shortfall with margin**, preserving all evidence and existing reservations. Do not lower the reviewed threshold solely to pass or blindly rerun preparation: metadata is already bound to v10, and a future boot requires an explicitly preserved fresh boot-anchor procedure. Then complete a fresh independently protected preparation and all still-unperformed backup/readiness/timer/launch gates. No automatic restart or additional preparation attempt was performed here.

Absolute stop remains **2026-10-25T15:24:23.810674Z**; 432-hour anchor, US$70 admission / US$75 total limits, 80-GiB caps and study remain unchanged. Root-retention decision is due **2026-10-27T15:24:23.810674Z**; no deletion is authorized.

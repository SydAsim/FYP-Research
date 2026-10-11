# Phase 8.5 complete v4 continuation — actual deployment

## Actual admission

The accepted complete v4 package was verified, accepted, frozen against its parent chain, deployed to a fresh Sydney host, and launched through its readiness gates. This is an actual admission, not merely authorization.

- Run: `p85-01a116f7-3b82-7a79-8653-3aee62dc99e9`.
- Host: `i-057344e5372faf62f`, `ap-southeast-2`, m7i-flex.large.
- New retained encrypted 160-GiB gp3 root: `vol-09dbb42bbf607f5de`; DeleteOnTermination=false. Its deletion is not authorized.
- Campaign service started: **2026-10-08 20:04:25 UTC** / **9 October, 01:04:25 Pakistan time**.
- Sequence **39**, case `p8v4-0240`, **B3**, attempt **1**, execution `01a11705-11f0-73c0-af15-dd9f1d590b08` admitted **2026-10-08T20:04:32.331920Z** / **9 October, 01:04:32 Pakistan time**.
- Its original 600-second observation deadline: **2026-10-08T20:14:42.799509Z**. No window was shortened or replayed.
- Admission evidence snapshot: **38 BACKED_UP, 1 RUNNING, 1,461 PLANNED**, no pause. Thus 1,462 executions remain unfinished, including the active one.
- Absolute stop remains **2026-10-22T15:24:23.810674Z** / **22 October, 20:24:23.810674 Pakistan time**. The original operational clock was not reset.

## Acceptance, freeze and provenance

- Accepted package: `a869745a6c1807e4f2427cc9597e5d85f41a2b4eb2aa4aa8abd4bdb8cc9b7306`.
- Archive SHA-256: `7044595739003670be74669eea70c50b0c99ff9a537cf8fde4587405182cc1c9`.
- New freeze manifest: `cf6d4ff9e6e8916a8204c420076676fe9d9c746545ad686357b4e65a8f78710c`.
- Immediate parent: accepted v3 freeze `49ec78e719d9d28e017f62e6a40dd69cc236a45c5406d5be1a209ef59b9d2c86`; original receipt chain and historical ancestors were verified.
- Actual-host launch receipt: `367e35c28028b9fdf8c27a64835078eb3455e23d2bf3270edacff70ee2c9e404`.
- Actual-host readiness SHA-256: `f22479a108d223f7b65837de899f131438c2b11c671621916760eea343eb33df`.
- All **2,115** frozen files and **2,107** candidate source files verified. Historical verification covered 4,489 protected files, 1,788 parent source members, 1,796 v3 frozen members and 37 prior local correction members.
- No application, runner, oracle, analysis, fixture, migration or frozen configuration file was edited during deployment. Operational preparation scripts and receipts are separate artifacts in this directory.

## Readiness and backups

All 16 accepted readiness checks passed before admission: source/runtime and dependency hashes; exact 1,500-identity import; 38 closed originals and 1,462 planned; original policy; no replay; S3 permissions/versioning/cap; resource capacity; owner permissions; no inbound access; prelaunch backup; absolute/preparation timers; and old-disk disposition.

The fresh host installed pinned CPython 3.12.13 through the accepted download catalog/archive checksum, pinned uv and PostgreSQL/Redis image digests. Actual installed versions and **13,629 dependency RECORD file hashes** were verified. One empty diagnostic service stack returned HTTP 200 from API, voice, worker and simulator health routes; its logs and database dumps were retained and its owned resources removed. No research driver was called by preparation.

Measured RAM available with empty services: 7,078,969,344 bytes. Immediately before admission: 7,338,201,088 bytes available RAM and 159,871,975,424 bytes free disk, exceeding the unchanged 2-GiB / 20-GiB admission thresholds. Active thresholds remain 1 GiB / 10 GiB. Cloud all-version evidence was 278,862,782 bytes before admission, under 30 GiB; conservative reviewed end projection remains approximately 12 GB.

All 38 original complete archives and their exact S3 versions/checksums were verified independently of the imported metadata. The authoritative stopped-boundary archive was also verified. Raw original statuses, grades, exports, historical notices and separately accepted timing sidecars remain unchanged; no old application database was restored.

Two new versioned metadata backups were uploaded, verified, downloaded through the version-pinned bounded postflight path, extracted to short paths and checked against manifests and the exact imported boundary:

| Backup | SHA-256 | S3 version |
|---|---|---|
| Pre-readiness handover | `d80aa912ff4126e9e1c37e1854db99cc0977c0b82be3ee8682846e45bb1eb9de` | `JAiUXNh3PnKM47JN.FsxYGbISz1fZQZY` |
| Authorized prelaunch, including actual launch/readiness controls | `e089034afc560e30e135ed610ddbadcbbbf9d12ad65c165ec7e9b27571b0c7bf` | `sD.zMPeoOhh6h0IIrOPA0Rg_vsRMGt3N` |

Bucket: `fyp-p82-20261005-018da1d6-803656589923`. Both use the unchanged campaign export prefix. These are metadata backups; they reference the separately retained 38 complete per-execution PostgreSQL backups. Sequence 39 had not completed or received its final verified per-slot backup in the admission snapshot. The unchanged runner must verify that backup before admitting the next slot.

## Feasibility and controls

Current official price reads confirmed compute $0.1197/hour, public IPv4 $0.005/hour, gp3 $0.096/GiB-month and conservative S3 $0.025/GiB-month. The project remains FREE/ACTIVE with $118.14 credits reported. No paid plan or model/speech services were added.

The full reviewed remaining planning allowance was retained: **283.03070761014686 hours**, scaled solely for the 36 newly completed originals. Before provisioning, adding two hours for preparation and 30 minutes for shutdown gave a conservative original-clock estimate **$53.761695**, and separately accounted resources **$52.598551**, including previous compute, retained disks/storage, request allowance and the $1.25 reserve. Both fit the $55 guard and $65 total limit.

After actual preparation, immediately before admission the same full remaining allowance plus 30-minute shutdown margin projected completion **20 October 2026, 15:06:13.996632 UTC**, conservative committed cost **$53.509945**. The allowance was not reduced to obtain a pass. Runtime is not guaranteed: initial throughput evidence covers 13 inputs, and later recipes can take longer. Billing delays and retention mean the estimate is not an instantaneous invoice ceiling. Failed resource, evidence, cost or protocol gates still stop admissions; limits cannot automatically increase.

Campaign and watchdog services are active. Both independent absolute-stop timers are active at the original deadline; the systemd calendar uses 15:24:23 UTC, conservatively truncating the fractional second. The two-hour relative and absolute preparation timers were verified and disabled only after successful campaign service activation. The watchdog reads the ledger through the accepted snapshot correction.

Pause/shutdown behaviour is unchanged. A protocol pause stops admissions and retains required collection/evidence; **it does not immediately shut down compute**. The reviewed bounded operator drain/backup/stop procedure applies, with eight reconciliation attempts and 30 drain passes, not seconds. Successful queue completion verifies its final backup and requests host shutdown. Independent absolute timers remain the fallback. The new root disk remains retained after stop; its deletion requires separate authority.

After the fresh handover and independent local/S3 evidence checks passed, only old stopped host `i-002b63326e1566005` and its owned root `vol-04fa91b4840804295` were removed, within the reviewed retention deadline. No S3 or local evidence was deleted. The new root was untouched.

## Retained operational failures

1. The initial preparation helper incorrectly used `final_backup` before `continuation-readiness.json` existed. It failed before upload/admission. Its partial directory remains; a durable preparation notice was added. The already reviewed pre-readiness snapshot procedure subsequently passed. No frozen code or policy was changed.
2. A Windows-generated activation wrapper had CRLF line endings. Bash rejected its first line before any receipt/control action. The failed script and SSM result remain; a separate LF-formatted copy, using the previously qualified transfer correction, succeeded.
3. Two read-only Windows CLI polls could not encode a systemd arrow character. Both unsuccessful results remain. A UTF-8 poll read the same successful remote operation; activation was not replayed.

These preparation failures do not replace any main outcome. Passing readiness does not guarantee an error-free campaign. Unexpected main responses, genuine defects, evidence corruption and failed backup gates must still pause according to the accepted v4 policy.

The failed initial backup directory, empty-host diagnostic logs/dumps and operational preparation files were additionally retained in S3 and verified by checksum and full GET readback: SHA-256 `611334d261aa5c1fc5955fdbb4b5ccd3c8a7814cf3ff318e7dfb897f142e50b8`, version `vmDKaOrSiiT5Hq5kwDorSsuNQuR8X4oo`, 832,489 bytes. The original files remain on the new retained disk. No private owner key was included.

## Check progress independently

From a normal PowerShell terminal with AWS CLI and the configured `fyp-research` profile, in the repository directory:

```powershell
& .\artifacts\phase-8-continuation-deployment\v4\Check-Progress.ps1
```

This reports the actual host, service state, counts, current identity/deadline and pause reason. It never restarts the host, admits a slot or clears a pause. The standalone systemd service performs collection, grading, verified backup and saved-order admission independently of an active Codex conversation. Closing the local terminal/chat does not stop it.

The exact normal-terminal command was exercised successfully. At 2026-10-08T20:06:58.912321Z it reported sequence 39 RUNNING, the same original observation deadline, 38 BACKED_UP / 1,461 PLANNED, active campaign/watchdog/absolute timers and no pause. Its retained collector output showed continuing collection through 25 polls; this is protocol collection evidence, not a completed outcome or human speech-comprehension claim.

Evidence: `freeze-verification.json` in the separate v4 freeze directory; `final-verification.json`, `actual-continuation-start.json`, all immutable AWS/SSM request/results, `terminal-progress-qualification.txt`, backup proofs and the deployment evidence inventory in this directory.

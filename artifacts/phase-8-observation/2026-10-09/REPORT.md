# Phase 8 paused-host preservation — 9 October 2026

## Result

**STOPPED, evidence preserved, admissions paused.** Instance `i-057344e5372faf62f` was verified stopped at **2026-10-09 09:34:32.955162 UTC** (14:34:32 Pakistan time). Its encrypted 160-GiB root `vol-09dbb42bbf607f5de` remains attached and retained, with DeleteOnTermination=false. No evidence or root storage was deleted.

The unchanged boundary is **82 BACKED_UP / 1,418 PLANNED / zero active**. All 1,500 identities and their saved order match the retained identity inventory. Next remains sequence 83, B3, attempt 1, execution `01a11705-11f1-792b-ae1e-36bfc6773842`; it was not admitted.

## Earliest trigger and exact error

At **2026-10-09T03:39:42.848340Z**, the watchdog recorded `PROTOCOL_STOP`, type **ConnectionClosedError**, detail:

> Connection was closed before we received a valid response from endpoint URL: "https://fyp-p82-20261005-018da1d6-803656589923.s3.ap-southeast-2.amazonaws.com/?versions&prefix=exports%2Fphase8%2Fp85-01a116f7-3b82-7a79-8653-3aee62dc99e9%2F&encoding-type=url".

This was the S3 **ListObjectVersions** inventory request used to measure evidence storage. It was not an application refusal, an outcome-grade failure, or a reported SQLite corruption. The evidence establishes a closed transport connection; it does not establish whether AWS, the network or another transport component caused it. No response body or HTTP status was recorded for this failed request.

In the accepted frozen source:

- `artifacts/phase-8-runner-amendment/v4-complete/storage.py:82–90`: `S3Cloud.inventory()` paginates `list_object_versions`; client configuration at lines 68–72 sets connect/read timeouts and `total_max_attempts=1`.
- `runner.py:769–772`: the watchdog evaluates `cloud.inventory()` before entering `watchdog_tick()`. Consequently this exception bypasses the inner watchdog checks at lines 592–598.
- `runner.py:786–791`: the outer exception handler durably records `PROTOCOL_STOP`, pauses admissions and exits with status 1.
- `controls.py:373–374`: a paused campaign refuses new admission with `PAUSED_ADMISSIONS`.

The three local source files match their accepted v4 inventory hashes. This inspection did not requalify or alter runtime behaviour.

## Event sequence

All following times are UTC on 9 October:

| Time | Recorded event |
|---|---|
| 03:31:45.394611 | Slot 82, P2, was admitted. |
| 03:31:57.566308 | Last external request anchor; its unchanged 600-second deadline was 03:41:57.566308. |
| 03:32:00.825181 | The scenario driver finished. |
| 03:39:42.848340 | Watchdog S3 inventory connection closed; first PROTOCOL_STOP notice. |
| 03:39:42.854299 | STOP_NEW_ADMISSIONS recorded; pause file persisted at 03:39:42.861710. |
| 03:39:42.960498 | Watchdog exited unsuccessfully. |
| 03:39:48 | Existing systemd/watchdog recovery occurred: campaign parent stopped; detached collection continued; systemd started the units again. These are historical events, not actions taken during this inspection. |
| 03:41:57.566490 | Slot 82's last recorded collection poll, after its original deadline. |
| 03:42:02.498204 | Owned application services were quiesced before backup. |
| 03:42:07.890328 | Slot 82's versioned cloud backup was verified. |
| 03:42:12.530769 | Journal printed VERIFIED BACKUP 82 / 1500. |
| 03:42:17.641954 | Next admission encountered PAUSED_ADMISSIONS. A secondary PROTOCOL_STOP was recorded; the campaign then exited unsuccessfully. |

Slot 82's retained raw export status is **COMPLETED**, with no recorded driver error, collection error, permissive-response error or oracle failure. Its final export finished at 03:41:58.340210. The campaign's failed service state is distinct from that research execution's recorded status. No grades were recalculated or replaced. Scripted tone/playback evidence remains synthetic protocol evidence.

## Preservation and verification

Preservation used a read-only SQLite connection with explicit BEGIN, deriving rows, notices and a master SQLite backup from the same snapshot. Both the remote and downloaded copies pass SQLite integrity checks. The notice hash chain validates, transition/row comparisons have no mismatches, and every saved identity/order matches. The pause bytes and historical import pause were copied without clearing them.

All **82** existing full per-slot archives were hash/member verified locally on the host, and their pinned S3 object versions were independently verified for size, SHA-256 metadata and checksum. Their backup receipt hashes match the master ledger. Complete archives remain on retained root storage and S3; the new inspection bundle is supplementary preservation, not a replacement for those database-bearing backups.

The supplemental bundle preserves the consistent master snapshot, all 82 exports/backup receipts/version references, notices, pause, binding/clock/handover records, complete campaign/watchdog journal, process/container state, and detailed raw slot folders for slots 79–82. No live owned application process remained. Campaign MainPID was zero; watchdog was still running before the explicit host stop.

Independent S3 preservation copy:

- Bucket: `fyp-p82-20261005-018da1d6-803656589923`
- Key: `exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/observations/a51a9ee4274de714c73a338de6905e846021ecb65143b936af8ddad5f0178fd6.tar.gz`
- Version: `G5ADuMNUUko.W7UqyBFXtP1WIPJUOqBz`
- SHA-256: `a51a9ee4274de714c73a338de6905e846021ecb65143b936af8ddad5f0178fd6`
- Size: 13,743,005 bytes; independently downloaded to `E:/FYP Project/p8-observation-20261009-1/evidence.tar.gz`; all **763** manifest file hashes verified after safe short-path extraction.

Slot 82's full backup remains separately pinned:

- SHA-256: `0ba54e3352a761ec2e68b24c266fe3f90ae9faffe60e82f133c9cf909d6b75a6`
- Version: `J6ASv81MUK6orQTmkpsGll00puvy6diC`
- Size: 8,335,773 bytes. See the preserved receipt and `backup-verification.json` for all 82 references.

The initial quick SSM journal output was truncated by SSM's output cap. That response was retained. A compact read and the full independently downloaded journal supplied the missing detail; no research execution was rerun.

## Safe shutdown and retention

After preservation/readback passed, ownership and root-retention settings were checked. The authorized EC2 stop request was recorded at **2026-10-09T09:33:51.252814Z**. AWS confirmed stopped at **09:34:32.955162Z**; a separate volume query confirmed the encrypted retained root remains attached. No service was restarted, pause cleared, execution admitted, original replayed, frozen code changed or evidence/root deleted during this work.

The reviewed 48-hour stopped-disk retention decision is due **no later than 2026-10-11T09:33:51.252814Z**, or **11 October 2026, 14:33:51 Pakistan time**, anchored conservatively to the earliest stop request. Stopping compute does not eliminate root/S3 retention charges; deletion is not authorized by this request. Escalate for a retention decision before that deadline; do not infer permission to delete.

The original campaign deadline remains **22 October 2026, 15:24:23.810674 UTC**. Neither the operational clock nor spending limits were reset. No deployment, fix, freeze or launch is included in this task.

## Evidence records

- `remote-observation-result.json`, `evidence-readback.json`, `local-snapshot-validation.json`
- `trigger-detail-status1-result.json` and downloaded `stop-notices.json` / `stop-journal.log`
- Downloaded `campaign.sqlite3`, `ledger-read-only.json`, `backup-verification.json`, and `pause.json`
- `observation-stop-host-request.json` / `observation-stop-host-result.json`
- `observation-poststop-host-result.json` / `observation-poststop-root-result.json`
- `stopped-state.json` and `retention-clock.json`

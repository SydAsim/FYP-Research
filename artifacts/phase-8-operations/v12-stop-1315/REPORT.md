# Credential-discovery recovery at the closed-1315 boundary

**PASS: actual guarded continuation, independently verified.**

## Actual state

Sequence **1316/B3/attempt1**, case **p8v4-0470**, execution **01a11705-11f4-7875-b6f4-62729851bd64**, was admitted at **2026-10-23T19:42:07.134315+00:00**, or **2026-10-24T00:42:07.134315+05:00 Pakistan time**. At the postlaunch read: **1315 BACKED_UP /1 RUNNING /184 PLANNED**, no pause, campaign PID30373 and watchdog PID30368 active/running. The collector began at 2026-10-23T19:42:47.215669+00:00. Admission and a running collector are not claims about the eventual oracle grade.

Host **i-057344e5372faf62f** is verified RUNNING on the same retained root and boot. No boot, replacement infrastructure, filesystem expansion, dependency installation or application change was needed. The standalone service continues without this chat. Existing progress script remains valid.

## Demonstrated cause and limits of diagnosis

The first triggering notice was InventoryUnavailable at **2026-10-23T15:14:03.137773Z**, wrapping NoCredentialsError from signing list_object_versions. The inventory subprocess could not obtain credentials; no S3 request could be signed. This is not evidence of expired credentials or an IAM denial. Later PAUSED_ADMISSIONS was secondary. Sequence1315 nevertheless finished the full observation window, exported and received a verified versioned backup.

Read-only inspection established: IMDSv2 is required/enabled, the expected instance role is attached and reachable, the owned service environment contained no static AWS credentials or metadata-disabling setting, and a fresh complete all-version inventory succeeded on the same host. The qualified SDK defaults were one second and one metadata attempt. Historical logs do not identify which IMDS request failed or establish its network cause; the supported diagnosis is transient credential-discovery unavailability, with that transport-level cause unresolved.

## Narrow external configuration repair

Added `/etc/systemd/system/fyp-phase8-campaign.service.d/75-fyp-imds-discovery.conf` and the equivalent watchdog drop-in:

```ini
[Service]
Environment=AWS_METADATA_SERVICE_TIMEOUT=3 AWS_METADATA_SERVICE_NUM_ATTEMPTS=3
```

Both actual service processes were checked for these values. These settings affect credential discovery only. Frozen source, shared S3 request retries, upload behaviour, appointment writes, refusal classification, B3/P1/P2 behaviour, claim selection, fixtures, endpoints, oracle, grades, analysis, saved order and600-second windows remain unchanged. Missing credentials after bounded discovery, incomplete inventory, genuine errors and failed resource/evidence guards still stop admissions. This does not guarantee the absence of future external failures.

Five offline controls on the exact retained Linux3.12.13 interpreter passed in0.608 seconds: SDK defaults; override parsing; metadata timeout then success; finite exhaustion; unchanged inventory failure on absent credentials. No AWS calls, scenarios, live application stack, pilot or observation windows were used for these controls. Python binary SHA-256021044895e95be79dc2f110367607e684119afbc8ce75f6f0eec94844e0acec7 was verified. Existing qualification was reused.

## Retained unsuccessful release and external correction

My first release wrapper preserved/moved the pause file but omitted the durable `RESUME_SAVED_ORDER` event required by frozen controls.py:390–396. The campaign correctly stopped at **2026-10-23T19:35:06.700118Z** with DURABLE_PAUSE_REQUIRES_REVIEW. No slot1316 directory, driver or admission existed; all185 pending identities stayed PLANNED. The failed wrapper and all request/result records remain unchanged.

The separately versioned `release-v2.py` follows the existing frozen handover pattern: authenticate this human repair/resume instruction and the exact new failure pause; verify unchanged rows/source/authority/backups/clock/resources/timers; preserve the failed attempt independently; append the authorized durable RESUME_SAVED_ORDER decision; move the exact pause; start the standalone service. Until the pause file moves, it still prevents admission. The frozen admission guard itself was not altered or bypassed.

Three additional offline SQLite metadata controls passed in0.160 seconds: rename-only remains rejected; the explicit reviewed decision admits the same saved identity; an existing pause file still blocks admission even with a resume decision. Their temporary control ledgers were retained. No research driver ran. There were no failed qualification controls; the failed live external release is retained explicitly.

## Preservation and verified backups

All1315 original receipt hashes and the exact1500 identity/order bindings were checked before and after recovery. The prior1297 archive/version qualification was reused; the18 later archives and pinned S3 versions were verified, including full member verification for1315. Original raw statuses, grades, timestamps and archives were neither replayed nor regraded. The shared revision-only claim-selection limitation is unchanged.

Frozen v12 remains package `cad8fb4960c0e451e7d749ce2ce29cb386216611acd552424714f2f03fba7c9d`, archive `60218b4a7b7a9ac5862b1792e28cd93e1fc2ea7b6bc163da12ef4576b6955e0b`, freeze receipt `a4f183251498e90c86b1787b3856dcd5a485401e404a59442cfe3f330b630a88`. The local archive/receipt were rehashed after recovery; the actual installed source and authority chain passed the unchanged verifier. No new acceptance or freeze was invented.

The same-source/same-boot PRELAUNCH, COMPLETE, genuine readiness and launch bindings were verified and reused. One additional current-boundary master backup received independent version-specific981-piece retrieval, full archive/member and continuation-metadata verification:

- Archive SHA-256 `cb7b39820b9a9ab6f60a2ffb72260657dc8412d9dbbded28d832bd3fe5dbda99`, 64231807bytes.
- S3 version `GuYNFmv7e1VRFLX.96LyVLQQp0Eb1QyX`.
- Readback-record SHA-256 `35e68bc34499d7bd4a2715f05e799fb7bf3b88f7fa3e62e5316f03e2707d2986`.
- Measured local growth 1474329319bytes within the1.5-GiB preparation bound.

The failed release's consistent SQLite snapshot, exact pause, original wrapper and diagnosis were separately preserved with independent readback, linked to that full backup:

- Archive SHA-256 `94b9342224d6b5e72b009c0f425635441969eece93ec64540fc75c01b06fb12b`, 11217464bytes.
- Pinned version `tkI9.G0nXjEY_LdPG2alOU5.56oCRkrX`.
- Retained staging 165297713bytes within192MiB; capacity was checked before readback using measured archive and expanded sizes.

Bucket: fyp-p82-20261005-018da1d6-803656589923. Exact keys and receipts are in verified-remote-records.json. Original pause hash89bf7369aaa355e52c0bd3f59afb101d87701db33d85379b2b64549f24c4a95c and failed-release pause hashdf12217c948342161c7768d20a91248d89a2ffc483da60cfb8800432e68cbfea are retained under separate root filenames. No evidence/root deletion occurred.

## Time, cost, storage and shutdown

Accepted policy remains **US$76 admission guard /US$77 total ceiling**,80-GiB cloud all-version and dedicated backup caps, original elapsed history and absolute stop **2026-10-26T12:00:00Z /17:00 Pakistan**. Root-retention decision remains due by28October12:00UTC; no deletion is authorized.

At the final pre-release check (2026-10-23T19:41:05.845222+00:00), using the unchanged185-execution rate,2.5-hour preparation/shutdown allowance,24-hour uncertainty and30-minute margin:

- Planning completion: **2026-10-25T09:59:57.754434+00:00** (about25October3PM Pakistan).
- Uncertainty plus margin: **2026-10-26T10:29:57.754434+00:00** (about26October3:30PM Pakistan), before the5PM stop.
- Uncertainty forecast: **US$75.65786**, below76.
- Full-deadline forecast: **US$75.87656**, below77.
- Cloud projection: **67.789GiB**; dedicated backup projection **78.597GiB**. Including the separately retained diagnostic staging conservatively gives **78.751GiB**, below80.
- Available RAM **6.660GiB**. Physical free **73.725GiB**, required **73.569GiB** with all working/slot/free-space reservations retained. Headroom beyond this conservative projection is limited; guards remain active.

These are conservative accepted-accounting forecasts, not actual billed spending. Free Tier was FREE/ACTIVE withUS$69.38 credits remaining; that balance is not campaign spending. No plan upgrade or model/speech service was introduced. No allowance was reduced to pass.

A fresh independent preparation-stop guard was created and read back before quiescing/restarting units. After positive sequence1316 admission, it was disabled and independently verified. The final AWS schedule inventory has only the accepted v12 absolute stop enabled. On-host hardstop/bootstrap/admission-cutoff timers were verified. Ordinary pause does not guarantee immediate poweroff; the accepted shutdown policy is unchanged.

## Files, commands and evidence

New files are confined to this external recovery directory: PLAN.md; diagnostic/qualification scripts; control.py; preparation_guard.py; recover1315.py and immutable rendered wrappers/inventory; release-v2.py and its separate hash binding; post-launch verification; guard retirement; requests/results/backup receipts and this report. Two systemd drop-ins are the only persistent service configuration additions. There are no migrations or frozen application-source diffs. External initial controller hash7ed694d7feb06cf28973f525cc2aaa9a1e7b0e4bb32e0b00dd9e006134e38323; corrected release controller hash1b21a666efdda58db212df3fc7558efe94b61b71e42aa6fe535d6e35f832bea0.

Commands: recorded single-send control.py send/poll for diagnostic, five-control qualification, prepare, current master backup/readback, failed initial release, positive-error inspection, corrected release with three SQLite controls and small failure-evidence readback, postlaunch verification; scheduler read/create/readback/update/readback; read-only EC2/FreeTier queries; frozen archive/receipt hashing. Each mutation was reconciled from its result before another step; no automatic boot/resend loop occurred.

`final-verification.json` is PASS_ACTUAL_RESUME; `admission-verification.json`, actual-admission.json and immutable raw SSM results distinguish authorization/service start from actual admission. Evidence inventory records exact local file hashes. This report makes no interim comparative-effectiveness or publication claim.

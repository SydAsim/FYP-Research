# Combined continuation v3 — actual deployment and start

## Result

**STARTED**, observed 8 October 2026 at 07:34:55 UTC. This records an actual admission, not merely permission or service activation.

- Run: `p85-01a116f7-3b82-7a79-8653-3aee62dc99e9`.
- Fresh Sydney host: `i-002b63326e1566005`; encrypted 160-GiB gp3 root `vol-04fa91b4840804295`. Root deletion on termination is disabled.
- Campaign service active since 07:34:23 UTC; watchdog active; campaign hard-stop and independent bootstrap stop timers active. Preparation timers were disabled only after successful service activation.
- Saved sequence 3: P2, case `p8v4-0484`, attempt 1, execution `01a11705-11f0-7a68-8c68-4da5c8126c84`, admitted **2026-10-08T07:34:26.980053Z**.
- Its original 600-second observation deadline is **2026-10-08T07:44:36.578171Z**. Observation was running, with no pause, at the recorded progress snapshot.
- Snapshot: two historical BACKED_UP executions, one RUNNING, 1,497 PLANNED. Thus 1,498 executions remain unfinished including the active original. No retained original was replayed.
- Absolute operational stop remains **2026-10-22T15:24:23.810674Z**. Timer precision follows the accepted runtime; neither the clock nor spending limits were reset.

## Exact acceptance, freeze and launch chain

Accepted package `2963b5b1b88b33b39bd66010dc9f7efa0914ea55cfd7014625ed65ecd3100736`; archive `0878ad052db96b9c075f527dc53194b0eb013d7b98e47603a74acf36b8ff3aaf`.

The immutable v3 freeze manifest is `49ec78e719d9d28e017f62e6a40dd69cc236a45c5406d5be1a209ef59b9d2c86`. Freeze verification passed against the original and immediate continuation parent chains. Historical receipts remain unchanged. Separately recorded CONTINUATION_LAUNCH has file SHA-256 `2afc58348fd5f768704f2d8823df12c3232649c26d99ff3f6c3df4d412c8389c`, binding the actual fresh host to readiness `3c95a1496b94c921d4c2256e9e9ce7e9d737607203d91439eb114329b195be2c`. Owner HMAC signatures record authorized operator action; they are not a cryptographic human identity signature. The private key is outside source and cloud evidence.

Both originals retain raw FAILED status, original grades and separate timing sidecars. Exactly 1,500 saved identities and order were imported, with two BACKED_UP and 1,498 PLANNED before launch. No old live application database was restored. The accepted v3 runner alone governs refusals and permissive responses; application behaviour, study inputs, endpoints, analysis and observation windows are unchanged.

## Verified readiness and evidence

Actual-host checks passed: 1,788 accepted source member hashes, pinned Python/uv/container artifacts, dependency RECORD validation (13,629 files), both retained exports, exact ledger import, signed authority, key permissions, no inbound security-group access, versioned S3 PUT/GET/hash checks, resource headroom, port availability, clock and budget gates. One dedicated empty diagnostic stack verified real PostgreSQL migration/seeding and all four service health endpoints; it made no scientific driver call and was removed after retaining logs and dumps.

The versioned authorized prelaunch backup was uploaded, read back by exact version, hash verified, extracted with bounded short-path transport, and checked against both originals and saved identities:

- Bucket: `fyp-p82-20261005-018da1d6-803656589923`.
- Key: `exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/792ed6b159411bb771c6286c019efdf49ad05497c04c193ab5e74772df0f94f9.tar.gz`.
- Version: `8MoAyzy1Wp3ulKlYYaBpA5_wAxQ1i_fP`; SHA-256 `792ed6b159411bb771c6286c019efdf49ad05497c04c193ab5e74772df0f94f9`; 1,379,121 bytes.

The active execution has not yet completed observation or received its per-slot backup. Every next admission remains conditional on full collection, export, grading and verified backup. Failures, unknown outcomes and unexpected responses retain the accepted durable pause/collection rules.

## Feasibility and unchanged controls

Before provisioning and again immediately before admission, the plan fit the unchanged deadline and budget. Fresh official pricing read: m7i-flex.large US$0.1197/hour; public IPv4 US$0.005/hour; Sydney gp3 US$0.096/GiB-month; S3 first-tier US$0.025/GiB-month. Project plan remained FREE/ACTIVE with US$119.08 available credits. No upgrade or paid model/speech service was introduced.

At 07:34:22 UTC, conservative original-elapsed-clock accounting projected **US$52.7038355**, below the **US$55 admission guard** and **US$65 total limit**, including previous spending, retained storage and accepted reserve allowances. A 290-hour remaining allowance projected finish **20 October 2026 at 09:34:22 UTC**. It is an estimate, not a guaranteed 12-day completion; slower throughput may exhaust the guard before the absolute deadline. Limits will not increase automatically. Delayed AWS billing is not a real-time hard billing cap.

Measured pre-admission MemAvailable was 7,365,582,848 bytes (about 6.86 GiB); filesystem free was 160,425,840,640 bytes (about 149.41 GiB). All-version campaign-prefix storage was 82,737,310 bytes. Accepted disk/RAM/30-GiB cloud evidence thresholds, reserve, admission cutoff, shutdown tail and bounded recovery remain executable guards. Reconciliation is limited to **eight attempts**; drain to **30 passes**, not seconds.

## Previous resource disposition

After exact stopped-host/root ownership verification, two originals plus master/operational evidence were verified independently in retained local and pinned S3 versions, and the fresh prelaunch handover backup passed. Only old host `i-034252c3e9b083abf` and its owned root `vol-0f667d76019af7a47` were terminated/deleted. All S3/local evidence remains. The new root was not deleted and has no deletion authorization. Future stop and disk/evidence retention follow the accepted policy; expiration requires a retention decision rather than deleting the only copy.

## Retained operational failures and resolutions

1. Initial local freeze verification hit a Windows long-path read; the failed record remains. A separate operational helper used extended paths and verified all parent hashes before freezing.
2. Initial source preparation verified accepted members but lacked the original Linux bootstrap seal. The original source archive was downloaded by pinned version/hash. Only its bootstrap metadata seal was copied; all 1,642 seal hashes and 300 alias targets were checked. This follows the reviewed original-source-plus-amendment route and did not edit accepted source.
3. The empty-stack postflight plain socket bind failed immediately after clean shutdown. Its earlier TCP state was not captured. A retained read-only inspection and later unchanged plain binds passed with no listeners or diagnostic containers. No socket reuse bypass or scientific execution was used to hide the failure.
4. First control-activation shell exited before commands because of Windows line endings. A separately retained LF operational transfer succeeded; frozen code was untouched.
5. Two local status reads could not encode systemd's arrow character. Their raw partial responses/errors remain. UTF-8 status retrieval then retained the complete successful remote result. Commands were not replayed.

Passing readiness does not guarantee an error-free campaign. Any new failed guard or unrecognized refusal must preserve evidence and pause admissions under frozen rules, without changing source or replacing outcomes.

## Independent progress check

From a normal PowerShell terminal with AWS CLI and the configured `fyp-research` profile, run:

```powershell
& 'C:\Users\syeda\OneDrive\ドキュメント\ChatGPT\Final Year Project\artifacts\phase-8-continuation-deployment\v3\Check-Progress.ps1'
```

This checks host state and reads ledger/service/collector progress through SSM. It does not start, restart, resume, replay or change campaign state. The standalone system service continues without an active Codex conversation. No new pilot or research extension was added.

Relevant evidence: `final-verification.json`, `actual-continuation-start.json`, `actual-launch-authorization-binding.json`, `final-readiness-status1-result.json`, `activate-controls-lf-status3-result.json`, `launch-service-status1-result.json`, `progress-status1-result.json`, `terminal-progress-qualification.txt`, `old-cleanup-complete.json`, and immutable per-operation request/result records. The operational inventory hashes these separate deployment files; it does not replace the accepted study inventory.

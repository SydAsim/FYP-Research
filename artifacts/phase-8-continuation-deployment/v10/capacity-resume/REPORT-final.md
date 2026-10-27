# Frozen v10 deployed — sequence146 actually running

## Verified result

Sequence **146 / P2 / attempt1**, execution **01a11705-11f1-772d-8190-c43552871801**, was admitted at **2026-10-12T20:40:36.131479+00:00**. Its original observation deadline is **2026-10-12T20:50:56.517530+00:00**. At 2026-10-12T20:41:10.767473+00:00, the consistent ledger showed **145 BACKED_UP / 1 RUNNING / 1,354 PLANNED**. Both campaign and watchdog services were active/running. EC2 was independently read back **running** after the preparation guard was retired. The standalone service continues without a Codex conversation.

All first145 rows remain exactly equal to frozen original records. All1500 identities/order were preserved. The historical DRIVER_FAILURE pause was preserved byte-for-byte as `retained-driver145-pause-v10.json`, SHA-256 `28ea1aec440408f1d9e467ece07e54c39485d14c29434dc79b35b9460919d519`; only its authorized active placement was released after all gates. No original was replayed, regraded or replaced, and no timing sidecar was added.

## Authority reused

| Binding | SHA-256 |
|---|---|
| Unchanged frozen package | `bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c` |
| Unchanged deployment archive | `212269264d45ac8bd6637c2ca0ca5e09c951d354cb445c9bf7a16c6ba2d0ba37` |
| Existing frozen receipt, exact file | `b886fff14d4e8384c406deb68a875bc21a9c53e2bac5a17787d800fc1d2d192f` |
| Genuine readiness | `33b7ab10523a2f68805364a74ebd7c9d4165a26f22ad6247c2fb01ae424ff416` |
| Linux launch receipt, committed by COMPLETE | `2d95adc05d0d93a67e0f9f7b78647fe4ca4c393ad4b8c42363ce148b30e1187a` |

The installed3441 source files, frozen authority, host Python build and installed dependency RECORD hashes were verified. No exclusive bootstrap, deployment upload, old metadata migration, refreeze or dependency installation occurred. Application/claim selection, fixtures, endpoints, grading/oracle/analysis and600-second windows remain unchanged. The shared revision-only claim-selection limitation remains part of the studied application behavior.

The local new launch receipt uses Windows CRLF while the Linux transfer writes LF. [launch-receipt-transfer-binding.json](launch-receipt-transfer-binding.json) preserves both exact file hashes and verifies the transmitted bytes against COMPLETE. Signed JSON content and canonical HMAC chain are unchanged; no differing hash was represented as identical.

## Capacity and necessary external controls

Owned volume `vol-09dbb42bbf607f5de`, attached to retained host `i-057344e5372faf62f`, remains encrypted gp3 with3000IOPS/125MiB/s and DeleteOnTermination=false. Its verified NVMe serial identifies the same volume. Root is `/dev/nvme0n1p1`, ext4, UUID `6064d37b-2f18-4067-a280-abb8a265f6a7`.

Initial160→165 sizing allowed a1-GiB margin and0.5GiB preparation allowance, but the actual PRELAUNCH roundtrip demonstrated that this preparation allowance underestimated retained raw copies: **482,620,674 bytes raw metadata +557,498,526 bytes readback tree +37,359,023 bytes archive**. A16-MiB allowance yielded **1,094,255,439 bytes** for COMPLETE. Preserving that entire footprint plus the1-GiB final margin required **167GiB** under the same95% usable-increment assumption. This correction was calculated before readiness/admission; nothing was deleted or compacted to pass.

AWS's initial modification was independently verified `completed` before the second request. The second167GiB modification was verified `optimizing`, when AWS permits filesystem expansion. On the **same single boot**, actual layout checks preceded `growpart /dev/nvme0n1 1` and `resize2fs /dev/nvme0n1p1`. Partition-table and before/after layout records are retained. Root UUID was unchanged.

After COMPLETE and actual admission:

| Measurement | Value |
|---|---:|
| EBS requested/verified capacity |167GiB |
| Actual root filesystem total |172,576,260,096 bytes (160.724167GiB) |
| Actual free filesystem sample |147,664,572,416 bytes (137.523350GiB) |
| Unchanged reviewed free requirement |145,670,462,448 bytes |
| Remaining margin above requirement |1,994,109,968 bytes (1.857160GiB) |

The actual filesystem capacity, not only an EBS request, passed. Both80-GiB caps and all existing reservations remain unchanged. The final cloud projection at release was83,846,751,724.73685bytes before its1-GiB reservation. All originals and unsuccessful attempts were retained.

The unchanged frozen policy prices160GiB. To preserve the actual70USD admission guard without modifying it, external readiness/release checks included a conservative **US$0.326965** reserve for all7 added GiB through the absolute stop+48h. A separate owned systemd admission fence is active at **2026-10-24T21:25:47Z**, before the original formula plus that reserve can reach70USD, including its30-minute lookahead. It calls the existing durable pause API and **does not shorten active collection windows**. Its code, unit files and authorization/provenance are preserved in restart-history and COMPLETE. The superseded165GiB fence was verified as owned and disabled only after the167GiB replacement was activated/read back. Existing frozen controls are unchanged; no new application behavior is introduced. A cost pause does not imply immediate compute shutdown; existing absolute/safe-stop mechanisms retain their documented behavior.

## Guarded deployment gates

- Fresh independent preparation-stop protection was created and read back before the only boot. All owned obsolete preparation guards were accounted for. Root/host/role/security-group ownership and no-inbound access were verified.
- Old unit state and effects were preserved; owned v9 units were quiesced before readiness. The old watchdog was observed failing/restarting against already-v10-bound metadata; it admitted no slot and did not change the historical pause. Replaced unit files remain preserved.
- The reviewed frozen `bind_host_segment` sampled a fresh bracketed wall/monotonic anchor after metadata/authority checks. Its occupied historical target was preserved first so POSIX rename could not overwrite an earlier anchor. Original elapsed start/deadline and five-second rollback guard remain unchanged. No old metadata migration was repeated.
- All145 materialized export bytes were checked against handover commitments; frozen closed145 validator passed. Local archive/member and pinned S3 version checks passed. No original archive retrieval was repeated.
- Actual dependency/image/owner permissions/ports/RAM/disk/capacity checks passed. Live available memory was7,472,783,360bytes. Absolute432-hour timers, AWS guard and extra-storage admission fence were active.
- **PRELAUNCH → independent version-specific readback → genuine readiness → readiness-bound launch receipt → COMPLETE → independent readback** all passed, then the authorized pause was released and the campaign started.
- Actual ledger ADMITTED event and RUNNING state were verified. The preparation-stop schedule was disabled and independently read back **only after actual admission and service checks**; its historical record remains. Absolute AWS protection remains enabled.

## Verified backup receipts

| Phase | Archive SHA-256 | Pinned S3 version | Bytes | Independent readback record SHA-256 |
|---|---|---|---:|---|
| PRELAUNCH |`397411d66a22dfdb614f29261245c1ea87e6c44cd516db2b17cc9b474a4eb24f` |`WGPdPg91Kq11xZpzCidcD_BXFr435nJg` |37359023 |`00d87afebe2cb2b010d5a4b31c7a4bddba97658120b01468bd7055da09eff5ab` |
| COMPLETE |`bc7018d3bd35aa4c7fd1ea351d1af418c160db31a79da7d37be7128518a8f166` |`HV4DN0zPvJXggke0yMFQm9zJAhhp6OZy` |37368341 |`04d1cc148678db397827ce065704dfc52625f02a8bfa7619ef4088c1dbb364ad` |

Both are in bucket `fyp-p82-20261005-018da1d6-803656589923`, under `exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/<archive-sha256>.tar.gz`. The original pinned backups are unchanged. Each new readback verified571 required evidence pieces. These are actual receipts, not authorization alone. Sequence146's own per-slot backup is pending completion of its full observation window; it is not yet counted as BACKED_UP.

## Costs and remaining uncertainty

Sydney gp3 rate was read from AWS Price List: **US$0.096/GiB/month**, verified in [current-gp3-price-result.json](current-gp3-price-result.json), consistent with [AWS EBS pricing](https://aws.amazon.com/ebs/pricing/). Added7GiB costs **US$0.672/month**; the reviewed48-hour retention allowance for the whole167GiB root is **US$1.054159**, or **US$0.527079/day** if retained. Capacity changes preserve the accepted total ceiling/admission guard.

At 2026-10-12T20:46:31.796900+00:00, refreshed arithmetic keeps the original **262.316422 hours for1355 unfinished originals +2.5 hours preparation/shutdown +24 hours uncertainty**. It conservatively retains all original elapsed stopped/running history and charges all7 extra GiB from the first resize calculation through stop+48h, including the two added GiB before their actual request. Full80-GiB S3 month and5USD request/1.25USD handover reserves remain.

- Completion forecast: **US$66.4530**.
- Completion plus unchanged24-hour uncertainty: **US$69.9508**.
- Full absolute-deadline forecast: **US$72.5471**.
- Uncertainty completion estimate: 2026-10-24T21:35:30.915725+00:00.

These are conservative forecasts, **not actual billed spending**. The uncertainty budget margin is small; this does not guarantee the remaining campaign will finish. Failed guards/technical defects still pause admissions; no limits will be silently increased. AWS Free plan remained active, with107.81USD credits on the bounded preboot read; it was not upgraded.

## Retained control failures and verification scope

Existing qualification was reused. Only focused local Python/Bash/PowerShell syntax/argument checks were run; no pilot, scenario, application-stack calibration or600-second test was repeated.

Retained control records include: expected `InvalidVolumeModification.NotFound` before any resize; an incorrect read-only IAM policy name corrected against the retained request; and a local AWS CLI CP1252 encoding failure reading a Unicode systemctl symlink message. The latter was reconciled with the same command ID using UTF-8; the successful command was **not resent**. All these were external controls, not reclassified research outcomes. The initial capacity underestimate and both measured sizing calculations remain documented. No prior evidence/receipts/packages were removed.

## Terminal progress and deadlines

Use the new absolute path, which is independent of the terminal's working directory:

```powershell
& "C:\Users\syeda\OneDrive\ドキュメント\ChatGPT\Final Year Project\artifacts\phase-8-continuation-deployment\v10\Check-Progress.ps1"
```

Prerequisites: AWS CLI authenticated profile `fyp-research`, PowerShell, and permission for bounded EC2/SSM reads plus the read-only SSM progress command. The script does not restart, unpause or admit work. It retains requests/replies and reconciles by command ID instead of resending unresolved commands.

Absolute stop remains **2026-10-25T15:24:23.810674Z**; original anchor **2026-10-07T15:24:23.810674Z** and432-hour elapsed history are unchanged. Root-retention decision is due **2026-10-27T15:24:23.810674Z**. No deletion is authorized.

No further deployment or repeated boot is needed for this successful admission. The campaign runs under its standalone service and accepted failure/backup/observation rules.

## Final independent terminal check

The exact `Check-Progress.ps1` was invoked from PowerShell, not through the deployment controller. It successfully read EC2 and the consistent live ledger at **2026-10-12T20:47:27.384576+00:00**:145 BACKED_UP,1 RUNNING,1354 PLANNED; both services active; no active pause; first145 unchanged; both backup proofs verified. Raw request/response files are retained in `progress-reads/`. PowerShell's parsed summary displayed timestamps with a+05:00 offset; the raw response and original ledger timestamps remain UTC and unchanged.

Final measured free filesystem was **147,640,389,632 bytes (137.500828GiB)**, above the unchanged requirement by **1.834638GiB**. The campaign service remained running after the preparation schedule was disabled. This check is a status read, not another research execution or a replacement outcome.

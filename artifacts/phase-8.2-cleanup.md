# Phase 8.2 — cleanup addendum

**Final resource state, verified 2026-10-05 18:51:42 UTC:** the temporary server is terminated and its root disk is deleted. S3 evidence and local archives are retained. The 500-input main campaign remains unstarted.

The user selected “Remove temporary server/disk; keep S3 evidence.” Before termination, the owner tag, stopped instance identity, single encrypted 40 GiB root attachment and DeleteOnTermination setting were checked. The final S3 archive's original VersionId and SHA-256, plus project and D: archive hashes, were verified again.

| Resource | Verified disposition |
| --- | --- |
| Instance `i-0938c2aa962389253` | TERMINATED |
| Root volume `vol-0694cf892831a56c4` | DELETED; exact-ID DescribeVolumes returned InvalidVolume.NotFound |
| Bucket `fyp-p82-20261005-018da1d6-803656589923` | RETAINED; source, all unsuccessful attempts and final exports preserved |
| Local project archives, E: extraction, D:/P82 backups | RETAINED |
| Temporary role/profile and empty security group | RETAINED configuration; no running compute or retained root disk |

The stopped-disk daily charge discussed in the earlier report no longer applies to this deleted disk. S3 storage/request charges remain; displayed credits are not a final invoice.

The [Phase 8.2 report](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8.2-report.md>) and sealed `review-v1` supplement describe the state before this cleanup choice and remain unchanged. This addendum records the later authorized action. It does not change qualification results, study design, source, fixture versions or launch guards.

Evidence: [approval and preconditions](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-aws-qualification/cleanup-v1/preconditions.json>), [confirmed final state](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-aws-qualification/cleanup-v1/state-check1.json>). Exact AWS requests/responses are retained in the v1 journal under the cleanup names.

**Verdict:** finite Phase 8.2 work and authorized server/disk cleanup are complete. The package is ready for review. Representative pilot/campaign capacity, candidate acceptance, protocol freeze and separate launch approval still remain; no main launch was performed.

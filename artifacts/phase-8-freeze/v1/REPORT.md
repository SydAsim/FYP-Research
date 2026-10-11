# Phase 8.4 v2 — accepted and frozen

**Verification: PASS. Main launch remains unauthorized and unstarted.**

Your explicit acceptance and instruction to freeze are preserved in `acceptance-statement.json`. The original candidate files retain their historical review-only flags and bytes. The separate `REVIEW_ACCEPTED.json`, `FREEZE.json` and signed `freeze-manifest.json` are the current acceptance/freeze records.

## Frozen fingerprints

- Package inventory content: `c76fc54018ce6b9e9f77eeb2946cea253271ad4a8573f8fe047961d7b6f6dc6b`
- Accepted archive: `0e841d7dd7ab1329c4e30fa4dc32179b76655b2cf728ec1ad28db714258d7b62` (30,075,526 bytes).
- Inventory file: `a31f2e032a55539f933e42fa495b1df6f1f85b724776b9dd07c90178f41ee4ee`.
- Freeze receipt file: `0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2`.
- Signed freeze manifest: `b5a45c2e1648dc8acb79e4d63ba19528669d9799acabdf08f7c9d72c3591cb1f`.

## What was verified

The accepted `final-verification.json` is PASS and matches the candidate. Before signing: all 1,678 source hashes, 1,680 archive members, 144 verification-evidence artifacts, and 5,597 historical file hashes matched. After signing: the unchanged runtime verifier checked source closure, static policy, schedule and both receipt signatures/predecessors, then correctly refused authorization because `LAUNCH.json` does not exist. All 144 review-evidence hashes and all 5,597 historical hashes were reread unchanged. Nine exact copies in `frozen-source/` provide an additional local archive/inventory/document copy. No application or migration changes were made.

## Accepted scope and limits

500 inputs across B3/P1/P2; 1,500 serial originals in the saved order; 600-second observation windows; unchanged endpoints and analysis. US$65 campaign policy, US$55 estimated committed-cost admission guard, 360-hour host limit, 30-minute admission cutoff, documented RAM/disk thresholds, 30-GiB cloud evidence cap, retention/escalation and same-execution recovery limits are bound through the static policy and exact reviewed source. Existing billing, retention, synthetic-evidence and recovery limitations remain as reviewed.

## Receipt protection

The owner key and runtime receipt copies are outside the source at `C:/Users/syeda/.fyp-research/phase8-owner/phase84-final-v2`, with verified owner-only Windows ACLs. The key is not included in any archive or public record. Signatures are local operator HMAC attestations of the explicit human instruction, not independent human digital-identity proof. Static receipts use the schema's far-future expiry sentinel for enduring acceptance/freeze provenance; this does not authorize execution or extend the 360-hour operational clock. Any later launch requires its own receipt binding the actual run/start and operational validity.

Files are exclusively created and sealed read-only, with a signed manifest and SHA256 checksums. This is logical immutability with tamper detection, not filesystem WORM. Preserve the private key securely; loss prevents signature validation and is not permission to silently reseal. New versions must retain these records.

## Stop condition

All 1,500 original execution identities remain unset and NOT_STARTED. No launch policy, host-start authorization, main ledger or LAUNCH receipt was created. No AWS calls, provisioning, spending or Phase 8.5 execution occurred. Freeze is complete; separate launch authorization and the already documented deployment checks remain required.

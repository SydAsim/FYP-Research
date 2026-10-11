# Phase 8.4 — completion report

The concrete final candidate, validation evidence, file inventories and remaining
decision checklist are in [the v2 completion report](phase-8-review-freeze/v2/COMPLETION.md).
Review [the exact plan](phase-8-review-freeze/v2/REVIEW.md) and
[terminal operation instructions](phase-8-review-freeze/v2/OPERATING.md).

The final source archive SHA-256 is
`0e841d7dd7ab1329c4e30fa4dc32179b76655b2cf728ec1ad28db714258d7b62`.
The package inventory fingerprint is
`c76fc54018ce6b9e9f77eeb2946cea253271ad4a8573f8fe047961d7b6f6dc6b`.

59 checks passed in the final independently rebuilt Linux capsule, 57 on Windows
(two Linux-only skips covered), 77 relevant regressions passed, 27 static-policy
checks passed, and all 24 retained pilot grades/analysis rows remained identical.
Real existing isolated PostgreSQL dumps and offline pinned SDK checks passed.
5,597 protected historical files are unchanged. Application code/migrations were
not changed. Earlier candidate assemblies and unsuccessful attempts are retained.

500 unchanged inputs, B3/P1/P2, 1,500 original serial executions, fixed endpoints,
analysis rules and 600s windows remain. No main execution, AWS request/provisioning,
cloud spending, acceptance, freeze or launch authorization occurred.

**Ready for acceptance review.** Actual host activation checks remain mandatory
after separate launch authorization. Budget/billing/retention and recovery limits
are explicit in the review. Phase 8.5 is unstarted and launch-guarded.

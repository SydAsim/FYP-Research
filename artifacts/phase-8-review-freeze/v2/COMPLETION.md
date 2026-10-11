# Phase 8.4 completion and verification

**Ready for acceptance review. No acceptance, freeze, launch or AWS provisioning
was recorded. The 500-input main campaign is still unstarted.**

Review `REVIEW.md`, then `OPERATING.md` and `checklist.json`. The final candidate
has 1,678 source files. `review-inventory.json` contains their exact SHA-256 values
and executable/configuration/fixture/oracle/analysis categories. `bundle-receipt.json`
binds the concrete source archive; these are candidate fingerprints, not a freeze.

- Source archive: `campaign-source.tar.gz`, 30,075,526 bytes.
- Archive SHA-256: `0e841d7dd7ab1329c4e30fa4dc32179b76655b2cf728ec1ad28db714258d7b62`.
- Package inventory fingerprint: `c76fc54018ce6b9e9f77eeb2946cea253271ad4a8573f8fe047961d7b6f6dc6b`.
- Inventory file SHA-256: `a31f2e032a55539f933e42fa495b1df6f1f85b724776b9dd07c90178f41ee4ee`.
- Locally rebuilt Linux image ID: `sha256:4cd77c849c25a74b3aea3d68c8fa29976a51cc9b3abcd2d3963f18ceee7964ae`.

The first assembly, its archive/receipts/verification and local image remain retained
as `assembly-attempt1` / `fyp-phase84-v2:assembly-attempt1`. Final assembly pins all
12 transport dependencies and carries the saved v1 comparator schedule. Metadata,
unsuccessful tests, SDK/import attempts and partial backup attempts remain separate.

## Files and invariants

| Files in this v2 package | Invariant |
|---|---|
| `controls.py`, `runner.py` | Chained review/freeze/launch gates; exact original identity/order; static policy binding; durable pause/transition/clock seals; serial admissions; deadline, cost and capacity guards; standalone systemd ownership. |
| `collector.py`, `window.py` | Preserve normal arm recipe methods and budgets; issued-request and acceptance anchors separate; fixed 600s collection; original SQL checkpoint recovery without driver replay; raw later evidence retained. |
| `storage.py` | Verified per-slot/final backups, both independent PostgreSQL dumps, all-version storage reservations, ambiguous PUT read-only reconciliation, safe exact-owned retirement. |
| `transport.py`, `postflight.py`, `requirements.txt` | Bounded version-specific download, hashes/trailer/members, original transfer deadline, short extraction, retained interrupted copies, fully pinned separate dependency layer. |
| `instrument.py`, `analyze.py` | Same revised oracle and analysis functions; original bindings; missing/failed originals explicitly UNKNOWN; no calibration/main mixing or rerun substitution. |
| `test_*.py`, `qualify_sdk.py`, `verify_pilot.py` | Finite separate control calibrations; real checkpoint/OS boundaries; SDK model stubs; retained 24-trace parity. |
| `build_package.py`, `Dockerfile`, `prepare_review.py`, `verify_history.py`, `verify_package.py` | Review-only deterministic capsule, isolated dependencies, exact source inventory and historical preservation. No signing/freeze/launch API. |
| `schedule.*`, `policy-proposal.json`, `budget.json`, `measurements.json`, review/operating/checklist records | Fixed scientific design and explicit operational proposals pending acceptance. |

Application files and migrations were not changed. PostgreSQL remains application
correctness authority. UUIDv7 is used only for the new research execution ledger;
the previously approved SQL UUID default exception remains unchanged. Arm logic,
claim permits, reconciliation-before-retry and repair correctness are unchanged.

## Finite verification evidence

The checks and stopping criteria were recorded first in `qualification-plan.json`.

| Check | Result and retained evidence |
|---|---|
| Windows integrated controls | 57 passed, 2 Linux-only skips; `windows-final.txt`. Both skipped checks passed on Linux. |
| Linux controls using the earlier qualified environment | 59 passed; `linux-final.txt`. |
| **Actual final source capsule and complete pinned dependency layers** | Local image build passed; networking-disabled `capsule-linux-tests.txt`: **59 passed**. No workspace source mount was needed. |
| Main source closure/static proposals/authentication boundary | `capsule-main-guard.txt`: exact capsule validated, missing owner authority rejected, no admission. No main receipt was created. |
| Pinned SDK request models and checks | Windows `sdk-qualification-attempt1/result.json`, Linux final image `image-sdk-qualification/attempt1/result.json`: PASS; conditional single PUT, pinned checksum HEAD, all-version inventory, unique-version reconciliation. Stubbed SDK only, zero cloud requests. |
| Existing revised instrument/runner regressions | **77 passed**; `regression-final.txt`. |
| Final static-policy controls regression | **27 passed**; `static-policy-regression.txt`. |
| Static checks | Ruff PASS; strict mypy PASS for **15 production/helper files**; `ruff-final-candidate.txt`, `mypy-final-candidate.txt`. |
| Saved real pilot evidence | **24 identical grades and analysis rows**; `retained-pilot-replay-final/replay.json`. Integrated outcome report unchanged; reduced bootstrap draws here qualify plumbing only, not the main analysis. |
| PostgreSQL storage | Real read-only `pg_dump` of both already-isolated databases, SQLite backup and archive member/trailer verification PASS; `local-postgres-qualification/result.json`. No test DB or cloud server was provisioned. |
| Postflight | Offline version/chunk/expiry/drift/interruption/path tests and real final capsule short extraction PASS; `capsule-extraction-final.txt`. Before-decisive and actual speech claims remain the original study's limits; no new audio campaign. |
| Scientific scope and units | Exact 500 inputs / 1,500 saved slots / 600s unchanged. SQL/worker prove **8 reconciliation attempts**; recipe loop proves **30 drain passes**. |
| Historical preservation | **5,597 protected files unchanged**; `preservation-before-assembly.json`, `preservation-after.json`, `final-verification.json`. Hash baseline was copied before v2 edits; stream rereads are before/after assembly, not misrepresented as an earlier independent pre-edit reread. |

Successful trace: `retained-pilot-replay-final/replay.json` links all saved live
exports and SHA-256 values. Expected failure: missing authority in
`capsule-main-guard.txt`; backup damage/ambiguous write and no-replay refusals are
covered in the saved passing control tests. Control-only virtual-clock snapshots
deliberately retain oracle failures rather than mocking business success.

Commands executed were limited to local pytest/Ruff/mypy, read-only existing PG
dumps, saved replay, SDK Stubber, deterministic packaging/extraction and local
Docker build/test. All command outputs and failed attempts are retained here.
No AWS network request, new AWS resource, paid API or main input was executed.

## Operational decision summary

- Exact saved order, entirely serial; **500 inputs × B3/P1/P2**.
- Plan **12–13 continuous days**; 10.65-day calibration median reference.
- Proposed **US$65** ceiling; estimated committed-cost admission guard at **US$55**.
- At retained rates: approximately **US$52.23** for 13 days, **US$59.23** for the
  360h maximum including 48h stopped disk, first cloud month and US$5 allowance.
- 160 GiB disk, 50/50/25/35 GiB reservations, 1 GiB next-slot reserve, 30 GiB
  versioned cloud evidence cap; RAM/disk admission and active-pressure guards.
- No replay or deadline reset; original unknown/failure results retained.
- Verified local/cloud per-slot backups and final master receipts before completion
  shutdown; never delete the sole evidence copy.

## Limitations and remaining actions

Source/code/controls are qualified locally. Matching active systemd timers, role
and bucket permissions, shutdown-as-stop behaviour, actual headroom and current
price/credit configuration must be checked on the **later authorized host before
its first admission**. This is an activation prerequisite, not a fresh cloud
qualification executed in this task. No 360h endurance or full-host/PITR restore
is claimed. New per-slot overhead is not a whole-bank runtime measurement.

Billing lag and retained disks/S3 mean US$65 is not a mathematically instantaneous
hard cap. Escalate before the proposed 48h/first-month retention boundary if
verification or continued evidence protection requires an extension. Scripted
tones/ACKs do not prove human understanding or actual intelligible speech exposure.

Four user decisions remain: accept this exact candidate/saved schedule; accept
the proposed budget/time/capacity controls; accept retention/escalation; accept
UNKNOWN/recovery/clustered timing and synthetic-evidence limits. See the short
checklist in `REVIEW.md`. Then freezing is a separate step; launch requires
another explicit authorization. No optional research extension is added.

**Verdict: Phase 8.4 implementation and finite local verification complete;
concrete candidate ready for acceptance review. Phase 8.5 remains blocked.**

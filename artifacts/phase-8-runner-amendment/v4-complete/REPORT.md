# Phase 8.5 combined continuation candidate v3

**Disposition: review candidate only.** Both requested blockers have been addressed.
The campaign remains paused; AWS remains stopped. No acceptance, freeze, deployment,
main execution, outcome replacement, clock reset or new cloud write was performed.

## Narrow changes

| Files | Invariant |
|---|---|
| `response_guard.py`, `collector.py` | Every reachable permissive request is checked against its endpoint, request, scenario condition and recorded response. Unexpected responses durably pause admissions even if later driver steps succeed. Collection continues through its original deadline. |
| `instrument.py` | An earlier permissive-response defect cannot be masked by an expected evidence refusal. Business endpoints remain independently graded; technical timing classification remains separately visible. |
| `two_originals.py`, `handover.py` | Exactly two BACKED_UP originals and 1,498 untouched PLANNED identities are imported. Order, attempts, hashes, notices, complete backups and sidecars are verified. Neither original is replayed and no old live application database is restored. |
| `runner.py` | Both imported originals are excluded from resource retirement/re-execution. Main admission requires this version's acceptance/freeze/separate launch chain; previous one-original receipts cannot authorize it. Fresh identity generation remains prohibited. |
| `imported_analysis.py`, `analyze.py` | Both raw FAILED originals enter the existing analysis through separately verified sidecars. Original grades remain unchanged. No endpoint, estimand, statistical method or window changes. |
| `storage.py` | Backups carry a verified compressed original-history bundle, including sidecars, instead of duplicating all raw historical polls. Partial metadata extraction is retained and never restores a live database. |
| Tests, assembly helpers, inventories and reports in this directory | Separate local qualification and auditable version provenance. |

No application code, migration, main fixture, arm, main order, endpoint definition
or 600-second observation window changed. Reconciliation remains **eight attempts**;
drain remains **30 passes**, not seconds. The B3/P1/P2 refusal classifier remains
byte-identical to qualified v2; the new response guard addresses deliberate stale
attempts and polling, not arbitrary HTTP errors or ambiguous provider writes.

## Response contracts

`permissive-call-sites.json` inventories all eight literal sites and the ACK
forwarding path. The legacy E2 call is not reachable through v4 dispatch; it receives
no generic exemption. Reachable paths are:

| Context | Accepted response / expected refusal |
|---|---|
| Configured held provider barrier | Matching barrier 200, including not-yet-reached state; exact `404 {"detail":"Unknown barrier"}` for that scenario and declared barrier. Other errors are defects. |
| B3 old scheduling after accepted correction | Bound observable success, or exact voice wrapper around `b3-scope`. No blanket `voice-command-rejected` exemption. |
| P1/P2 old receipt claim after correction | Bound observable authorization, or exact `stale-intent-revision` for that recorded old receipt and accepted revision. |
| P1/P2 queued old segment release | Bound observable publication, or the documented segment/revision/state conflicts, with the old segment and accepted correction established. |
| Buffered old STARTED | Matching event/segment STARTED acknowledgement remains observable evidence; exact `stale-audio` is an expected refusal after correction. |
| Version-change-before-start | Matching STARTED remains observable, including baseline acceptance. P1/P2 `fresh-evidence-required` qualifies only with ordinary successful provider observations showing the named version-only change during the request. Unavailable evidence does not qualify. |

An unexpected reply is retained in the HTTP journal, response proof, transactional
checkpoint and admission-stop notices. It makes the driver classification FAILED
even after a later successful update. The active original can finish observation,
grading and verified backup; the next original cannot be admitted. No refusal is
retried. Provider send uncertainty continues through the existing reconciliation
path rather than becoming automatic business failure. Malformed response parsing
and transport exceptions remain technical pauses, not expected refusals.

## Both originals and metadata handover

| Sequence | Arm | Execution identity | Preserved raw status |
|---|---|---|---|
| 1 | B3 | `01a11705-11f0-79f1-9293-78f7f8207f70` | FAILED |
| 2 | P1 | `01a11705-11f0-7826-bd9d-9066d82c4452` | FAILED |
| 3, unstarted | P2 | `01a11705-11f0-7a68-8c68-4da5c8126c84` | PLANNED |

The first export hash remains `283001dc1a5904f3e8b4de893ef658d2e7fe8053b8e98ed7baad6f242d318d8b`;
the second remains `bd4d32f4968eaff243d65d9cfe8fad36c603cd709c09ee7fdebd29746e90da42`.
The saved study is still 500 inputs, 500 executions per arm, 1,500 original
identities, attempt 1 throughout. Exactly 1,498 remain unstarted.

Actual retained archives were read through their gzip trailers, checked against
their pinned backup receipts, and every manifest member was verified. Both SQL
dumps are required, but only retained as evidence. The historical notice prefix
must match the retained master exactly. Changed identities/order/attempts, active
slots, missing dumps, altered archives/receipts and changed sidecars are rejected.
Packed evidence recovery verifies every member before publishing the restored
metadata directory; incomplete extraction remains in a separate attempt directory.

Both sidecars retain original grades and propose the already qualified timing
classification: `INFRASTRUCTURE_FAILURE` to `NO_SUPPORTED_COMPLETION`, 600 seconds,
event false. Business correction remains TRUE; correct final spoken update remains
FALSE. They do not replace the original FAILED exports. The previously accepted
first v1 sidecar is also retained separately. The historical 8.3 report-heading
discrepancy remains documented in v2; old headings are not rewritten.

## Finite qualification and retained failures

The plan was recorded before execution: no new live applications or main inputs,
nine reused PostgreSQL/full-window executions, at most 120 distinct focused
checks, and a 30-minute qualification budget. Cross-platform reruns are validation
repetitions, not additional independent research observations.

- Windows combined suite: **120 passed**. Six previously failing 409/500 controls
  now retain defects, verify offline backups and prevent next admission.
- Linux affected suite: **55 passed**. The initial Linux attempt retained **113
  passes and one failure** because the old launch policy was absent from the cached
  image. The candidate now includes that exact policy and historical first sidecar.
- Relevant unchanged oracle/study/policy regressions: **61 passed**.
- Existing collector recovery tests exercise the same identity, original 600-second
  cutoff and driver-once rule under a virtual clock, including an unexpected
  permissive response. Their control snapshots do not fabricate oracle success.
- Reused v2 PostgreSQL evidence: nine full-window executions, all retained with
  verified backups, covering B3/P1/P2 refusals, technical-defect pauses and same
  execution recovery. Those executions are not rerun or counted toward the study.
- Ruff and strict native Python checking pass. Configured repository Python
  checking passes for 156 files. The inherited Linux-wide Windows-helper typing
  limitation is unchanged; it is not hidden as a runtime qualification.

The first Windows attempt retained 34 passes/11 setup errors from a missing
temporary parent directory. The second retained 39 passes/six test failures from
an illegal RUNNING-to-BACKED_UP test transition. Tests were corrected to traverse
EXPORTED and verified offline backup. Invalid test-path and static-check attempts
are also retained. These were control/qualification attempts, not replacements
for either main original. No failed main status or historical grade was edited.

Post-packing Windows checks passed **eight tests**. A Linux check using Windows
mounted files hit its declared 100-second limit and is retained as a timeout.
A separate, predeclared **one-check, three-minute** diagnostic then used the same
verified archives on native Linux storage: import, packed recovery, both sidecar
regrades and all 1,500 identities passed, with zero driver calls. This supplements
the original bounded plan; it does not replace the mounted timeout or reset any
campaign clock. The pinned historical master was independently checked afterward.
The initial archive passed its member hashes but failed runtime closure because
the original review inventory did not include itself. That archive and its receipt
are retained as packaging attempt 1. The assembly fix adds the original authority
inventory and verifies exact archive membership; qualified runner code is unchanged.
All historical preservation fingerprints and original source inventory members
are checked again before archive creation.

## Storage, time and cost

Raw history duplication would add 62.30 GiB across working/backup staging and was
rejected during implementation. The hash-verified compressed history is about
1.23 MB: repeating its payload across 1,498 slots adds approximately 1.72 GiB cloud
and 3.43 GiB across two local copies. It retains full original evidence and keeps
the existing 50-GiB working/backup allowances and 30-GiB cloud cap unchanged.
These are incremental payload measurements, not a guarantee of every future
slot's growth; actual resource and storage guards remain mandatory.

`feasibility.json` recalculates using the original start, unchanged accepted rates,
US$1.25 reserve, two hours preparation and 30 minutes shutdown/backup allowance.
The observation-only lower bound is 249.67 hours. The retained pilot median
reference gives 255.24 hours, excluding new main preparation/backup variation.
At the report's measurement time, the 12-day allowance fits at approximately
US$52.5; the 13-day allowance exceeds US$55 at approximately US$56.0 and therefore
does not fit the admission policy. No limit is increased.

The unchanged absolute deadline is **22 October 2026, 15:24:23.810674 UTC**.
The 12-day planning route must begin preparation by **8 October 2026,
23:19:40.337448 UTC** under the conservative cost clock. Later review consumes that
margin. Credits read US$119.37, FREE/ACTIVE; credits do not override the US$65
campaign policy or US$55 guard. Billing is delayed and retained disk/S3 charges
continue while stopped. The current stopped disk requires a retention disposition
by **9 October 2026, 21:05:37.547530 UTC**.

## Review readiness and remaining actions

The two requested implementation blockers are resolved subject to the final
verification record. This is ready for review, **not deployment approval**.

1. Review the exact candidate inventory/archive and both separate timing sidecars.
2. Decide acceptance, then freeze this exact version; launch remains separate.
3. Recheck remaining time/cost at any authorized deployment. Stop if it no longer fits.
4. Qualify actual fresh-host source/dependencies, imports, permissions, versioned
   backups, resources and independent absolute timers before any next admission.
5. Resolve retained stopped-disk disposition within its original limit.

No broad pilot or research extension is proposed. Tests do not guarantee an
error-free campaign. Scripted/tone/client-ACK evidence supports protocol outcomes,
not actual speech exposure, hearing or comprehension; no superiority claim is made.

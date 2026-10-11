# v7 combined continuation decision

**Ready for review, not accepted, frozen or deployed.** AWS instance
`i-057344e5372faf62f` was independently read as **stopped** during this task.
Its retained encrypted 160-GiB root and every S3/local evidence copy remain.
No research execution, pilot, application-stack start or cloud write occurred.

## Two decisions

| Decision | Recommendation | Why and consequence |
|---|---|---|
| Cost admission | US$55 → **US$60**, total ceiling **US$65** unchanged | Original-clock accounting now exhausts the old guard before the unchanged planning allowance ends. About US$56 conservative projected total includes prior spending, retained disk, US$1.25 handover reserve, requests and full 60-GiB monthly storage. US$5 remains between admission guard and ceiling. No automatic increase. |
| Evidence capacity | Cloud all-version cap **30 → 60 GiB**; dedicated future local backup cap **50 → 60 GiB** | Revised complete metadata archives and growing ledger project **52.64 GiB**, including twice observed compressed-ledger growth and backup-index allowance. Keep every local archive, original raw trace/grade and pinned S3 version. Remove only redundant future staging after committed BACKED_UP and verification of local archive members, pinned cloud checksum, identity and owned path. Preserve all 82 originals, partial transfers/extractions and unsuccessful attempts. |

60 GiB is **64,424,509,440 bytes**. The projection leaves **7.36 GiB**,
including the unchanged 1-GiB next-slot reservation. Cloud inventory counts all
versions and outstanding reservations; unavailable or incomplete inventory stops
admissions. Existing 50-GiB working limit, 20/10-GiB disk and 2/1-GiB available-RAM
thresholds remain. No disk enlargement or paid service is proposed. Uncompressed
duplicate staging must not accumulate once the verified archive is retained.

## Feasibility and limits

The reviewed **274.512683578 hours** remaining allowance is unchanged. With two
hours preparation and 30 minutes shutdown, the 9 October 14:26 UTC estimate
finishes **21 October about 03:27 UTC**, before the original absolute stop of
**22 October 2026, 15:24:23.810674 UTC**. Conservative projected cost is **US$55.99**;
explicit-resource estimate is **US$53.31**. Full original-clock cost at the
absolute deadline is approximately **US$61.23**, within US$65; the US$60 guard
would prohibit new admissions earlier. Conservative latest preparation start
is **10 October 2026, 17:58:35.361023 UTC**, subject to fresh feasibility.

These are estimates, not guaranteed completion or invoice caps. Rates are the
retained 9 October pricing measurements: compute US$0.1197/hour, IPv4 US$0.005/hour,
gp3 US$0.096/GiB-month and conservative S3 US$0.025/GiB-month. The proposal reserves
US$1.50 for a full month at 60 GiB, US$0.75 above the old storage reserve. Paused
elapsed time is still charged conservatively; the clock is never reset. The
observed ~245-hour throughput projection does **not** replace the reviewed
allowance. Largest observed archive and twice observed ledger growth are
planning assumptions; unusually large results, more delays or backup failures
can still prevent completion. Fresh prices, credits, retained storage, all
previous spending and capacity must pass before host start and admission.

Billing latency means these guards cannot enforce an instantaneous invoiced
US$65 cap. Unknown usage, reserve exhaustion, unexpected responses, failed
backups and time/resource limits still pause; none is bypassed. Escalate before
retention consumes its reserve. The existing root-retention decision remains
**11 October 2026, 09:33:51.252814 UTC**; review does not reset that limit.

## Evidence and narrow runtime changes

Reused v6: **14 distinct backup-closure/order controls**, all three actual
metadata readbacks, pinned Linux evidence, source closure and static checks.
Its two timed full-suite attempts remain recorded as timed out, not PASS.
No completed v6 test was rerun. Frozen v5 and unaccepted v6 are unchanged;
v7 freezes against **frozen v5**, citing v6 qualification separately.

The declared new-only set ran once: **8/8 PASS**, 0.248 seconds test time,
3.110 seconds wall time, network disabled, pinned deployment Linux image.
It covers historic defaults, proposed effective limits, cost/archive stop
thresholds, safe redundant removal/recovery, missing/corrupted archive,
unexpected staging content, outside paths and historical exclusion. These tiny
temporary-data checks are not live-host or research qualification. Existing
authorization/refusal/collector/backup qualifications are reused. Initial lint
format failures were retained; final Ruff and mypy passed seven runtime modules.

Runtime differences from v6, exactly:

- `controls.py`: accepts explicit 60/60 continuation thresholds; historical
  55/30 defaults and serialized original policy remain identical. Admission uses
  effective cost/local archive limits. Legacy `CLOUD_30GIB_*` error names remain;
  they report a capacity stop against the effective limit, not a 30-GiB policy.
- `operational_limits.py` and immutable proposal: pin exact amendment bytes;
  retain original elapsed clock and add full 60-GiB storage/US$1.25 reserve.
- `handover.py`: authenticate original authority against original 55/30 policy;
  additionally require the exact amendment hash in new signed continuation
  receipts, readiness and version provenance. Historical receipts are not
  rewritten or retrospectively reinterpreted.
- `closed_restart.py`: new v7 source/receipt/metadata paths and dedicated v7 backup
  directory; same imported 82/1,418 identities and notices, same sequence 83.
- `staging_retention.py`, narrow `runner.py` hooks: verify two retained copies,
  remove only redundant future staging after backup/retirement, retain durable
  intent/completion and recover interrupted removal without executing a driver.
  Failure reaches the existing durable protocol pause before next admission.
- New offline control file and unexecuted post-acceptance freeze helper.

`storage.py`, `postflight.py`, `prelaunch_backup.py`, refusal/response guards,
application, migrations, inputs, saved order, endpoints, oracle, analysis and
600-second windows are byte-identical to v6. No shutdown-policy change:
pause alone can leave compute running; existing watchdog, absolute timer,
independent preparation guard and bounded operator shutdown remain required.

## One combined acceptance, freeze and deployment decision

The exact package/archive hashes are in `candidate-package.json`. Acceptance must
identify those bytes and both proposed decisions, including future redundant
staging retention. It may simultaneously authorize immutable freeze verification,
the reviewed retained-host deployment route and continuation **only if all live
gates pass**. Neither this report nor the prepared helper records acceptance.

After acceptance: verify/freeze parent chain and amendment; record separate
deployment authorization bound to actual run/host; recalculate feasibility;
verify independent pre-start stop guard; boot retained host only under that
authorization; import metadata and verify all 82 backups; execute the qualified
prelaunch-backup → genuine readiness/launch receipt → complete-backup order;
verify timers, permissions, hashes, capacity and backup readbacks; release only
the reviewed import pause; start standalone service. Never start the old campaign
service or clear a later failure pause.

Exactly **82 BACKED_UP + 1,418 PLANNED**, no active original. Next:
**sequence 83, B3, attempt 1, `01a11705-11f1-792b-ae1e-36bfc6773842`**.
No replay or replacement. Original raw FAILED statuses, grades and separate
timing sidecars stay traceable. Actual admission must be reported separately
from authorization.

Remaining action: **one human decision on this exact combined package**. Live
gates remain mandatory afterwards; their results are not fabricated here.

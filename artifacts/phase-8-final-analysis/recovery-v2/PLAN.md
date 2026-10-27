# Interrupted extraction recovery v2

This changes an evidence-access helper only. Frozen application, oracle, grades,
analysis, original executions and campaign host remain untouched. Do not run v1
again. The first interrupted attempt and every existing file remain in place.

Files: cloud_recover_final_v2.py (bounded, single recovery read process),
qualification.txt and verification.json (offline checks and exact executable hash),
REPORT.md (reported boundary, uncertainty and manual handoff).

Fixed qualification before any cloud recovery: eight small, offline synthetic
controls; at most 60 seconds. Cover exact reused identity/receipt binding, changed
identity rejection, incomplete/noncanonical record rejection, ambiguous request
binding, preservation of the original absolute deadline and expired refusal,
one-read failure with durable evidence/no retry, preservation of old files on
collision and bounded final bundle production. Reuse v1's eight archive/storage
controls; do not rerun them or any research scenario.

Reported boundary: cached 1–735; 393 completed compact records 736–1128;
394 request records 736–1129. Request 1129 has UNKNOWN transport completion.
393 saved records are not described as independently received until returned.

An explicitly invoked recovery may make exactly one additional GET for pinned
1129 and one first GET for each 1130–1500: 372 total recovery GETs, 22,198,827,558
compressed bytes. This is a separate, labelled evidence retrieval, not a research
execution retry. Aggregate conservative bound including possibly fully read
interrupted 1129 is 41,994,945,578 bytes and 766 GET requests across both attempts.
No automatic retries/restarts. Unknown original 1129 completion remains UNKNOWN.

Keep the original absolute extraction deadline: 2026-10-25T16:40:05.249100Z
(original wall_started 1792932005.2491002 + 14400 seconds). Never reset it.
The campaign's separate deadline is unchanged. Preserve 192-MiB total staging,
2-MiB failure reserve, 48-MiB compact records and 32-MiB final bundle bounds.
Existing directory contents count. Original attempt.json stays unchanged;
recovery metadata explicitly records the extra read and original deadline.

Foreground only, with a manual Enter prompt every 50 retrieved archives and a
process timeout derived from the original deadline. This is not an unattended
CloudShell service. AWS documents that background activity does not prevent
20–30-minute idle termination; that is consistent with, but does not establish,
the observed stop around 1196.5 seconds. Exact termination cause is unknown.

Preconditions: exact v1 script hash; exact extraction control; exact existing
boundary and request/receipt bindings; no existing recovery attempt; no active
extractor; expected project/region; campaign EC2 STOPPED; disk capacity; original
deadline still live. Any failed check stops. SIGINT/TERM, timeouts, read errors,
identity/hash/manifest failures preserve a durable failure when possible.

No AWS calls in local qualification. No campaign boot, S3 write, evidence deletion,
dependency installation, new analysis or retrospective grading.

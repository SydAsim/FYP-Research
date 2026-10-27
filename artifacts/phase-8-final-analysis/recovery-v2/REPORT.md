# Final evidence extraction recovery v2

Status: READY_FOR_MANUAL_BOUNDED_HANDOFF; NOT EXECUTED IN CLOUDSHELL.

## What is demonstrated

The user returned 393 retained compact records (736–1128), 394 request records
(736–1129), no matching extractor process, no failure.json, no verification.json,
and no final bundle. The first735 results are retained separately. Request1129
is durably recorded but its transport completion is UNKNOWN. It is not counted
as a verified result. No research execution failed merely because this retrieval
was interrupted. All1500 original executions remain backed up.

CloudShell idle termination after20–30minutes is documented; the last progress
was1196.5seconds. This is consistent with that possibility, not proof of cause.
No kernel/session termination evidence was returned. nohup protects against
hangup signals; it cannot guarantee survival of the CloudShell environment.
Reference: https://docs.aws.amazon.com/cloudshell/latest/userguide/limits.html

## Narrow helper changes and checks

The original v1 executable remains unchanged, SHA256
4890790c30a48f3c7e243e5cf5c50ad3ced1a0fcae4b79065c83f1b7b40f8b50.
The new helper imports only that hash-pinned verifier. It validates every reused
identity/receipt/record/request, preserves original file hashes, and appends
recovery metadata. It explicitly labels one additional pinned1129GET; it does
not convert unknown completion into a success/failure, replay a scenario, call an
oracle, or change grades. No application, analysis or frozen source is edited.

Eight focused offline controls pass (qualification-attempt2.txt,7.909seconds),
including a temporary exact393-record/394-request filesystem boundary, changed
identities/receipts, incomplete data, original deadline expiry, mocked single-read
failure with durable evidence/no retry, collision preservation and final bundle
member/hash/buffer bounds. Earlier successful small controls are retained in
qualification-attempt1.txt. Initial lint failures (unused import/line lengths)
and initial mypy missing AWS SDK stubs were resolved; logs remain. Ruff passes.
Mypy Linux-target passes with missing third-party SDK imports treated as untyped
boundaries; no dependency was installed. These are local Windows executions,
not claimed to be a pinned-Linux execution. Handoff repeats the same eight small
offline controls once on the available CloudShell Linux runtime before any AWS
call. Reuse prior v1 archive/storage qualification; no research scenarios or
pilot were run. Passing controls do not guarantee an error-free retrieval.

## Fixed recovery budget and evidence

Exactly372 recovery GETs (1129–1500),22198827558 compressed bytes. First393 compact
records are reused, not redownloaded. Original1129request remains unchanged;
its separately labelled additional read is bounded to51589081bytes, one GET.
Conservative aggregate bound across attempts:766GETs and41994945578bytes,
including a possibly fully transferred original1129GET. Each new call has
5-second connect/25-second read timeouts and no SDK retries. Any failure stops;
there is no automatic restart. Invoking the recovery requires the explicit
--recover-request-1129-once option; this is a labelled exception to the first
attempt's one-GET plan, not a claim the old budget is unchanged.

The original extraction deadline remains2026-10-25T16:40:05.249100Z
(21:40Pakistan), with no clock reset. The helper and outer process timeout use
only time remaining to that deadline. If already expired, do not run it or edit
the anchor. Total192MiBstage includes all existing records/requests/logs;2MiB
failure reserve,48MiBcompact bound and32MiBbundle bound are preserved. Files
use exclusive creation; partial records/failed attempts are not erased. Original
attempt.json is not rewritten. Final four-member bundle remains compatible with
the existing dataset assembler; recovery provenance is embedded in its hashed
all-results.json. All original outcome/analysis rows are preserved.

Use foreground timeout --foreground (TTY interaction enabled), no nohup or '&'.
Manual Enter prompts every50new archives avoid relying on background output as
interaction; they do not constitute an unattended service or prove cause/fix of
the previous termination. Keep the CloudShell tab active; if it stops again,
retain evidence and do not rerun v1/v2. No campaign boot, S3 write or new resource.

## Exact handoff

File: C:/Users/syeda/Downloads/cloud_recover_final_v2.py
SHA256: bdb1ed3791410dbdbeea1c50026d8e90179ea26ea7b2e537a312bf7f8271508d
Bytes: 26368

Upload this new file beside the existing unchanged v1 script in
/home/cloudshell-user. Follow HANDOFF.md. Expected result is PASS with1500records,
bytes and SHA256 of /home/cloudshell-user/fyp-phase8-final-evidence-v1/final-records.tar.gz.
Download that file and return its printed SHA256. Only then verify/assemble the
complete dataset and run the unchanged statistical analysis. No final analysis
or superiority claim has been made.

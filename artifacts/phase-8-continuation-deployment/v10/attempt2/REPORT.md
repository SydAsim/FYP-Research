# Guarded v10 attempt 2 — stopped before boot

## Result

**BLOCKED: deployment control and storage verification did not pass.** There was
no boot, SSM mutation/resend, source upload, pause release, readiness/launch
receipt, new backup, or sequence-146 admission in this attempt. Required
qualification was reused; no research scenarios or successful tests were rerun.

EC2 DescribeInstances verified the owned retained host
`i-057344e5372faf62f` **STOPPED** at **2026-10-12T17:44:36.106893Z** (the exact
request/result files are authoritative for the recorded time). The owned root
`vol-09dbb42bbf607f5de` remains attached and DeleteOnTermination is false. Nothing
was deleted. No service can execute while EC2 is stopped; internal systemd state
was not freshly inspected.

## Bounded reconciliation and exact failures

The original request at **2026-10-12T16:27:20.228195Z**, its ReadTimeout and exact
parameters are preserved in the parent deployment directory. This attempt used
a wider 16:20–16:45 UTC window, not just InvokedAfter the client request instant:

| Read | Retained result |
| --- | --- |
| EC2 instance | Successful, stopped, owned project/root |
| SSM ListCommands, wider window | Empty, no continuation token |
| SSM ListCommandInvocations, details | Empty, no continuation token |
| CloudTrail SendCommand lookup, wider window | Empty, no continuation token |
| STS identity | ReadTimeout on the Sydney STS endpoint |
| SSM unfiltered instance history | Process deadline at 45 seconds |
| Free Tier plan | FREE/ACTIVE, project 803656589923, US$108.01 credits |
| Pinned existing source HEAD | ReadTimeout on the Sydney S3 endpoint |
| All-version campaign-prefix inventory | Process deadline at 45 seconds |
| Absolute AWS shutdown schedule | Successful, ENABLED, exact owned target |

All ten finite requests are retained. No request automatically retried. The
four-request reconciliation plan and four-request feasibility preflight each
had explicit per-process bounds. The two extra read-only identity/unfiltered
history checks are separately recorded. This is an intermittent control-plane
access failure, **not** a demonstrated authentication rejection. Listing absence
and CloudTrail absence do not establish the original command's nonexecution.
Its historical execution status remains **UNKNOWN**.

## Justified recovery procedure for the ambiguous command

The original request contains delivery TimeoutSeconds **60** and document
executionTimeout **1200**. AWS documents delivery expiry using their sum,
**1260 seconds**, and execution timeout separately. See
[AWS command timeout semantics](https://docs.aws.amazon.com/systems-manager/latest/userguide/monitor-commands.html).
The nominal delivery deadline from the recorded request is 16:48:20.228195 UTC.
This calculation is a temporal fence, not evidence that the command did not run.
Allowing the previous 90-second caller process bound, an additional full
execution allowance and five minutes of uncertainty gives a conservative
fence of **17:14:50.228195 UTC**. This had passed before the new reads. The host
is stopped, so an old local process is not executing now.

Before any later guarded boot, CloudShell must establish reliable ownership,
history and capacity reads. A located command must have its exact parameters
matched and status inspected; pending/delayed execution is not ignored.
After a verified independent preparation-stop guard and feasibility pass, the
first remote operation must inspect the original transferred script, preserved
unit-state record, quiescence proof, agent status/journal and durable pause.
Verify script hash **7eefdb7535e94d39d39bc02facb54c7c97aeb9160f6ec16f8ae59b81ef3575ff**
and parameters hash **4f562f64821af73d684d016fecbe972c710cadd8375d1005491d0342aa161d5d**.
Retain every partial file and record; do not re-execute the original exclusive
`xb` transfer wrapper or overwrite its evidence. A proven completed quiescence
can be verified in place. A partial/absent result requires a separately named,
owned-unit conditional quiescence operation after confirming no active old
operation. Any unresolved execution hazard or unexpected root state stops the
attempt. No deployment-write retry is justified by an empty listing alone.

That procedure was **not executed**: today's response reliability/source and
inventory gates failed. The read-only CloudShell controller and complete manual
instructions are in `CLOUDSHELL-HANDOFF.md`. Only the read-only controller stage
has been prepared and statically reviewed; alternate-route launch qualification
and actual host readiness are not claimed.

## Frozen package and evidence

Existing local verification passed: all **3,441** inventoried source files,
archive bytes/hash, freeze-manifest signature, accepted/freeze receipt signatures,
and parent-v9 manifest binding. This verifies the unchanged freeze, not a new
freeze or another test qualification.

- Package: `bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c`
- Archive: `212269264d45ac8bd6637c2ca0ca5e09c951d354cb445c9bf7a16c6ba2d0ba37`
- Freeze manifest: `e4b6888f560575c5808267947a0a8b62b9b678dbbf6e1d07c20880a88aeda74b`
- Overlay: `6d86b62931593e80e7cedd5371d9a72c14075b17d9a30c541e950e0f6af9af68`

The previously successful uploaded source version
`QmAcYmVhFW5GHo08qBB01sD.laBJlcyo` is retained and was not uploaded again. Its
current HEAD verification failed; the prior successful receipt is not represented
as a fresh pass.

All **145 BACKED_UP / 1,355 PLANNED** identities/order remain protected. This
is the last verified research boundary; a fresh root audit was not reached.
Next remains **146 / P2 / attempt 1**, execution
`01a11705-11f1-772d-8190-c43552871801`. No original, raw FAILED status, grade,
timestamp, archived trace, sidecar or backup was changed.

Existing independent backup references remain:

- Original 145: `8abe7597a0e59154cf66e682fd08f3440fff815c458db0bdc8fe83666091ad24`,
  pinned S3 version `RPSiYO12M2tM251ZCuLVOEK3IUn4NYHM`.
- Closed-145 master: `b40bc792c0e7c9d94edc513a24bfae1abe8536475947be13a1ee35949b6ced08`,
  pinned S3 version `3pLbzfgLl6SW0nbeiXBi3QZiCEvGt4pt`.

No fresh PRELAUNCH or COMPLETE backup receipts were created. Both independent
readbacks remain mandatory in the accepted order before admission.

## Feasibility and guards

At **2026-10-12T17:52:01.664717Z**, unchanged planning allowance is **262.3164 h**
for 1,355 slots, plus **2.5 h** preparation/shutdown and **24 h** operational
uncertainty. These assumptions were not reduced to pass.

- Expected shutdown: **2026-10-23T18:41:00.783542Z**; forecast **US$65.70**.
- With uncertainty reserve: **2026-10-24T18:41:00.783542Z**; **US$69.20**.
- Full amended deadline forecast: **US$72.22**, separate from completion estimate.
- Admission/total remain **US$70 / US$75**. Planning headroom before the reserved
  admission forecast reaches US$70 is approximately **5.49 further elapsed hours**,
  if the accepted rates and remaining allowance remain valid. This is not a new
  deadline or permission to omit later feasibility checks.

Accounting retains every elapsed stopped/running hour from the original anchor,
the earlier preparation boot, full 80-GiB S3 month, 48-hour root, request and
handover reserves. Latest credits are US$108.01. Fresh actual billing was not
available in this attempt; prior Cost Explorer US$11.3541 was estimated project-wide
gross usage and is not substituted for accepted campaign accounting.

The last complete inventory plus known successful source upload gives a
**minimum** projected 78.7753 GiB including the 1-GiB slot reservation. Fresh
all-version inventory timed out, so actual capacity and projection **do not
pass**. No zero-use assumption or old measurement was substituted.

Absolute Scheduler readback at **17:48:21.131604Z** confirms enabled exact-host
stop at **2026-10-25T15:24:23 UTC**, less than one second before the authoritative
fractional stop. No new preparation guard was created because boot gates failed.
The existing disabled preparation schedules were not changed. Internal timer/
watchdog upgrade remains unperformed. Root evidence is retained; retention
decision remains due no later than **2026-10-27T15:24:23.810674Z**.

**Recommended next action:** run the single supplied read-only CloudShell handoff
and return its small verified control bundle. No additional acceptance or freeze
is requested. Current authorization is retained; boot/admission remain blocked
until reconciliation, live storage and all accepted readiness gates actually pass.

## External artifact changes only

`reconcile.py`, `read_control.py` and `preflight_read.py` record bounded read-only
requests, errors and deadlines without a write/retry path. `verify_existing.py`
rechecks immutable source/archive/signatures. `finish_status.py` records the
unchanged planning model and exact blocked state. `cloudshell-control-preflight.py`
and its handoff are the portable read-only control stage, with hash, finite
requests and retained outcomes. Its only validation here was syntax/static
review; it has not run in the user's CloudShell session. The handoff binding
supersedes the earlier intermediate script hash in `final-status.json` after a
portable streaming-hash adjustment made before any upload. `final-state.json`
binds the exact final handoff. No frozen study code/package was edited.

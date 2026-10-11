# Phase 8.2 — finite AWS execution qualification v1

Prepared before AWS resource creation. Status: awaiting finite spending-limit
decision. This is calibration, not a protocol freeze or the main campaign.

## Scope and preservation

Keep 500 inputs across B3/P1/P2 (1,500 main slots), all NOT_STARTED. Preserve
application, migrations, existing endpoints, v4 fixture bytes, observation and
retry budgets. Preserve Phase 7 and every earlier qualification, including
unsuccessful attempts. Verify `preserved-before.json` before and after work.

Use the verified 8.1 source capsule unchanged, SHA-256
`2cbc081470257e3fa7c9c9c25ec749af1024b2d29496f99fbaf6511d1e4a1fe5`.
New AWS orchestration, run records and any calibration-only derivative plans live
in this separate versioned package. Source/fixture edits require a new package;
failed outcomes cannot be overwritten by reruns.

## Proposed resources and spending rules

One temporary Ubuntu 24.04 x86_64 `t3.large`: two vCPUs, 8GiB RAM, 40GiB encrypted
gp3 root disk. Region ap-southeast-2, profile fyp-research. Standard CPU credits
prevent surplus-credit charges; throttling is measured and reported. Start with
one execution; the extra headroom permits a conditional, finite two-lane check.

Use no inbound network ports. Access through Systems Manager with a dedicated
EC2 instance role; grant only SSM node management and access to a dedicated
research S3 bucket/prefix. No human access-role changes, credentials in source,
NAT gateway, load balancer, paid voice APIs or managed database purchases.

Recommend a **US$2 credit-consumption ceiling** and a maximum **four-hour powered
session**, covering preparation, tests and downloads. Do not provision until the
human accepts the spending limit. Stop new admissions at least 20 minutes before
the host stop deadline; keep the existing 600-second windows. A host deadline
interrupting an unfinished observation is an infrastructure failure with retained
missingness, never a completed result.

Automatically stop the instance at the four-hour limit and after qualification
finishes. Retain disk/evidence until verified exports reach S3 and the local
backup. Obtain the user's keep/cleanup choice before deleting successful AWS
resources. A stopped 40GiB disk still costs approximately US$0.126/day; the US$2
estimate assumes at most seven days of disk retention and <=1GiB research exports.
These are operational controls, not an instantaneous AWS billing hard cap. A
failure of shutdown/export must produce a clear notice and preserve the disk.

## Finite admission order and qualification gates

1. Record AMI, Python, OS, Docker/image identities, UTC clock, RAM/disk headroom,
   CPU credit configuration, quota and pricing. Verify the capsule and original
   evidence hashes. Native host boot uses separate PostgreSQL truth/application
   servers and companion cache; no existing resource is reset.
2. Execute the existing two-slot Linux qualification queue under fresh execution
   UUIDs and dedicated AWS resources. The `cal-v4-linux-v1-*` IDs come only from
   the calibration bank; their AWS run directory distinguishes this qualification
   from the earlier boot-only package, which admitted zero slots.
3. For clean B3, checkpoint after the first two polls. Resume from a separate
   process with exactly the same execution ID, SQL checkpoint and original
   deadline. Pause after its immutable export. Resume saved order for the P1
   buffered stale-start refusal. Collect both complete 600-second windows after
   the actual final-request anchor, including effects after normal return/refusal.
4. Run the finite queue under systemd/normal terminal, independent of Codex. Test
   parent stop and reattach while the detached collector continues. Never replay
   an interrupted driver. Verify drift rejection, unchanged main guard, immutable
   backup/export hashes and original-attempt retention. Missing final anchors
   retain the fixed fallback cutoff and unknown outcome/timing rules.
5. Only after one full execution establishes >=4GiB available host RAM and disk
   reserves, consider exactly two concurrent isolated calibration executions.
   Before their admission, seal their IDs, fixtures, faults and checks separately.
   Service/process namespaces, PostgreSQL servers, cache, query scopes and source
   bindings must be separate. Exercise owned worker restart and cache operations
   against an unaffected peer. If isolation is not demonstrated, retain a serial
   recommendation and label those cases exclusive. Do not expand testing to
   optimize throughput.
6. Record every failure, timeout, refusal, unresolved result and collection gap.
   Debugging runs need new attempt IDs and DIAGNOSTIC labels; no replacements.
   Export and hash-verify evidence before shutdown/cleanup decisions.

## Measurements and interpretation

Retain sampled RAM/available RAM, CPU load/credits, database/WAL sizes, logs,
scripted audio, polls, exports, backup growth, runtime, poll gaps and overshoot.
Sampled peaks do not bound unsampled peaks. No shortened observation windows.
No cloud latency inference or concurrency speedup claim without its evidence.

Continue the accepted clustered timing pipeline: paired inputs are the sampling
unit; repeated calibration executions are not new independent inputs. Any
concurrent host blocks induce shared dependence and must be recorded. Calibration
outcomes qualify infrastructure; they cannot establish superiority or novelty.
All audio/ACK evidence here is synthetic protocol evidence, not proof of hearing,
ASR performance or human understanding.

Exit only after reporting PASS/FAIL/UNRESOLVED for each actual check, retained
trace links, measured serial/qualified parallel estimates and remaining main
review/freeze/launch gates. Do not launch any main input.

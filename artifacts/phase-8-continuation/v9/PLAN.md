# Authorized storage-only completion of qualified v8

Create a new short source copy and complete v9 inventory/archive. Do not edit
v7 or v8 in place. Preserve the pinned 120/1,380 boundary and qualified v8
clock, refusal, response, ledger, backup and handover implementations.

Runtime changes: `controls.py` permits the explicitly authorized 80-GiB
cloud value; `operational_limits.py` and its JSON bind 80-GiB cloud/local
caps and reserve the full 80 GiB for one month. `handover.py` and
`closed_restart.py` bind the new overlay hash; v9 source/receipt/backup paths
replace proposed v8 paths. No other runtime differences are permitted.
All application, fixture, oracle, analysis and observation code stays unchanged.

Fixed qualification: eight offline control tests, zero research executions,
120-second maximum wall time, existing pinned Linux image, network disabled.
Tests cover effective caps/default historical policy, full-month cost reserve,
cloud pass/boundary stop with reservation, local pass/boundary stop with
reservation, unauthorised larger cap rejection, overlay tamper rejection,
unchanged five-second clock guard, and unchanged qualified source closure.
Stop on a failed check; retain every attempt. Reuse v8's 18 qualified checks.

Measure local disk/memory, reuse recorded host measurements for preboot capacity
planning, refresh prices/credits/S3 versions and conservative cost allowance.
Actual host headroom remains a mandatory postboot gate. No deadline or budget
reset. User authority is conditional, not personal review of unseen final code.

After exact verification, record that instruction and condition evidence, freeze
against frozen v7 and verify the chain. Establish and read back an independent
preparation stop before retained-host boot. Preserve/quiesce owned old units
before readiness. Complete prelaunch backup/readback, real readiness/launch,
complete backup/readback and unchanged timers before admitting sequence 121.
On any failed gate preserve evidence and stop safely. No historical deletion.

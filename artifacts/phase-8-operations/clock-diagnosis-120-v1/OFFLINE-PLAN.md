# Bounded clock diagnosis controls

Ten deterministic offline controls, maximum 30 seconds. No research execution,
services, observation windows, real clock changes or AWS boot.

Use the exact frozen v7 `clock_check` function extracted by Python AST (hashed
source), then the exact watchdog call expression and function with isolated
in-memory doubles. Test paired clocks, stale reads at 4.999/5/5.001 seconds,
fresh reads after slow work, true six-second rollback, a six-second anchor
offset, wrong boot, decreasing monotonic time, and the actual watchdog argument
evaluation order with eight seconds of synthetic resource/inventory work.

PASS means the expected check result was reproduced. These controls demonstrate
the measurement mechanism; they do not manufacture historical trigger readings
or qualify a deployment correction. Retain every result and failure. Stop on any
unexpected result and report it; do not patch the frozen implementation.

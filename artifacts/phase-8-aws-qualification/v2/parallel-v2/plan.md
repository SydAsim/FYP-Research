# Conditional two-lane calibration, revision 1

Sealed before either lane is admitted. Main inputs remain disabled. This package
does not change application code, migrations, v4 fixtures or endpoints.

Files added: `lane.py` constructs a separate, immutable one-slot calibration
ledger; `parallel.py` supervises two separate PID/network namespaces and retains
cross-execution checks. Each supports ownership isolation and original-attempt
retention. The historical Linux runner, oracle, 600-second windows and fault
budgets are reused unchanged. This extends its previously local-validation
bridge mode to a dedicated AWS qualification; it is not a native-host deployment
qualification for overlapping fixed host ports.

Admission requires a completed serial export, >=4 GiB available host RAM, and
the existing disk reserves. Exactly two new calibration cases use unchanged v4
calibration recipes: A `restart-before-repair`, P2; B `redis-loss`, P2. IDs are
`cal-v4-linux-v1-aws-parallel-v2-A` and `cal-v4-linux-v1-aws-parallel-v2-B`. Neither is a
main input or an additional independent study unit.

Each lane has its own network and PID namespace, PostgreSQL application and
truth servers, Redis, service processes, bindings, collection queries, ledger,
outputs and backup. Host dependencies and sealed source are shared read-only.
Limits: each service namespace 2 GiB and one CPU; existing database/cache limits
remain unchanged. No AWS credentials, paid API calls or public service ports.

A named `BOTH_RESOURCES_READY` release starts both collectors. Plant separate
cache sentinels before release. B's FLUSHDB must erase only B's sentinel. A's
worker restart must use its own saved PID identity and leave B's worker lifecycle
unchanged. Verify disjoint workflow IDs in the independently collected histories,
no published database ports, complete windows, oracle success, immutable exports
and backup verification. Preserve each failure and stop admissions; no replacement
or tuning run is authorized by this finite plan.

These two recipes qualify their observed isolation only. Other recipes remain
serial/exclusive until their own isolation is demonstrated. Do not halve the
entire main-campaign runtime or claim equal latency distributions from this pair.
Synthetic playback acknowledgements and tones are protocol proxies.

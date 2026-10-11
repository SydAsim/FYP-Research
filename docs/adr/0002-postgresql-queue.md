# ADR 0002: PostgreSQL queue

Accepted for Phase 0 topology. PostgreSQL will own durable jobs, leases, intent, effects, evidence, permits, repair, outbox, and experiment records. Later workers will lease rows with `FOR UPDATE SKIP LOCKED`; Phase 0 has no leasing behavior. A migration and crash tests are required in the implementing phase.

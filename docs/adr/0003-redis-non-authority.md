# ADR 0003: Redis is disposable

Accepted. Redis is optional and profile-gated in Compose. It may carry expiring routing hints, scratch turn state, wakeups, or cache entries with explicit source version. Deleting Redis must not change correctness or erase recovery. No Phase 0 code reads Redis.

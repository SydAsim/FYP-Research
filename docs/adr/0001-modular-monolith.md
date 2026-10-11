# ADR 0001: Modular monolith

Accepted for Phase 0. Keep one repository and independently runnable web, API, voice, durable worker, and simulator processes. Shared domain and protocol code has no framework dependencies. This preserves explicit trust and latency boundaries without adding a distributed workflow system. Revisit only with measured requirements and a new ADR.

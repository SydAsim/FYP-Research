# Phase 5 implementation report

Status: **Phase 5 automated exit gate passed.** The strict local voice path and browser workspace are running in the Docker Compose stack. Work stops at Phase 5 on 2026-09-28.

## Scope implemented

- Indigo Intelligence shell and 17 caller, operations, and research routes, backed by controller APIs and PostgreSQL projections.
- LiveKit room joining by the voice worker. The media-token API reports READY only after the worker joins. The browser asks for microphone access when the user clicks Start microphone.
- Free local cascaded voice path: Vosk speech recognition, local Qwen typed intent proposal, deterministic server command and verification, then permit-bound eSpeak speech. Raw provider output and normalized events are durably recorded.
- Spoken booking and spoken time correction over real LiveKit PCM audio, using isolated synthetic fixtures and repeatable recorded WAV files.
- Browser journeys for normal booking, hidden commit correction, partial stale playback repair, Redis loss, call-end recovery, and all route views.

## Files changed

- Controller: apps/api_controller/phase5_models.py, phase5_service.py, phase5_routes.py, phase3_verification_service.py, phase3_claim_service.py, phase4_audio_service.py, and main.py.
- Voice worker: apps/voice_worker/main.py, live_agent.py, offline_adapters.py, cascade.py, and existing scheduler and transport integration.
- Protocol and contract: packages/protocol/voice.py, contracts/openapi.yaml, and generated apps/web/lib/api-types.ts.
- Web: apps/web/components/live-call.tsx, apps/web/app/call/[callId]/page.tsx, the Phase 5 shell and routes, API client, playback reporter, and Playwright suites.
- Environment: compose.yaml, deployment/livekit-local.yaml, Dockerfile.python, pyproject.toml, uv.lock, .dockerignore, and .gitignore. Large model files are ignored under models/.
- Tests and evidence: tests/unit/test_phase5_local_voice.py, tests/integration/test_phase5_ui.py, tests/audio/phase5-booking.wav, tests/audio/phase5-correction.wav, acceptance/phase5_live_voice.py, artifacts/phase-5-live-voice.json, README.md, and this report.

## Migrations added

- 0006_phase5_ui_data: scoped notes and stable synthetic demo records.
- 0007_phase5_drafts: unique evaluation draft command ID. No existing migration was edited. The live voice follow-up required no further schema migration.

## Invariants covered

- PostgreSQL owns revisions, operations, effects, receipts, permits, audio state, repair, and playback evidence. Redis can stop without changing the correct browser read state.
- The local LLM only proposes a typed start. A deterministic parser grounds date and time in the transcript and rejects disagreement; the model cannot create records or pronounce success.
- A rescheduled claim needs a current confirmed appointment row plus a linked local reschedule effect with before/after facts and the matching resource version. This proof is rechecked on permit publication and audio release.
- UNKNOWN, rejected clarification, and failure stay distinct. Ambiguous HTTP outcomes are recorded and not blindly retried.
- A decisive 3 PM or 4 PM speech segment needs an applicable SATISFIED receipt and current permit. The worker publishes no audio directly from an LLM response.
- The browser reports STARTED, progress, interruption, and completion. An exposed stale outcome creates durable repair; a queued stale outcome cannot start after revision change.

## Commands executed and results

- Docker Compose media/local-voice build and health wait: passed for API, web, voice worker, PostgreSQL, LiveKit, simulator, and local LLM.
- Python pytest with the project PostgreSQL on port 15432 and simulator truth PostgreSQL on port 5433: **60 passed, 0 failed**. After the final reschedule publication change, the focused Phase 5 PostgreSQL suite passed **3/3**.
- Ruff check and format, mypy across 55 typed source files, web TypeScript typecheck, ESLint, Prettier, production Next.js build, and six Vitest tests: passed.
- Playwright against the production Compose stack with system Chrome and the Redis fault enabled: **26 passed, 0 failed, 0 skipped**. The Redis container was restarted by the test.
- Recorded-audio acceptance command: .\.venv\Scripts\python.exe acceptance\phase5_live_voice.py. The final run passed in 19.2 seconds and wrote artifacts/phase-5-live-voice.json. The script requires both speech segments to reach PUBLISHED and no AgentTurnFailed or AgentTurnUnknown event.

## Successful trace

Call 617af39e-010c-4a64-a209-fbfdd8cc1807, workflow 9b15aad9-5259-479c-a7b9-912f0f540eea: LiveKit caller audio was transcribed as an October 3 booking at 3 PM and a correction to 4 PM. Revision 1 committed CREATE_APPOINTMENT and issued a SATISFIED CURRENT_APPOINTMENT receipt. Revision 2 superseded it, committed RESCHEDULE_APPOINTMENT, and issued a SATISFIED RESCHEDULED_APPOINTMENT receipt bound to appointment version 1. Two eSpeak segments reached PUBLISHED; the corrected deterministic text says the appointment has been moved to 4:00 PM on 2026-10-03 (Asia/Karachi). The saved acceptance artifact has the call, workflow, appointment, audio hashes, receipt and permit IDs, publication times, segment texts, and UTC check time.

## Expected failure trace

Earlier live call d933e827-f352-48f7-944f-25b7452d6d82 transcribed a 4 PM correction while the tiny local model proposed 2 PM. The grounding guard recorded ClarificationRequired and did not apply the incorrect time. A separate first reschedule proof returned UNKNOWN until the verifier was taught to read the local committed effect as well as the appointment row; it did not authorize moved-to speech. The partial stale playback browser test also confirmed that acknowledged exposure creates an OPEN repair obligation instead of silently discarding the stale statement.

## Known limitations

- The automated live speech acceptance streams recorded voice files through the LiveKit SDK; a human speaking into this machine's physical microphone has not been independently observed in this run. The browser room join, microphone control, and playback paths have Playwright coverage.
- The local Vosk model is English-only and small; noisy or differently accented speech can require clarification. The Qwen model is only 0.5B and may disagree with grounded time; such proposals are rejected.
- Loopback LiveKit advertisement is configured for this Windows Compose setup. Other devices need a reachable media address. Browser autoplay is gated by an explicit microphone gesture; previously published segments remain available through Play approved audio.
- The UI screen prose describes appointment create/cancel, dashboard SSE, and WebSocket timeline routes that lack executable contracts. OpenAPI lists reschedule without a controller route. The UI uses read-only appointment views and PostgreSQL polling; docs/06_SOURCE_CONFLICT_REPORT.md records the conflict.
- Route-specific empty, identity failure, offline, accessibility, and mobile checks are not exhaustive. The Phase 6 independent oracle, research arms, and statistical runner are not implemented.

## Deferred work

- Phase 6 scenario DSL, named barriers, independent simulator oracle, explicit B0/B1/B2/B3/P1/P2 profiles, replay bundles, and statistical analysis.
- Contract-backed appointment mutation and streaming UI routes after their request, response, and durable behavior are resolved.
- A user-assisted physical microphone check on this Windows machine, if desired, and broader speech robustness evaluation.

## Contract ambiguity requiring human decision

The UI specification routes listed above lack matching executable contracts; their mutation and stream semantics need definition before implementation. The earlier approved UUID exception remains: authoritative SQL keeps gen_random_uuid() defaults, and the existing application uses UUIDv4 consistently.

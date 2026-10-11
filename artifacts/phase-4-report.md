# Phase 4 implementation report

Status: **exit gate passed** on 2026-09-27. Work stops at Phase 4.

## Scope implemented

- Provider-neutral cascaded voice event interface, strict scripted research STT and typed-intent adapters, deterministic tone TTS, and server-controlled speech scheduler.
- Optional local LiveKit media service and worker transport that checks the durable segment state and revision while sending frames.
- Raw and normalized voice events; typed proposal acceptance through the server's revision command.
- Durable synthesized audio, queued/released/started/stopped/completed states, client playback event IDs and frame/word progress, fresh evidence checks on release/start/resume, and a durable stale-span repair obligation.
- Browser playback reporter library with server start acknowledgement, interruption buffer clearing, persisted retry IDs, and completion acknowledgement.
- Prerecorded P8 correction replay from synthetic spoken WAV through revised intent, repair, LiveKit send, and simulator truth.

## Files changed

- Migration: `database/migrations/versions/0005_phase4_playback_repair.py`.
- Controller: `apps/api_controller/phase1_service.py`, `phase4_models.py`, `phase4_audio_service.py`, `phase4_playback_service.py`, `phase4_voice_service.py`, `phase4_routes.py`, `main.py`.
- Voice: `apps/voice_worker/cascade.py`, `scheduler.py`, `livekit_transport.py`, `main.py`.
- Shared policy and protocol: `packages/speech_policy/phase4.py`, `packages/protocol/voice.py`.
- Client: `apps/web/lib/playback-reporter.ts`, `playback-reporter.test.ts`.
- Research and tests: `research/fixtures/audio/p8_correction.wav`, `p8_correction.json`, `research/replay/livekit_token.py`, `phase4_p8.py`, `tests/unit/test_phase4_cascade.py`, `test_phase4_playback_policy.py`, `tests/integration/test_phase4_postgres.py`, `artifacts/phase-4-p8-replay.json`.
- Configuration and documentation: `compose.yaml`, `.env.example`, local ignored `.env`, `pyproject.toml`, `uv.lock`, `contracts/openapi.yaml`, `.github/workflows/ci.yml`, `acceptance/traceability.csv`, `README.md`, this report.

## Migrations added

- `0005_phase4_playback`: durable raw/normalized voice events, segment audio and progress fields, playback response replay, one-segment-per-permit and one-repair-per-stale-span uniqueness, and repair claim constraint. Earlier migrations were not edited.

## Invariants covered

- A model proposal cannot directly create an appointment or authorize speech. The server validates the proposal, accepts an intent revision, verifies independent source state, and issues a single-use claim permit.
- A queued stale segment cannot start. Publication, start, and resume check the current revision and applicable evidence. LiveKit checks state and revision while carrying frames.
- An acknowledged stale decisive span opens a PostgreSQL repair obligation. Unplayed stale audio is cancelled without a repair. Late progress after a revision can still create or extend the same obligation.
- Corrected evidence and a repair segment do not satisfy the obligation until full client playback acknowledgement.
- Media end does not cancel durable external reconciliation. Redis is not a correctness store.
- Playback and voice events use stable IDs and conflict on changed facts.

## Commands executed and results

- `docker compose up -d --build --wait` with `POSTGRES_HOST_PORT=15432`: healthy core services. Host port 5432 was owned by an unrelated `wslrelay`; no process was stopped.
- `docker compose config` without a shell override resolved PostgreSQL to `127.0.0.1:15432` from the local ignored `.env`, so Docker Desktop's Compose start also uses the free port.
- `docker compose --profile media up -d --build --wait livekit voice-worker`: LiveKit and worker healthy.
- `docker compose --profile redis up -d --wait redis`: Redis healthy.
- `python -m pytest -q`: **52 passed, 0 failed**, two third-party TestClient deprecation warnings.
- After the final stale-audio fetch guard, `python -m pytest tests/integration/test_phase4_postgres.py -q`: **7 passed, 0 failed**; the LiveKit P8 replay passed again against rebuilt services.
- `ruff format --check .`, `ruff check .`, `mypy`: all passed (67 formatted Python files; 50 typed source files).
- `pnpm --dir apps/web typecheck`, `test`, `lint`, `build`, and Prettier check: all passed; **4 web tests, 0 failures**.
- Fresh temporary PostgreSQL database: Alembic `upgrade head`, `downgrade base`, `upgrade head` passed; database removed after the check.
- OpenAPI YAML parsed successfully: 30 paths, 27 schemas.
- `PHASE4_LIVEKIT_SMOKE=true python -m research.replay.phase4_p8`: passed and wrote `artifacts/phase-4-p8-replay.json`.
- Restarted API controller, voice worker, and Redis while a separate repair obligation was `OPEN`; a fresh HTTP request still returned `OPEN` afterward.

## Successful trace

`artifacts/phase-4-p8-replay.json` records prerecorded audio SHA-256 `96ca029eb97abef12a51320a3de68f84fa3a04c550f10d989f38687299c99032`. Revision 1's decisive segment began and acknowledged 500 ms, 8,000 frames, and two words. The scripted client reported interruption; the browser reporter's buffer clearing is tested separately. Twelve normalized voice events included `InterruptionCandidate` and `InterruptionAccepted`; the server accepted the 4 PM correction as revision 2. The stale segment remained `STOPPED`; the repair obligation captured the exact reported span and remained `OPEN` through correction. Independent simulator truth ended with `CREATE`, `RESCHEDULE` and one 4 PM appointment. Fresh revision-2 evidence authorized the repair text. LiveKit sent 51,840 corrected frames, and only the client's full completion acknowledgement changed the obligation to `REPAIR_PLAYED`.

## Expected failure trace

`test_queued_stale_audio_never_starts` prepared revision-1 audio, accepted revision 2 before playback, and received HTTP 409 for `STARTED`. The segment was `CANCELLED` and no `RepairRequired` event existed. `test_backchannel_resume_rejects_changed_provider_version` changed the simulator resource version after interruption; resume returned HTTP 409 `fresh-evidence-required` and the segment stayed `STOPPED`.

## Known limitations

- The deterministic research adapters use scripted transcription and typed intent plus tone WAV output. The P8 input itself is prerecorded spoken synthetic audio. Live model/provider adapters can be added behind the same interfaces without changing the protocol.
- The browser reporter is a tested library; attaching it to the Phase 5 live call screen and exercising real browser audio/WebRTC is deferred. The P8 gate uses a scripted playback client and a LiveKit publish smoke test; it does not prove a remote listener heard every frame.
- The word timeline divides deterministic speech duration evenly across words. A real TTS provider should supply alignment for a more accurate word exposure estimate. Milliseconds and frames are reported directly by the client.
- The local LiveKit dev server uses `devkey`/`secret` and is an optional Compose profile for research testing, not a production deployment.
- Windows host uses 15432 for this project's PostgreSQL because 5432 is occupied. CI retains default 5432.

## Deferred work

- Phase 5 UI route integration, identity/permission and offline screen states, and real browser playback tests.
- Phase 6 research arms, independent oracle, and full fault scheduler.
- Optional native-audio comparison adapter, after the strict cascaded arm is frozen.

## Contract ambiguity requiring human decision

None for Phase 4. The previously approved UUID exception remains: authoritative SQL `gen_random_uuid()` defaults are retained despite the general sortable-UUID instruction.

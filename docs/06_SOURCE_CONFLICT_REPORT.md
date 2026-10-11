# Source conflict report (pre-implementation, 2026-09-22)

Authority: the extracted implementation pack is authoritative for behavior, data, APIs, events, tests, and research. The guide explains it; UI references specify appearance only; the proposal and architecture image are background. No contradictory requirements have been merged.

| Lower-authority source | Conflict | Resolution |
|---|---|---|
| Landing mockup | Supabase branding | PostgreSQL is the durable authority; no Supabase claim. |
| Live call and A3 trace mockups | One linear PLAN-to-COMPLETE state | Persist and expose independent processing, effect knowledge, applicability, and speech eligibility dimensions. Explanatory stages may be shown separately. |
| Call summary, calendar, and appointment mockups | Immediate confirmed/complete state after a tool action | Display confirmed outcomes only with applicable verification evidence and claim authorization. Preserve UNKNOWN and recovering states. |
| A3 trace mockup | Model-style verification confidence is treated as proof | Show SATISFIED, VIOLATED, or UNKNOWN, predicates, source version, freshness, and applicability. |
| Evaluation mockup | A generic 500-test pass count | Report independent scenarios, repetitions, arms, exclusions, timeouts, endpoints, and confidence intervals. |
| Customer record mockup | Allergy/medical information | Use synthetic maintenance access, scheduling, and contact information only. |
| Escalations & Emergencies mockup | Medical inference and automated emergency protocols | Implement human maintenance handoffs only; no emergency automation. |
| Architecture image | Gemini Live/native audio appears to be the protocol center; Redis depicted alongside PostgreSQL | Strict research path is provider-neutral cascaded voice; native audio is optional comparison. PostgreSQL owns correctness; Redis is disposable. |

## Pack-internal UUID decision for Phase 1

`AGENTS.md` requests UUIDv7 or another sortable UUID consistently, but `database/001_initial_schema.sql` uses PostgreSQL `gen_random_uuid()` defaults. This affects Phase 1 ID generation and migration fidelity. Phase 0 does not generate business IDs or translate the supplied schema, so it leaves both source files unchanged. Resolve before Phase 1 rather than silently selecting either behavior.

On 2026-09-25 the user chose to keep the authoritative SQL defaults and document a UUID exception. The Phase 1 Alembic migration therefore preserves every `gen_random_uuid()` default in the supplied SQL, while application-created IDs use UUIDv4 consistently with that schema. This is an explicit exception to the sortable UUID instruction, not an implicit reinterpretation. A future UUIDv7 change requires a new migration and a separately reviewed compatibility decision; the Phase 1 migration and source SQL remain immutable.

The Compose and environment blueprints contain placeholder credentials and relative build paths for their packaging location. The executable Phase 0 Compose file will use repo-root build paths and local-only development defaults; those blueprint values do not define domain behavior.

## Phase 5 contract gaps (2026-09-27)

The UI screen specification describes calendar create/cancel actions, a dashboard time-series endpoint and SSE stream, and a live-call WebSocket timeline. These routes are absent from the executable OpenAPI contract and current controller. The OpenAPI contract lists appointment reschedule, but the controller has no matching route. Phase 5 does not invent their behavior: the UI uses read-only calendar/appointment views and PostgreSQL-backed polling, and its report records these gaps. The Phase 5 read endpoints added to OpenAPI support the implemented screens.

The supplied UI mockups also imply that a completed call or a successful tool response means a booking is confirmed. The browser instead waits for an applicable receipt tied to the current intent revision and resource version. The workflow trace keeps conversation, processing, effect knowledge, applicability, and speech eligibility visible as separate dimensions.

## Phase 6 research baseline and decisive speech (2026-09-28)

The user's global correction says decisive outcome speech needs an applicable claim permit. The Phase 6 B3 research profile explicitly removes claim permits to measure that mechanism, and the P8 ablation needs the same scripted partial playback across B3, P1, and P2. These instructions cannot both describe a real caller-facing B3 audio path. The implementation confines B3 to synthetic experiment-tagged workflows, stores its unpermitted WAV and scripted client acknowledgement for oracle analysis, and blocks its normal audio download and LiveKit transport. P1, P2, and all null-arm production workflows retain the permit requirement. The B3 record is a counterfactual research observation, not authorization for caller-facing permitless outcome speech.

## Phase 6 closure clarifications (2026-10-03)

- The earlier generated coverage matrix incorrectly listed physical listener
  exposure as necessary to close Phase 6. Authoritative `docs/04` makes human
  belief/hearing research optional RQ9 and forbids inferring hearing from client
  acknowledgements. The derived matrix now follows that scope; no human study
  or physical-hearing claim is added.
- B0–B2 playout counterfactuals use the same isolated synthetic TTS and research
  acknowledgement ports as the B3 baseline. Their records never authorize
  permitless audio on a real caller-facing channel.
- The executable claim-type enum contains no cancellation outcome template.
  Retraction fixtures implement the durable cancellation effect and verify it
  independently, while withholding decisive cancellation speech. Adding that
  public claim/API contract remains a separate future change.
- Original safe-resolution metric v1 counted completed correct state. Definition
  v2 in the completion analysis separately credits an evidenced honest durable
  handoff, as required by `docs/04`. Historical rows are retained; task success
  and outcome coverage stay false for unresolved effects. Controller handoff
  facts are process evidence and never replace the simulator truth oracle.
# Phase 7 implementation decisions

- No executable contract was changed. Migration head remains
  `0011_phase6_b3_audio`; UUIDv4 defaults retain the user's approved exception.
- The pack names a non-inferiority condition without a numeric margin. Phase 7
  documents a 5-percentage-point margin, one-sided 95% conservative paired bound,
  primary P2/B3 comparison and 500-instance stratum allocation as design choices.
  They are not presented as values supplied by SQL/OpenAPI or as proven pilot
  conclusions.
- The 40-instance pilot is distinct from Phase 6 smoke checks. Six acoustic
  versions share one scenario and never increase its independent sample count.
- The pilot reports zero primary-endpoint discordance for B3/P1/P2, and separate
  repair differences. It does not manufacture superiority or an adequate-power
  claim from this result. Population independence is not assumed for shared
  synthetic templates.
- Existing cancellation speech and counterfactual audio limitations remain
  explicit. No emergency, phone transfer, dialer or native-audio scope was added.


# UI screen specification

## 1. Design system

Preserve the supplied Indigo Intelligence visual language while correcting the research semantics.

- Headings and labels: Geist.
- Body and tables: Inter.
- Technical identifiers and event payloads: JetBrains Mono.
- Primary: `#5D5FEF`; background: `#F9FAFB`; cards: `#FFFFFF`.
- Status colors are reserved: emerald for verified/satisfied, amber for unknown/pending, red for violated/failed or urgent human action, violet for informational protocol state.
- Desktop sidebar: 260 px. Tablet: collapsible. Mobile: drawer or bottom navigation.
- Minimum interactive target: 44 px.
- All status meaning must be conveyed by text/icon as well as color.
- Respect reduced motion and keyboard navigation.
- Use skeletons for initial loading and inline refresh indicators for background updates.
- Never show a success chip solely because a model or tool returned successfully.

## 2. Corrections to the supplied mockups

| Existing mockup | Required correction |
|---|---|
| Landing footer says Supabase | Use “PostgreSQL” or “Managed PostgreSQL”; do not imply Supabase-specific architecture unless explicitly selected later |
| Live call shows linear PLAN→COMPLETE | Show conversation phase separately from durable operation/effect/speech state |
| Call summary immediately says booked | Show `Confirmed` only with an applicable receipt; otherwise show `Still checking`, `Unresolved`, or `Human follow-up created` |
| Customer card contains allergy data | Replace with maintenance access constraints, contact preference, unit/property details, and scheduling preference |
| A3 trace is a single linear state machine | Rename to Workflow Trace and show four orthogonal state dimensions plus the explanatory A3 stage |
| Evaluation dashboard treats “500 tests” as a generic pass count | Report system arm, scenario count, repetitions, exclusions, timeouts, confidence intervals, and primary endpoints |
| Escalations & Emergencies automates emergency protocols | Rename to Human Handoffs; remove emergency dispatch, authority notification, medical inference, and “take over emergency” features |
| Verification confidence is shown as model probability | Show result (`SATISFIED`, `VIOLATED`, `UNKNOWN`), evidence source, freshness, predicates, and applicability; probability is optional metadata only |

## 3. Navigation and route map

### Caller-facing routes

| Route | Screen |
|---|---|
| `/` | Landing and consent |
| `/call/[callId]` | Live voice session |
| `/call/[callId]/summary` | Call outcome summary |

### Operations routes

| Route | Screen |
|---|---|
| `/dashboard` | Operations and research overview |
| `/calendar` | Appointment calendar |
| `/appointments` | Appointment list |
| `/appointments/[appointmentId]` | Appointment detail drawer/page |
| `/residents` | Synthetic resident list |
| `/residents/[residentId]` | Resident record |
| `/notes` | Scoped resident notes and preferences |
| `/calls` | Call history |
| `/calls/[callId]/trace` | Workflow trace and replay |
| `/handoffs` | Human handoff queue |

### Research routes

| Route | Screen |
|---|---|
| `/evaluation` | Evaluation overview and arm comparison |
| `/evaluation/runs/[runId]` | Evaluation run detail |
| `/experiments/new` | Scenario and fault schedule launcher |
| `/settings` | Model, voice, thresholds, and system information |

No login/role-management screen is required for this FYP. In demo mode a server-issued synthetic actor session is created. If deployment requires authentication, use one simple operator identity flow without making authorization part of the research claim.

## 4. Shared application shell

### Components

- `AppSidebar`: routes, active item, environment badge (`DEMO`, `EXPERIMENT`, `SANDBOX`).
- `TopBar`: page title, trace search, connection status, notification drawer, actor badge.
- `GlobalSearch`: exact lookup by call, workflow, operation, appointment, resident, receipt, or run ID.
- `EnvironmentBanner`: red banner when fault injection is enabled; amber banner when provider or verifier is degraded.
- `ProblemDetailsPanel`: displays safe message, retryability, trace ID, and developer details toggle.
- `StatusChip`: typed variants; no arbitrary strings.
- `IdentifierLink`: monospace, copy button, links to canonical detail.
- `TimeWithZone`: user-friendly local time plus accessible UTC tooltip.

### Shared data rules

- TanStack Query caches reads only; every mutation uses the server response as truth.
- Mutations include `expected_version` or `expected_revision`.
- On `409`, show a conflict dialog and reload current state. Never automatically replay a changed mutation.
- Server-sent events update dashboards and traces; missing events trigger a full reload from PostgreSQL.
- Never infer verified status from optimistic UI state.

## 5. Screen specifications

## S01 Landing and consent

**Route:** `/`

**Purpose:** Explain the synthetic research prototype, collect microphone/recording consent, and start a call.

**Sections:** brand header; research-scope notice; three capability cards; privacy/recording notice; `Start conversation`; `How it works`; current service health.

**API:** `GET /v1/public/config`; `POST /v1/calls`.

**States:** microphone unsupported; permission denied; LiveKit unavailable; API unavailable; session created but room connection failed.

**Rules:** do not claim that every action is verified; say “consequential outcomes are confirmed only after verification.” The start button remains disabled until consent is checked.

**Acceptance:** keyboard-only call start works; denial provides recovery instructions; call ID is created before media connection; double-click creates one call.

## S02 Live voice session

**Route:** `/call/[callId]`

**Purpose:** Conduct the call while exposing enough state for a research demonstration without overwhelming the caller.

**Components:** connection indicator; elapsed time; assistant avatar/waveform; transcript panel toggle; mute; speaker; end call; reconnect notice; safe progress caption; compact state drawer.

**State drawer:**

- Conversation: `LISTENING`, `INTERPRETING`, `CLARIFYING`, `SPEAKING_PROGRESS`, `SPEAKING_OUTCOME`, `YIELDING`, `CLOSED`.
- Latest accepted revision number and short summary.
- Durable operation phase.
- Effect knowledge.
- Speech eligibility.
- Reconciliation or repair badge.

**Connections:** LiveKit media; `WS /v1/calls/{id}/timeline` for low-latency normalized events; `POST /v1/calls/{id}/playback-events`; `POST /v1/calls/{id}/end`.

**Rules:** free-form model speech is allowed for greeting, clarification, and non-consequential conversation. While a mutation is unresolved, outcome claims must use the deterministic speech scheduler. Barge-in immediately stops or pauses output and reports the final played frame/word.

**Acceptance:** reconnect does not create a second call; ending media leaves unresolved operations visible in summary; stale queued claim never starts after permit invalidation; partly played stale decisive claim creates repair state.

## S03 Call outcome summary

**Route:** `/call/[callId]/summary`

**Purpose:** Report what is known after media ends without inventing certainty.

**Variants:**

- `RESOLVED_VERIFIED`: confirmed final appointment and evidence receipt.
- `RESOLVED_REFUSED`: requested action validly refused with reason.
- `UNRESOLVED_RECOVERING`: background reconciliation continues.
- `HANDOFF_CREATED`: human follow-up identifier and expected service window.
- `REPAIR_PENDING`: caller may have heard stale information; show corrected current statement.

**Components:** duration; final accepted request; current business state; historical effects; verification badge; receipt ID; outstanding recovery; transcript download if consent permits; return home.

**API:** `GET /v1/calls/{id}/summary`.

**Rules:** “completed” refers to media completion, not necessarily business resolution. Historical 3 PM and current 4 PM claims must be visually distinguished.

## S04 Dashboard

**Route:** `/dashboard`

**Purpose:** Operational overview and research health, not a marketing analytics page.

**Cards:** calls; clean task success; correction success; unsupported confirmation rate; unresolved outcome count; stale confirmation rate; p95 end-to-first-useful-response; repair obligations overdue.

**Charts:** calls by day; correction timing distribution P0-P9; outcomes by system arm; recent durable events; active recovery queue.

**API:** `GET /v1/dashboard/summary`; `GET /v1/dashboard/timeseries`; SSE `/v1/events/stream`.

**Rules:** display denominators and time ranges. Do not combine independent scenarios with repetitions. Link each metric to its definition.

## S05 Calendar

**Route:** `/calendar`

**Purpose:** Show authoritative appointment state and resource conflicts.

**Views:** day, week, month. Filters: provider/resource, appointment status, synthetic resident.

**Actions:** create, inspect, reschedule, cancel. All mutation dialogs display current row version and require expected version.

**API:** `GET /v1/appointments?from=&to=`; `POST /v1/appointments`; `POST /v1/appointments/{id}/reschedule`; `POST /v1/appointments/{id}/cancel`.

**Rules:** pending controller belief cannot masquerade as provider truth. Use a striped/amber placeholder for `UNKNOWN`, not a confirmed calendar block.

## S06 Appointment list

**Route:** `/appointments`

**Columns:** ID; resident; ticket; local date/time; IANA zone; resource; status; source revision; observed version; last verified; actions.

**Filters:** date range; status; verification freshness; reconciliation required.

**Actions:** open detail, reschedule, cancel, inspect source workflow.

**API:** `GET /v1/appointments`; same mutation APIs as S05.

**Acceptance:** pagination is server-side; filters are URL-addressable; CSV export includes UTC and IANA zone; stale versions return conflict instead of overwriting.

## S07 Appointment detail

**Route:** `/appointments/[appointmentId]`

**Panels:** current authoritative state; business version; linked workflow/revision; effect history; verification history; compensation relationships; audit events.

**Rules:** compensation is a separate linked effect. The page must never rewrite history to look like the original effect did not happen.

## S08 Resident list

**Route:** `/residents`

**Purpose:** Find synthetic residents used by the controlled maintenance domain.

**Columns:** resident ID; display name; property/unit; scheduling preference; open tickets; next appointment; last interaction.

**Excluded:** medical facts and real personal data.

## S09 Resident record

**Route:** `/residents/[residentId]`

**Tabs:** overview, appointments, maintenance tickets, notes/preferences, calls, workflow history.

**Overview:** synthetic contact; property/unit; access instructions; preferred appointment window; communication preference; current tickets; upcoming verified appointment; unresolved actions.

**API:** `GET /v1/residents/{id}` plus scoped collection endpoints.

**Rules:** labels must say synthetic demo data. Show actor/resource binding source. Remove allergy and medical UI from the supplied mockup.

## S10 Notes and preferences

**Route:** `/notes`

**Categories:** scheduling preference, access instruction, maintenance context, communication preference, follow-up.

**Fields:** resident; note text; source (`HUMAN`, `CALL_EXTRACTED`, `SYSTEM`); source call/utterance span; created time; superseded time.

**Rules:** an LLM-extracted note is provisional until server validation. Do not store medical or emergency data. Never use an old note without checking supersession.

## S11 Call history

**Route:** `/calls`

**Columns:** call ID; started; duration; final accepted purpose; media status; business resolution; verification; correction count; handoff; experiment run.

**Filters:** outcome; correction timing; system arm; fault family; date.

**Actions:** summary, workflow trace, transcript (consent-aware), replay bundle.

**Rules:** separate call success from end-to-end task correctness.

## S12 Workflow trace and replay

**Route:** `/calls/[callId]/trace`

**Purpose:** Primary professor demonstration and debugging screen.

**Layout:** synchronized timeline with filters plus right-side detail inspector.

**Tracks:** user utterances; accepted revisions; candidate intents; operation transitions; provider send/commit/response; verification receipts; claim permits; audio segments; playback acknowledgements; repair obligations; faults; oracle result.

**Summary cards:** current accepted revision; operation phase; effect knowledge; applicability; speech eligibility; final provider truth; controller belief; oracle grade.

**Actions:** jump to named barrier; compare raw/normalized event; copy replay command; download replay bundle; overlay B3/P1/P2 traces.

**API:** `GET /v1/calls/{id}/timeline`; `GET /v1/workflows/{id}`; `GET /v1/operations/{id}`; `GET /v1/operations/{id}/receipt`; `GET /v1/evaluation/executions/{id}/replay`.

**Rules:** do not display verification “confidence” as authority. Show three-valued result and exact predicates. Preserve actual event order and causal links.

## S13 Human handoffs

**Route:** `/handoffs`

**Purpose:** Manage unresolved maintenance workflows that exceed automatic recovery capability.

**Columns:** handoff ID; priority; resident; workflow; reason; known facts; unknown facts; provider effects; deadline; assignee text; status.

**Actions:** acknowledge, add resolution note, link observed state, resolve, reopen.

**API:** `GET /v1/handoffs`; `POST /v1/handoffs/{id}/acknowledge`; `POST /v1/handoffs/{id}/resolve`.

**Rules:** no emergency-service automation. High priority means urgent maintenance review, not medical/emergency classification. Resolving a handoff requires recorded evidence or an explicit “administrative closure,” not a fabricated receipt.

## S14 Evaluation overview

**Route:** `/evaluation`

**Purpose:** Compare B0, B1, B2, B3, P1, and P2 using paired scenario instances.

**Cards:** independent scenarios; executions; exclusions; timeouts; correction success; unsupported confirmation; clean task success; outcome coverage; p50/p95 latency.

**Tables:** system-arm comparison with raw numerators/denominators and confidence intervals; category breakdown; fault breakdown; timing-phase breakdown; ablations.

**Charts:** paired outcome differences; latency distribution; failure heatmap; utility/safety frontier.

**Rules:** never display only “472/500 passed.” The unit of analysis, arm, fault, repetition, and exclusion must be visible.

## S15 Evaluation run detail

**Route:** `/evaluation/runs/[runId]`

**Panels:** frozen manifest; hashes; model/provider versions; system arms; scenario list; execution status; failures; exclusions; metric results; downloadable raw data; analysis version.

**Actions:** resume incomplete executions; replay exact execution; compare trace; export report.

**Rules:** a resumed run preserves the frozen manifest. Any changed fixture, prompt, model snapshot, schema, or analysis code creates a new run version.

## S16 Experiment launcher

**Route:** `/experiments/new`

**Audience:** research mode only.

**Inputs:** scenario fixture version; final intended state; correction phase P0-P9; provider behavior; fault schedule; system arms; seed list; model profile; turn policy; retry budget; execution count.

**Validation:** forbid production provider credentials; require independent oracle; display Cartesian-product size; require confirmation for expensive runs.

**API:** `POST /v1/evaluation/runs`; `POST /v1/evaluation/runs/{id}/start`.

## S17 Settings

**Route:** `/settings`

**Sections:** environment information; native-audio/cascade profile; STT/LLM/TTS identifiers; endpointing and interruption thresholds; speech policy version; provider simulator version; retention settings; feature flags; read-only dependency/build hashes.

**Rules:** never reveal secrets. Changing correctness-relevant settings is versioned and disabled during frozen evaluation runs.

## 6. Component inventory

Build these reusable components before screen-specific copies emerge:

- `MetricCard`, `MetricDefinitionPopover`, `ConfidenceInterval`.
- `StatusChip`, `ThreeValuedResult`, `FreshnessBadge`, `ApplicabilityBadge`.
- `RevisionBadge`, `OperationIdentity`, `ReceiptLink`, `ClaimPermitLink`.
- `EventTimeline`, `TimelineTrack`, `CausalEdge`, `BarrierMarker`, `RawEventDrawer`.
- `AppointmentForm`, `ConflictDialog`, `ExpectedVersionField`.
- `TranscriptViewer`, `AudioSegmentBar`, `PlaybackSpan`, `RepairAlert`.
- `DataTable`, `FilterBar`, `Pagination`, `ExportMenu`.
- `EmptyState`, `DegradedState`, `RecoveringState`, `ProblemDetailsPanel`.
- `ExperimentManifest`, `ArmSelector`, `FaultScheduleBuilder`, `ReplayCommand`.

## 7. Frontend test matrix

Every route must have component tests and at least one Playwright happy path. Critical routes S02, S03, S05, S12, S14, and S16 also require failure-path E2E tests.

Minimum scenarios:

- Network reconnect and duplicate submission.
- Stale resource version conflict.
- Unknown external outcome.
- Receipt invalidated between render and publish.
- Old audio queued but not played.
- Old audio partly played and repaired.
- Redis unavailable.
- API unavailable with LiveKit still connected.
- Call ended while reconciliation continues.
- Replay bundle download and deterministic rerun.


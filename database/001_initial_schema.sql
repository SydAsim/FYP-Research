BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TYPE conversation_phase AS ENUM (
  'LISTENING','INTERPRETING','CLARIFYING','SPEAKING_PROGRESS',
  'SPEAKING_OUTCOME','YIELDING','CLOSED'
);
CREATE TYPE processing_phase AS ENUM (
  'DRAFT','READY','DISPATCH_RECORDED','RESPONSE_RECEIVED','VERIFYING',
  'RECONCILING','COMPENSATING','TERMINAL'
);
CREATE TYPE effect_knowledge AS ENUM (
  'NOT_ATTEMPTED','ABSENT','PRESENT','PARTIAL','UNKNOWN','COMPENSATED'
);
CREATE TYPE applicability AS ENUM ('CURRENT','SUPERSEDED','REUSABLE','INCOMPATIBLE');
CREATE TYPE speech_eligibility AS ENUM ('BLOCKED','PROGRESS_ONLY','CLAIM_PERMITTED','REPAIR_REQUIRED');
CREATE TYPE verification_result AS ENUM ('SATISFIED','VIOLATED','UNKNOWN');
CREATE TYPE appointment_status AS ENUM ('HELD','CONFIRMED','CANCELLED','COMPLETED');

CREATE TABLE actors (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject text NOT NULL UNIQUE,
  display_name text NOT NULL,
  synthetic boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE properties (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  external_ref text NOT NULL UNIQUE,
  display_name text NOT NULL,
  timezone text NOT NULL,
  synthetic boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE residents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id uuid NOT NULL UNIQUE REFERENCES actors(id),
  property_id uuid NOT NULL REFERENCES properties(id),
  unit_ref text NOT NULL,
  contact_json jsonb NOT NULL DEFAULT '{}',
  scheduling_preference_json jsonb NOT NULL DEFAULT '{}',
  version integer NOT NULL DEFAULT 0 CHECK (version >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (property_id, unit_ref)
);

CREATE TABLE call_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id uuid NOT NULL REFERENCES actors(id),
  resident_id uuid NOT NULL REFERENCES residents(id),
  experiment_run_id uuid NULL,
  media_status text NOT NULL CHECK (media_status IN ('CREATED','CONNECTING','CONNECTED','ENDED')),
  conversation_phase conversation_phase NOT NULL DEFAULT 'LISTENING',
  consent_json jsonb NOT NULL,
  livekit_room text NOT NULL UNIQUE,
  started_at timestamptz NOT NULL DEFAULT now(),
  ended_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workflows (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  call_id uuid NOT NULL REFERENCES call_sessions(id),
  actor_id uuid NOT NULL REFERENCES actors(id),
  resident_id uuid NOT NULL REFERENCES residents(id),
  workflow_type text NOT NULL,
  current_revision integer NOT NULL DEFAULT 0 CHECK (current_revision >= 0),
  workflow_sequence bigint NOT NULL DEFAULT 0 CHECK (workflow_sequence >= 0),
  desired_state_json jsonb NOT NULL DEFAULT '{}',
  resolution_status text NOT NULL DEFAULT 'OPEN' CHECK (resolution_status IN ('OPEN','RESOLVED','HANDOFF','ABANDONED')),
  version integer NOT NULL DEFAULT 0 CHECK (version >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE utterances (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  call_id uuid NOT NULL REFERENCES call_sessions(id),
  speaker text NOT NULL CHECK (speaker IN ('USER','ASSISTANT','SYSTEM')),
  transcript text NOT NULL,
  transcript_version integer NOT NULL CHECK (transcript_version >= 1),
  audio_start_ms integer NULL CHECK (audio_start_ms >= 0),
  audio_end_ms integer NULL CHECK (audio_end_ms >= 0),
  finalized boolean NOT NULL DEFAULT false,
  content_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (call_id, id, transcript_version)
);

CREATE TABLE intent_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id uuid NOT NULL REFERENCES workflows(id),
  revision integer NOT NULL CHECK (revision >= 1),
  parent_revision integer NULL,
  change_class text NOT NULL,
  desired_state_json jsonb NOT NULL,
  structured_intent_json jsonb NOT NULL,
  source_utterance_id uuid NOT NULL REFERENCES utterances(id),
  source_span_json jsonb NOT NULL DEFAULT '{}',
  model_id text NOT NULL,
  prompt_hash text NOT NULL,
  accepted_by text NOT NULL,
  accepted_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workflow_id, revision),
  CHECK (parent_revision IS NULL OR parent_revision < revision)
);

CREATE TABLE maintenance_tickets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  resident_id uuid NOT NULL REFERENCES residents(id),
  property_id uuid NOT NULL REFERENCES properties(id),
  issue_type text NOT NULL,
  description text NOT NULL,
  status text NOT NULL CHECK (status IN ('OPEN','SCHEDULED','IN_PROGRESS','RESOLVED','CANCELLED')),
  version integer NOT NULL DEFAULT 0 CHECK (version >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE appointments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id uuid NOT NULL REFERENCES maintenance_tickets(id),
  resident_id uuid NOT NULL REFERENCES residents(id),
  resource_key text NOT NULL,
  starts_at timestamptz NOT NULL,
  ends_at timestamptz NOT NULL,
  timezone text NOT NULL,
  requested_local_start text NOT NULL,
  status appointment_status NOT NULL,
  source_workflow_id uuid NOT NULL REFERENCES workflows(id),
  source_intent_revision integer NOT NULL CHECK (source_intent_revision >= 1),
  provider_ref text NULL,
  version integer NOT NULL DEFAULT 0 CHECK (version >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (ends_at > starts_at)
);

ALTER TABLE appointments
ADD CONSTRAINT appointments_no_active_overlap
EXCLUDE USING gist (
  resource_key WITH =,
  tstzrange(starts_at, ends_at, '[)') WITH &&
)
WHERE (status IN ('HELD','CONFIRMED'));

CREATE TABLE operations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id uuid NOT NULL REFERENCES workflows(id),
  intent_revision integer NOT NULL CHECK (intent_revision >= 1),
  parent_operation_id uuid NULL REFERENCES operations(id),
  supersedes_operation_id uuid NULL REFERENCES operations(id),
  action_type text NOT NULL,
  target_resource_type text NOT NULL,
  target_resource_id uuid NULL,
  processing_phase processing_phase NOT NULL DEFAULT 'DRAFT',
  effect_knowledge effect_knowledge NOT NULL DEFAULT 'NOT_ATTEMPTED',
  applicability applicability NOT NULL DEFAULT 'CURRENT',
  speech_eligibility speech_eligibility NOT NULL DEFAULT 'BLOCKED',
  idempotency_key text NOT NULL UNIQUE,
  request_hash text NOT NULL,
  normalized_request_json jsonb NOT NULL,
  provider_adapter text NOT NULL,
  provider_operation_id text NULL,
  reconciliation_required boolean NOT NULL DEFAULT false,
  dispatch_recorded_at timestamptz NULL,
  response_received_at timestamptz NULL,
  effect_observed_at timestamptz NULL,
  resolved_at timestamptz NULL,
  version integer NOT NULL DEFAULT 0 CHECK (version >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workflow_id, id),
  UNIQUE (workflow_id, intent_revision, request_hash)
);

CREATE TABLE operation_attempts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operation_id uuid NOT NULL REFERENCES operations(id),
  attempt_number integer NOT NULL CHECK (attempt_number >= 1),
  attempt_type text NOT NULL CHECK (attempt_type IN ('WRITE','STATUS_LOOKUP','POSTCONDITION_READ','COMPENSATION')),
  request_hash text NOT NULL,
  request_sent_at timestamptz NULL,
  response_received_at timestamptz NULL,
  raw_response_json jsonb NULL,
  normalized_result_json jsonb NULL,
  result_code text NULL,
  trace_id text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (operation_id, attempt_number)
);

CREATE TABLE effect_ledger (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operation_id uuid NOT NULL REFERENCES operations(id),
  effect_type text NOT NULL,
  resource_type text NOT NULL,
  resource_id text NOT NULL,
  before_facts jsonb NULL,
  after_facts jsonb NULL,
  observed_version text NULL,
  evidence_hash text NOT NULL,
  observed_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE reconciliation_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operation_id uuid NOT NULL REFERENCES operations(id),
  job_type text NOT NULL,
  state text NOT NULL DEFAULT 'READY' CHECK (state IN ('READY','LEASED','DONE','FAILED','HANDOFF')),
  attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  max_attempts integer NOT NULL DEFAULT 8 CHECK (max_attempts >= 1),
  next_run_at timestamptz NOT NULL DEFAULT now(),
  lease_owner text NULL,
  lease_until timestamptz NULL,
  last_error_json jsonb NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX reconciliation_jobs_due_idx ON reconciliation_jobs (next_run_at) WHERE state IN ('READY','LEASED');

CREATE TABLE verification_receipts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id uuid NOT NULL REFERENCES workflows(id),
  operation_id uuid NOT NULL REFERENCES operations(id),
  intent_revision integer NOT NULL CHECK (intent_revision >= 1),
  actor_assumption text NOT NULL,
  claim_type text NOT NULL,
  predicates_json jsonb NOT NULL,
  result verification_result NOT NULL,
  observed_resource_version text NULL,
  verifier_version text NOT NULL,
  valid_from timestamptz NOT NULL,
  valid_until timestamptz NULL,
  invalidated_at timestamptz NULL,
  invalidating_event_id uuid NULL,
  receipt_hash text NOT NULL UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE evidence_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  receipt_id uuid NOT NULL REFERENCES verification_receipts(id),
  source_type text NOT NULL,
  source_identifier text NOT NULL,
  query_hash text NOT NULL,
  observed_facts jsonb NOT NULL,
  source_version text NULL,
  observed_at timestamptz NOT NULL,
  evidence_hash text NOT NULL,
  UNIQUE (receipt_id, evidence_hash)
);

CREATE TABLE claims (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id uuid NOT NULL REFERENCES workflows(id),
  operation_id uuid NULL REFERENCES operations(id),
  intent_revision integer NOT NULL CHECK (intent_revision >= 1),
  claim_type text NOT NULL,
  semantic_predicates_json jsonb NOT NULL,
  tense text NOT NULL,
  resource_version text NULL,
  template_version text NOT NULL,
  content_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE claim_permits (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  claim_id uuid NOT NULL REFERENCES claims(id),
  receipt_id uuid NOT NULL REFERENCES verification_receipts(id),
  workflow_id uuid NOT NULL REFERENCES workflows(id),
  intent_revision integer NOT NULL CHECK (intent_revision >= 1),
  policy_version text NOT NULL,
  state text NOT NULL CHECK (state IN ('AUTHORIZED','QUEUED','PUBLISHED','INVALIDATED','CONSUMED','EXPIRED')),
  authorized_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  invalidated_at timestamptz NULL,
  invalidating_event_id uuid NULL,
  version integer NOT NULL DEFAULT 0 CHECK (version >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (claim_id, receipt_id)
);

CREATE TABLE audio_segments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  call_id uuid NOT NULL REFERENCES call_sessions(id),
  claim_permit_id uuid NULL REFERENCES claim_permits(id),
  segment_class text NOT NULL CHECK (segment_class IN ('FREE_CONVERSATION','PROGRESS','UNCERTAINTY','OUTCOME','REPAIR')),
  content_hash text NOT NULL,
  tts_model_id text NOT NULL,
  tts_config_hash text NOT NULL,
  generated_at timestamptz NOT NULL,
  queued_at timestamptz NULL,
  published_at timestamptz NULL,
  cancelled_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE playback_events (
  id uuid PRIMARY KEY,
  segment_id uuid NOT NULL REFERENCES audio_segments(id),
  call_id uuid NOT NULL REFERENCES call_sessions(id),
  event_type text NOT NULL CHECK (event_type IN ('RECEIVED','QUEUED','STARTED','PROGRESS','INTERRUPTED','COMPLETED')),
  played_ms integer NULL CHECK (played_ms >= 0),
  last_frame bigint NULL CHECK (last_frame >= 0),
  last_word_index integer NULL CHECK (last_word_index >= 0),
  client_time timestamptz NOT NULL,
  server_received_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE repair_obligations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id uuid NOT NULL REFERENCES workflows(id),
  stale_claim_id uuid NOT NULL REFERENCES claims(id),
  stale_segment_id uuid NOT NULL REFERENCES audio_segments(id),
  triggering_revision integer NOT NULL CHECK (triggering_revision >= 1),
  played_span_json jsonb NOT NULL,
  required_predicates_json jsonb NOT NULL,
  state text NOT NULL CHECK (state IN ('OPEN','REPAIR_AUTHORIZED','REPAIR_PLAYED','ESCALATED','CLOSED')),
  deadline_at timestamptz NOT NULL,
  repair_claim_id uuid NULL REFERENCES claims(id),
  satisfied_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE handoffs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id uuid NOT NULL REFERENCES workflows(id),
  resident_id uuid NOT NULL REFERENCES residents(id),
  reason_code text NOT NULL,
  priority text NOT NULL CHECK (priority IN ('STANDARD','HIGH','URGENT_MAINTENANCE')),
  known_facts jsonb NOT NULL,
  unknown_facts jsonb NOT NULL,
  linked_operation_ids uuid[] NOT NULL DEFAULT '{}',
  deadline_at timestamptz NOT NULL,
  state text NOT NULL CHECK (state IN ('OPEN','ACKNOWLEDGED','RESOLVED','ADMIN_CLOSED')),
  resolution_json jsonb NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workflow_events (
  id uuid PRIMARY KEY,
  event_name text NOT NULL,
  schema_version integer NOT NULL CHECK (schema_version >= 1),
  occurred_at timestamptz NOT NULL,
  workflow_id uuid NOT NULL REFERENCES workflows(id),
  workflow_sequence bigint NOT NULL CHECK (workflow_sequence >= 1),
  operation_id uuid NULL REFERENCES operations(id),
  intent_revision integer NULL,
  correlation_id uuid NOT NULL,
  causation_id uuid NULL,
  trace_id text NOT NULL,
  actor_assumption text NOT NULL,
  experiment_run_id uuid NULL,
  payload jsonb NOT NULL,
  UNIQUE (workflow_id, workflow_sequence)
);

CREATE TABLE outbox (
  id uuid PRIMARY KEY REFERENCES workflow_events(id),
  topic text NOT NULL,
  payload jsonb NOT NULL,
  available_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz NULL,
  lease_owner text NULL,
  lease_until timestamptz NULL,
  attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0)
);
CREATE INDEX outbox_due_idx ON outbox (available_at) WHERE published_at IS NULL;

CREATE TABLE inbox_deliveries (
  consumer_name text NOT NULL,
  event_id uuid NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now(),
  processed_at timestamptz NULL,
  PRIMARY KEY (consumer_name, event_id)
);

CREATE TABLE evaluation_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  status text NOT NULL CHECK (status IN ('DRAFT','FROZEN','RUNNING','COMPLETED','FAILED','CANCELLED')),
  manifest_json jsonb NOT NULL,
  manifest_hash text NOT NULL UNIQUE,
  source_commit text NOT NULL,
  migration_version text NOT NULL,
  analysis_version text NOT NULL,
  frozen_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz NULL
);

ALTER TABLE call_sessions
ADD CONSTRAINT call_sessions_evaluation_run_fk
FOREIGN KEY (experiment_run_id) REFERENCES evaluation_runs(id);

CREATE TABLE scenario_cases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id uuid NOT NULL REFERENCES evaluation_runs(id),
  scenario_key text NOT NULL,
  fixture_hash text NOT NULL,
  externally_specified_final_intent jsonb NOT NULL,
  fault_schedule jsonb NOT NULL,
  seed bigint NOT NULL,
  UNIQUE (run_id, scenario_key)
);

CREATE TABLE executions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id uuid NOT NULL REFERENCES evaluation_runs(id),
  case_id uuid NOT NULL REFERENCES scenario_cases(id),
  system_arm text NOT NULL CHECK (system_arm IN ('B0','B1','B2','B3','P1','P2')),
  repetition integer NOT NULL DEFAULT 1 CHECK (repetition >= 1),
  status text NOT NULL CHECK (status IN ('READY','RUNNING','COMPLETED','TIMEOUT','EXCLUDED','FAILED')),
  workflow_id uuid NULL REFERENCES workflows(id),
  started_at timestamptz NULL,
  completed_at timestamptz NULL,
  exclusion_reason text NULL,
  UNIQUE (run_id, case_id, system_arm, repetition)
);

CREATE TABLE fault_occurrences (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_id uuid NOT NULL REFERENCES executions(id),
  barrier_name text NOT NULL,
  fault_type text NOT NULL,
  scheduled_target jsonb NOT NULL,
  actual_event_id uuid NULL,
  injected_at timestamptz NOT NULL,
  parameters jsonb NOT NULL
);

CREATE TABLE oracle_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_id uuid NOT NULL UNIQUE REFERENCES executions(id),
  oracle_version text NOT NULL,
  actual_provider_truth jsonb NOT NULL,
  final_intent jsonb NOT NULL,
  valid_outcomes jsonb NOT NULL,
  forbidden_effects jsonb NOT NULL,
  result_json jsonb NOT NULL,
  result_hash text NOT NULL,
  evaluated_at timestamptz NOT NULL
);

CREATE TABLE metrics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_id uuid NOT NULL REFERENCES executions(id),
  metric_name text NOT NULL,
  metric_version text NOT NULL,
  numeric_value double precision NULL,
  categorical_value text NULL,
  numerator bigint NULL,
  denominator bigint NULL,
  details jsonb NOT NULL DEFAULT '{}',
  recorded_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (execution_id, metric_name, metric_version)
);

COMMIT;


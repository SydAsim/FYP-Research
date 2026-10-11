-- Isolated simulator database. Controller credentials must not access this database.
CREATE TABLE IF NOT EXISTS simulator_scenarios (
  id uuid PRIMARY KEY,
  config_json jsonb NOT NULL,
  request_count integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS simulator_barriers (
  scenario_id uuid NOT NULL REFERENCES simulator_scenarios(id),
  barrier_name text NOT NULL,
  state text NOT NULL CHECK (state IN ('HELD','REACHED','RELEASED')),
  reached_at timestamptz NULL,
  released_at timestamptz NULL,
  PRIMARY KEY (scenario_id, barrier_name)
);

CREATE TABLE IF NOT EXISTS provider_appointments (
  id uuid PRIMARY KEY,
  scenario_id uuid NOT NULL REFERENCES simulator_scenarios(id),
  resource_key text NOT NULL,
  starts_at timestamptz NOT NULL,
  ends_at timestamptz NOT NULL,
  timezone text NOT NULL,
  status text NOT NULL CHECK (status IN ('CONFIRMED','HELD','CANCELLED')),
  version integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (ends_at > starts_at)
);
CREATE INDEX IF NOT EXISTS provider_appointments_resource_idx
ON provider_appointments (scenario_id, resource_key);

CREATE TABLE IF NOT EXISTS provider_requests (
  id bigserial PRIMARY KEY,
  scenario_id uuid NOT NULL REFERENCES simulator_scenarios(id),
  operation_id uuid NOT NULL,
  request_hash text NOT NULL,
  idempotency_key text NOT NULL,
  result_json jsonb NOT NULL,
  commit_sequence bigint NULL,
  status_reads integer NOT NULL DEFAULT 0,
  resource_reads integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS provider_requests_operation_idx
ON provider_requests (scenario_id, operation_id, id DESC);

CREATE TABLE IF NOT EXISTS provider_commits (
  sequence bigserial PRIMARY KEY,
  scenario_id uuid NOT NULL REFERENCES simulator_scenarios(id),
  operation_id uuid NULL,
  request_hash text NULL,
  idempotency_key text NULL,
  action text NOT NULL,
  appointment_id uuid NULL,
  resource_key text NOT NULL,
  before_facts jsonb NULL,
  after_facts jsonb NULL,
  result_code text NOT NULL,
  committed_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS provider_commits_scenario_idx
ON provider_commits (scenario_id, sequence);

CREATE OR REPLACE FUNCTION forbid_provider_commit_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'provider truth log is append-only';
END;
$$;
DROP TRIGGER IF EXISTS provider_commits_append_only ON provider_commits;
CREATE TRIGGER provider_commits_append_only
BEFORE UPDATE OR DELETE ON provider_commits
FOR EACH ROW EXECUTE FUNCTION forbid_provider_commit_mutation();

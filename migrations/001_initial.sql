CREATE TABLE jobs (
  id text PRIMARY KEY,
  idempotency_key text NOT NULL UNIQUE,
  job_type text NOT NULL,
  payload jsonb NOT NULL,
  status text NOT NULL DEFAULT 'QUEUED' CHECK (status IN ('QUEUED','LEASED','SUCCEEDED','RETRY_WAIT','DEAD','EXPIRED')),
  priority integer NOT NULL DEFAULT 50 CHECK (priority BETWEEN 0 AND 100),
  attempts integer NOT NULL DEFAULT 0,
  max_attempts integer NOT NULL DEFAULT 3,
  available_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX jobs_queue_idx ON jobs (status, available_at, priority DESC);
CREATE TABLE job_leases (
  job_id text PRIMARY KEY REFERENCES jobs(id),
  lease_token_hash text NOT NULL,
  worker_id text NOT NULL,
  leased_at timestamptz NOT NULL,
  lease_expires_at timestamptz NOT NULL,
  released_at timestamptz
);
CREATE TABLE analysis_results (
  job_id text PRIMARY KEY REFERENCES jobs(id),
  schema_version text NOT NULL,
  result jsonb NOT NULL,
  result_fingerprint text NOT NULL UNIQUE,
  model jsonb NOT NULL,
  prompt_version text NOT NULL,
  input_fingerprint text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
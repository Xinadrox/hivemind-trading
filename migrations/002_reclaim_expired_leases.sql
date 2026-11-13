CREATE INDEX IF NOT EXISTS job_leases_expiry_idx ON job_leases (lease_expires_at);
UPDATE jobs j
SET status = CASE WHEN j.attempts >= j.max_attempts THEN 'DEAD' ELSE 'RETRY_WAIT' END,
    available_at = CASE WHEN j.attempts >= j.max_attempts THEN j.available_at ELSE now() END,
    updated_at = now()
FROM job_leases l
WHERE l.job_id = j.id AND j.status = 'LEASED' AND l.released_at IS NULL AND l.lease_expires_at < now();
UPDATE job_leases SET released_at = now() WHERE released_at IS NULL AND lease_expires_at < now();
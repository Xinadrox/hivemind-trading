from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import secrets
import uuid

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .core import Job, Lease, LeaseConflict, _fingerprint, validate_analysis_result


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class PostgresJobStore:
    """PostgreSQL-backed job store using bound parameters and short transactions."""

    def __init__(self, connection):
        self.connection = connection

    def create_job(self, idempotency_key, payload, job_type, expires_at, priority=50):
        job_id = str(uuid.uuid7()) if hasattr(uuid, "uuid7") else str(uuid.uuid4())
        with self.connection.transaction():
            with self.connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO jobs (id, idempotency_key, job_type, payload, priority, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (idempotency_key) DO NOTHING
                    """,
                    (job_id, idempotency_key, job_type, Jsonb(payload), priority, expires_at),
                )
                cursor.execute(
                    "SELECT id, job_type, payload, status, attempts FROM jobs WHERE idempotency_key = %s",
                    (idempotency_key,),
                )
                row = cursor.fetchone()
        if row is None:
            raise RuntimeError("job was not persisted")
        if row["payload"] != json.loads(json.dumps(payload)):
            raise LeaseConflict("idempotency key reused with different payload")
        return Job(row["id"], idempotency_key, row["payload"], row["status"], row["attempts"])

    def lease_next(self, worker_id, ttl_seconds=300):
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=ttl_seconds)
        with self.connection.transaction():
            with self.connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT j.id, j.payload, j.status, j.attempts
                    FROM jobs AS j
                    LEFT JOIN job_leases AS l ON l.job_id = j.id AND l.released_at IS NULL
                    WHERE j.expires_at > now()
                      AND (j.status = 'QUEUED' OR (j.status = 'LEASED' AND l.lease_expires_at <= now()))
                    ORDER BY j.priority DESC, j.created_at
                    FOR UPDATE OF j SKIP LOCKED
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                cursor.execute(
                    "UPDATE jobs SET status = 'LEASED', attempts = attempts + 1, updated_at = now() WHERE id = %s",
                    (row["id"],),
                )
                cursor.execute(
                    """
                    INSERT INTO job_leases (job_id, lease_token_hash, worker_id, leased_at, lease_expires_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (job_id) DO UPDATE SET lease_token_hash = EXCLUDED.lease_token_hash,
                        worker_id = EXCLUDED.worker_id, leased_at = EXCLUDED.leased_at,
                        lease_expires_at = EXCLUDED.lease_expires_at, released_at = NULL
                    """,
                    (row["id"], _token_hash(token), worker_id, now, expires),
                )
        return Lease(row["id"], token, worker_id, expires.timestamp())

    def get_job(self, job_id):
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT id, payload, status, attempts FROM jobs WHERE id = %s", (job_id,))
            row = cursor.fetchone()
        if row is None:
            raise KeyError(job_id)
        return Job(row["id"], "", row["payload"], row["status"], row["attempts"])

    def accept_result(self, job_id, token, result):
        validate_analysis_result(result, job_id)
        result_fingerprint = _fingerprint(result)
        with self.connection.transaction():
            with self.connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute("SELECT result_fingerprint FROM analysis_results WHERE job_id = %s", (job_id,))
                existing = cursor.fetchone()
                if existing:
                    if existing["result_fingerprint"] == result_fingerprint:
                        return False
                    raise LeaseConflict("a different result already exists")
                cursor.execute(
                    "SELECT lease_token_hash FROM job_leases WHERE job_id = %s AND released_at IS NULL",
                    (job_id,),
                )
                lease = cursor.fetchone()
                if lease is None or not secrets.compare_digest(lease["lease_token_hash"], _token_hash(token)):
                    raise LeaseConflict("lease token is invalid")
                cursor.execute(
                    """
                    INSERT INTO analysis_results
                    (job_id, schema_version, result, result_fingerprint, model, prompt_version, input_fingerprint)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (job_id, result["schema_version"], Jsonb(result), result_fingerprint,
                     Jsonb(result["model"]), result["prompt_version"], result["input_fingerprint"]),
                )
                cursor.execute("UPDATE jobs SET status = 'SUCCEEDED', updated_at = now() WHERE id = %s", (job_id,))
        return True

    def fail_job(self, job_id, token, max_attempts=3):
        with self.connection.transaction():
            with self.connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    "SELECT l.lease_token_hash, j.attempts FROM job_leases AS l JOIN jobs AS j ON j.id = l.job_id WHERE l.job_id = %s AND l.released_at IS NULL",
                    (job_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    raise KeyError(job_id)
                if not secrets.compare_digest(row["lease_token_hash"], _token_hash(token)):
                    raise LeaseConflict("lease token is invalid")
                status = "DEAD" if row["attempts"] >= max_attempts else "QUEUED"
                cursor.execute("UPDATE jobs SET status = %s, updated_at = now() WHERE id = %s", (status, job_id))
                cursor.execute("UPDATE job_leases SET released_at = now() WHERE job_id = %s", (job_id,))
        return status

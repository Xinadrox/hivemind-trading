from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
import secrets
from typing import Any


class LeaseConflict(Exception):
    pass


class ResultRejected(Exception):
    pass


@dataclass
class Job:
    id: str
    idempotency_key: str
    payload: dict[str, Any]
    status: str = "QUEUED"
    attempts: int = 0


@dataclass
class Lease:
    job_id: str
    token: str
    worker_id: str
    expires_at: float


def _fingerprint(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_analysis_result(result: dict[str, Any], job_id: str) -> None:
    required = {"schema_version", "job_id", "status", "model", "prompt_version", "input_fingerprint", "analysis"}
    if set(result) != required or result["schema_version"] != "1.0" or result["job_id"] != job_id:
        raise ResultRejected("result shape or job_id is invalid")
    if result["status"] not in {"OK", "INSUFFICIENT_DATA", "REJECTED"}:
        raise ResultRejected("status is invalid")
    if set(result["model"]) != {"provider", "name"}:
        raise ResultRejected("model is invalid")
    if not isinstance(result["input_fingerprint"], str) or not result["input_fingerprint"].startswith("sha256:") or len(result["input_fingerprint"]) != 71:
        raise ResultRejected("input_fingerprint is invalid")
    analysis = result["analysis"]
    if set(analysis) != {"summary", "confidence", "signals", "risks", "next_step"}:
        raise ResultRejected("analysis shape is invalid")
    if not isinstance(analysis["summary"], str) or not 1 <= len(analysis["summary"]) <= 2000:
        raise ResultRejected("summary is invalid")
    if not isinstance(analysis["confidence"], (float, int)) or not 0 <= analysis["confidence"] <= 1:
        raise ResultRejected("confidence is invalid")
    if not all(isinstance(x, str) and x for x in analysis["signals"] + analysis["risks"]):
        raise ResultRejected("signals or risks are invalid")
    if analysis["next_step"] not in {"NO_ACTION", "REVIEW", "COLLECT_MORE_DATA"}:
        raise ResultRejected("next_step is invalid")


class InMemoryJobStore:
    def __init__(self):
        self.jobs = {}
        self.by_key = {}
        self.leases = {}
        self.results = {}
        self._counter = 0

    def create_job(self, idempotency_key, payload):
        existing_id = self.by_key.get(idempotency_key)
        if existing_id:
            existing = self.jobs[existing_id]
            if _fingerprint(existing.payload) != _fingerprint(payload):
                raise LeaseConflict("idempotency key reused with different payload")
            return existing
        self._counter += 1
        job = Job(f"01J{self._counter:08d}", idempotency_key, payload)
        self.jobs[job.id] = job
        self.by_key[idempotency_key] = job.id
        return job

    def lease_next(self, worker_id, now, ttl):
        for job in self.jobs.values():
            lease = self.leases.get(job.id)
            if job.status == "QUEUED" or (job.status == "LEASED" and lease and lease.expires_at <= now):
                job.status = "LEASED"
                job.attempts += 1
                lease = Lease(job.id, secrets.token_urlsafe(24), worker_id, now + ttl)
                self.leases[job.id] = lease
                return lease
        return None

    def accept_result(self, job_id, token, result):
        job = self.jobs[job_id]
        lease = self.leases[job_id]
        if self.results.get(job_id):
            if self.results[job_id] == _fingerprint(result):
                return False
            raise LeaseConflict("a different result already exists")
        if lease.token != token:
            raise LeaseConflict("lease token is invalid")
        validate_analysis_result(result, job_id)
        self.results[job_id] = _fingerprint(result)
        job.status = "SUCCEEDED"
        return True

    def fail_job(self, job_id, token, now, max_attempts=3):
        job = self.jobs[job_id]
        if self.leases[job_id].token != token:
            raise LeaseConflict("lease token is invalid")
        job.status = "DEAD" if job.attempts >= max_attempts else "QUEUED"
        return job.status
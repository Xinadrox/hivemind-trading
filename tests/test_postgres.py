from datetime import datetime, timedelta, timezone
import json

import pytest

from hivemind.core import LeaseConflict, ResultRejected
from hivemind.postgres import PostgresJobStore


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.row = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params=()):
        self.connection.calls.append((query, params))
        normalized = " ".join(query.split())
        if normalized.startswith("INSERT INTO jobs"):
            self.connection.job = {
                "id": "01JTEST",
                "job_type": params[2],
                "payload": params[3].obj if hasattr(params[3], "obj") else json.loads(params[3]),
                "status": "QUEUED",
                "attempts": 0,
            }
        elif normalized.startswith("SELECT id, job_type"):
            self.row = self.connection.job
        elif normalized.startswith("SELECT j.id, j.payload"):
            self.row = self.connection.job
        elif normalized.startswith("SELECT lease_token_hash"):
            self.row = self.connection.lease
        elif normalized.startswith("SELECT result_fingerprint"):
            self.row = self.connection.result
        elif normalized.startswith("INSERT INTO analysis_results"):
            self.connection.result = {"result_fingerprint": params[3]}
        elif normalized.startswith("UPDATE jobs"):
            self.connection.job["status"] = params[0]
        elif normalized.startswith("INSERT INTO job_leases"):
            self.connection.lease = {"lease_token_hash": params[1], "lease_expires_at": params[4]}
        return self

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self):
        self.calls = []
        self.job = None
        self.lease = None
        self.result = None

    def cursor(self, **kwargs):
        return FakeCursor(self)

    def transaction(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def valid_result(job_id):
    return {
        "schema_version": "1.0",
        "job_id": job_id,
        "status": "OK",
        "model": {"provider": "test", "name": "model"},
        "prompt_version": "analysis-1.0.0",
        "input_fingerprint": "sha256:" + "0" * 64,
        "analysis": {
            "summary": "ok",
            "confidence": 0.5,
            "signals": ["signal"],
            "risks": ["risk"],
            "next_step": "REVIEW",
        },
    }


def test_create_job_uses_bound_parameters_and_returns_job():
    connection = FakeConnection()
    store = PostgresJobStore(connection)
    expiry = datetime.now(timezone.utc) + timedelta(minutes=5)

    job = store.create_job("key' OR 1=1", {"input": {"x": 1}}, "analysis", expiry)

    assert job.id == "01JTEST"
    assert connection.calls[0][1][1] == "key' OR 1=1"
    assert "key' OR 1=1" not in connection.calls[0][0]


def test_lease_token_is_random_and_only_hash_is_persisted():
    connection = FakeConnection()
    connection.job = {"id": "01JTEST", "job_type": "analysis", "payload": {"input": {}}, "status": "QUEUED", "attempts": 0}
    store = PostgresJobStore(connection)

    lease = store.lease_next("worker-1", ttl_seconds=300)

    assert len(lease.token) >= 32
    assert connection.lease["lease_token_hash"] != lease.token
    assert "worker-1" in connection.calls[-1][1]


def test_accept_result_rejects_invalid_result_before_database_write():
    connection = FakeConnection()
    store = PostgresJobStore(connection)

    with pytest.raises(ResultRejected):
        store.accept_result("missing", "token", {"status": "OK"})

    assert not any("INSERT INTO analysis_results" in query for query, _ in connection.calls)


def test_accept_result_rejects_wrong_lease_token():
    connection = FakeConnection()
    connection.job = {"id": "01JTEST", "job_type": "analysis", "payload": {"input": {}}, "status": "LEASED", "attempts": 1}
    store = PostgresJobStore(connection)
    store.lease_next("worker-1", ttl_seconds=300)

    with pytest.raises(LeaseConflict, match="lease token"):
        store.accept_result("01JTEST", "wrong-token", valid_result("01JTEST"))

from fastapi import FastAPI, Header, HTTPException
import os
from datetime import datetime
import psycopg
from pydantic import BaseModel, ConfigDict, Field
from .core import InMemoryJobStore, LeaseConflict, ResultRejected
from .postgres import PostgresJobStore
from .outbox import DiscordOutboxMessage, DiscordWebhookClient
import time

app = FastAPI(title="Hivemind Trading Bot", version="1.0.0a1")
DATABASE_URL = os.getenv("DATABASE_URL")
WORKER_TOKEN = os.getenv("WORKER_TOKEN")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
_sent_notifications = set()


def get_store():
    if DATABASE_URL:
        return PostgresJobStore(psycopg.connect(DATABASE_URL))
    return store


store = InMemoryJobStore()


class JobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    job_type: str = Field(pattern="^[a-z_]{1,64}$")
    input: dict
    priority: int = Field(default=50, ge=0, le=100)
    expires_at: str


@app.get("/health/ready")
def readiness():
    return {"status": "ready", "mode": "fictional-data-only"}


def require_worker_token(token):
    if WORKER_TOKEN and token != WORKER_TOKEN:
        raise HTTPException(status_code=401, detail="invalid worker token")


@app.post("/api/v1/jobs", status_code=201)
def create_job(body: JobRequest, idempotency_key: str = Header(alias="Idempotency-Key"), authorization: str | None = Header(default=None)):
    require_worker_token(authorization.removeprefix("Bearer ") if authorization else None)
    try:
        active_store = get_store()
        payload = body.model_dump()
        job = active_store.create_job(idempotency_key, payload, body.job_type, datetime.fromisoformat(body.expires_at.replace("Z", "+00:00"))) if DATABASE_URL else active_store.create_job(idempotency_key, payload)
    except LeaseConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"job_id": job.id, "status": job.status, "expires_at": body.expires_at}


@app.post("/api/v1/jobs/lease")
def lease_job(worker_id: str = Header(alias="X-Worker-Id"), authorization: str | None = Header(default=None)):
    require_worker_token(authorization.removeprefix("Bearer ") if authorization else None)
    active_store = get_store()
    lease = active_store.lease_next(worker_id, ttl_seconds=300) if DATABASE_URL else active_store.lease_next(worker_id, now=time.time(), ttl=300)
    if lease is None:
        return {"job": None}
    job = active_store.get_job(lease.job_id) if DATABASE_URL else active_store.jobs[lease.job_id]
    return {"job_id": job.id, "lease_token": lease.token, "worker_id": worker_id, "lease_expires_at": lease.expires_at, "attempt": job.attempts, "input": job.payload["input"]}


@app.post("/api/v1/jobs/{job_id}/result")
def submit_result(job_id: str, result: dict, lease_token: str = Header(alias="X-Lease-Token"), authorization: str | None = Header(default=None)):
    require_worker_token(authorization.removeprefix("Bearer ") if authorization else None)
    try:
        accepted = get_store().accept_result(job_id, lease_token, result)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    except ResultRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LeaseConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if accepted and DISCORD_WEBHOOK_URL:
        analysis = result["analysis"]
        if job_id not in _sent_notifications:
            DiscordWebhookClient(DISCORD_WEBHOOK_URL).send(DiscordOutboxMessage(job_id, analysis["summary"], result["status"], float(analysis["confidence"])).render())
            _sent_notifications.add(job_id)
    return {"job_id": job_id, "status": "SUCCEEDED", "notification": "sent" if DISCORD_WEBHOOK_URL else "dry-run"}


@app.post("/api/v1/jobs/{job_id}/fail")
def fail_job(job_id: str, lease_token: str = Header(alias="X-Lease-Token"), authorization: str | None = Header(default=None)):
    require_worker_token(authorization.removeprefix("Bearer ") if authorization else None)
    active_store = get_store()
    try:
        status = active_store.fail_job(job_id, lease_token) if DATABASE_URL else active_store.fail_job(job_id, lease_token, now=time.time())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    except LeaseConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"job_id": job_id, "status": status}
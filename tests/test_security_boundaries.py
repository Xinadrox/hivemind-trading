import importlib

import pytest


def test_runtime_mode_defaults_to_fixture(monkeypatch):
    monkeypatch.delenv("HIVEMIND_MODE", raising=False)
    from hivemind.config import RuntimeConfig

    assert RuntimeConfig.from_env().mode == "fixture"


def test_runtime_mode_rejects_paper_and_live_until_explicitly_supported(monkeypatch):
    monkeypatch.setenv("HIVEMIND_MODE", "live")
    from hivemind.config import RuntimeConfig

    with pytest.raises(ValueError, match="unsupported mode"):
        RuntimeConfig.from_env()


def test_missing_worker_token_is_fail_closed(monkeypatch):
    monkeypatch.delenv("WORKER_TOKEN", raising=False)
    import hivemind.app as app_module

    importlib.reload(app_module)
    with pytest.raises(app_module.HTTPException) as exc:
        app_module.require_worker_token(None)
    assert exc.value.status_code == 503


def test_expired_job_date_is_rejected():
    from hivemind.validation import parse_expiry

    with pytest.raises(ValueError, match="future"):
        parse_expiry("1970-01-01T00:00:00Z")


def test_job_endpoint_fails_closed_without_worker_token(monkeypatch):
    monkeypatch.delenv("WORKER_TOKEN", raising=False)
    import hivemind.app as app_module
    from fastapi.testclient import TestClient

    importlib.reload(app_module)
    response = TestClient(app_module.app).post(
        "/api/v1/jobs",
        headers={"Idempotency-Key": "test-key"},
        json={
            "job_type": "analysis",
            "input": {"symbol": "FICT-001"},
            "expires_at": "2099-01-01T00:00:00Z",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "worker authentication is not configured"


def test_job_endpoint_rejects_invalid_expiry(monkeypatch):
    monkeypatch.setenv("WORKER_TOKEN", "test-token")
    import hivemind.app as app_module
    from fastapi.testclient import TestClient

    importlib.reload(app_module)
    response = TestClient(app_module.app).post(
        "/api/v1/jobs",
        headers={"Idempotency-Key": "test-key", "Authorization": "Bearer test-token"},
        json={"job_type": "analysis", "input": {}, "expires_at": "not-a-date"},
    )

    assert response.status_code == 422
    assert "valid ISO-8601" in response.json()["detail"]

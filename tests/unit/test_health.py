"""Smoke tests for Phase 0 process bootstraps."""

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from apps.api_controller.main import app as api_app
from apps.durable_worker.main import app as durable_app
from apps.voice_worker.main import app as voice_app
from research.provider_simulator.main import app as simulator_app


def test_liveness_endpoints() -> None:
    for app in (api_app, durable_app, voice_app, simulator_app):
        response = TestClient(app).get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_api_readiness_fails_closed_without_database(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://voice_agent:unused@127.0.0.1:1/voice_agent"
    )
    response = TestClient(api_app).get("/health/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == "Database unavailable"

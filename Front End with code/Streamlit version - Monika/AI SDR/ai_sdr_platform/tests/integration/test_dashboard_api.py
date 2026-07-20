from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai_sdr_platform.src.api.app import create_app
from ai_sdr_platform.src.auth.models import CreateUserRequest, UserRole
from ai_sdr_platform.src.auth.repository import SQLAlchemyAuthRepository
from ai_sdr_platform.src.auth.service import AuthService
from ai_sdr_platform.src.shared import config
import ai_sdr_platform.src.auth.dependencies as deps


@pytest.fixture
def authed_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(
        config,
        "settings",
        replace(config.settings, auth_enabled=True, auth_jwt_secret="test-secret-key-with-enough-length-32"),
    )
    db_url = f"sqlite:///{(tmp_path / 'dash_auth.db').resolve()}"
    repo = SQLAlchemyAuthRepository(db_url=db_url)
    service = AuthService(repository=repo)
    service.create_user(
        CreateUserRequest(
            email="admin@test.local",
            password="secret123",
            display_name="Test Admin",
            role=UserRole.ADMIN,
        )
    )
    monkeypatch.setattr(deps, "_service", service)
    return TestClient(create_app())


def test_dashboard_requires_auth(authed_client: TestClient) -> None:
    assert authed_client.get("/sdr/dashboard").status_code == 401


def test_dashboard_returns_counts(authed_client: TestClient) -> None:
    login = authed_client.post(
        "/auth/login",
        json={"email": "admin@test.local", "password": "secret123"},
    )
    token = login.json()["access_token"]
    response = authed_client.get(
        "/sdr/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "icp_count" in body
    assert "pending_campaigns" in body
    assert body["icp_count"] >= 0

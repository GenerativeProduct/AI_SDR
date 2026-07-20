from pathlib import Path

import pytest
from dataclasses import replace
from fastapi.testclient import TestClient

from ai_sdr_platform.src.api.app import create_app
from ai_sdr_platform.src.auth.models import CreateUserRequest, UserRole
from ai_sdr_platform.src.auth.repository import SQLAlchemyAuthRepository
from ai_sdr_platform.src.auth.service import AuthService
from ai_sdr_platform.src.shared import config


@pytest.fixture
def auth_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(
        config,
        "settings",
        replace(
            config.settings,
            auth_enabled=True,
            auth_jwt_secret="test-secret-key-with-enough-length-32",
        ),
    )

    db_url = f"sqlite:///{(tmp_path / 'auth_test.db').resolve()}"
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
    import ai_sdr_platform.src.auth.dependencies as deps

    monkeypatch.setattr(deps, "_service", service)
    return TestClient(create_app())


def test_login_and_me(auth_client: TestClient) -> None:
    login = auth_client.post(
        "/auth/login",
        json={"email": "admin@test.local", "password": "secret123"},
    )
    assert login.status_code == 200
    tokens = login.json()
    assert "access_token" in tokens
    me = auth_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "admin@test.local"


def test_refresh_token(auth_client: TestClient) -> None:
    login = auth_client.post(
        "/auth/login",
        json={"email": "admin@test.local", "password": "secret123"},
    )
    refresh = auth_client.post(
        "/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]


def test_protected_route_without_token(auth_client: TestClient) -> None:
    response = auth_client.get("/icp")
    assert response.status_code == 401

from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ai_sdr_platform.src.auth.models import AuthUser, UserRole
from ai_sdr_platform.src.auth.service import AuthService, role_can_approve, role_can_manage_icp
from ai_sdr_platform.src.shared import config
from ai_sdr_platform.src.shared.exceptions import ValidationError

_bearer = HTTPBearer(auto_error=False)
_service = AuthService()


def get_auth_service() -> AuthService:
    return _service


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    service: AuthService = Depends(get_auth_service),
) -> AuthUser | None:
    if not config.settings.auth_enabled:
        return AuthUser(
            user_id="dev-user",
            email="dev@localhost",
            display_name="Dev User",
            role=UserRole.ADMIN,
            is_active=True,
        )
    if credentials is None:
        return None
    try:
        return service.get_user_from_access_token(credentials.credentials)
    except ValidationError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    service: AuthService = Depends(get_auth_service),
) -> AuthUser:
    if not config.settings.auth_enabled:
        return AuthUser(
            user_id="dev-user",
            email="dev@localhost",
            display_name="Dev User",
            role=UserRole.ADMIN,
            is_active=True,
        )
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return service.get_user_from_access_token(credentials.credentials)
    except ValidationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def require_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


def require_operator(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if not role_can_approve(user.role):
        raise HTTPException(status_code=403, detail="Operator role required")
    return user


def require_manager(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if not role_can_manage_icp(user.role):
        raise HTTPException(status_code=403, detail="Manager role required")
    return user


PUBLIC_PATH_PREFIXES = (
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/auth/login",
    "/auth/refresh",
)


PUBLIC_PATHS = {
    "/health",
    "/openapi.json",
    "/docs",
    "/redoc",
}


WEBHOOK_PATHS = {
    "/outreach/events",
    "/outreach/events/brevo",
    "/conversations/inbound",
    "/conversations/inbound/brevo",
    "/meetings/webhooks/provider",
}


def is_public_path(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES if prefix not in PUBLIC_PATHS)


async def auth_middleware(request: Request, call_next):
    if not config.settings.auth_enabled:
        return await call_next(request)
    path = request.url.path.rstrip("/") or "/"
    if path in PUBLIC_PATHS or path.startswith("/auth/login") or path.startswith("/auth/refresh"):
        return await call_next(request)
    if path in WEBHOOK_PATHS:
        return await call_next(request)
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        from starlette.responses import JSONResponse

        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    token = auth_header[7:]
    try:
        user = _service.get_user_from_access_token(token)
        request.state.user = user
    except ValidationError:
        from starlette.responses import JSONResponse

        return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})
    return await call_next(request)

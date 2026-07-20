from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ai_sdr_platform.src.auth.dependencies import get_auth_service, get_current_user, require_admin
from ai_sdr_platform.src.auth.models import (
    CreateUserRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenPair,
    UserPublic,
)
from ai_sdr_platform.src.auth.service import AuthService
from ai_sdr_platform.src.shared.exceptions import ValidationError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenPair:
    try:
        user = service.authenticate(payload.email, payload.password)
        return service.issue_tokens(user)
    except ValidationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, service: AuthService = Depends(get_auth_service)) -> TokenPair:
    try:
        return service.refresh_tokens(payload.refresh_token)
    except ValidationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/logout")
def logout(payload: LogoutRequest, service: AuthService = Depends(get_auth_service)) -> dict[str, str]:
    service.logout(payload.refresh_token)
    return {"status": "ok"}


@router.get("/me", response_model=UserPublic)
def me(user=Depends(get_current_user)) -> UserPublic:
    return UserPublic(
        user_id=user.user_id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
    )


@router.post("/users", response_model=UserPublic)
def create_user(
    payload: CreateUserRequest,
    service: AuthService = Depends(get_auth_service),
    _admin=Depends(require_admin),
) -> UserPublic:
    try:
        user = service.create_user(payload)
        return UserPublic(
            user_id=user.user_id,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

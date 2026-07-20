from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    OPERATOR = "operator"
    MANAGER = "manager"
    ADMIN = "admin"


class AuthUser(BaseModel):
    user_id: str
    email: str
    display_name: str
    role: UserRole
    is_active: bool = True


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserPublic(BaseModel):
    user_id: str
    email: str
    display_name: str
    role: UserRole


class CreateUserRequest(BaseModel):
    email: str
    password: str
    display_name: str = ""
    role: UserRole = UserRole.OPERATOR


class LogoutRequest(BaseModel):
    refresh_token: str | None = None

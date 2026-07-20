from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from ai_sdr_platform.src.auth.models import AuthUser, CreateUserRequest, TokenPair, UserRole
from ai_sdr_platform.src.auth.repository import AuthRepository, SQLAlchemyAuthRepository
from ai_sdr_platform.src.shared.config import settings
from ai_sdr_platform.src.shared.exceptions import ValidationError


class AuthService:
    def __init__(self, repository: AuthRepository | None = None) -> None:
        self.repository = repository or SQLAlchemyAuthRepository()

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    def create_user(self, request: CreateUserRequest) -> AuthUser:
        existing = self.repository.get_by_email(request.email)
        if existing:
            raise ValidationError("User with this email already exists")
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        return self.repository.create_user(
            user_id=user_id,
            email=request.email,
            password_hash=self.hash_password(request.password),
            display_name=request.display_name,
            role=request.role,
        )

    def authenticate(self, email: str, password: str) -> AuthUser:
        record = self.repository.get_by_email(email)
        if record is None:
            raise ValidationError("Invalid email or password")
        user, password_hash = record
        if not user.is_active or not self.verify_password(password, password_hash):
            raise ValidationError("Invalid email or password")
        return user

    def issue_tokens(self, user: AuthUser) -> TokenPair:
        access_expires = timedelta(minutes=settings.auth_jwt_expire_minutes)
        refresh_expires = timedelta(days=settings.auth_refresh_expire_days)
        now = datetime.now(UTC)
        access_payload = {
            "sub": user.user_id,
            "email": user.email,
            "role": user.role.value,
            "type": "access",
            "exp": int((now + access_expires).timestamp()),
            "iat": int(now.timestamp()),
        }
        refresh_token_id = f"rt_{uuid.uuid4().hex}"
        refresh_payload = {
            "sub": user.user_id,
            "type": "refresh",
            "jti": refresh_token_id,
            "exp": int((now + refresh_expires).timestamp()),
            "iat": int(now.timestamp()),
        }
        access_token = jwt.encode(access_payload, settings.auth_jwt_secret, algorithm="HS256")
        refresh_token = jwt.encode(refresh_payload, settings.auth_jwt_secret, algorithm="HS256")
        token_hash = self._hash_token(refresh_token)
        self.repository.store_refresh_token(refresh_token_id, user.user_id, token_hash)
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_expires.total_seconds()),
        )

    def refresh_tokens(self, refresh_token: str) -> TokenPair:
        payload = self._decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValidationError("Invalid refresh token")
        token_id = payload.get("jti", "")
        token_hash = self._hash_token(refresh_token)
        if not self.repository.is_refresh_token_valid(token_id, token_hash):
            raise ValidationError("Refresh token revoked or invalid")
        user = self.repository.get_by_id(payload["sub"])
        if user is None or not user.is_active:
            raise ValidationError("User not found")
        self.repository.revoke_refresh_token(token_id)
        return self.issue_tokens(user)

    def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        try:
            payload = self._decode_token(refresh_token)
            if payload.get("type") == "refresh" and payload.get("jti"):
                self.repository.revoke_refresh_token(payload["jti"])
        except ValidationError:
            return

    def get_user_from_access_token(self, token: str) -> AuthUser:
        payload = self._decode_token(token)
        if payload.get("type") != "access":
            raise ValidationError("Invalid access token")
        user = self.repository.get_by_id(payload["sub"])
        if user is None or not user.is_active:
            raise ValidationError("User not found")
        return user

    def ensure_default_admin(self) -> AuthUser | None:
        if self.repository.get_by_email(settings.auth_default_admin_email):
            return None
        return self.create_user(
            CreateUserRequest(
                email=settings.auth_default_admin_email,
                password=settings.auth_default_admin_password,
                display_name="Admin",
                role=UserRole.ADMIN,
            )
        )

    def _decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, settings.auth_jwt_secret, algorithms=["HS256"])
        except jwt.PyJWTError as exc:
            raise ValidationError("Invalid or expired token") from exc

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()


def role_can_approve(role: UserRole) -> bool:
    return role in {UserRole.OPERATOR, UserRole.ADMIN}


def role_can_manage_icp(role: UserRole) -> bool:
    return role in {UserRole.MANAGER, UserRole.ADMIN, UserRole.OPERATOR}

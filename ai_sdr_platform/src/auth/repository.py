from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from sqlalchemy import Boolean, Column, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from ai_sdr_platform.src.auth.models import AuthUser, UserRole
from ai_sdr_platform.src.shared.config import settings

Base = declarative_base()


class UserORM(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=False, default="")
    role = Column(String, nullable=False, default=UserRole.OPERATOR.value)
    is_active = Column(Boolean, nullable=False, default=True)
    refresh_tokens_json = Column(Text, nullable=False, default="[]")


class RefreshTokenORM(Base):
    __tablename__ = "refresh_tokens"

    token_id = Column(String, primary_key=True)
    user_id = Column(String, index=True, nullable=False)
    token_hash = Column(String, nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)


class AuthRepository(Protocol):
    def create_user(
        self,
        user_id: str,
        email: str,
        password_hash: str,
        display_name: str,
        role: UserRole,
    ) -> AuthUser:
        ...

    def get_by_email(self, email: str) -> tuple[AuthUser, str] | None:
        ...

    def get_by_id(self, user_id: str) -> AuthUser | None:
        ...

    def store_refresh_token(self, token_id: str, user_id: str, token_hash: str) -> None:
        ...

    def revoke_refresh_token(self, token_id: str) -> None:
        ...

    def is_refresh_token_valid(self, token_id: str, token_hash: str) -> bool:
        ...


class SQLAlchemyAuthRepository:
    def __init__(self, db_url: str | None = None) -> None:
        database_url = db_url or self._default_db_url()
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, future=True, connect_args=connect_args, pool_pre_ping=True, pool_recycle=300)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, future=True)
        Base.metadata.create_all(self.engine)

    def create_user(
        self,
        user_id: str,
        email: str,
        password_hash: str,
        display_name: str,
        role: UserRole,
    ) -> AuthUser:
        with self.SessionLocal() as session:
            orm = UserORM(
                user_id=user_id,
                email=email.lower().strip(),
                password_hash=password_hash,
                display_name=display_name or email.split("@")[0],
                role=role.value,
                is_active=True,
            )
            session.add(orm)
            session.commit()
        return AuthUser(
            user_id=user_id,
            email=email.lower().strip(),
            display_name=display_name or email.split("@")[0],
            role=role,
            is_active=True,
        )

    def get_by_email(self, email: str) -> tuple[AuthUser, str] | None:
        with self.SessionLocal() as session:
            row = session.query(UserORM).filter(UserORM.email == email.lower().strip()).first()
            if row is None:
                return None
            return self._to_user(row), row.password_hash

    def get_by_id(self, user_id: str) -> AuthUser | None:
        with self.SessionLocal() as session:
            row = session.query(UserORM).filter(UserORM.user_id == user_id).first()
            return self._to_user(row) if row else None

    def store_refresh_token(self, token_id: str, user_id: str, token_hash: str) -> None:
        with self.SessionLocal() as session:
            session.add(
                RefreshTokenORM(
                    token_id=token_id,
                    user_id=user_id,
                    token_hash=token_hash,
                    revoked=False,
                )
            )
            session.commit()

    def revoke_refresh_token(self, token_id: str) -> None:
        with self.SessionLocal() as session:
            row = session.query(RefreshTokenORM).filter(RefreshTokenORM.token_id == token_id).first()
            if row:
                row.revoked = True
                session.commit()

    def is_refresh_token_valid(self, token_id: str, token_hash: str) -> bool:
        with self.SessionLocal() as session:
            row = (
                session.query(RefreshTokenORM)
                .filter(
                    RefreshTokenORM.token_id == token_id,
                    RefreshTokenORM.token_hash == token_hash,
                    RefreshTokenORM.revoked.is_(False),
                )
                .first()
            )
            return row is not None

    @staticmethod
    def _to_user(row: UserORM) -> AuthUser:
        return AuthUser(
            user_id=row.user_id,
            email=row.email,
            display_name=row.display_name,
            role=UserRole(row.role),
            is_active=bool(row.is_active),
        )

    @staticmethod
    def _default_db_url() -> str:
        if settings.auth_database_url:
            return settings.auth_database_url
        data_dir = Path(__file__).resolve().parents[2] / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(data_dir / 'auth.db').resolve()}"

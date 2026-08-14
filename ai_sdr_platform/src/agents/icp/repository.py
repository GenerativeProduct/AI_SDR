from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from sqlalchemy import Column, Integer, String, Text, create_engine, desc
from sqlalchemy.orm import declarative_base, sessionmaker

from ai_sdr_platform.src.agents.icp.models import ICPDefinition
from ai_sdr_platform.src.shared.config import settings

Base = declarative_base()


class ICPVersionORM(Base):
    __tablename__ = "icp_versions"

    version_id = Column(String, primary_key=True)
    icp_id = Column(String, index=True, nullable=False)
    version = Column(Integer, nullable=False)
    icp_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    payload_json = Column(Text, nullable=False)


class ICPRepository(Protocol):
    def save(self, icp: ICPDefinition) -> ICPDefinition:
        ...

    def get_latest(self, icp_id: str) -> ICPDefinition | None:
        ...

    def get_version(self, icp_id: str, version: int) -> ICPDefinition | None:
        ...

    def list_latest(self) -> list[ICPDefinition]:
        ...

    def list_versions(self, icp_id: str) -> list[ICPDefinition]:
        ...


class SQLAlchemyICPRepository:
    def __init__(self, db_url: str | None = None) -> None:
        database_url = db_url or self._default_db_url()
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, future=True, connect_args=connect_args, pool_pre_ping=True, pool_recycle=300)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, future=True)
        Base.metadata.create_all(self.engine)

    def save(self, icp: ICPDefinition) -> ICPDefinition:
        payload = icp.model_dump(mode="json")
        with self.SessionLocal() as session:
            orm = ICPVersionORM(
                version_id=icp.version_id,
                icp_id=icp.icp_id,
                version=icp.version,
                icp_name=icp.icp_name,
                status=icp.status,
                payload_json=json.dumps(payload),
            )
            session.add(orm)
            session.commit()
        return icp

    def get_latest(self, icp_id: str) -> ICPDefinition | None:
        with self.SessionLocal() as session:
            row = (
                session.query(ICPVersionORM)
                .filter(ICPVersionORM.icp_id == icp_id)
                .order_by(desc(ICPVersionORM.version))
                .first()
            )
            return self._to_model(row)

    def get_version(self, icp_id: str, version: int) -> ICPDefinition | None:
        with self.SessionLocal() as session:
            row = (
                session.query(ICPVersionORM)
                .filter(ICPVersionORM.icp_id == icp_id, ICPVersionORM.version == version)
                .first()
            )
            return self._to_model(row)

    def list_latest(self) -> list[ICPDefinition]:
        with self.SessionLocal() as session:
            rows = session.query(ICPVersionORM).order_by(ICPVersionORM.icp_id, desc(ICPVersionORM.version)).all()
            latest: dict[str, ICPDefinition] = {}
            for row in rows:
                if row.icp_id not in latest:
                    latest[row.icp_id] = self._to_model(row)
            return list(latest.values())

    def list_versions(self, icp_id: str) -> list[ICPDefinition]:
        with self.SessionLocal() as session:
            rows = (
                session.query(ICPVersionORM)
                .filter(ICPVersionORM.icp_id == icp_id)
                .order_by(ICPVersionORM.version.asc())
                .all()
            )
            return [self._to_model(r) for r in rows if r]

    @staticmethod
    def _to_model(row: ICPVersionORM | None) -> ICPDefinition | None:
        if row is None:
            return None
        return ICPDefinition.model_validate(json.loads(row.payload_json))

    @staticmethod
    def _default_db_url() -> str:
        if settings.icp_database_url:
            return settings.icp_database_url
        base_dir = Path("ai_sdr_platform/data")
        base_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(base_dir / 'icp.db').resolve()}"

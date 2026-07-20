from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from sqlalchemy import Column, DateTime, String, Text, create_engine, desc
from sqlalchemy.orm import declarative_base, sessionmaker

from ai_sdr_platform.src.agents.qualification.models import QualificationResult
from ai_sdr_platform.src.shared.config import settings

Base = declarative_base()


class QualificationORM(Base):
    __tablename__ = "qualification_results"

    qualification_id = Column(String, primary_key=True)
    intelligence_id = Column(String, index=True, nullable=False)
    account_id = Column(String, index=True, nullable=False)
    contact_id = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    payload_json = Column(Text, nullable=False)


class QualificationRepository(Protocol):
    def save(self, result: QualificationResult) -> QualificationResult:
        ...

    def get_latest(self, contact_id: str) -> QualificationResult | None:
        ...

    def list_latest(self, account_id: str | None = None) -> list[QualificationResult]:
        ...


class SQLAlchemyQualificationRepository:
    def __init__(self, db_url: str | None = None) -> None:
        database_url = db_url or self._default_db_url()
        connect_args = (
            {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        )
        self.engine = create_engine(
            database_url, future=True, connect_args=connect_args
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False, future=True
        )
        Base.metadata.create_all(self.engine)

    def save(self, result: QualificationResult) -> QualificationResult:
        with self.SessionLocal() as session:
            session.merge(
                QualificationORM(
                    qualification_id=result.qualification_id,
                    intelligence_id=result.intelligence_id,
                    account_id=result.account_id,
                    contact_id=result.contact_id,
                    created_at=result.created_at,
                    payload_json=json.dumps(result.model_dump(mode="json")),
                )
            )
            session.commit()
        return result

    def get_latest(self, contact_id: str) -> QualificationResult | None:
        with self.SessionLocal() as session:
            row = (
                session.query(QualificationORM)
                .filter(QualificationORM.contact_id == contact_id)
                .order_by(desc(QualificationORM.created_at))
                .first()
            )
            return self._to_model(row)

    def list_latest(self, account_id: str | None = None) -> list[QualificationResult]:
        with self.SessionLocal() as session:
            query = session.query(QualificationORM)
            if account_id:
                query = query.filter(QualificationORM.account_id == account_id)
            rows = query.order_by(desc(QualificationORM.created_at)).all()
            latest: dict[str, QualificationResult] = {}
            for row in rows:
                if row.contact_id not in latest:
                    result = self._to_model(row)
                    if result:
                        latest[row.contact_id] = result
            return list(latest.values())

    @staticmethod
    def _to_model(row: QualificationORM | None) -> QualificationResult | None:
        if row is None:
            return None
        return QualificationResult.model_validate(json.loads(row.payload_json))

    @staticmethod
    def _default_db_url() -> str:
        if settings.qualification_database_url:
            return settings.qualification_database_url
        base_dir = Path("ai_sdr_platform/data")
        base_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(base_dir / 'qualification.db').resolve()}"

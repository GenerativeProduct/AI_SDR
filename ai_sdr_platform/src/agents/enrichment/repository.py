from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from sqlalchemy import Column, DateTime, String, Text, create_engine, desc
from sqlalchemy.orm import declarative_base, sessionmaker

from ai_sdr_platform.src.agents.enrichment.models import EnrichmentResult
from ai_sdr_platform.src.shared.config import settings

Base = declarative_base()


class EnrichmentORM(Base):
    __tablename__ = "enrichment_results"

    enrichment_id = Column(String, primary_key=True)
    account_id = Column(String, index=True, nullable=False)
    company_name = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    payload_json = Column(Text, nullable=False)


class EnrichmentRepository(Protocol):
    def save(self, result: EnrichmentResult) -> EnrichmentResult:
        ...

    def get_latest(self, account_id: str) -> EnrichmentResult | None:
        ...

    def list_latest(self) -> list[EnrichmentResult]:
        ...


class SQLAlchemyEnrichmentRepository:
    def __init__(self, db_url: str | None = None) -> None:
        database_url = db_url or self._default_db_url()
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, future=True, connect_args=connect_args, pool_pre_ping=True, pool_recycle=300)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, future=True)
        Base.metadata.create_all(self.engine)

    def save(self, result: EnrichmentResult) -> EnrichmentResult:
        payload = result.model_dump(mode="json")
        with self.SessionLocal() as session:
            orm = EnrichmentORM(
                enrichment_id=result.enrichment_id,
                account_id=result.account_id,
                company_name=result.company_name,
                status=result.status,
                created_at=result.created_at,
                updated_at=result.updated_at,
                payload_json=json.dumps(payload),
            )
            session.merge(orm)
            session.commit()
        return result

    def get_latest(self, account_id: str) -> EnrichmentResult | None:
        with self.SessionLocal() as session:
            row = (
                session.query(EnrichmentORM)
                .filter(EnrichmentORM.account_id == account_id)
                .order_by(desc(EnrichmentORM.updated_at))
                .first()
            )
            return self._to_model(row)

    def list_latest(self) -> list[EnrichmentResult]:
        with self.SessionLocal() as session:
            rows = session.query(EnrichmentORM).order_by(desc(EnrichmentORM.updated_at)).all()
            latest: dict[str, EnrichmentResult] = {}
            for row in rows:
                if row.account_id not in latest:
                    model = self._to_model(row)
                    if model:
                        latest[row.account_id] = model
            return list(latest.values())

    @staticmethod
    def _to_model(row: EnrichmentORM | None) -> EnrichmentResult | None:
        if row is None:
            return None
        return EnrichmentResult.model_validate(json.loads(row.payload_json))

    @staticmethod
    def _default_db_url() -> str:
        if settings.enrichment_database_url:
            return settings.enrichment_database_url
        base_dir = Path("ai_sdr_platform/data")
        base_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(base_dir / 'enrichment.db').resolve()}"

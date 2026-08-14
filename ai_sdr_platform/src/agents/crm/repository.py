from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import Column, DateTime, String, Text, create_engine, desc
from sqlalchemy.orm import declarative_base, sessionmaker

from ai_sdr_platform.src.agents.crm.models import CRMSyncRecord
from ai_sdr_platform.src.shared.config import settings

Base = declarative_base()


class CRMSyncORM(Base):
    __tablename__ = "sdr_crm_syncs"
    sync_id = Column(String, primary_key=True)
    meeting_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, index=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    payload_json = Column(Text, nullable=False)


class SQLAlchemyCRMRepository:
    def __init__(self, db_url: str | None = None) -> None:
        url = db_url or settings.crm_database_url or self._default_url()
        args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        self.engine = create_engine(url, future=True, connect_args=args, pool_pre_ping=True, pool_recycle=300)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)
        Base.metadata.create_all(self.engine)

    def save(self, record: CRMSyncRecord) -> CRMSyncRecord:
        with self.SessionLocal() as session:
            session.merge(
                CRMSyncORM(
                    sync_id=record.sync_id,
                    meeting_id=record.meeting_id,
                    status=record.status,
                    updated_at=record.updated_at,
                    payload_json=json.dumps(record.model_dump(mode="json")),
                )
            )
            session.commit()
        return record

    def get_by_meeting(self, meeting_id: str) -> CRMSyncRecord | None:
        with self.SessionLocal() as session:
            row = (
                session.query(CRMSyncORM)
                .filter(CRMSyncORM.meeting_id == meeting_id)
                .first()
            )
            return self._model(row)

    def list(self) -> list[CRMSyncRecord]:
        with self.SessionLocal() as session:
            return [
                model
                for row in session.query(CRMSyncORM)
                .order_by(desc(CRMSyncORM.updated_at))
                .all()
                if (model := self._model(row)) is not None
            ]

    @staticmethod
    def _model(row: CRMSyncORM | None) -> CRMSyncRecord | None:
        return (
            CRMSyncRecord.model_validate(json.loads(row.payload_json))
            if row is not None
            else None
        )

    @staticmethod
    def _default_url() -> str:
        directory = Path("ai_sdr_platform/data")
        directory.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(directory / 'crm.db').resolve()}"

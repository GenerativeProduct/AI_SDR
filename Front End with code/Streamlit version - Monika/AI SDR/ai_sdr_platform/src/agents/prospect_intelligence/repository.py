from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from sqlalchemy import Boolean, Column, DateTime, String, Text, create_engine, desc
from sqlalchemy.orm import declarative_base, sessionmaker

from ai_sdr_platform.src.agents.prospect_intelligence.models import (
    ProspectIntelligenceResult,
    ProspectOutcome,
)
from ai_sdr_platform.src.shared.config import settings

Base = declarative_base()


class ProspectIntelligenceORM(Base):
    __tablename__ = "prospect_intelligence_results"

    intelligence_id = Column(String, primary_key=True)
    account_id = Column(String, index=True, nullable=False)
    contact_id = Column(String, index=True, nullable=False)
    company_name = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    payload_json = Column(Text, nullable=False)


class ProspectOutcomeORM(Base):
    __tablename__ = "prospect_intelligence_outcomes"

    outcome_id = Column(String, primary_key=True)
    intelligence_id = Column(String, index=True, nullable=False)
    account_id = Column(String, index=True, nullable=False)
    contact_id = Column(String, index=True, nullable=False)
    replied = Column(Boolean, nullable=False)
    positive_reply = Column(Boolean, nullable=False)
    meeting_booked = Column(Boolean, nullable=False)
    qualified = Column(Boolean, nullable=False)
    opportunity_created = Column(Boolean, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    payload_json = Column(Text, nullable=False)


class ProspectIntelligenceRepository(Protocol):
    def save(self, result: ProspectIntelligenceResult) -> ProspectIntelligenceResult:
        ...

    def get_latest(self, contact_id: str) -> ProspectIntelligenceResult | None:
        ...

    def list_latest(self, account_id: str | None = None) -> list[ProspectIntelligenceResult]:
        ...

    def save_outcome(self, outcome: ProspectOutcome) -> ProspectOutcome:
        ...

    def list_training_rows(self) -> list[tuple[ProspectIntelligenceResult, ProspectOutcome]]:
        ...


class SQLAlchemyProspectIntelligenceRepository:
    def __init__(self, db_url: str | None = None) -> None:
        database_url = db_url or self._default_db_url()
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, future=True, connect_args=connect_args)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, future=True)
        Base.metadata.create_all(self.engine)

    def save(self, result: ProspectIntelligenceResult) -> ProspectIntelligenceResult:
        with self.SessionLocal() as session:
            session.merge(
                ProspectIntelligenceORM(
                    intelligence_id=result.intelligence_id,
                    account_id=result.account_id,
                    contact_id=result.contact_id,
                    company_name=result.company_name,
                    created_at=result.created_at,
                    payload_json=json.dumps(result.model_dump(mode="json")),
                )
            )
            session.commit()
        return result

    def get_latest(self, contact_id: str) -> ProspectIntelligenceResult | None:
        with self.SessionLocal() as session:
            row = (
                session.query(ProspectIntelligenceORM)
                .filter(ProspectIntelligenceORM.contact_id == contact_id)
                .order_by(desc(ProspectIntelligenceORM.created_at))
                .first()
            )
            return self._to_model(row)

    def list_latest(self, account_id: str | None = None) -> list[ProspectIntelligenceResult]:
        with self.SessionLocal() as session:
            query = session.query(ProspectIntelligenceORM)
            if account_id:
                query = query.filter(ProspectIntelligenceORM.account_id == account_id)
            rows = query.order_by(desc(ProspectIntelligenceORM.created_at)).all()
            latest: dict[str, ProspectIntelligenceResult] = {}
            for row in rows:
                if row.contact_id not in latest:
                    model = self._to_model(row)
                    if model:
                        latest[row.contact_id] = model
            return list(latest.values())

    def save_outcome(self, outcome: ProspectOutcome) -> ProspectOutcome:
        with self.SessionLocal() as session:
            exists = (
                session.query(ProspectIntelligenceORM)
                .filter(ProspectIntelligenceORM.intelligence_id == outcome.intelligence_id)
                .first()
            )
            if exists is None:
                raise ValueError("intelligence_id does not reference a stored prospect intelligence result")
            if exists.account_id != outcome.account_id or exists.contact_id != outcome.contact_id:
                raise ValueError("outcome account_id/contact_id must match the intelligence snapshot")
            session.merge(
                ProspectOutcomeORM(
                    outcome_id=outcome.outcome_id,
                    intelligence_id=outcome.intelligence_id,
                    account_id=outcome.account_id,
                    contact_id=outcome.contact_id,
                    replied=outcome.replied,
                    positive_reply=outcome.positive_reply,
                    meeting_booked=outcome.meeting_booked,
                    qualified=outcome.qualified,
                    opportunity_created=outcome.opportunity_created,
                    occurred_at=outcome.occurred_at,
                    payload_json=json.dumps(outcome.model_dump(mode="json")),
                )
            )
            session.commit()
        return outcome

    def list_training_rows(self) -> list[tuple[ProspectIntelligenceResult, ProspectOutcome]]:
        with self.SessionLocal() as session:
            rows = (
                session.query(ProspectIntelligenceORM, ProspectOutcomeORM)
                .join(
                    ProspectOutcomeORM,
                    ProspectOutcomeORM.intelligence_id == ProspectIntelligenceORM.intelligence_id,
                )
                .order_by(ProspectOutcomeORM.occurred_at.asc())
                .all()
            )
            aggregated: dict[str, tuple[ProspectIntelligenceResult, ProspectOutcome]] = {}
            for intelligence, outcome_row in rows:
                result = ProspectIntelligenceResult.model_validate(json.loads(intelligence.payload_json))
                outcome = ProspectOutcome.model_validate(json.loads(outcome_row.payload_json))
                existing = aggregated.get(intelligence.intelligence_id)
                if existing:
                    prior = existing[1]
                    outcome.replied = outcome.replied or prior.replied
                    outcome.positive_reply = outcome.positive_reply or prior.positive_reply
                    outcome.meeting_booked = outcome.meeting_booked or prior.meeting_booked
                    outcome.qualified = outcome.qualified or prior.qualified
                    outcome.opportunity_created = outcome.opportunity_created or prior.opportunity_created
                aggregated[intelligence.intelligence_id] = (result, outcome)
            return list(aggregated.values())

    @staticmethod
    def _to_model(row: ProspectIntelligenceORM | None) -> ProspectIntelligenceResult | None:
        if row is None:
            return None
        return ProspectIntelligenceResult.model_validate(json.loads(row.payload_json))

    @staticmethod
    def _default_db_url() -> str:
        if settings.intelligence_database_url:
            return settings.intelligence_database_url
        base_dir = Path("ai_sdr_platform/data")
        base_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(base_dir / 'prospect_intelligence.db').resolve()}"

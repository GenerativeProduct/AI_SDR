from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import Column, DateTime, String, Text, create_engine, desc
from sqlalchemy.orm import declarative_base, sessionmaker

from ai_sdr_platform.src.agents.follow_up.models import FollowUpPlan
from ai_sdr_platform.src.shared.config import settings

Base = declarative_base()


class FollowUpORM(Base):
    __tablename__ = "sdr_follow_up_plans"
    plan_id = Column(String, primary_key=True)
    campaign_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, index=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    payload_json = Column(Text, nullable=False)


class SQLAlchemyFollowUpRepository:
    def __init__(self, db_url: str | None = None) -> None:
        url = db_url or settings.follow_up_database_url or self._default_url()
        args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        self.engine = create_engine(url, future=True, connect_args=args, pool_pre_ping=True, pool_recycle=300)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)
        Base.metadata.create_all(self.engine)

    def save(self, plan: FollowUpPlan) -> FollowUpPlan:
        with self.SessionLocal() as session:
            session.merge(
                FollowUpORM(
                    plan_id=plan.plan_id,
                    campaign_id=plan.campaign_id,
                    status=plan.status,
                    updated_at=plan.updated_at,
                    payload_json=json.dumps(plan.model_dump(mode="json")),
                )
            )
            session.commit()
        return plan

    def get(self, plan_id: str) -> FollowUpPlan | None:
        with self.SessionLocal() as session:
            return self._model(session.get(FollowUpORM, plan_id))

    def get_by_campaign(self, campaign_id: str) -> FollowUpPlan | None:
        with self.SessionLocal() as session:
            row = (
                session.query(FollowUpORM)
                .filter(FollowUpORM.campaign_id == campaign_id)
                .first()
            )
            return self._model(row)

    def list(self, status: str | None = None) -> list[FollowUpPlan]:
        with self.SessionLocal() as session:
            query = session.query(FollowUpORM)
            if status:
                query = query.filter(FollowUpORM.status == status)
            return [
                model
                for row in query.order_by(desc(FollowUpORM.updated_at)).all()
                if (model := self._model(row)) is not None
            ]

    @staticmethod
    def _model(row: FollowUpORM | None) -> FollowUpPlan | None:
        return (
            FollowUpPlan.model_validate(json.loads(row.payload_json))
            if row is not None
            else None
        )

    @staticmethod
    def _default_url() -> str:
        directory = Path("ai_sdr_platform/data")
        directory.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(directory / 'follow_up.db').resolve()}"

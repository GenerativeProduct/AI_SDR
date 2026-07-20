from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from sqlalchemy import Column, DateTime, String, Text, create_engine, desc
from sqlalchemy.orm import declarative_base, sessionmaker

from ai_sdr_platform.src.agents.outreach.models import OutreachCampaign, OutreachEvent
from ai_sdr_platform.src.shared.config import settings

Base = declarative_base()


class OutreachCampaignORM(Base):
    __tablename__ = "outreach_campaigns"
    campaign_id = Column(String, primary_key=True)
    account_id = Column(String, index=True, nullable=False)
    contact_id = Column(String, index=True, nullable=False)
    status = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    payload_json = Column(Text, nullable=False)


class OutreachEventORM(Base):
    __tablename__ = "outreach_events"
    event_id = Column(String, primary_key=True)
    provider_event_id = Column(String, unique=True, index=True, nullable=False)
    message_id = Column(String, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    payload_json = Column(Text, nullable=False)


class OutreachRepository(Protocol):
    def save_campaign(self, campaign: OutreachCampaign) -> OutreachCampaign: ...
    def get_campaign(self, campaign_id: str) -> OutreachCampaign | None: ...
    def list_campaigns(self, status: str | None = None) -> list[OutreachCampaign]: ...
    def get_by_intelligence(self, intelligence_id: str) -> OutreachCampaign | None: ...
    def find_by_provider_message_id(self, provider_message_id: str) -> OutreachCampaign | None: ...
    def save_event(self, event: OutreachEvent) -> bool: ...


class SQLAlchemyOutreachRepository:
    def __init__(self, db_url: str | None = None) -> None:
        database_url = db_url or self._default_db_url()
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, future=True, connect_args=connect_args)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)
        Base.metadata.create_all(self.engine)

    def save_campaign(self, campaign: OutreachCampaign) -> OutreachCampaign:
        with self.SessionLocal() as session:
            session.merge(
                OutreachCampaignORM(
                    campaign_id=campaign.campaign_id,
                    account_id=campaign.account_id,
                    contact_id=campaign.contact_id,
                    status=campaign.status,
                    created_at=campaign.created_at,
                    updated_at=campaign.updated_at,
                    payload_json=json.dumps(campaign.model_dump(mode="json")),
                )
            )
            session.commit()
        return campaign

    def get_campaign(self, campaign_id: str) -> OutreachCampaign | None:
        with self.SessionLocal() as session:
            row = session.get(OutreachCampaignORM, campaign_id)
            return self._to_model(row)

    def list_campaigns(self, status: str | None = None) -> list[OutreachCampaign]:
        with self.SessionLocal() as session:
            query = session.query(OutreachCampaignORM)
            if status:
                query = query.filter(OutreachCampaignORM.status == status)
            return [
                model
                for row in query.order_by(desc(OutreachCampaignORM.updated_at)).all()
                if (model := self._to_model(row)) is not None
            ]

    def get_by_intelligence(self, intelligence_id: str) -> OutreachCampaign | None:
        with self.SessionLocal() as session:
            rows = session.query(OutreachCampaignORM).order_by(
                desc(OutreachCampaignORM.updated_at)
            ).all()
            for row in rows:
                campaign = self._to_model(row)
                if (
                    campaign
                    and campaign.intelligence_id == intelligence_id
                    and campaign.status != "cancelled"
                ):
                    return campaign
        return None

    def find_by_provider_message_id(
        self, provider_message_id: str
    ) -> OutreachCampaign | None:
        for campaign in self.list_campaigns():
            if any(
                message.provider_message_id == provider_message_id
                for message in campaign.messages
            ):
                return campaign
        return None

    def save_event(self, event: OutreachEvent) -> bool:
        with self.SessionLocal() as session:
            existing = (
                session.query(OutreachEventORM)
                .filter(OutreachEventORM.provider_event_id == event.provider_event_id)
                .first()
            )
            if existing:
                return False
            session.add(
                OutreachEventORM(
                    event_id=event.event_id,
                    provider_event_id=event.provider_event_id,
                    message_id=event.message_id,
                    occurred_at=event.occurred_at,
                    payload_json=json.dumps(event.model_dump(mode="json")),
                )
            )
            session.commit()
            return True

    @staticmethod
    def _to_model(row: OutreachCampaignORM | None) -> OutreachCampaign | None:
        if row is None:
            return None
        return OutreachCampaign.model_validate(json.loads(row.payload_json))

    @staticmethod
    def _default_db_url() -> str:
        if settings.outreach_database_url:
            return settings.outreach_database_url
        base_dir = Path("ai_sdr_platform/data")
        base_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(base_dir / 'outreach.db').resolve()}"

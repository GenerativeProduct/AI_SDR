from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import Column, DateTime, String, Text, create_engine, desc
from sqlalchemy.orm import declarative_base, sessionmaker

from ai_sdr_platform.src.agents.conversation.models import ConversationThread
from ai_sdr_platform.src.shared.config import settings

Base = declarative_base()


class ConversationORM(Base):
    __tablename__ = "sdr_conversations"
    conversation_id = Column(String, primary_key=True)
    campaign_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, index=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    payload_json = Column(Text, nullable=False)


class SQLAlchemyConversationRepository:
    def __init__(self, db_url: str | None = None) -> None:
        url = db_url or settings.conversation_database_url or self._default_url()
        args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        self.engine = create_engine(url, future=True, connect_args=args, pool_pre_ping=True, pool_recycle=300)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)
        Base.metadata.create_all(self.engine)

    def save(self, thread: ConversationThread) -> ConversationThread:
        with self.SessionLocal() as session:
            session.merge(
                ConversationORM(
                    conversation_id=thread.conversation_id,
                    campaign_id=thread.campaign_id,
                    status=thread.status,
                    updated_at=thread.updated_at,
                    payload_json=json.dumps(thread.model_dump(mode="json")),
                )
            )
            session.commit()
        return thread

    def get(self, conversation_id: str) -> ConversationThread | None:
        with self.SessionLocal() as session:
            row = session.get(ConversationORM, conversation_id)
            return self._model(row)

    def get_by_campaign(self, campaign_id: str) -> ConversationThread | None:
        with self.SessionLocal() as session:
            row = (
                session.query(ConversationORM)
                .filter(ConversationORM.campaign_id == campaign_id)
                .first()
            )
            return self._model(row)

    def list(self, status: str | None = None) -> list[ConversationThread]:
        with self.SessionLocal() as session:
            query = session.query(ConversationORM)
            if status:
                query = query.filter(ConversationORM.status == status)
            return [
                model
                for row in query.order_by(desc(ConversationORM.updated_at)).all()
                if (model := self._model(row)) is not None
            ]

    @staticmethod
    def _model(row: ConversationORM | None) -> ConversationThread | None:
        return (
            ConversationThread.model_validate(json.loads(row.payload_json))
            if row is not None
            else None
        )

    @staticmethod
    def _default_url() -> str:
        directory = Path("ai_sdr_platform/data")
        directory.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(directory / 'conversations.db').resolve()}"

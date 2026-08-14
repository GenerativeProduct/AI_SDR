from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import Column, DateTime, String, Text, create_engine, desc
from sqlalchemy.orm import declarative_base, sessionmaker

from ai_sdr_platform.src.agents.meeting.models import MeetingBooking
from ai_sdr_platform.src.shared.config import settings

Base = declarative_base()


class MeetingORM(Base):
    __tablename__ = "sdr_meetings"
    meeting_id = Column(String, primary_key=True)
    conversation_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, index=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    payload_json = Column(Text, nullable=False)


class SQLAlchemyMeetingRepository:
    def __init__(self, db_url: str | None = None) -> None:
        url = db_url or settings.meeting_database_url or self._default_url()
        args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        self.engine = create_engine(url, future=True, connect_args=args, pool_pre_ping=True, pool_recycle=300)
        self.SessionLocal = sessionmaker(bind=self.engine, future=True)
        Base.metadata.create_all(self.engine)

    def save(self, meeting: MeetingBooking) -> MeetingBooking:
        with self.SessionLocal() as session:
            session.merge(
                MeetingORM(
                    meeting_id=meeting.meeting_id,
                    conversation_id=meeting.conversation_id,
                    status=meeting.status,
                    updated_at=meeting.updated_at,
                    payload_json=json.dumps(meeting.model_dump(mode="json")),
                )
            )
            session.commit()
        return meeting

    def get(self, meeting_id: str) -> MeetingBooking | None:
        with self.SessionLocal() as session:
            return self._model(session.get(MeetingORM, meeting_id))

    def get_by_conversation(self, conversation_id: str) -> MeetingBooking | None:
        with self.SessionLocal() as session:
            row = (
                session.query(MeetingORM)
                .filter(MeetingORM.conversation_id == conversation_id)
                .first()
            )
            return self._model(row)

    def list(self, status: str | None = None) -> list[MeetingBooking]:
        with self.SessionLocal() as session:
            query = session.query(MeetingORM)
            if status:
                query = query.filter(MeetingORM.status == status)
            return [
                model
                for row in query.order_by(desc(MeetingORM.updated_at)).all()
                if (model := self._model(row)) is not None
            ]

    def get_by_provider_event_id(
        self, provider_event_id: str
    ) -> MeetingBooking | None:
        for meeting in self.list():
            if meeting.provider_event_id == provider_event_id:
                return meeting
        return None

    @staticmethod
    def _model(row: MeetingORM | None) -> MeetingBooking | None:
        return (
            MeetingBooking.model_validate(json.loads(row.payload_json))
            if row is not None
            else None
        )

    @staticmethod
    def _default_url() -> str:
        directory = Path("ai_sdr_platform/data")
        directory.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(directory / 'meetings.db').resolve()}"

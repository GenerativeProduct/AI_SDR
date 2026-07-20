from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Protocol

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine, desc
from sqlalchemy.orm import declarative_base, sessionmaker

from ai_sdr_platform.src.agents.prospect_discovery.models import DiscoveredAccount, DiscoveredContact
from ai_sdr_platform.src.shared.config import settings

Base = declarative_base()


class DiscoveredAccountORM(Base):
    __tablename__ = "discovered_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, unique=True, index=True, nullable=False)
    icp_id = Column(String, index=True)
    company_name = Column(String)
    website = Column(String)
    linkedin_url = Column(String)
    industry = Column(String)
    location = Column(String)
    employee_count = Column(Integer)
    revenue_range = Column(String)
    source = Column(String)
    fit_score = Column(Integer)
    fit_reasons_json = Column(Text)
    status = Column(String, default="new")
    discovered_at = Column(DateTime)


class DiscoveredContactORM(Base):
    __tablename__ = "discovered_contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(String, unique=True, index=True, nullable=False)
    account_id = Column(String, index=True)
    full_name = Column(String)
    title = Column(String)
    department = Column(String)
    seniority = Column(String)
    email = Column(String)
    linkedin_url = Column(String)
    phone = Column(String)
    email_verification_status = Column(String, default="unknown")
    phone_verification_status = Column(String, default="unknown")
    contact_status = Column(String, default="active")
    is_former_employee = Column(Boolean, default=False)
    confidence = Column(Integer, default=0)
    persona_match_score = Column(Integer, default=0)
    source = Column(String, default="mock")
    status = Column(String, default="new")
    discovered_at = Column(DateTime)


class ProspectDiscoveryRepository(Protocol):
    def save_account(self, account: DiscoveredAccount) -> DiscoveredAccount:
        ...

    def save_contact(self, contact: DiscoveredContact) -> DiscoveredContact:
        ...

    def list_accounts(self, icp_id: str | None = None) -> list[DiscoveredAccount]:
        ...

    def list_contacts(self, account_id: str | None = None) -> list[DiscoveredContact]:
        ...


class SQLAlchemyProspectDiscoveryRepository:
    def __init__(self, db_url: str | None = None) -> None:
        database_url = db_url or self._default_db_url()
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, future=True, connect_args=connect_args)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, future=True)
        Base.metadata.create_all(self.engine)

    def save_account(self, account: DiscoveredAccount) -> DiscoveredAccount:
        data = account.model_dump()
        fit_reasons = data.pop("fit_reasons", [])
        discovered_at = data.pop("discovered_at", datetime.now())
        with self.SessionLocal() as session:
            existing = session.query(DiscoveredAccountORM).filter_by(account_id=account.account_id).first()
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                existing.fit_reasons_json = json.dumps(fit_reasons)
                existing.discovered_at = discovered_at
            else:
                session.add(DiscoveredAccountORM(**data, fit_reasons_json=json.dumps(fit_reasons), discovered_at=discovered_at))
            session.commit()
        return account

    def save_contact(self, contact: DiscoveredContact) -> DiscoveredContact:
        data = contact.model_dump()
        discovered_at = data.pop("discovered_at", datetime.now())
        with self.SessionLocal() as session:
            existing = session.query(DiscoveredContactORM).filter_by(contact_id=contact.contact_id).first()
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                existing.discovered_at = discovered_at
            else:
                session.add(DiscoveredContactORM(**data, discovered_at=discovered_at))
            session.commit()
        return contact

    def list_accounts(self, icp_id: str | None = None) -> list[DiscoveredAccount]:
        with self.SessionLocal() as session:
            query = session.query(DiscoveredAccountORM)
            if icp_id:
                query = query.filter(DiscoveredAccountORM.icp_id == icp_id)
            rows = query.order_by(desc(DiscoveredAccountORM.discovered_at)).all()
            return [self._to_account_model(row) for row in rows]

    def list_contacts(self, account_id: str | None = None) -> list[DiscoveredContact]:
        with self.SessionLocal() as session:
            query = session.query(DiscoveredContactORM)
            if account_id:
                query = query.filter(DiscoveredContactORM.account_id == account_id)
            rows = query.order_by(desc(DiscoveredContactORM.discovered_at)).all()
            return [self._to_contact_model(row) for row in rows]

    @staticmethod
    def _to_account_model(row: DiscoveredAccountORM) -> DiscoveredAccount:
        data = {c.name: getattr(row, c.name) for c in row.__table__.columns if c.name != "fit_reasons_json"}
        data["fit_reasons"] = json.loads(row.fit_reasons_json or "[]")
        return DiscoveredAccount(**data)

    @staticmethod
    def _to_contact_model(row: DiscoveredContactORM) -> DiscoveredContact:
        data = {c.name: getattr(row, c.name) for c in row.__table__.columns}
        return DiscoveredContact(**data)

    @staticmethod
    def _default_db_url() -> str:
        if settings.discovery_database_url:
            return settings.discovery_database_url
        base_dir = Path("ai_sdr_platform/data")
        base_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(base_dir / 'prospects.db').resolve()}"

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, and_, create_engine, desc, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("sdr.prospect_discovery")


def _naive_utc(value: datetime | None) -> datetime:
    """Normalize to naive UTC so it matches the naive DateTime columns (and the
    cache TTL comparison). Prevents tz-aware vs naive mismatches on Postgres."""
    dt = value or datetime.now(timezone.utc)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

from ai_sdr_platform.src.agents.prospect_discovery.models import DiscoveredAccount, DiscoveredContact
from ai_sdr_platform.src.agents.prospect_discovery.identity import company_key, contact_key
from ai_sdr_platform.src.shared.config import settings

Base = declarative_base()


def _merge_sources(existing_json: str | None, new_source: str | None) -> str:
    """Union the set of provider names that contributed to a record. `new_source`
    may be a '+'-joined combo (e.g. 'apollo+hunter') which is split into parts."""
    try:
        current = set(json.loads(existing_json) if existing_json else [])
    except Exception:
        current = set()
    for part in str(new_source or "").split("+"):
        part = part.strip()
        if part:
            current.add(part)
    return json.dumps(sorted(current))


def _prefer_text(new: object, old: object) -> object:
    """Keep the new value unless it is blank/placeholder, then keep the old."""
    if new in (None, "", "Unknown", "unknown", "unknown industry", "unknown location"):
        return old
    return new


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
    icp_signature = Column(String, index=True)  # cache key: which ICP produced this
    company_key = Column(String, index=True)    # canonical identity (domain/slug)
    sources = Column(Text)                        # JSON list of contributing providers


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
    contact_key = Column(String, index=True)    # canonical identity (email/li/name)
    sources = Column(Text)                        # JSON list of contributing providers


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
        self._ensure_cache_columns()

    def _ensure_cache_columns(self) -> None:
        """Idempotently add columns introduced after the tables already existed
        (icp_signature, company_key/contact_key, sources). Safe to run every start."""
        migrations = [
            ("discovered_accounts", "icp_signature"),
            ("discovered_accounts", "company_key"),
            ("discovered_accounts", "sources"),
            ("discovered_contacts", "contact_key"),
            ("discovered_contacts", "sources"),
        ]
        for table, column in migrations:
            self._add_column_if_missing(table, column)
        self._backfill_identity_keys()
        self._ensure_identity_indexes()

    def _ensure_identity_indexes(self) -> None:
        """Enforce one row per canonical key with a UNIQUE index when the data
        allows it; fall back to a plain index if pre-Phase-3 duplicates block it
        (the merge-on-save logic still prevents new duplicates either way)."""
        targets = [
            ("discovered_accounts", "company_key"),
            ("discovered_contacts", "contact_key"),
        ]
        for table, column in targets:
            unique = True
            try:
                with self.engine.begin() as conn:
                    conn.execute(text(
                        f"CREATE UNIQUE INDEX IF NOT EXISTS uq_{table}_{column} ON {table} ({column})"
                    ))
            except Exception as exc:
                unique = False
                logger.warning(
                    "UNIQUE index on %s.%s blocked (pre-existing duplicates?): %s",
                    table, column, str(exc)[:120],
                )
                try:
                    with self.engine.begin() as conn:
                        conn.execute(text(
                            f"CREATE INDEX IF NOT EXISTS ix_{table}_{column} ON {table} ({column})"
                        ))
                except Exception:
                    pass
            logger.info("Identity index on %s.%s: %s", table, column, "UNIQUE" if unique else "non-unique")

    def _add_column_if_missing(self, table: str, column: str) -> None:
        try:
            with self.engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} VARCHAR"))
        except Exception:
            try:  # SQLite has no IF NOT EXISTS for columns
                with self.engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} VARCHAR"))
            except Exception:
                pass

    def _backfill_identity_keys(self) -> None:
        """Populate canonical keys on rows saved before Phase 3 (one-time)."""
        try:
            with self.SessionLocal() as session:
                acct_rows = session.query(DiscoveredAccountORM).filter(
                    DiscoveredAccountORM.company_key.is_(None)
                ).all()
                for row in acct_rows:
                    row.company_key = company_key(row.company_name, row.website)
                    if not row.sources:
                        row.sources = json.dumps([row.source] if row.source else [])
                contact_rows = session.query(DiscoveredContactORM).filter(
                    DiscoveredContactORM.contact_key.is_(None)
                ).all()
                for row in contact_rows:
                    row.contact_key = contact_key(row.email, row.linkedin_url, row.full_name, row.account_id)
                    if not row.sources:
                        row.sources = json.dumps([row.source] if row.source else [])
                if acct_rows or contact_rows:
                    session.commit()
                    logger.info(
                        "Backfilled identity keys: %d accounts, %d contacts",
                        len(acct_rows), len(contact_rows),
                    )
        except Exception as exc:
            logger.error("Identity key backfill skipped: %s", exc)

    def save_account(
        self, account: DiscoveredAccount, icp_signature: str | None = None
    ) -> DiscoveredAccount:
        data = account.model_dump()
        fit_reasons = data.pop("fit_reasons", [])
        discovered_at = _naive_utc(data.pop("discovered_at", None))
        ckey = company_key(account.company_name, account.website)
        new_source = account.source

        def _merge(existing: DiscoveredAccountORM) -> None:
            existing.company_name = _prefer_text(data.get("company_name"), existing.company_name)
            existing.website = _prefer_text(data.get("website"), existing.website)
            existing.linkedin_url = _prefer_text(data.get("linkedin_url"), existing.linkedin_url)
            existing.industry = _prefer_text(data.get("industry"), existing.industry)
            existing.location = _prefer_text(data.get("location"), existing.location)
            existing.revenue_range = _prefer_text(data.get("revenue_range"), existing.revenue_range)
            if (data.get("employee_count") or 0) > (existing.employee_count or 0):
                existing.employee_count = data.get("employee_count")
            if (data.get("fit_score") or 0) >= (existing.fit_score or 0):
                existing.fit_score = data.get("fit_score")
                existing.fit_reasons_json = json.dumps(fit_reasons)
            existing.status = data.get("status") or existing.status
            existing.company_key = ckey
            existing.sources = _merge_sources(existing.sources, new_source)
            existing.discovered_at = discovered_at
            if icp_signature:
                existing.icp_signature = icp_signature

        def _lookup(session):
            return (
                session.query(DiscoveredAccountORM).filter_by(account_id=account.account_id).first()
                or session.query(DiscoveredAccountORM).filter_by(company_key=ckey).first()
            )

        with self.SessionLocal() as session:
            existing = _lookup(session)
            if existing:
                _merge(existing)
                session.commit()
                return account
            session.add(DiscoveredAccountORM(
                **data,
                fit_reasons_json=json.dumps(fit_reasons),
                discovered_at=discovered_at,
                icp_signature=icp_signature,
                company_key=ckey,
                sources=json.dumps([new_source] if new_source else []),
            ))
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                existing = _lookup(session)
                if existing:
                    _merge(existing)
                    session.commit()
        return account

    def save_contact(self, contact: DiscoveredContact) -> DiscoveredContact:
        data = contact.model_dump()
        discovered_at = _naive_utc(data.pop("discovered_at", None))
        ckey = contact_key(contact.email, contact.linkedin_url, contact.full_name, contact.account_id)
        new_source = contact.source

        def _merge(existing: DiscoveredContactORM) -> None:
            existing.full_name = _prefer_text(data.get("full_name"), existing.full_name)
            existing.title = _prefer_text(data.get("title"), existing.title)
            existing.department = _prefer_text(data.get("department"), existing.department)
            existing.seniority = _prefer_text(data.get("seniority"), existing.seniority)
            existing.email = _prefer_text(data.get("email"), existing.email)
            existing.linkedin_url = _prefer_text(data.get("linkedin_url"), existing.linkedin_url)
            existing.phone = _prefer_text(data.get("phone"), existing.phone)
            # Prefer a verified email status; never downgrade verified -> unverified.
            incoming_status = data.get("email_verification_status")
            if incoming_status == "verified":
                existing.email_verification_status = "verified"
            elif existing.email_verification_status != "verified":
                existing.email_verification_status = incoming_status or existing.email_verification_status
            existing.phone_verification_status = data.get("phone_verification_status") or existing.phone_verification_status
            existing.contact_status = data.get("contact_status") or existing.contact_status
            if (data.get("confidence") or 0) >= (existing.confidence or 0):
                existing.confidence = data.get("confidence")
            if (data.get("persona_match_score") or 0) >= (existing.persona_match_score or 0):
                existing.persona_match_score = data.get("persona_match_score")
            existing.status = data.get("status") or existing.status
            existing.contact_key = ckey
            existing.sources = _merge_sources(existing.sources, new_source)
            existing.discovered_at = discovered_at

        def _lookup(session):
            return (
                session.query(DiscoveredContactORM).filter_by(contact_key=ckey).first()
                or session.query(DiscoveredContactORM).filter_by(contact_id=contact.contact_id).first()
            )

        with self.SessionLocal() as session:
            existing = _lookup(session)
            if existing:
                _merge(existing)
                session.commit()
                return contact
            session.add(DiscoveredContactORM(
                **data,
                discovered_at=discovered_at,
                contact_key=ckey,
                sources=json.dumps([new_source] if new_source else []),
            ))
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                existing = _lookup(session)
                if existing:
                    _merge(existing)
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

    def find_accounts_by_signature(
        self, icp_signature: str, since: datetime
    ) -> list[DiscoveredAccount]:
        """Cache lookup: fresh accounts previously discovered for the same ICP."""
        with self.SessionLocal() as session:
            rows = (
                session.query(DiscoveredAccountORM)
                .filter(and_(
                    DiscoveredAccountORM.icp_signature == icp_signature,
                    DiscoveredAccountORM.discovered_at >= since,
                ))
                .order_by(desc(DiscoveredAccountORM.fit_score))
                .all()
            )
            return [self._to_account_model(row) for row in rows]

    def find_contacts_by_accounts(
        self, account_ids: list[str], since: datetime
    ) -> list[DiscoveredContact]:
        """Cache lookup: fresh contacts already discovered for these accounts."""
        if not account_ids:
            return []
        with self.SessionLocal() as session:
            rows = (
                session.query(DiscoveredContactORM)
                .filter(and_(
                    DiscoveredContactORM.account_id.in_(list(account_ids)),
                    DiscoveredContactORM.discovered_at >= since,
                ))
                .order_by(desc(DiscoveredContactORM.persona_match_score))
                .all()
            )
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

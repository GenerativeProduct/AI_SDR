from __future__ import annotations

import json
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from ai_sdr_platform.src.shared.config import settings

Base = declarative_base()


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobRecordORM(Base):
    __tablename__ = "job_records"

    job_id = Column(String, primary_key=True)
    job_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    progress = Column(String, nullable=False, default="0")
    result_json = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)


class JobStatusResponse(BaseModel):
    job_id: str
    job_type: str
    status: JobStatus
    progress: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str
    updated_at: str


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus


_executor = ThreadPoolExecutor(max_workers=4)


class JobStore:
    def __init__(self, db_url: str | None = None) -> None:
        database_url = db_url or self._default_db_url()
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, future=True, connect_args=connect_args, pool_pre_ping=True, pool_recycle=300)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, future=True)
        Base.metadata.create_all(self.engine)

    def create_job(self, job_type: str) -> str:
        job_id = f"job_{uuid.uuid4().hex[:16]}"
        now = datetime.now(UTC).isoformat()
        with self.SessionLocal() as session:
            session.add(
                JobRecordORM(
                    job_id=job_id,
                    job_type=job_type,
                    status=JobStatus.PENDING.value,
                    progress="0",
                    created_at=now,
                    updated_at=now,
                )
            )
            session.commit()
        return job_id

    def update_job(
        self,
        job_id: str,
        *,
        status: JobStatus | None = None,
        progress: int | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with self.SessionLocal() as session:
            row = session.query(JobRecordORM).filter(JobRecordORM.job_id == job_id).first()
            if row is None:
                return
            if status is not None:
                row.status = status.value
            if progress is not None:
                row.progress = str(progress)
            if result is not None:
                row.result_json = json.dumps(result)
            if error is not None:
                row.error = error
            row.updated_at = now
            session.commit()

    def get_job(self, job_id: str) -> JobStatusResponse | None:
        with self.SessionLocal() as session:
            row = session.query(JobRecordORM).filter(JobRecordORM.job_id == job_id).first()
            if row is None:
                return None
            result = json.loads(row.result_json) if row.result_json else None
            return JobStatusResponse(
                job_id=row.job_id,
                job_type=row.job_type,
                status=JobStatus(row.status),
                progress=int(row.progress or 0),
                result=result,
                error=row.error,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )

    def run_in_background(self, job_id: str, fn: Callable[[], dict[str, Any]]) -> None:
        def _runner() -> None:
            self.update_job(job_id, status=JobStatus.RUNNING, progress=10)
            try:
                result = fn()
                self.update_job(job_id, status=JobStatus.COMPLETED, progress=100, result=result)
            except Exception as exc:
                self.update_job(job_id, status=JobStatus.FAILED, error=str(exc))

        _executor.submit(_runner)

    @staticmethod
    def _default_db_url() -> str:
        if settings.jobs_database_url:
            return settings.jobs_database_url
        data_dir = Path(__file__).resolve().parents[2] / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(data_dir / 'jobs.db').resolve()}"


job_store = JobStore()

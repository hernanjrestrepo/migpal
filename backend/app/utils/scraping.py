from __future__ import annotations

"""Utility helpers for MigPAL scraping jobs (skeleton for MVP)."""

from datetime import datetime
from typing import Optional

from sqlmodel import Session

from app.models.data_source import DataSource, ScrapeJob


class ScrapeStatus:
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


def start_job(session: Session, source: DataSource, job: ScrapeJob) -> None:
    job.status = ScrapeStatus.RUNNING
    job.started_at = datetime.utcnow()
    session.add(job)
    session.commit()


def finish_job(session: Session, job: ScrapeJob, *, records: int = 0, error: Optional[str] = None) -> None:
    job.finished_at = datetime.utcnow()
    job.records_ingested = records

    if error:
        job.status = ScrapeStatus.FAILED
        job.error_message = error[:2000]
    else:
        job.status = ScrapeStatus.SUCCESS

    session.add(job)
    session.commit()

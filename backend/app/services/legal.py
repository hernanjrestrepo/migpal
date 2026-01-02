from __future__ import annotations

import hashlib
from datetime import datetime

import httpx
from sqlmodel import Session

from app.models.data_source import DataSource, ScrapeJob, ScrapedDocument


def _fetch_text(url: str) -> str:
    headers = {"User-Agent": "MigPAL/0.1"}
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.text


def sync_uscis(session: Session, source: DataSource, job: ScrapeJob) -> None:
    html = _fetch_text("https://www.uscis.gov/forms/filing-fees")
    _store_doc(session, source, job, html, "USCIS filing fees")


def sync_dos_travel(session: Session, source: DataSource, job: ScrapeJob) -> None:
    html = _fetch_text("https://travel.state.gov/content/travel/en/us-visas/visa-information-resources/visa-bulletin.html")
    _store_doc(session, source, job, html, "Visa bulletin")


def _store_doc(session: Session, source: DataSource, job: ScrapeJob, text: str, title: str) -> None:
    content_hash = hashlib.sha256(text.encode()).hexdigest()
    doc = ScrapedDocument(
        source_id=source.id,
        title=title,
        content=text,
        content_hash=content_hash,
        metadata_blob=None,
        created_at=datetime.utcnow()
    )
    session.add(doc)
    session.commit()

    job.records_ingested = 1
    job.status = "success"
    session.add(job)
    session.commit()

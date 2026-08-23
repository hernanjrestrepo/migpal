from __future__ import annotations

import json

from sqlmodel import Session, select

from app.models.data_source import DataSource, ScrapeJob
from app.models.job_listing import JobListing

LINKEDIN_SLUG = "linkedin-jobs"


def sync_linkedin_jobs(session: Session, source: DataSource, job: ScrapeJob) -> None:
    # Placeholder implementation (LinkedIn official API requires OAuth / not public)
    payload = [
        {
            "job_id": "sample-001",
            "title": "Software Engineer",
            "company": "Acme Corp",
            "location": "San Francisco, CA",
            "url": "https://www.linkedin.com/jobs/view/sample-001",
            "salary": None,
        }
    ]
    _persist_jobs(session, source, payload)
    job.records_ingested = len(payload)
    job.status = "success"
    session.add(job)
    session.commit()


def _persist_jobs(session: Session, source: DataSource, jobs: list[dict]):
    for item in jobs:
        job_id = item.get("job_id")
        if not job_id:
            continue
        existing = session.exec(select(JobListing).where(JobListing.job_id == job_id)).first()
        data = JobListing(
            source_id=source.id,
            job_id=job_id,
            title=item.get("title", "Job"),
            company=item.get("company"),
            location=item.get("location"),
            url=item.get("url", ""),
            salary=item.get("salary"),
            metadata_blob=json.dumps(item),
        )
        if existing:
            for field in ["title", "company", "location", "url", "salary", "metadata_blob"]:
                setattr(existing, field, getattr(data, field))
        else:
            session.add(data)
    session.commit()

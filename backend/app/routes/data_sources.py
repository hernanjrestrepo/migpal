from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session, select

from app.auth import get_current_user
from app.config import settings
from app.db.session import get_session
from app.models.data_source import (
    DataSource,
    DataSourceCreate,
    DataSourceRead,
    DataSourceUpdate,
    ScrapeJob,
    ScrapeJobRead,
)
from app.models.user import User
from app.services import businesses, legal, zillow
from app.services import education as education_service
from app.services import jobs as jobs_service
from app.utils.audit import log_action
from app.utils.rbac import require_admin
from app.utils.scraping import finish_job

router = APIRouter(prefix="/data-sources", tags=["data_sources"])


@router.get("", response_model=list[DataSourceRead])
def list_data_sources(
    *,
    session: Session = Depends(get_session),
    category: str | None = Query(default=None),
    enabled: bool | None = Query(default=None),
    search: str | None = Query(default=None, min_length=2),
):
    query = select(DataSource)
    if category:
        query = query.where(DataSource.category == category)
    if enabled is not None:
        query = query.where(DataSource.enabled == enabled)
    if search:
        like = f"%{search.lower()}%"
        query = query.where(DataSource.name.ilike(like))
    query = query.order_by(DataSource.priority.desc(), DataSource.name.asc())
    return session.exec(query).all()


@router.post("", response_model=DataSourceRead, status_code=status.HTTP_201_CREATED)
def create_data_source(
    *,
    payload: DataSourceCreate,
    session: Session = Depends(get_session),
    current_user: Annotated[User, Depends(require_admin)],
    request: Request,
):
    existing = session.exec(select(DataSource).where(DataSource.slug == payload.slug)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Slug already exists")

    source = DataSource(**payload.model_dump(), created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    session.add(source)
    session.commit()
    session.refresh(source)

    log_action(
        session=session,
        action="create",
        resource="data_source",
        user_id=current_user.id,
        resource_id=source.id,
        request=request,
        details={"slug": source.slug},
    )
    return source


@router.get("/{source_id}", response_model=DataSourceRead)
def get_data_source(*, source_id: int, session: Session = Depends(get_session)):
    source = session.get(DataSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return source


@router.put("/{source_id}", response_model=DataSourceRead)
def update_data_source(
    *,
    source_id: int,
    payload: DataSourceUpdate,
    session: Session = Depends(get_session),
    current_user: Annotated[User, Depends(require_admin)],
    request: Request,
):
    source = session.get(DataSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, key, value)
    source.updated_at = datetime.utcnow()

    session.add(source)
    session.commit()
    session.refresh(source)

    log_action(
        session=session,
        action="update",
        resource="data_source",
        user_id=current_user.id,
        resource_id=source.id,
        request=request,
        details={"slug": source.slug},
    )
    return source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_data_source(
    *,
    source_id: int,
    session: Session = Depends(get_session),
    current_user: Annotated[User, Depends(require_admin)],
    request: Request,
):
    source = session.get(DataSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    session.delete(source)
    session.commit()

    log_action(
        session=session,
        action="delete",
        resource="data_source",
        user_id=current_user.id,
        resource_id=source.id,
        request=request,
        details={"slug": source.slug},
    )


@router.post("/{source_id}/jobs", response_model=ScrapeJobRead, status_code=status.HTTP_201_CREATED)
def create_scrape_job(
    *,
    source_id: int,
    session: Session = Depends(get_session),
    current_user: Annotated[User, Depends(require_admin)],
    request: Request,
):
    source = session.get(DataSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    job = ScrapeJob(
        source_id=source_id,
        status="pending",
        run_by_user_id=current_user.id,
        metadata_blob=None,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    try:
        if not settings.ENABLE_EXTERNAL_SCRAPERS:
            finish_job(session, job, records=0)
        elif source.slug == zillow.ZILLOW_SOURCE_SLUG:
            zillow.sync_city(session, city="Miami", state="FL", job=job)
        elif source.slug == "bizbuysell":
            businesses.sync_bizbuysell(session, job)
        elif source.slug == "businessesforsale":
            businesses.sync_businesses_for_sale(session, job)
        elif source.slug == "uscis":
            legal.sync_uscis(session, source, job)
        elif source.slug == "dos-travel":
            legal.sync_dos_travel(session, source, job)
        elif source.slug == "greatschools":
            education_service.sync_greatschools(session, source, job)
        elif source.slug == "linkedin-jobs":
            jobs_service.sync_linkedin_jobs(session, source, job)
        else:
            finish_job(session, job, records=0)
    except Exception as exc:
        finish_job(session, job, error=str(exc))
        raise

    log_action(
        session=session,
        action="create",
        resource="scrape_job",
        user_id=current_user.id,
        resource_id=job.id,
        request=request,
        details={"source_id": source_id},
    )
    return job


@router.get("/{source_id}/jobs", response_model=list[ScrapeJobRead])
def list_scrape_jobs(
    *,
    source_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: Annotated[User, Depends(get_current_user)],
):
    source = session.get(DataSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    query = (
        select(ScrapeJob)
        .where(ScrapeJob.source_id == source_id)
        .order_by(ScrapeJob.started_at.desc())
        .limit(limit)
    )
    return session.exec(query).all()


@router.get("/jobs/{job_id}", response_model=ScrapeJobRead)
def get_scrape_job(*, job_id: int, session: Session = Depends(get_session)):
    job = session.get(ScrapeJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.business_listing import BusinessListing
from app.models.job_listing import JobListing

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.get("/businesses", response_model=list[BusinessListing])
def list_business_listings(
    state: str = Query(None, min_length=2, max_length=2), session: Session = Depends(get_session)
):
    query = select(BusinessListing)
    if state:
        query = query.where(BusinessListing.state == state)
    results = session.exec(query).all()
    if not results:
        raise HTTPException(status_code=404, detail="No business listings cached")
    return results


@router.get("/jobs", response_model=list[JobListing])
def list_job_listings(session: Session = Depends(get_session)):
    jobs = session.exec(select(JobListing).order_by(JobListing.created_at.desc()).limit(100)).all()
    if not jobs:
        raise HTTPException(status_code=404, detail="No job listings cached")
    return jobs

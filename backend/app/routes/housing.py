from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.zillow_listing import ZillowListing

router = APIRouter(prefix="/housing", tags=["housing"])


@router.get("/rentals", response_model=list[ZillowListing])
def list_rentals(
    city: str = Query(..., min_length=2),
    state: str = Query(..., min_length=2, max_length=2),
    session: Session = Depends(get_session),
):
    query = (
        select(ZillowListing)
        .where(ZillowListing.city == city, ZillowListing.state == state)
        .order_by(ZillowListing.created_at.desc())
    )
    results = session.exec(query).all()
    if not results:
        raise HTTPException(status_code=404, detail="No rentals cached for that city")
    return results

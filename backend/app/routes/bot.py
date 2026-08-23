from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.business_listing import BusinessListing
from app.models.planner_task import PlannerTask
from app.models.zillow_listing import ZillowListing

router = APIRouter(prefix="/bot", tags=["bot"])


@router.get("/next-step")
def bot_next_step(session: Session = Depends(get_session)):
    task = session.exec(select(PlannerTask).order_by(PlannerTask.updated_at.desc())).first()
    rental = session.exec(select(ZillowListing).order_by(ZillowListing.created_at.desc())).first()
    business = session.exec(select(BusinessListing).order_by(BusinessListing.created_at.desc())).first()
    return {
        "task": task,
        "rental": rental,
        "business": business,
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.referral_level import ReferralLevel

router = APIRouter(prefix="/referral-levels", tags=["referral-levels"])


@router.post("", response_model=ReferralLevel)
def create_level(level: ReferralLevel, session: Session = Depends(get_session)):
    session.add(level)
    session.commit()
    session.refresh(level)
    return level


@router.get("", response_model=list[ReferralLevel])
def list_levels(session: Session = Depends(get_session)):
    return session.exec(select(ReferralLevel)).all()


@router.get("/{level_id}", response_model=ReferralLevel)
def get_level(level_id: int, session: Session = Depends(get_session)):
    level = session.get(ReferralLevel, level_id)
    if not level:
        raise HTTPException(status_code=404, detail="ReferralLevel not found")
    return level


@router.put("/{level_id}", response_model=ReferralLevel)
def update_level(level_id: int, payload: ReferralLevel, session: Session = Depends(get_session)):
    level = session.get(ReferralLevel, level_id)
    if not level:
        raise HTTPException(status_code=404, detail="ReferralLevel not found")

    level.name = payload.name
    level.commission_rate = payload.commission_rate

    session.add(level)
    session.commit()
    session.refresh(level)
    return level


@router.delete("/{level_id}")
def delete_level(level_id: int, session: Session = Depends(get_session)):
    level = session.get(ReferralLevel, level_id)
    if not level:
        raise HTTPException(status_code=404, detail="ReferralLevel not found")
    session.delete(level)
    session.commit()
    return {"deleted": True}

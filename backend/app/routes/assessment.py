from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth import get_current_user
from app.db.session import get_session
from app.models.migration_process import MigrationProcess
from app.models.user import User
from app.models.user_migration_profile import (
    UserMigrationProfile,
    UserMigrationProfileCreate,
    UserMigrationProfileRead,
    UserMigrationProfileUpdate,
)

router = APIRouter(prefix="/assessment", tags=["assessment"])


@router.post("/", response_model=UserMigrationProfileRead)
def create_or_update_assessment(
    profile_data: UserMigrationProfileCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    """
    Create or update migration assessment
    """
    # Check if profile already exists
    existing = session.exec(
        select(UserMigrationProfile).where(UserMigrationProfile.user_id == current_user.id)
    ).first()

    if existing:
        # Update existing profile
        for key, value in profile_data.model_dump(exclude_unset=True).items():
            setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    else:
        # Create new profile
        profile = UserMigrationProfile(user_id=current_user.id, **profile_data.model_dump())
        session.add(profile)
        session.commit()
        session.refresh(profile)
        return profile


@router.put("/me", response_model=UserMigrationProfileRead)
def update_my_assessment(
    profile_update: UserMigrationProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    """
    Update current user's migration assessment
    """
    profile = session.exec(
        select(UserMigrationProfile).where(UserMigrationProfile.user_id == current_user.id)
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Migration profile not found")

    # Update fields
    for key, value in profile_update.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)

    profile.updated_at = datetime.utcnow()
    session.add(profile)
    session.commit()
    session.refresh(profile)

    return profile


@router.get("/me", response_model=UserMigrationProfileRead)
def get_my_assessment(
    current_user: Annotated[User, Depends(get_current_user)], session: Session = Depends(get_session)
):
    """
    Get current user's migration assessment
    """
    profile = session.exec(
        select(UserMigrationProfile).where(UserMigrationProfile.user_id == current_user.id)
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Migration profile not found")

    return profile


@router.post("/start", response_model=UserMigrationProfileRead)
def start_assessment(
    profile_data: UserMigrationProfileCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    """
    Start migration assessment by creating user's migration profile
    """
    # Check if profile already exists
    existing = session.exec(
        select(UserMigrationProfile).where(UserMigrationProfile.user_id == current_user.id)
    ).first()

    if existing:
        raise HTTPException(
            status_code=409, detail="Migration profile already exists. Use update endpoint instead."
        )

    profile = UserMigrationProfile(user_id=current_user.id, **profile_data.model_dump())

    session.add(profile)
    session.commit()
    session.refresh(profile)

    return profile


@router.get("/my-profile", response_model=UserMigrationProfileRead)
def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)], session: Session = Depends(get_session)
):
    """
    Get current user's migration profile
    """
    profile = session.exec(
        select(UserMigrationProfile).where(UserMigrationProfile.user_id == current_user.id)
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Migration profile not found")

    return profile


@router.put("/my-profile", response_model=UserMigrationProfileRead)
def update_my_profile(
    profile_update: UserMigrationProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
):
    """
    Update current user's migration profile
    """
    profile = session.exec(
        select(UserMigrationProfile).where(UserMigrationProfile.user_id == current_user.id)
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Migration profile not found")

    # Update only provided fields
    update_data = profile_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    profile.updated_at = datetime.utcnow()

    session.add(profile)
    session.commit()
    session.refresh(profile)

    return profile


@router.get("/results")
def get_assessment_results(
    current_user: Annotated[User, Depends(get_current_user)], session: Session = Depends(get_session)
):
    """
    Get assessment results with recommended migration processes
    """
    profile = session.exec(
        select(UserMigrationProfile).where(UserMigrationProfile.user_id == current_user.id)
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Migration profile not found. Complete assessment first.")

    # Get matching migration processes
    processes = session.exec(
        select(MigrationProcess).where(
            MigrationProcess.country_to == profile.target_country, MigrationProcess.is_active is True
        )
    ).all()

    # Simple matching algorithm (can be enhanced with AI)
    recommendations = []
    for process in processes:
        match_score = 0.0

        # Budget match
        if profile.budget_usd >= process.estimated_cost_min:
            match_score += 30

        # Education level match (simplified)
        if profile.education_level in ["master", "phd"] and process.visa_type == "work":
            match_score += 20

        # Urgency vs time match
        if profile.urgency == "high" and process.estimated_time_months <= 12:
            match_score += 25
        elif profile.urgency == "medium" and process.estimated_time_months <= 24:
            match_score += 20
        elif profile.urgency == "low":
            match_score += 15

        # Success rate bonus
        match_score += process.success_rate * 0.25

        recommendations.append({"process": process, "match_score": min(match_score, 100)})  # Cap at 100

    # Sort by match score
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)

    return {"profile": profile, "recommendations": recommendations[:10]}  # Top 10 matches

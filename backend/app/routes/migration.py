from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime

from app.auth import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.models.migration_process import MigrationProcess, MigrationProcessRead
from app.models.user_migration_profile import UserMigrationProfile

router = APIRouter(prefix="/migration", tags=["migration"])


@router.get("/recommended", response_model=list[MigrationProcessRead])
def get_recommended_routes(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """
    Get recommended migration routes based on user's profile
    """
    # Get user's migration profile
    profile = session.exec(
        select(UserMigrationProfile).where(UserMigrationProfile.user_id == current_user.id)
    ).first()
    
    if not profile:
        # Return all active processes if no profile exists
        processes = session.exec(
            select(MigrationProcess).where(MigrationProcess.is_active == True)
        ).all()
        return processes
    
    # Filter processes based on user's profile
    query = select(MigrationProcess).where(
        MigrationProcess.is_active == True,
        MigrationProcess.country_to == profile.target_country
    )
    
    # Filter by budget if specified
    if profile.budget_usd:
        query = query.where(MigrationProcess.estimated_cost_max <= profile.budget_usd)
    
    processes = session.exec(query).all()
    return processes


@router.get("/processes", response_model=list[MigrationProcessRead])
def list_migration_processes(
    country_to: Optional[str] = Query(None),
    visa_type: Optional[str] = Query(None),
    max_cost: Optional[float] = Query(None),
    max_time_months: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """
    List available migration processes with optional filters
    """
    query = select(MigrationProcess).where(MigrationProcess.is_active == True)
    
    if country_to:
        query = query.where(MigrationProcess.country_to == country_to)
    
    if visa_type:
        query = query.where(MigrationProcess.visa_type == visa_type)
    
    if max_cost:
        query = query.where(MigrationProcess.estimated_cost_max <= max_cost)
    
    if max_time_months:
        query = query.where(MigrationProcess.estimated_time_months <= max_time_months)
    
    processes = session.exec(query).all()
    return processes


@router.get("/processes/{process_id}", response_model=MigrationProcessRead)
def get_migration_process(
    process_id: int,
    session: Session = Depends(get_session)
):
    """
    Get detailed information about a specific migration process
    """
    process = session.get(MigrationProcess, process_id)
    
    if not process:
        raise HTTPException(status_code=404, detail="Migration process not found")
    
    return process


@router.post("/select/{process_id}")
def select_migration_process(
    process_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """
    Select a migration process for the user
    """
    # Verify process exists
    process = session.get(MigrationProcess, process_id)
    if not process:
        raise HTTPException(status_code=404, detail="Migration process not found")
    
    # Get user's profile
    profile = session.exec(
        select(UserMigrationProfile).where(UserMigrationProfile.user_id == current_user.id)
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Migration profile not found. Complete assessment first."
        )
    
    # Update profile with selected process
    profile.selected_process_id = process_id
    profile.current_stage = "preparation"
    profile.updated_at = datetime.utcnow()
    
    session.add(profile)
    session.commit()
    session.refresh(profile)
    
    return {
        "message": "Migration process selected successfully",
        "process": process,
        "profile": profile
    }


@router.get("/my-process")
def get_my_migration_process(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """
    Get current user's selected migration process and progress
    """
    profile = session.exec(
        select(UserMigrationProfile).where(UserMigrationProfile.user_id == current_user.id)
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Migration profile not found. Complete assessment first."
        )
    
    if not profile.selected_process_id:
        return {
            "message": "No migration process selected yet",
            "profile": profile,
            "process": None
        }
    
    process = session.get(MigrationProcess, profile.selected_process_id)
    
    return {
        "profile": profile,
        "process": process,
        "current_stage": profile.current_stage
    }


@router.put("/update-stage")
def update_migration_stage(
    new_stage: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """
    Update current stage of migration process
    Valid stages: assessment, preparation, application, waiting, approved, rejected
    """
    valid_stages = ["assessment", "preparation", "application", "waiting", "approved", "rejected"]
    
    if new_stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage. Must be one of: {', '.join(valid_stages)}"
        )
    
    profile = session.exec(
        select(UserMigrationProfile).where(UserMigrationProfile.user_id == current_user.id)
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Migration profile not found")
    
    profile.current_stage = new_stage
    profile.updated_at = datetime.utcnow()
    
    session.add(profile)
    session.commit()
    session.refresh(profile)
    
    return {
        "message": "Stage updated successfully",
        "current_stage": profile.current_stage
    }


@router.get("/timeline")
def get_migration_timeline(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """
    Get migration timeline/stages for the user's selected process
    """
    profile = session.exec(
        select(UserMigrationProfile).where(UserMigrationProfile.user_id == current_user.id)
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Migration profile not found. Complete assessment first."
        )
    
    if not profile.selected_process_id:
        raise HTTPException(
            status_code=404,
            detail="No migration process selected. Select a route first."
        )
    
    process = session.get(MigrationProcess, profile.selected_process_id)
    
    if not process:
        raise HTTPException(status_code=404, detail="Selected migration process not found")
    
    # Create a simple timeline based on the process
    stages = [
        {
            "stage": "Assessment",
            "status": "completed",
            "description": "Initial migration assessment completed"
        },
        {
            "stage": "Documentation",
            "status": "in_progress" if profile.current_stage == "documentation" else "pending",
            "description": "Gather and prepare required documents"
        },
        {
            "stage": "Application",
            "status": "in_progress" if profile.current_stage == "application" else "pending",
            "description": f"Submit {process.visa_type} application"
        },
        {
            "stage": "Processing",
            "status": "in_progress" if profile.current_stage == "processing" else "pending",
            "description": "Application under review"
        },
        {
            "stage": "Approval",
            "status": "completed" if profile.current_stage == "approved" else "pending",
            "description": "Receive approval and finalize"
        }
    ]
    
    return {
        "process": process,
        "current_stage": profile.current_stage,
        "estimated_time_months": process.estimated_time_months,
        "stages": stages
    }

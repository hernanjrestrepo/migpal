from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.planner_task import PlannerTask
from app.services.scheduler import sync_scheduler

router = APIRouter(prefix="/planner", tags=["planner"])


@router.get("", response_model=list[PlannerTask])
def list_tasks(session: Session = Depends(get_session)):
    tasks = session.exec(select(PlannerTask)).all()
    return tasks


@router.post("", response_model=PlannerTask)
def create_task(task: PlannerTask, session: Session = Depends(get_session)):
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.put("/{task_id}", response_model=PlannerTask)
def update_task(task_id: int, payload: PlannerTask, session: Session = Depends(get_session)):
    existing = session.get(PlannerTask, task_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing, key, value)
    session.add(existing)
    session.commit()
    session.refresh(existing)
    return existing


@router.post("/sync")
def sync_tasks(session: Session = Depends(get_session)):
    tasks = sync_scheduler(session)
    return tasks

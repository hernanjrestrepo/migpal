from __future__ import annotations

from datetime import datetime

from sqlmodel import Session, select

from app.models.data_source import DataSource
from app.models.planner_task import PlannerTask


def ensure_task(session: Session, slug: str, owner: str = "system") -> PlannerTask:
    task = session.exec(select(PlannerTask).where(PlannerTask.linked_source_slug == slug)).first()
    if task:
        return task
    task = PlannerTask(
        title=f"Actualizar fuente {slug}",
        description=f"Scraper y validación para {slug}",
        owner=owner,
        linked_source_slug=slug,
        status="pending",
        progress=0,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def sync_scheduler(session: Session) -> list[PlannerTask]:
    sources = session.exec(select(DataSource)).all()
    tracked = []
    for source in sources:
        task = ensure_task(session, source.slug or source.name)
        task.updated_at = datetime.utcnow()
        tracked.append(task)
    return tracked

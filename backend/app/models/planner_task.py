from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class PlannerTask(SQLModel, table=True):
    __tablename__ = "planner_tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True, min_length=3, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    owner: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(default="pending", max_length=50)
    progress: int = Field(default=0, ge=0, le=100)
    linked_source_slug: Optional[str] = Field(default=None, max_length=100)
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

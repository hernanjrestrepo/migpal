from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class SchoolRanking(SQLModel, table=True):
    __tablename__ = "school_rankings"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="data_sources.id")
    school_id: str = Field(index=True)
    name: str
    city: Optional[str] = None
    state: Optional[str] = None
    rating: Optional[float] = None
    grades: Optional[str] = None
    metadata_blob: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

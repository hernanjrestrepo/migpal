from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class SchoolRanking(SQLModel, table=True):
    __tablename__ = "school_rankings"

    id: int | None = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="data_sources.id")
    school_id: str = Field(index=True)
    name: str
    city: str | None = None
    state: str | None = None
    rating: float | None = None
    grades: str | None = None
    metadata_blob: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

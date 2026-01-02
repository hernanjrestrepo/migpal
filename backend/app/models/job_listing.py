from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class JobListing(SQLModel, table=True):
    __tablename__ = "job_listings"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="data_sources.id")
    job_id: str = Field(index=True)
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    url: str
    salary: Optional[str] = None
    metadata_blob: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

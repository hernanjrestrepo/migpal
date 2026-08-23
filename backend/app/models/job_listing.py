from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class JobListing(SQLModel, table=True):
    __tablename__ = "job_listings"

    id: int | None = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="data_sources.id")
    job_id: str = Field(index=True)
    title: str
    company: str | None = None
    location: str | None = None
    url: str
    salary: str | None = None
    metadata_blob: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

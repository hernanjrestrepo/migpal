from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class DataSourceBase(SQLModel):
    """Base shared attributes for data sources."""

    name: str = Field(min_length=3, max_length=200)
    slug: str = Field(min_length=3, max_length=200, regex=r"^[a-z0-9-]+$")
    category: str = Field(min_length=3, max_length=100, description="legal, housing, education, etc")
    source_type: str = Field(default="website", description="website, api, dataset")
    base_url: str = Field(description="Entry URL or endpoint")
    description: Optional[str] = Field(default=None, max_length=2000)
    access_type: str = Field(default="public", description="public, api_key, oauth, scraping")
    access_config: Optional[str] = Field(default=None, description="JSON blob with auth params")
    default_frequency_hours: int = Field(default=24, ge=1, le=168)
    priority: int = Field(default=3, ge=1, le=5)
    enabled: bool = Field(default=True)


class DataSource(DataSourceBase, table=True):
    """Catalog of external sources (APIs, websites) MigPAL needs to ingest."""

    __tablename__ = "data_sources"

    id: Optional[int] = Field(default=None, primary_key=True)
    last_status: Optional[str] = Field(default=None)
    last_success_at: Optional[datetime] = Field(default=None)
    last_error_at: Optional[datetime] = Field(default=None)
    last_error: Optional[str] = Field(default=None, max_length=2000)
    metadata_blob: Optional[str] = Field(default=None, description="JSON with extra info")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DataSourceCreate(DataSourceBase):
    """Payload to register a new source."""


class DataSourceUpdate(SQLModel):
    """Editable fields for a source."""

    name: Optional[str] = None
    category: Optional[str] = None
    source_type: Optional[str] = None
    base_url: Optional[str] = None
    description: Optional[str] = None
    access_type: Optional[str] = None
    access_config: Optional[str] = None
    default_frequency_hours: Optional[int] = Field(default=None, ge=1, le=168)
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    enabled: Optional[bool] = None


class DataSourceRead(DataSourceBase):
    """API response schema for a source."""

    id: int
    last_status: Optional[str]
    last_success_at: Optional[datetime]
    last_error_at: Optional[datetime]
    last_error: Optional[str]
    metadata_blob: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScrapeJob(SQLModel, table=True):
    """Represents an execution against a data source."""

    __tablename__ = "scrape_jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="data_sources.id")
    status: str = Field(default="pending", description="pending|running|success|failed")
    run_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    records_ingested: int = Field(default=0)
    error_message: Optional[str] = Field(default=None, max_length=2000)
    metadata_blob: Optional[str] = None


class ScrapeJobRead(SQLModel):
    id: int
    source_id: int
    status: str
    run_by_user_id: Optional[int]
    started_at: datetime
    finished_at: Optional[datetime]
    records_ingested: int
    error_message: Optional[str]
    metadata_blob: Optional[str]

    class Config:
        from_attributes = True


class ScrapedDocument(SQLModel, table=True):
    """Stores normalized content ready for embeddings/RAG."""

    __tablename__ = "scraped_documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="data_sources.id", index=True)
    title: str = Field(max_length=500)
    content: str
    content_hash: str = Field(index=True, unique=True)
    language: Optional[str] = Field(default=None, max_length=10)
    published_at: Optional[datetime] = None
    metadata_blob: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScrapedDocumentRead(SQLModel):
    id: int
    source_id: int
    title: str
    language: Optional[str]
    published_at: Optional[datetime]
    metadata_blob: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

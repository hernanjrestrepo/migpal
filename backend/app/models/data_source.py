from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class DataSourceBase(SQLModel):
    """Base shared attributes for data sources."""

    name: str = Field(min_length=3, max_length=200)
    slug: str = Field(min_length=3, max_length=200, regex=r"^[a-z0-9-]+$")
    category: str = Field(min_length=3, max_length=100, description="legal, housing, education, etc")
    source_type: str = Field(default="website", description="website, api, dataset")
    base_url: str = Field(description="Entry URL or endpoint")
    description: str | None = Field(default=None, max_length=2000)
    access_type: str = Field(default="public", description="public, api_key, oauth, scraping")
    access_config: str | None = Field(default=None, description="JSON blob with auth params")
    default_frequency_hours: int = Field(default=24, ge=1, le=168)
    priority: int = Field(default=3, ge=1, le=5)
    enabled: bool = Field(default=True)


class DataSource(DataSourceBase, table=True):
    """Catalog of external sources (APIs, websites) MigPAL needs to ingest."""

    __tablename__ = "data_sources"

    id: int | None = Field(default=None, primary_key=True)
    last_status: str | None = Field(default=None)
    last_success_at: datetime | None = Field(default=None)
    last_error_at: datetime | None = Field(default=None)
    last_error: str | None = Field(default=None, max_length=2000)
    metadata_blob: str | None = Field(default=None, description="JSON with extra info")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DataSourceCreate(DataSourceBase):
    """Payload to register a new source."""


class DataSourceUpdate(SQLModel):
    """Editable fields for a source."""

    name: str | None = None
    category: str | None = None
    source_type: str | None = None
    base_url: str | None = None
    description: str | None = None
    access_type: str | None = None
    access_config: str | None = None
    default_frequency_hours: int | None = Field(default=None, ge=1, le=168)
    priority: int | None = Field(default=None, ge=1, le=5)
    enabled: bool | None = None


class DataSourceRead(DataSourceBase):
    """API response schema for a source."""

    id: int
    last_status: str | None
    last_success_at: datetime | None
    last_error_at: datetime | None
    last_error: str | None
    metadata_blob: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScrapeJob(SQLModel, table=True):
    """Represents an execution against a data source."""

    __tablename__ = "scrape_jobs"

    id: int | None = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="data_sources.id")
    status: str = Field(default="pending", description="pending|running|success|failed")
    run_by_user_id: int | None = Field(default=None, foreign_key="user.id")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    records_ingested: int = Field(default=0)
    error_message: str | None = Field(default=None, max_length=2000)
    metadata_blob: str | None = None


class ScrapeJobRead(SQLModel):
    id: int
    source_id: int
    status: str
    run_by_user_id: int | None
    started_at: datetime
    finished_at: datetime | None
    records_ingested: int
    error_message: str | None
    metadata_blob: str | None

    class Config:
        from_attributes = True


class ScrapedDocument(SQLModel, table=True):
    """Stores normalized content ready for embeddings/RAG."""

    __tablename__ = "scraped_documents"

    id: int | None = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="data_sources.id", index=True)
    title: str = Field(max_length=500)
    content: str
    content_hash: str = Field(index=True, unique=True)
    language: str | None = Field(default=None, max_length=10)
    published_at: datetime | None = None
    metadata_blob: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScrapedDocumentRead(SQLModel):
    id: int
    source_id: int
    title: str
    language: str | None
    published_at: datetime | None
    metadata_blob: str | None
    created_at: datetime

    class Config:
        from_attributes = True

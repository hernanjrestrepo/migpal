from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class BusinessListing(SQLModel, table=True):
    __tablename__ = "business_listings"

    id: int | None = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="data_sources.id")
    listing_id: str = Field(index=True)
    title: str
    url: str
    asking_price_usd: float | None = None
    cash_flow_usd: float | None = None
    city: str | None = None
    state: str | None = None
    industry: str | None = None
    summary: str | None = None
    metadata_blob: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

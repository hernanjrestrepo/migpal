from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class ZillowListing(SQLModel, table=True):
    __tablename__ = "zillow_listings"

    id: int | None = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="data_sources.id")
    listing_id: str = Field(index=True)
    url: str
    title: str | None = None
    price_usd: float | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zipcode: str | None = None
    beds: float | None = None
    baths: float | None = None
    area_sqft: int | None = None
    metadata_blob: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

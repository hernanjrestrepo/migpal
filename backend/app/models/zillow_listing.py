from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class ZillowListing(SQLModel, table=True):
    __tablename__ = "zillow_listings"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="data_sources.id")
    listing_id: str = Field(index=True)
    url: str
    title: Optional[str] = None
    price_usd: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None
    beds: Optional[float] = None
    baths: Optional[float] = None
    area_sqft: Optional[int] = None
    metadata_blob: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

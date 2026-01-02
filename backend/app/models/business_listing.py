from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class BusinessListing(SQLModel, table=True):
    __tablename__ = "business_listings"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="data_sources.id")
    listing_id: str = Field(index=True)
    title: str
    url: str
    asking_price_usd: Optional[float] = None
    cash_flow_usd: Optional[float] = None
    city: Optional[str] = None
    state: Optional[str] = None
    industry: Optional[str] = None
    summary: Optional[str] = None
    metadata_blob: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

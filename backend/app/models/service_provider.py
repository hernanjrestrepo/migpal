from datetime import datetime

from sqlmodel import Field, SQLModel


class ServiceProvider(SQLModel, table=True):
    """
    Directory of service providers (lawyers, housing, employment, education)
    """

    __tablename__ = "service_providers"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    type: str = Field(index=True)  # "lawyer", "housing", "employment", "education"
    country: str = Field(index=True)
    city: str
    description: str

    # Contact information
    contact_email: str | None = None
    contact_phone: str | None = None
    website: str | None = None

    # Rating and verification
    rating: float = Field(default=0.0)  # 0-5 stars
    verified: bool = Field(default=False)

    # Specializations (JSON string)
    specializations: str  # JSON array of specializations

    # Pricing (optional)
    price_range: str | None = None  # "$", "$$", "$$$", "$$$$"

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ServiceProviderCreate(SQLModel):
    name: str
    type: str
    country: str
    city: str
    description: str
    contact_email: str | None = None
    contact_phone: str | None = None
    website: str | None = None
    specializations: str
    price_range: str | None = None


class ServiceProviderRead(SQLModel):
    id: int
    name: str
    type: str
    country: str
    city: str
    description: str
    contact_email: str | None
    contact_phone: str | None
    website: str | None
    rating: float
    verified: bool
    specializations: str
    price_range: str | None
    created_at: datetime
    updated_at: datetime

from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class ServiceProvider(SQLModel, table=True):
    """
    Directory of service providers (lawyers, housing, employment, education)
    """
    __tablename__ = "service_providers"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    type: str = Field(index=True)  # "lawyer", "housing", "employment", "education"
    country: str = Field(index=True)
    city: str
    description: str
    
    # Contact information
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    
    # Rating and verification
    rating: float = Field(default=0.0)  # 0-5 stars
    verified: bool = Field(default=False)
    
    # Specializations (JSON string)
    specializations: str  # JSON array of specializations
    
    # Pricing (optional)
    price_range: Optional[str] = None  # "$", "$$", "$$$", "$$$$"
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ServiceProviderCreate(SQLModel):
    name: str
    type: str
    country: str
    city: str
    description: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    specializations: str
    price_range: Optional[str] = None


class ServiceProviderRead(SQLModel):
    id: int
    name: str
    type: str
    country: str
    city: str
    description: str
    contact_email: Optional[str]
    contact_phone: Optional[str]
    website: Optional[str]
    rating: float
    verified: bool
    specializations: str
    price_range: Optional[str]
    created_at: datetime
    updated_at: datetime

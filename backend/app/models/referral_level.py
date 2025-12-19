from typing import Optional, TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.orm import Mapped

if TYPE_CHECKING:
    from .user import User

# Pydantic models for API requests and responses
class ReferralLevelCreate(SQLModel):
    name: str
    commission_rate: float

class ReferralLevelRead(SQLModel):
    id: int
    name: str
    commission_rate: float

# Database model for ReferralLevel
class ReferralLevel(SQLModel, table=True):
    __tablename__ = "referral_levels"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False)
    commission_rate: float = Field(default=0.0, nullable=False)  # 0.01 = 1%

    users: Mapped[List["User"]] = Relationship(back_populates="level")

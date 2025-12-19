from typing import Optional, TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.orm import Mapped

if TYPE_CHECKING:
    from .referral_level import ReferralLevel

# Pydantic models for API requests and responses
class UserCreate(SQLModel):
    email: str
    username: str
    password: str
    referrer_code: Optional[str] = None

class UserRead(SQLModel):
    id: int
    email: str
    username: str
    referral_code: str
    level_id: Optional[int] = None
    referrer_id: Optional[int] = None


# Database model for the User
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    referral_code: str = Field(index=True, unique=True)
    referrer_id: Optional[int] = Field(default=None, foreign_key="user.id")
    level_id: Optional[int] = Field(default=None, foreign_key="referral_levels.id")

    # The 'back_populates' establish the two-way relationship
    referrer: Mapped[Optional["User"]] = Relationship(
        back_populates="referees",
        sa_relationship_kwargs={
            "primaryjoin": lambda: User.referrer_id == User.id,
            "remote_side": lambda: User.id,
        },
    )
    referees: Mapped[List["User"]] = Relationship(back_populates="referrer")
    level: Mapped[Optional["ReferralLevel"]] = Relationship(back_populates="users")

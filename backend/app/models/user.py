from datetime import datetime

from sqlmodel import Field, SQLModel


# Pydantic models for API requests and responses
class UserCreate(SQLModel):
    email: str
    username: str
    password: str


class UserRead(SQLModel):
    id: int
    email: str
    username: str
    role: str = "user"
    email_verified: bool = False
    created_at: datetime
    updated_at: datetime


# Database model for the User
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: str = Field(default="user", index=True)  # user, admin
    email_verified: bool = Field(default=False)
    email_verification_token: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

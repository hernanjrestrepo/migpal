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

    # --- Verificación de email y recuperación de contraseña ---
    # Los tokens se guardan HASHEADOS (SHA-256), nunca en claro: si alguien
    # se lleva una copia de la base, no puede usarlos para tomar cuentas.
    # El token en claro solo existe en el email que recibe la persona.
    # Ver core/identity/domain/rules.py.
    email_verified: bool = Field(default=False)
    email_verification_token: str | None = Field(default=None, index=True)
    email_verification_expires_at: datetime | None = Field(default=None)

    password_reset_token: str | None = Field(default=None, index=True)
    password_reset_expires_at: datetime | None = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

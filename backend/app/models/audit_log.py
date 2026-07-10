from datetime import datetime

from sqlmodel import Field, SQLModel


class AuditLogRead(SQLModel):
    id: int
    user_id: int | None
    action: str
    resource: str
    resource_id: int | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    action: str = Field(index=True)  # create, read, update, delete, login, logout
    resource: str = Field(index=True)  # user, document, migration_process, service_provider, etc.
    resource_id: int | None = Field(default=None, index=True)
    details: str | None = Field(default=None)  # JSON string with additional info
    ip_address: str | None = Field(default=None)
    user_agent: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

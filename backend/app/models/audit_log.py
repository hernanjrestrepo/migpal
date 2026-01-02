from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class AuditLogRead(SQLModel):
    id: int
    user_id: Optional[int]
    action: str
    resource: str
    resource_id: Optional[int]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    action: str = Field(index=True)  # create, read, update, delete, login, logout
    resource: str = Field(index=True)  # user, document, migration_process, service_provider, etc.
    resource_id: Optional[int] = Field(default=None, index=True)
    details: Optional[str] = Field(default=None)  # JSON string with additional info
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

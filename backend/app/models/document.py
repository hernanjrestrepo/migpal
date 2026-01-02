from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class Document(SQLModel, table=True):
    """
    User's migration documents
    """
    __tablename__ = "documents"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    process_id: Optional[int] = Field(default=None, foreign_key="migration_processes.id")
    
    # Document information
    name: str
    type: str = Field(index=True)  # "passport", "diploma", "work_permit", "birth_certificate", etc.
    file_path: str  # Path to stored file
    file_size: Optional[int] = None  # Size in bytes
    mime_type: Optional[str] = None
    
    # Status
    status: str = Field(default="pending", index=True)  # "pending", "verified", "rejected"
    verification_notes: Optional[str] = None
    
    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    verified_at: Optional[datetime] = None


class DocumentCreate(SQLModel):
    name: str
    type: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    process_id: Optional[int] = None


class DocumentRead(SQLModel):
    id: int
    user_id: int
    process_id: Optional[int]
    name: str
    type: str
    file_path: str
    file_size: Optional[int]
    mime_type: Optional[str]
    status: str
    verification_notes: Optional[str]
    uploaded_at: datetime
    verified_at: Optional[datetime]

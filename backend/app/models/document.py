from datetime import datetime

from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    """
    User's migration documents
    """

    __tablename__ = "documents"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    process_id: int | None = Field(default=None, foreign_key="migration_processes.id")

    # Document information
    name: str
    type: str = Field(index=True)  # "passport", "diploma", "work_permit", "birth_certificate", etc.
    file_path: str  # Path to stored file
    file_size: int | None = None  # Size in bytes
    mime_type: str | None = None

    # Status
    status: str = Field(default="pending", index=True)  # "pending", "verified", "rejected"
    verification_notes: str | None = None

    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    verified_at: datetime | None = None


class DocumentCreate(SQLModel):
    name: str
    type: str
    file_path: str
    file_size: int | None = None
    mime_type: str | None = None
    process_id: int | None = None


class DocumentRead(SQLModel):
    id: int
    user_id: int
    process_id: int | None
    name: str
    type: str
    file_path: str
    file_size: int | None
    mime_type: str | None
    status: str
    verification_notes: str | None
    uploaded_at: datetime
    verified_at: datetime | None

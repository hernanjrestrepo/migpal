from datetime import datetime

from sqlmodel import Field, SQLModel


class AIConversation(SQLModel, table=True):
    """
    Stores AI assistant conversations with users
    """

    __tablename__ = "ai_conversations"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    # Conversation content
    message: str  # User's message
    response: str  # AI's response

    # Context (JSON string with conversation context)
    context: str | None = None

    # Metadata
    model_used: str | None = None  # "gpt-4", "claude-3", etc.
    tokens_used: int | None = None

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AIConversationCreate(SQLModel):
    message: str
    context: str | None = None


class AIConversationRead(SQLModel):
    id: int
    user_id: int
    message: str
    response: str
    context: str | None
    model_used: str | None
    created_at: datetime

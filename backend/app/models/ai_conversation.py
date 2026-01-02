from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class AIConversation(SQLModel, table=True):
    """
    Stores AI assistant conversations with users
    """
    __tablename__ = "ai_conversations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    
    # Conversation content
    message: str  # User's message
    response: str  # AI's response
    
    # Context (JSON string with conversation context)
    context: Optional[str] = None
    
    # Metadata
    model_used: Optional[str] = None  # "gpt-4", "claude-3", etc.
    tokens_used: Optional[int] = None
    
    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AIConversationCreate(SQLModel):
    message: str
    context: Optional[str] = None


class AIConversationRead(SQLModel):
    id: int
    user_id: int
    message: str
    response: str
    context: Optional[str]
    model_used: Optional[str]
    created_at: datetime

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.models.ai_conversation import AIConversation, AIConversationCreate, AIConversationRead
from app.models.user_migration_profile import UserMigrationProfile
from app.models.migration_process import MigrationProcess
from app.utils.ai_assistant import chat_with_ai, build_ai_context

router = APIRouter(prefix="/ai", tags=["ai-assistant"])


@router.post("/chat", response_model=AIConversationRead)
async def chat(
    message_data: AIConversationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """
    Send a message to AI assistant and get response
    """
    # Get user's migration profile for context
    profile = session.exec(
        select(UserMigrationProfile).where(UserMigrationProfile.user_id == current_user.id)
    ).first()
    
    # Get selected migration process if exists
    migration_process = None
    if profile and profile.selected_process_id:
        migration_process = session.get(MigrationProcess, profile.selected_process_id)
    
    # Build context
    context = build_ai_context(
        user_profile=profile.model_dump() if profile else None,
        migration_process=migration_process.model_dump() if migration_process else None
    )
    
    # Get AI response
    ai_response = await chat_with_ai(
        message=message_data.message,
        context=context
    )
    
    # Save conversation
    conversation = AIConversation(
        user_id=current_user.id,
        message=message_data.message,
        response=ai_response["response"],
        context=message_data.context,
        model_used=ai_response.get("model_used"),
        tokens_used=ai_response.get("tokens_used")
    )
    
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    
    return conversation


@router.get("/history", response_model=list[AIConversationRead])
def get_conversation_history(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session),
    limit: int = 50
):
    """
    Get conversation history with AI assistant
    """
    conversations = session.exec(
        select(AIConversation)
        .where(AIConversation.user_id == current_user.id)
        .order_by(AIConversation.created_at.desc())
        .limit(limit)
    ).all()
    
    # Reverse to show oldest first
    return list(reversed(conversations))


@router.post("/guidance")
async def get_personalized_guidance(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    """
    Get personalized migration guidance based on user profile
    """
    from app.utils.ai_assistant import generate_guidance
    
    # Get user's migration profile
    profile = session.exec(
        select(UserMigrationProfile).where(UserMigrationProfile.user_id == current_user.id)
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Migration profile not found. Complete assessment first."
        )
    
    # Get selected migration process if exists
    migration_process = None
    if profile.selected_process_id:
        migration_process = session.get(MigrationProcess, profile.selected_process_id)
    
    # Generate guidance
    guidance = await generate_guidance(
        user_profile=profile.model_dump(),
        migration_process=migration_process.model_dump() if migration_process else None
    )
    
    return {
        "guidance": guidance,
        "profile": profile,
        "process": migration_process
    }

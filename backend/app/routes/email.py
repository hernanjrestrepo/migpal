from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from app.db.session import get_session
from app.auth import get_current_user
from app.models.user import User
from app.utils.email_verification import generate_verification_token, verify_email_token
from app.utils.audit import log_action
from datetime import datetime

router = APIRouter(prefix="/email", tags=["email"])

@router.post("/send-verification")
def send_verification_email(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    request: Request = None
):
    """Send email verification token (in production, this would send an email)."""
    if current_user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Generate token
    token = generate_verification_token()
    current_user.email_verification_token = token
    current_user.updated_at = datetime.utcnow()
    
    session.commit()
    
    log_action(
        session=session,
        action="create",
        resource="email_verification_token",
        user_id=current_user.id,
        request=request
    )
    
    # In production, send email here
    # For now, return token for testing
    return {
        "message": "Verification email sent",
        "token": token  # Remove this in production
    }

@router.post("/verify")
def verify_email(
    token: str,
    session: Session = Depends(get_session),
    request: Request = None
):
    """Verify email with token."""
    user = verify_email_token(session, token)
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    user.email_verified = True
    user.email_verification_token = None
    user.updated_at = datetime.utcnow()
    
    session.commit()
    
    log_action(
        session=session,
        action="update",
        resource="email_verified",
        user_id=user.id,
        request=request
    )
    
    return {"message": "Email verified successfully"}

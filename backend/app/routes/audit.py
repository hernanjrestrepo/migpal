from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from typing import List, Optional
from app.db.session import get_session
from app.auth import get_current_user
from app.models.user import User
from app.models.audit_log import AuditLog, AuditLogRead
from app.utils.rbac import require_admin
from datetime import datetime, timedelta

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/logs", response_model=List[AuditLogRead])
def get_audit_logs(
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    days: int = 7,
    limit: int = 100
):
    """Get audit logs (admin only)."""
    query = select(AuditLog)
    
    # Filter by date
    since = datetime.utcnow() - timedelta(days=days)
    query = query.where(AuditLog.created_at >= since)
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    
    if action:
        query = query.where(AuditLog.action == action)
    
    if resource:
        query = query.where(AuditLog.resource == resource)
    
    query = query.order_by(AuditLog.created_at.desc()).limit(limit)
    
    logs = session.exec(query).all()
    return logs

@router.get("/my-activity", response_model=List[AuditLogRead])
def get_my_activity(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    days: int = 30,
    limit: int = 50
):
    """Get current user's activity logs."""
    since = datetime.utcnow() - timedelta(days=days)
    
    query = select(AuditLog).where(
        AuditLog.user_id == current_user.id,
        AuditLog.created_at >= since
    ).order_by(AuditLog.created_at.desc()).limit(limit)
    
    logs = session.exec(query).all()
    return logs

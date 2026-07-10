import json

from fastapi import Request
from sqlmodel import Session

from app.models.audit_log import AuditLog


def log_action(
    session: Session,
    action: str,
    resource: str,
    user_id: int | None = None,
    resource_id: int | None = None,
    details: dict | str | None = None,
    request: Request | None = None,
):
    """Log an action to the audit log."""
    ip_address = None
    user_agent = None

    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    serialized_details = None
    if isinstance(details, dict):
        serialized_details = json.dumps(details)
    else:
        serialized_details = details

    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=serialized_details,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    session.add(audit_log)
    session.commit()

import secrets

from sqlmodel import Session, select

from app.models.user import User


def generate_verification_token() -> str:
    """Generate a secure verification token."""
    return secrets.token_urlsafe(32)


def verify_email_token(session: Session, token: str) -> User | None:
    """Verify email token and return user if valid."""
    user = session.exec(select(User).where(User.email_verification_token == token)).first()
    return user

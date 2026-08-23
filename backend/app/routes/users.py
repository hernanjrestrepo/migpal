from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.auth import get_current_user
from app.db.session import get_session
from app.models.user import User, UserCreate, UserRead
from app.utils.audit import log_action
from app.utils.email_verification import generate_verification_token
from app.utils.password import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.post("", response_model=UserRead)
def create_user(user_in: UserCreate, session: Session = Depends(get_session), request: Request = None):
    """
    Create a new user.
    """
    # Check for existing email
    existing = session.exec(select(User).where(User.email == user_in.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    # Check for existing username
    existing = session.exec(select(User).where(User.username == user_in.username)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    hashed_password = get_password_hash(user_in.password)
    verification_token = generate_verification_token()

    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        username=user_in.username,
        email_verification_token=verification_token,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    log_action(
        session=session,
        action="create",
        resource="user",
        user_id=new_user.id,
        resource_id=new_user.id,
        request=request,
    )

    return new_user

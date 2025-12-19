import secrets
import string
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth import get_current_user
from app.db.session import get_session
from app.models.user import User, UserCreate, UserRead
from app.models.referral_level import ReferralLevel
from app.utils.password import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])


def generate_referral_code(session: Session, length: int = 8) -> str:
    """Generate a unique referral code."""
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(length))
        existing = session.exec(select(User).where(User.referral_code == code)).first()
        if not existing:
            return code


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user


@router.post("", response_model=UserRead)
def create_user(user_in: UserCreate, session: Session = Depends(get_session)):
    """
    Create a new user and handle referral logic.
    """
    # Check for existing email
    existing = session.exec(select(User).where(User.email == user_in.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    # Check for existing username
    existing = session.exec(select(User).where(User.username == user_in.username)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    # --- Referral Logic ---
    referrer_id = None
    level_id = None

    if user_in.referrer_code:
        referrer = session.exec(
            select(User).where(User.referral_code == user_in.referrer_code)
        ).first()
        if not referrer:
            raise HTTPException(
                status_code=404,
                detail=f"Referrer with code '{user_in.referrer_code}' not found.",
            )
        
        referrer_id = referrer.id
        
        # New user gets the next level up from their referrer
        next_level_id = referrer.level_id + 1
        next_level = session.get(ReferralLevel, next_level_id)
        if not next_level:
            # Fallback or error if the next level doesn't exist.
            # For now, let's raise an error. This can be changed based on business rules.
            raise HTTPException(
                status_code=500,
                detail=f"Configuration error: Referral level {next_level_id} not found.",
            )
        level_id = next_level.id
    else:
        # All new users without a referrer start at the base level
        base_level = session.get(ReferralLevel, 1)
        if not base_level:
            raise HTTPException(
                status_code=500,
                detail="Base referral level not found. System configuration error.",
            )
        level_id = base_level.id
    # --- End Referral Logic ---

    hashed_password = get_password_hash(user_in.password)
    referral_code = generate_referral_code(session)

    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        referral_code=referral_code,
        referrer_id=referrer_id,
        level_id=level_id,
        username=user_in.username,
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return new_user


@router.get("/me/referrals", response_model=list[UserRead])
def get_my_referrals(
    current_user: User = Depends(get_current_user),
):
    """
    Get the list of users referred by the current user.
    """
    return current_user.referees

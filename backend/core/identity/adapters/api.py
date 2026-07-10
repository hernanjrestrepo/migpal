"""
Identity — adapters: superficie Web API (Anexo C).

POST /v1/auth/register: paso "Registro" del vertical. El login
(/api/v1/auth/token) sigue en app/routes/auth.py (Foundation, funcionando)
-- no se duplica aquí; migrarlo es trabajo de un bloque futuro, no de este.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import Session

from app.db.session import get_session
from core.identity.application.commands import RegisterUserCommand
from core.identity.application.handlers import handle_register_user
from core.identity.infrastructure.repository import UserRepository
from core.shared.exceptions import IdentityAlreadyExists

router = APIRouter(prefix="/v1/auth", tags=["identity"])


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class RegisterResponse(BaseModel):
    id: int
    email: str
    username: str


def _repo(session: Session = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, repo: UserRepository = Depends(_repo)):
    cmd = RegisterUserCommand(email=body.email, username=body.username, password=body.password)
    try:
        user = handle_register_user(cmd, repo)
    except IdentityAlreadyExists as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return RegisterResponse(id=user.id, email=user.email, username=user.username)

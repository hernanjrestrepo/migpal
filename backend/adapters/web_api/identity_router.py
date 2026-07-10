"""
Adaptador Web API — superficie pública de Identity (Anexo C).

POST /v1/auth/register es el paso "Registro" del vertical de Sprint 1
(Landing -> Registro -> Migration Case). El login (/api/v1/auth/token, JWT)
ya existe y funciona (Foundation) -- no se duplica aquí.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import Session

from app.db.session import get_session
from core.identity.services import register_user
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


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, session: Session = Depends(get_session)):
    try:
        user = register_user(session, email=body.email, username=body.username, password=body.password)
    except IdentityAlreadyExists as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return RegisterResponse(id=user.id, email=user.email, username=user.username)

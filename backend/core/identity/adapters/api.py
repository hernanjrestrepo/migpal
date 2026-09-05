"""
Identity — adapters: superficie Web API.

`POST /v1/auth/register` y el ciclo de verificación de email / recuperación
de contraseña. El login (`/api/v1/auth/token`) sigue en `app/routes/auth.py`.

Solo traduce HTTP <-> application: ninguna decisión de negocio vive acá.

Dos criterios de seguridad que se aplican en este archivo y conviene no
"simplificar" después:

1. **`/forgot-password` responde SIEMPRE lo mismo**, exista o no el email.
   Responder distinto convertiría el endpoint en un oráculo para averiguar
   qué direcciones tienen cuenta.
2. **El fallo al enviar el email no se propaga como error del request.** Si
   el servidor SMTP está caído, la cuenta igual se creó; devolver 500 haría
   que la persona reintente y choque con "ya existe ese usuario".
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session

from app.config import settings
from app.db.session import get_session
from app.services.email_sender import password_reset_email, send_email, verification_email
from core.identity.application.commands import (
    RegisterUserCommand,
    RequestPasswordResetCommand,
    ResetPasswordCommand,
    VerifyEmailCommand,
)
from core.identity.application.handlers import (
    handle_issue_verification_token,
    handle_register_user,
    handle_request_password_reset,
    handle_reset_password,
    handle_verify_email,
)
from core.identity.domain.rules import InvalidTokenError, WeakPasswordError
from core.identity.infrastructure.repository import UserRepository
from core.shared.exceptions import IdentityAlreadyExists

router = APIRouter(prefix="/v1/auth", tags=["identity"])


def _repo(session: Session = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


def _frontend_link(path: str, token: str) -> str:
    base = (settings.FRONTEND_URL or "http://localhost:3000").rstrip("/")
    return f"{base}{path}?token={token}"


# --------------------------------------------------------------- esquemas


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class RegisterResponse(BaseModel):
    id: int
    email: str
    username: str
    email_verified: bool
    # Solo informa si el correo salió; nunca expone el token.
    verification_email_sent: bool


class MessageResponse(BaseModel):
    message: str


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


# --------------------------------------------------------------- endpoints


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, repo: UserRepository = Depends(_repo)):
    cmd = RegisterUserCommand(email=body.email, username=body.username, password=body.password)
    try:
        user, raw_token = handle_register_user(cmd, repo)
    except IdentityAlreadyExists as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except WeakPasswordError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    subject, text, html = verification_email(_frontend_link("/verificar.html", raw_token))
    sent = await send_email(
        to=user.email,
        subject=subject,
        text_body=text,
        html_body=html,
        link=_frontend_link("/verificar.html", raw_token),
    )

    return RegisterResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        email_verified=user.email_verified,
        verification_email_sent=sent,
    )


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(body: VerifyEmailRequest, repo: UserRepository = Depends(_repo)):
    try:
        handle_verify_email(VerifyEmailCommand(token=body.token), repo)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MessageResponse(message="Tu cuenta quedó verificada.")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(body: ResendVerificationRequest, repo: UserRepository = Depends(_repo)):
    """Respuesta idéntica exista o no el email, y esté o no verificado --
    mismo criterio anti-enumeración que `/forgot-password`."""
    generic = MessageResponse(
        message="Si esa dirección tiene una cuenta sin verificar, te enviamos un enlace nuevo."
    )

    user = repo.get_by_email(body.email)
    if user is None or user.email_verified:
        return generic

    raw_token = handle_issue_verification_token(user, repo)
    subject, text, html = verification_email(_frontend_link("/verificar.html", raw_token))
    await send_email(
        to=user.email,
        subject=subject,
        text_body=text,
        html_body=html,
        link=_frontend_link("/verificar.html", raw_token),
    )
    return generic


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(body: ForgotPasswordRequest, repo: UserRepository = Depends(_repo)):
    generic = MessageResponse(
        message="Si esa dirección tiene una cuenta, te enviamos un enlace para restablecer tu contraseña."
    )

    result = handle_request_password_reset(RequestPasswordResetCommand(email=body.email), repo)
    if result is None:
        return generic          # email inexistente: misma respuesta, a propósito

    user, raw_token = result
    link = _frontend_link("/restablecer.html", raw_token)
    subject, text, html = password_reset_email(link)
    await send_email(to=user.email, subject=subject, text_body=text, html_body=html, link=link)
    return generic


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(body: ResetPasswordRequest, repo: UserRepository = Depends(_repo)):
    cmd = ResetPasswordCommand(token=body.token, new_password=body.new_password)
    try:
        handle_reset_password(cmd, repo)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except WeakPasswordError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return MessageResponse(message="Tu contraseña se actualizó. Ya podés iniciar sesión.")

"""
Progression — adapters: superficie Web API (Sprint 7, Hito 5).

Un único endpoint de lectura -- no hay nada que crear ni actualizar acá,
todo se deriva de lo que otros bounded contexts ya persistieron."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.auth import get_current_user
from app.db.session import get_session
from core.case_engine.application.queries import GetCaseForUserQuery, handle_get_case_for_user
from core.case_engine.infrastructure.repository import CaseRepository
from core.identity.domain.aggregates import User
from core.progression.application.queries import ConsultarProgresoQuery, handle_consultar_progreso
from core.shared.exceptions import CaseNotFound

router = APIRouter(prefix="/v1/progression", tags=["progression"])


class BadgeRead(BaseModel):
    badge_id: str
    label: str
    earned: bool


class ProgressRead(BaseModel):
    xp: int
    level: str
    next_level_name: str | None
    xp_to_next_level: int | None
    badges: list[BadgeRead]


@router.get("", response_model=ProgressRead)
def get_mi_progreso(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case_repo = CaseRepository(session)
    try:
        case = handle_get_case_for_user(GetCaseForUserQuery(user_id=current_user.id), case_repo)
    except CaseNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    result = handle_consultar_progreso(
        ConsultarProgresoQuery(case_id=case.id, user_id=current_user.id), session
    )
    return ProgressRead(
        xp=result.xp,
        level=result.level,
        next_level_name=result.next_level_name,
        xp_to_next_level=result.xp_to_next_level,
        badges=[BadgeRead(badge_id=b.badge_id, label=b.label, earned=b.earned) for b in result.badges],
    )

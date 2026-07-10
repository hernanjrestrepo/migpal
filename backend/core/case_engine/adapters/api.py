"""
Case Engine — adapters: superficie Web API (Anexo C).

Regla del Sprint 1: este router NUNCA importa domain/aggregates.py ni
infrastructure/repository.py más allá de construir el repositorio una vez
por request. Toda decisión pasa por application/handlers.py y
application/queries.py.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.auth import get_current_user
from app.db.session import get_session
from core.case_engine.application.commands import (
    AddFamilyMemberCommand,
    OpenCaseCommand,
    UpdateObjectiveCommand,
)
from core.case_engine.application.handlers import (
    handle_add_family_member,
    handle_open_case,
    handle_update_objective,
)
from core.case_engine.application.queries import GetCaseForUserQuery, handle_get_case_for_user
from core.case_engine.infrastructure.repository import CaseRepository
from core.identity.domain.aggregates import User
from core.shared.exceptions import CaseNotFound

router = APIRouter(prefix="/v1/case", tags=["case"])


class CaseRead(BaseModel):
    id: int
    status: str
    objective_country: str | None
    objective_visa_type: str | None
    next_step_ref: str | None


class CaseObjectiveUpdate(BaseModel):
    objective_country: str | None = None
    objective_visa_type: str | None = None


class FamilyMemberCreate(BaseModel):
    full_name: str
    relationship_type: str


class FamilyMemberRead(BaseModel):
    id: int
    full_name: str
    relationship_type: str


def _repo(session: Session = Depends(get_session)) -> CaseRepository:
    return CaseRepository(session)


def _to_read(case) -> CaseRead:
    return CaseRead(
        id=case.id,
        status=case.status.value if hasattr(case.status, "value") else case.status,
        objective_country=case.objective_country,
        objective_visa_type=case.objective_visa_type,
        next_step_ref=case.next_step_ref,
    )


@router.get("", response_model=CaseRead)
def get_my_case(current_user: User = Depends(get_current_user), repo: CaseRepository = Depends(_repo)):
    case = handle_open_case(OpenCaseCommand(user_id=current_user.id), repo)
    return _to_read(case)


@router.post("", response_model=CaseRead)
def open_my_case(current_user: User = Depends(get_current_user), repo: CaseRepository = Depends(_repo)):
    case = handle_open_case(OpenCaseCommand(user_id=current_user.id), repo)
    return _to_read(case)


@router.put("", response_model=CaseRead)
def update_my_case_objective(
    body: CaseObjectiveUpdate,
    current_user: User = Depends(get_current_user),
    repo: CaseRepository = Depends(_repo),
):
    cmd = UpdateObjectiveCommand(
        user_id=current_user.id,
        objective_country=body.objective_country,
        objective_visa_type=body.objective_visa_type,
    )
    try:
        case = handle_update_objective(cmd, repo)
    except CaseNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_read(case)


@router.post("/family-members", response_model=FamilyMemberRead)
def add_my_family_member(
    body: FamilyMemberCreate,
    current_user: User = Depends(get_current_user),
    repo: CaseRepository = Depends(_repo),
):
    cmd = AddFamilyMemberCommand(
        user_id=current_user.id, full_name=body.full_name, relationship_type=body.relationship_type
    )
    try:
        member = handle_add_family_member(cmd, repo)
    except CaseNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FamilyMemberRead(
        id=member.id, full_name=member.full_name, relationship_type=member.relationship_type
    )


# Reexportado para que app/db/base.py pueda seguir importando desde una
# ruta estable si hace falta -- ver core/case_engine/__init__.py.
__all__ = ["router", "GetCaseForUserQuery", "handle_get_case_for_user"]

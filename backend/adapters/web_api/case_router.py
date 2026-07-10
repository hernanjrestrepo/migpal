"""
Adaptador Web API — superficie pública de Case Engine (Anexo C, API Contract).

Regla obligatoria 06/07 (Constitución): este adaptador solo traduce HTTP <->
llamadas a core/case_engine. Cero lógica de negocio aquí.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.auth import get_current_user
from app.db.session import get_session
from core.case_engine.models import CaseFamilyMember, MigrationCase
from core.case_engine.services import add_family_member, get_case_for_user, open_case, update_objective
from core.identity.models import User

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


def _to_read(case: MigrationCase) -> CaseRead:
    return CaseRead(
        id=case.id,
        status=case.status.value if hasattr(case.status, "value") else case.status,
        objective_country=case.objective_country,
        objective_visa_type=case.objective_visa_type,
        next_step_ref=case.next_step_ref,
    )


@router.get("", response_model=CaseRead)
def get_my_case(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Landing/Registro ya creó el caso (ver POST /v1/case) -- este endpoint
    lo consulta; si por algún motivo no existe, lo abre de forma idempotente."""
    case = open_case(session, user_id=current_user.id)
    return _to_read(case)


@router.post("", response_model=CaseRead)
def open_my_case(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Registro -> Migration Case: primer paso real del vertical de Sprint 1."""
    case = open_case(session, user_id=current_user.id)
    return _to_read(case)


@router.put("", response_model=CaseRead)
def update_my_case_objective(
    body: CaseObjectiveUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = get_case_for_user(session, user_id=current_user.id)
    case = update_objective(
        session, case=case, country=body.objective_country, visa_type=body.objective_visa_type
    )
    return _to_read(case)


@router.post("/family-members", response_model=FamilyMemberRead)
def add_my_family_member(
    body: FamilyMemberCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = get_case_for_user(session, user_id=current_user.id)
    member: CaseFamilyMember = add_family_member(
        session, case=case, full_name=body.full_name, relationship_type=body.relationship_type
    )
    return FamilyMemberRead(
        id=member.id, full_name=member.full_name, relationship_type=member.relationship_type
    )

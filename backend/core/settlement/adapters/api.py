"""
Settlement — adapters: superficie Web API (Sprint 2, Hito 5).

Mismo criterio que core/execution_plan/adapters/api.py:
- 404: no hay Recommendation ACCEPTED (`RecommendationNotFound`), o no
  existe ningún checklist para este caso (`SettlementNotFound`, o `None`
  de `handle_consultar_mi_checklist`).
- 409: ya existe un checklist para este caso (`SettlementInvariantError`).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.auth import get_current_user
from app.db.session import get_session
from core.case_engine.application.queries import GetCaseForUserQuery, handle_get_case_for_user
from core.case_engine.infrastructure.repository import CaseRepository
from core.identity.domain.aggregates import User
from core.recommendation.infrastructure.repository import RecommendationRepository
from core.settlement.application.commands import ActualizarItemCommand, GenerarChecklistCommand
from core.settlement.application.handlers import handle_actualizar_item, handle_generar_checklist
from core.settlement.application.queries import (
    ConsultarMiChecklistQuery,
    SettlementChecklistView,
    build_checklist_view,
    handle_consultar_mi_checklist,
)
from core.settlement.domain.rules import SettlementInvariantError
from core.settlement.domain.value_objects import SettlementItemStatus
from core.settlement.infrastructure.repository import SettlementRepository
from core.shared.exceptions import CaseNotFound, RecommendationNotFound, SettlementNotFound

router = APIRouter(prefix="/v1/settlement", tags=["settlement"])


class SettlementItemRead(BaseModel):
    id: int
    title: str
    description: str
    sequence: int
    status: str
    updated_at: str | None


class SettlementChecklistRead(BaseModel):
    id: int
    case_id: int
    country: str
    items: list[SettlementItemRead]
    done_count: int
    total_count: int


class ActualizarItemRequest(BaseModel):
    status: SettlementItemStatus


def _to_read(view: SettlementChecklistView) -> SettlementChecklistRead:
    return SettlementChecklistRead(
        id=view.id,
        case_id=view.case_id,
        country=view.country,
        items=[
            SettlementItemRead(
                id=i.id, title=i.title, description=i.description, sequence=i.sequence,
                status=i.status.value, updated_at=i.updated_at,
            )
            for i in view.items
        ],
        done_count=view.done_count,
        total_count=view.total_count,
    )


def _get_case_or_404(current_user: User, session: Session):
    case_repo = CaseRepository(session)
    try:
        return handle_get_case_for_user(GetCaseForUserQuery(user_id=current_user.id), case_repo)
    except CaseNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=SettlementChecklistRead)
def generar_checklist(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    settlement_repo = SettlementRepository(session)
    recommendation_repo = RecommendationRepository(session)

    try:
        checklist = handle_generar_checklist(
            GenerarChecklistCommand(case_id=case.id), settlement_repo, recommendation_repo
        )
    except RecommendationNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SettlementInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_read(build_checklist_view(checklist))


@router.get("", response_model=SettlementChecklistRead)
def get_mi_checklist(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    repo = SettlementRepository(session)

    view = handle_consultar_mi_checklist(ConsultarMiChecklistQuery(case_id=case.id), repo)
    if view is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todavía no generaste tu checklist de instalación."
        )
    return _to_read(view)


@router.post("/items/{item_id}/status", response_model=SettlementChecklistRead)
def actualizar_item(
    item_id: int,
    body: ActualizarItemRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    repo = SettlementRepository(session)

    current = handle_consultar_mi_checklist(ConsultarMiChecklistQuery(case_id=case.id), repo)
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todavía no generaste tu checklist de instalación."
        )

    try:
        checklist = handle_actualizar_item(
            ActualizarItemCommand(checklist_id=current.id, item_id=item_id, case_id=case.id, status=body.status),
            repo,
        )
    except SettlementNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SettlementInvariantError as exc:
        # El checklist existe (ya se resolvió arriba) pero `item_id` no le
        # pertenece -- mismo criterio que ExecutionPlan::complete_step con
        # un step_id inexistente (ver execution_plan/domain/rules.py).
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_read(build_checklist_view(checklist))

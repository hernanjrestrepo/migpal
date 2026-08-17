"""
Execution Plan — adapters: superficie Web API (Sprint 3, Hito 4).

Solo traduce HTTP <-> application, mismo criterio que
core/recommendation/adapters/api.py -- ninguna decisión de negocio vive
acá, toda invariante vive en domain/rules.py (Sprint 2). Ver
docs/HITO_4_DESIGN.md §10 para el contrato exacto de cada código HTTP:

- 404: no hay Recommendation ACCEPTED (`RecommendationNotFound`, ver
  docstring de `handle_generar_execution_plan`) o no existe ningún
  ExecutionPlan/paso para este caso (`ExecutionPlanNotFound`, o `None` de
  `handle_consultar_mi_plan`).
- 409: invariantes reales de ExecutionPlan (`ExecutionPlanInvariantError`/
  `ExecutionPlanTransitionError`) -- ya existe un plan ACTIVE, paso
  bloqueado, plan ya COMPLETED.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.auth import get_current_user
from app.db.session import get_session
from core.case_engine.application.queries import GetCaseForUserQuery, handle_get_case_for_user
from core.case_engine.infrastructure.repository import CaseRepository
from core.execution_plan.application.commands import CompletarPasoCommand, GenerarExecutionPlanCommand
from core.execution_plan.application.handlers import handle_completar_paso, handle_generar_execution_plan
from core.execution_plan.application.queries import (
    ConsultarMiPlanQuery,
    ExecutionPlanView,
    build_plan_view,
    handle_consultar_mi_plan,
)
from core.execution_plan.domain.rules import ExecutionPlanInvariantError, ExecutionPlanTransitionError
from core.execution_plan.infrastructure.repository import ExecutionPlanRepository
from core.identity.domain.aggregates import User
from core.recommendation.infrastructure.repository import RecommendationRepository
from core.shared.exceptions import CaseNotFound, ExecutionPlanNotFound, RecommendationNotFound

router = APIRouter(prefix="/v1/execution-plan", tags=["execution-plan"])


class PlanStepRead(BaseModel):
    id: int
    title: str
    description: str
    sequence: int
    status: str
    depends_on: list[int]
    blocked: bool
    blocked_by: list[int]
    completed_at: str | None


class ExecutionPlanRead(BaseModel):
    id: int
    case_id: int
    recommendation_id: int
    status: str
    steps: list[PlanStepRead]
    completed_count: int
    total_count: int


def _to_read(view: ExecutionPlanView) -> ExecutionPlanRead:
    return ExecutionPlanRead(
        id=view.id,
        case_id=view.case_id,
        recommendation_id=view.recommendation_id,
        status=view.status.value,
        steps=[
            PlanStepRead(
                id=s.id,
                title=s.title,
                description=s.description,
                sequence=s.sequence,
                status=s.status.value,
                depends_on=s.depends_on,
                blocked=s.blocked,
                blocked_by=s.blocked_by,
                completed_at=s.completed_at.isoformat() if s.completed_at else None,
            )
            for s in view.steps
        ],
        completed_count=view.completed_count,
        total_count=view.total_count,
    )


def _get_case_or_404(current_user: User, session: Session):
    case_repo = CaseRepository(session)
    try:
        return handle_get_case_for_user(GetCaseForUserQuery(user_id=current_user.id), case_repo)
    except CaseNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=ExecutionPlanRead)
def generar_execution_plan(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    plan_repo = ExecutionPlanRepository(session)
    recommendation_repo = RecommendationRepository(session)

    try:
        plan = handle_generar_execution_plan(
            GenerarExecutionPlanCommand(case_id=case.id), plan_repo, recommendation_repo
        )
    except RecommendationNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ExecutionPlanInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_read(build_plan_view(plan))


@router.get("", response_model=ExecutionPlanRead)
def get_my_execution_plan(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    plan_repo = ExecutionPlanRepository(session)

    view = handle_consultar_mi_plan(ConsultarMiPlanQuery(case_id=case.id), plan_repo)
    if view is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todavía no generaste tu ExecutionPlan.")
    return _to_read(view)


@router.post("/steps/{step_id}/complete", response_model=ExecutionPlanRead)
def completar_paso(
    step_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    plan_repo = ExecutionPlanRepository(session)

    current = handle_consultar_mi_plan(ConsultarMiPlanQuery(case_id=case.id), plan_repo)
    if current is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todavía no generaste tu ExecutionPlan.")

    try:
        plan = handle_completar_paso(
            CompletarPasoCommand(execution_plan_id=current.id, step_id=step_id, case_id=case.id), plan_repo
        )
    except ExecutionPlanNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (ExecutionPlanTransitionError, ExecutionPlanInvariantError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_read(build_plan_view(plan))

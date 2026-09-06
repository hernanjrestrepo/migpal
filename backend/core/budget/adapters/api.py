"""
Budget — adapters: superficie Web API (Sprint 1, Hito 5).

Solo traduce HTTP <-> application, mismo criterio que
core/execution_plan/adapters/api.py -- ninguna decisión de negocio vive
acá, toda regla vive en domain/rules.py.

- 400: entrada inválida (`BudgetInvariantError`) -- rangos de costo
  invertidos, valores negativos, tamaño de grupo familiar menor a 1.
- 404: no existe ningún BudgetEstimate para el caso todavía (`GET`).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.auth import get_current_user
from app.db.session import get_session
from core.budget.application.commands import CalcularPresupuestoCommand
from core.budget.application.handlers import handle_calcular_presupuesto
from core.budget.application.queries import (
    BudgetView,
    ConsultarPresupuestoQuery,
    build_budget_view,
    handle_consultar_presupuesto,
)
from core.budget.domain.rules import BudgetInvariantError
from core.budget.infrastructure.repository import BudgetRepository
from core.case_engine.application.queries import GetCaseForUserQuery, handle_get_case_for_user
from core.case_engine.infrastructure.repository import CaseRepository
from core.identity.domain.aggregates import User
from core.shared.exceptions import CaseNotFound

router = APIRouter(prefix="/v1/budget", tags=["budget"])


class CalcularPresupuestoRequest(BaseModel):
    family_size: int = Field(ge=1)
    origin_monthly_income: float = Field(ge=0)
    destination_monthly_income: float = Field(ge=0)
    government_fee: float = Field(ge=0)
    relocation_cost_low: float = Field(ge=0)
    relocation_cost_high: float = Field(ge=0)
    settlement_cost: float = Field(ge=0)
    legal_fee_low: float = Field(default=0.0, ge=0)
    legal_fee_high: float = Field(default=0.0, ge=0)


class BudgetRead(BaseModel):
    id: int
    case_id: int
    family_size: int
    migpal_service_fee: float
    government_fee: float
    relocation_cost_low: float
    relocation_cost_high: float
    settlement_cost: float
    legal_fee_low: float
    legal_fee_high: float
    total_low: float
    total_high: float
    origin_monthly_income: float
    destination_monthly_income: float
    monthly_differential: float
    breakeven_months: float | None


def _to_read(view: BudgetView) -> BudgetRead:
    return BudgetRead(
        id=view.id,
        case_id=view.case_id,
        family_size=view.family_size,
        migpal_service_fee=view.breakdown.migpal_service_fee,
        government_fee=view.breakdown.government_fee,
        relocation_cost_low=view.breakdown.relocation_cost_low,
        relocation_cost_high=view.breakdown.relocation_cost_high,
        settlement_cost=view.breakdown.settlement_cost,
        legal_fee_low=view.breakdown.legal_fee_low,
        legal_fee_high=view.breakdown.legal_fee_high,
        total_low=view.breakdown.total_low,
        total_high=view.breakdown.total_high,
        origin_monthly_income=view.origin_monthly_income,
        destination_monthly_income=view.destination_monthly_income,
        monthly_differential=view.monthly_differential,
        breakeven_months=view.breakeven_months,
    )


def _get_case_or_404(current_user: User, session: Session):
    case_repo = CaseRepository(session)
    try:
        return handle_get_case_for_user(GetCaseForUserQuery(user_id=current_user.id), case_repo)
    except CaseNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=BudgetRead)
def calcular_presupuesto(
    body: CalcularPresupuestoRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    repo = BudgetRepository(session)

    try:
        estimate = handle_calcular_presupuesto(
            CalcularPresupuestoCommand(case_id=case.id, **body.model_dump()), repo
        )
    except BudgetInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _to_read(build_budget_view(estimate))


@router.get("", response_model=BudgetRead)
def get_mi_presupuesto(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    repo = BudgetRepository(session)

    view = handle_consultar_presupuesto(ConsultarPresupuestoQuery(case_id=case.id), repo)
    if view is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todavía no calculaste tu presupuesto.")
    return _to_read(view)

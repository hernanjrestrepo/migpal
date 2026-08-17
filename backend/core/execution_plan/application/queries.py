"""
Execution Plan — application: queries (Sprint 2, Hito 4).

`ExecutionPlanView`/`PlanStepView` calculan "bloqueado/disponible" (§4 del
diseño) a partir de `depends_on` + qué pasos están COMPLETED -- no es un
campo persistido, se deriva acá para que quien consuma esta query (Sprint 3,
API) no tenga que recalcular el grafo de dependencias. `completed_count`/
`total_count` son los números crudos; el texto de progreso ("2/4 pasos
completados") es responsabilidad de la UI (sprint posterior).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from core.execution_plan.domain.aggregates import ExecutionPlan, PlanStep
from core.execution_plan.domain.value_objects import ExecutionPlanStatus, PlanStepStatus
from core.execution_plan.infrastructure.repository import ExecutionPlanRepository


@dataclass(frozen=True)
class ConsultarMiPlanQuery:
    case_id: int


@dataclass(frozen=True)
class PlanStepView:
    id: int
    title: str
    description: str
    sequence: int
    status: PlanStepStatus
    depends_on: list[int]
    blocked: bool
    blocked_by: list[int]
    completed_at: datetime | None = None


@dataclass(frozen=True)
class ExecutionPlanView:
    id: int
    case_id: int
    recommendation_id: int
    status: ExecutionPlanStatus
    steps: list[PlanStepView] = field(default_factory=list)
    completed_count: int = 0
    total_count: int = 0


def _step_view(step: PlanStep, *, completed_ids: set[int]) -> PlanStepView:
    blocked_by = [dep_id for dep_id in step.depends_on if dep_id not in completed_ids]
    blocked = step.status == PlanStepStatus.PENDING and bool(blocked_by)
    return PlanStepView(
        id=step.id,
        title=step.title,
        description=step.description,
        sequence=step.sequence,
        status=step.status,
        depends_on=list(step.depends_on),
        blocked=blocked,
        blocked_by=blocked_by if step.status == PlanStepStatus.PENDING else [],
        completed_at=step.completed_at,
    )


def _plan_view(plan: ExecutionPlan) -> ExecutionPlanView:
    completed_ids = {s.id for s in plan.steps if s.status == PlanStepStatus.COMPLETED}
    steps = sorted(plan.steps, key=lambda s: s.sequence)
    return ExecutionPlanView(
        id=plan.id,
        case_id=plan.case_id,
        recommendation_id=plan.recommendation_id,
        status=plan.status,
        steps=[_step_view(s, completed_ids=completed_ids) for s in steps],
        completed_count=len(completed_ids),
        total_count=len(steps),
    )


def handle_consultar_mi_plan(
    query: ConsultarMiPlanQuery, repo: ExecutionPlanRepository
) -> ExecutionPlanView | None:
    """El plan del caso -- activo, o el último completado si no hay uno
    activo (mismo criterio que `get_latest_for_case`, §8 del diseño)."""

    plan = repo.get_latest_for_case(query.case_id)
    if plan is None:
        return None
    return _plan_view(plan)

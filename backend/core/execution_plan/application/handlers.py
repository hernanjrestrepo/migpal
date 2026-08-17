"""
Execution Plan — application: handlers (Sprint 2, Hito 4).

Único lugar (junto con `domain/rules.py`, que estos handlers envuelven)
donde vive orquestación de ExecutionPlan. Un futuro `adapters/api.py`
(Sprint 3) no debe importar `domain.rules` ni tomar ninguna decisión de
negocio -- solo llama a estos handlers y traduce las excepciones resultantes
a HTTP (mismo criterio que `core/recommendation/application/handlers.py`).

Flujo de dos llamadas en `handle_generar_execution_plan` (ver
`domain/rules.py`, docstring del módulo, y docs/HITO_4_DESIGN.md §12): el
paso final necesita el `depends_on` con los ids reales de los pasos de
documentos, pero esos ids no existen hasta que se persisten. Por eso:
1. `execution_plan_repo.add(plan)` con el plan + solo los pasos de
   documentos -- dispara `ExecutionPlanCreated`, y tras el `refresh()`
   interno cada `PlanStep` ya tiene su id real.
2. Se arma el paso final con esos ids y se agrega a `plan.steps` (ya
   trackeado por la sesión vía la relación), y `execution_plan_repo.save(plan)`
   (sin `completed_step_id`) lo persiste sin disparar ningún evento de más.
"""

from __future__ import annotations

from core.execution_plan.application.commands import CompletarPasoCommand, GenerarExecutionPlanCommand
from core.execution_plan.domain.aggregates import ExecutionPlan
from core.execution_plan.domain.rules import build_plan_steps, complete_step, start_plan
from core.execution_plan.infrastructure.repository import ExecutionPlanRepository
from core.recommendation.infrastructure.repository import RecommendationRepository
from core.shared.exceptions import ExecutionPlanNotFound, RecommendationNotFound


def handle_generar_execution_plan(
    cmd: GenerarExecutionPlanCommand,
    execution_plan_repo: ExecutionPlanRepository,
    recommendation_repo: RecommendationRepository,
) -> ExecutionPlan:
    """Si no hay ninguna Recommendation ACCEPTED para el caso, levanta
    `RecommendationNotFound` acá -- no es una invariante de ExecutionPlan
    (eso vive en `domain/rules.py::start_plan`, invariantes 1-2), es una
    regla de acceso/existencia (misma categoría que `_get_owned_recommendation`
    en `core/recommendation/application/handlers.py`; mapea a 404, no a 409,
    ver docs/HITO_4_DESIGN.md §10)."""

    recommendation = recommendation_repo.get_accepted_for_case(cmd.case_id)
    if recommendation is None:
        raise RecommendationNotFound(f"No hay una Recommendation ACCEPTED para el caso {cmd.case_id}.")

    existing_active = execution_plan_repo.get_active_for_case(cmd.case_id)
    plan = start_plan(recommendation, existing_active=existing_active)

    document_steps, final_step = build_plan_steps(
        recommendation.primary_route_evaluation(), recommendation.next_step_detail()
    )
    plan.steps = document_steps
    plan = execution_plan_repo.add(plan)

    final_step.depends_on = [s.id for s in plan.steps]
    plan.steps.append(final_step)
    return execution_plan_repo.save(plan)


def _get_owned_plan(execution_plan_id: int, case_id: int, repo: ExecutionPlanRepository) -> ExecutionPlan:
    plan = repo.get_by_id(execution_plan_id)
    if not plan or plan.case_id != case_id:
        raise ExecutionPlanNotFound(f"ExecutionPlan {execution_plan_id} no encontrado para este caso.")
    return plan


def handle_completar_paso(cmd: CompletarPasoCommand, execution_plan_repo: ExecutionPlanRepository) -> ExecutionPlan:
    plan = _get_owned_plan(cmd.execution_plan_id, cmd.case_id, execution_plan_repo)
    plan = complete_step(plan, cmd.step_id)
    return execution_plan_repo.save(plan, completed_step_id=cmd.step_id)

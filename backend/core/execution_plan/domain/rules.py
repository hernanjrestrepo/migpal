"""
Execution Plan — domain: invariantes y transiciones de estado (Sprint 2, Hito 4).

Funciones puras, sin DB -- mismo espíritu que
`core/recommendation/domain/rules.py`. Ver docs/HITO_4_DESIGN.md §5
(invariantes) y §12 (integración con Recommendation, solo lectura).

Nota sobre `depends_on` del paso final (§12): esta capa no puede resolverlo
por sí sola -- necesita los ids reales que Postgres asigna a los pasos de
documentos al insertarlos, y estas funciones no tocan DB. Por eso
`build_plan_steps()` devuelve el paso final con `depends_on=[]` sin resolver;
`application/handlers.py` lo completa después de persistir los pasos de
documentos (ver su docstring para el flujo de dos llamadas).
"""

from __future__ import annotations

from datetime import UTC, datetime

from core.execution_plan.domain.aggregates import ExecutionPlan, PlanStep
from core.execution_plan.domain.value_objects import ExecutionPlanStatus, PlanStepStatus
from core.recommendation.domain.aggregates import Recommendation
from core.recommendation.domain.value_objects import NextStep, RecommendationStatus, RouteEvaluation


class ExecutionPlanInvariantError(ValueError):
    """Se violó una invariante del aggregate ExecutionPlan."""


class ExecutionPlanTransitionError(ValueError):
    """Transición de estado no permitida para el status actual."""


def build_plan_steps(evaluation: RouteEvaluation, next_step: NextStep) -> tuple[list[PlanStep], PlanStep]:
    """Deriva los PlanStep iniciales de una Recommendation (invariante 7:
    determinístico -- mismo `evaluation`/`next_step` producen siempre la
    misma lista). Un paso sin dependencias por cada `required_documents`,
    más un paso final derivado de `next_step` cuyo `depends_on` queda sin
    resolver acá (ver docstring del módulo)."""

    document_steps = [
        PlanStep(title=document, description=document, sequence=index, depends_on=[])
        for index, document in enumerate(evaluation.required_documents, start=1)
    ]
    final_step = PlanStep(
        title=next_step.title,
        description=next_step.description,
        sequence=len(document_steps) + 1,
        depends_on=[],
    )
    return document_steps, final_step


def start_plan(
    recommendation: Recommendation | None, *, existing_active: ExecutionPlan | None
) -> ExecutionPlan:
    """Crea el `ExecutionPlan` (sin steps todavía -- se agregan aparte, ver
    `build_plan_steps`). Invariante 1: `recommendation` debe existir y estar
    ACCEPTED. Invariante 2: no puede haber ya un ExecutionPlan ACTIVE para
    este caso (`existing_active` lo trae quien orquesta, vía el repositorio
    -- mismo criterio que `Recommendation.accept()` con `existing_accepted`)."""

    if recommendation is None or recommendation.status != RecommendationStatus.ACCEPTED:
        raise ExecutionPlanInvariantError(
            "Un ExecutionPlan requiere una Recommendation ACCEPTED que lo origine (invariante 1)."
        )
    if existing_active is not None:
        raise ExecutionPlanInvariantError(
            "Ya existe un ExecutionPlan ACTIVE para este caso (invariante 2)."
        )

    return ExecutionPlan(
        case_id=recommendation.case_id,
        recommendation_id=recommendation.id,
        status=ExecutionPlanStatus.ACTIVE,
    )


def complete_step(plan: ExecutionPlan, step_id: int) -> ExecutionPlan:
    """PENDING -> COMPLETED para el PlanStep `step_id` dentro de `plan`.

    Invariante 6: un plan COMPLETED es terminal -- no se le pueden completar
    más pasos. Invariante 3: no se puede completar un paso mientras alguno
    de los ids en su `depends_on` siga sin estar COMPLETED. Invariante 5: si
    tras esto todos los pasos quedan COMPLETED, el plan pasa a COMPLETED
    automáticamente -- nunca se marca a mano."""

    if plan.status == ExecutionPlanStatus.COMPLETED:
        raise ExecutionPlanTransitionError("El ExecutionPlan ya está COMPLETED (invariante 6).")

    step = next((s for s in plan.steps if s.id == step_id), None)
    if step is None:
        raise ExecutionPlanInvariantError(f"El plan no tiene ningún PlanStep con id {step_id}.")
    if step.status == PlanStepStatus.COMPLETED:
        raise ExecutionPlanTransitionError(f"El PlanStep {step_id} ya está COMPLETED.")

    completed_ids = {s.id for s in plan.steps if s.status == PlanStepStatus.COMPLETED}
    unmet = [dep_id for dep_id in step.depends_on if dep_id not in completed_ids]
    if unmet:
        raise ExecutionPlanInvariantError(
            f"El PlanStep {step_id} está bloqueado -- depende de {unmet}, que aún no están COMPLETED (invariante 3)."
        )

    now = datetime.now(UTC)
    step.status = PlanStepStatus.COMPLETED
    step.completed_at = now

    if all(s.status == PlanStepStatus.COMPLETED for s in plan.steps):
        plan.status = ExecutionPlanStatus.COMPLETED
        plan.completed_at = now

    return plan

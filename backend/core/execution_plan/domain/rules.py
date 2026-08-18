"""
Execution Plan — domain: invariantes y transiciones de estado (Sprint 2, Hito 4).

Funciones puras, sin DB -- mismo espíritu que
`core/recommendation/domain/rules.py`. Ver docs/HITO_4_DESIGN.md §5
(invariantes) y §12 (integración con Recommendation, solo lectura).

Dependencia hacia `recommendation.domain` deliberadamente mínima: solo los
Value Objects `RouteEvaluation`/`NextStep` (datos puros para derivar
`PlanStep`s en `build_plan_steps`), nunca el aggregate `Recommendation` ni
su enum de estado -- ver docstring de `start_plan` para la corrección
aplicada en el cierre de Hito 4.

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
from core.recommendation.domain.value_objects import NextStep, RouteEvaluation


class ExecutionPlanInvariantError(ValueError):
    """Se violó una invariante del aggregate ExecutionPlan."""


class ExecutionPlanTransitionError(ValueError):
    """Transición de estado no permitida para el status actual."""


def build_plan_steps(evaluation: RouteEvaluation, next_step: NextStep) -> tuple[list[PlanStep], PlanStep]:
    """Deriva los PlanStep iniciales de una Recommendation (invariante 7:
    determinístico -- mismo `evaluation`/`next_step` producen siempre la
    misma lista). Un paso sin dependencias por cada `required_documents`,
    más un paso final derivado de `next_step` cuyo `depends_on` queda sin
    resolver acá (ver docstring del módulo).

    `description` de los pasos de documento es un texto distinto de
    `title`, no una repetición (corrección de la auditoría independiente de
    Hito 4, hallazgo mayor 1: criterio de éxito 6 exige que el usuario
    entienda qué tiene que lograr en cada paso, no solo un título genérico
    -- `RouteEvaluation.required_documents` es `list[str]`, sin ningún
    campo de descripción propio, así que se genera una plantilla explícita
    en vez de repetir el nombre del documento)."""

    document_steps = [
        PlanStep(
            title=document,
            description=f"Reunir y adjuntar: {document}.",
            sequence=index,
            depends_on=[],
        )
        for index, document in enumerate(evaluation.required_documents, start=1)
    ]
    final_step = PlanStep(
        title=next_step.title,
        description=next_step.description,
        sequence=len(document_steps) + 1,
        depends_on=[],
    )
    return document_steps, final_step


def validate_step_dependencies(steps: list[PlanStep]) -> None:
    """Invariante 4: `depends_on` de un PlanStep solo puede referenciar ids
    de otros PlanStep del mismo plan -- nunca de otro plan, nunca del propio
    paso. Hoy se sostiene "por construcción" (ningún endpoint permite fijar
    `depends_on` arbitrariamente), pero sin esta guarda explícita un futuro
    cambio en `application/handlers.py` podría introducir una violación sin
    que ningún test lo detectara (hallazgo menor 1 de la auditoría
    independiente de Hito 4). Se llama antes de persistir un plan recién
    ensamblado (ver `application/handlers.py::handle_generar_execution_plan`)."""

    ids = {s.id for s in steps if s.id is not None}
    for step in steps:
        for dep_id in step.depends_on:
            if step.id is not None and dep_id == step.id:
                raise ExecutionPlanInvariantError(
                    f"El PlanStep {step.id} no puede depender de sí mismo (invariante 4)."
                )
            if dep_id not in ids:
                raise ExecutionPlanInvariantError(
                    f"El PlanStep {step.id} depende de {dep_id}, que no pertenece a este plan (invariante 4)."
                )


def start_plan(*, case_id: int, recommendation_id: int, existing_active: ExecutionPlan | None) -> ExecutionPlan:
    """Crea el `ExecutionPlan` (sin steps todavía -- se agregan aparte, ver
    `build_plan_steps`). Invariante 1 (requiere una Recommendation ACCEPTED)
    ya está garantizada por construcción antes de llegar acá: quien llama
    (`application/handlers.py::handle_generar_execution_plan`) solo obtiene
    `recommendation_id` de `RecommendationRepository.get_accepted_for_case()`,
    cuyo contrato ya filtra por ACCEPTED -- si no hay ninguna, el handler
    levanta `RecommendationNotFound` antes de llegar acá, nunca llama a esta
    función con datos inválidos. Por eso esta función toma `case_id`/
    `recommendation_id` como primitivos, no el aggregate `Recommendation`
    completo -- no necesita importar ningún tipo de `recommendation.domain`
    (corrección de la auditoría independiente de Hito 4: la versión anterior
    importaba `Recommendation`/`RecommendationStatus` solo para repetir una
    verificación que el repositorio ya garantiza, violando la dirección de
    dependencia declarada en docs/HITO_4_DESIGN.md §12 -- "execution_plan/
    application depende de recommendation.domain", no execution_plan/domain).
    Invariante 2: no puede haber ya un ExecutionPlan ACTIVE para este caso
    (`existing_active` lo trae quien orquesta, vía el repositorio -- mismo
    criterio que `Recommendation.accept()` con `existing_accepted`)."""

    if existing_active is not None:
        raise ExecutionPlanInvariantError(
            "Ya existe un ExecutionPlan ACTIVE para este caso (invariante 2)."
        )

    return ExecutionPlan(
        case_id=case_id,
        recommendation_id=recommendation_id,
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

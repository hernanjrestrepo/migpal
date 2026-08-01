"""
Execution Plan — domain: interfaz del repositorio (Sprint 1, Hito 4).

Protocol, mismo criterio que Recommendation -- con la lección de la
auditoría de Hito 3 aplicada desde el día uno: se declara `save()` acá
mismo, no se agrega después cuando `application/` ya lo esté usando (ver
docs/HITO_3_AUDIT.md, hallazgo menor 2).
"""

from __future__ import annotations

from typing import Protocol

from core.execution_plan.domain.aggregates import ExecutionPlan


class ExecutionPlanRepository(Protocol):
    def add(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Persiste un ExecutionPlan nuevo (con sus PlanStep ya armados) y
        dispara `ExecutionPlanCreated`."""
        ...

    def save(self, plan: ExecutionPlan, *, completed_step_id: int | None = None) -> ExecutionPlan:
        """Persiste un ExecutionPlan ya mutado. Si `completed_step_id` se
        pasa, dispara `PlanStepCompleted` para ese paso; si además
        `plan.status == COMPLETED`, dispara también `ExecutionPlanCompleted`.
        Quién decide *cuándo* corresponde completar un paso es
        `application/` (Sprint 2) -- acá solo se persiste y se notifica lo
        que ya fue decidido."""
        ...

    def get_active_for_case(self, case_id: int) -> ExecutionPlan | None: ...

    def get_latest_for_case(self, case_id: int) -> ExecutionPlan | None:
        """El plan del caso, activo o completado -- para "ver mi plan"
        aunque ya haya terminado."""
        ...

    def get_by_id(self, execution_plan_id: int) -> ExecutionPlan | None: ...

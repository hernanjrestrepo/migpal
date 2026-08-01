"""
Execution Plan — infrastructure: persistencia (Sprint 1, Hito 4).

Implementa el Protocol homónimo en domain/repository.py contra Postgres
real -- mismo patrón que RecommendationRepository. `add()` es la única
operación que dispara `ExecutionPlanCreated` (creación inicial); `save()`
dispara `PlanStepCompleted`/`ExecutionPlanCompleted` según lo que ya haya
sido decidido por quien llama (application/, Sprint 2) -- este archivo no
decide nada, solo persiste y notifica.
"""

from __future__ import annotations

from sqlmodel import Session, select

from core.execution_plan.domain.aggregates import ExecutionPlan
from core.execution_plan.domain.value_objects import ExecutionPlanStatus
from core.shared.event_log import persist_event


class ExecutionPlanRepository:
    """Implementación concreta del Protocol homónimo en domain/repository.py."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, plan: ExecutionPlan) -> ExecutionPlan:
        self._session.add(plan)
        self._session.commit()
        self._session.refresh(plan)

        persist_event(
            self._session,
            name="ExecutionPlanCreated",
            payload={
                "case_id": plan.case_id,
                "recommendation_id": plan.recommendation_id,
                "execution_plan_id": plan.id,
            },
        )
        return plan

    def save(self, plan: ExecutionPlan, *, completed_step_id: int | None = None) -> ExecutionPlan:
        self._session.add(plan)
        self._session.commit()
        self._session.refresh(plan)

        if completed_step_id is not None:
            persist_event(
                self._session,
                name="PlanStepCompleted",
                payload={
                    "case_id": plan.case_id,
                    "execution_plan_id": plan.id,
                    "step_id": completed_step_id,
                },
            )

        if plan.status == ExecutionPlanStatus.COMPLETED:
            persist_event(
                self._session,
                name="ExecutionPlanCompleted",
                payload={
                    "case_id": plan.case_id,
                    "execution_plan_id": plan.id,
                    "recommendation_id": plan.recommendation_id,
                },
            )

        return plan

    def get_active_for_case(self, case_id: int) -> ExecutionPlan | None:
        return self._session.exec(
            select(ExecutionPlan).where(
                ExecutionPlan.case_id == case_id,
                ExecutionPlan.status == ExecutionPlanStatus.ACTIVE,
            )
        ).first()

    def get_latest_for_case(self, case_id: int) -> ExecutionPlan | None:
        return self._session.exec(
            select(ExecutionPlan).where(ExecutionPlan.case_id == case_id).order_by(ExecutionPlan.id.desc())
        ).first()

    def get_by_id(self, execution_plan_id: int) -> ExecutionPlan | None:
        return self._session.get(ExecutionPlan, execution_plan_id)

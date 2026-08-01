"""
Execution Plan — estructura del aggregate/entidad (Sprint 1, Hito 4).

Sin DB, sin reglas de dominio (no existen todavía -- Sprint 2). Solo
confirma que ExecutionPlan/PlanStep tienen la forma que dicta
docs/HITO_4_DESIGN.md §2-§4: estados por defecto, relación entre aggregate
y entidad, y que "bloqueado/disponible" NO es un campo -- no hay ningún
atributo de ese tipo en PlanStep.
"""

from core.execution_plan.domain.aggregates import ExecutionPlan, PlanStep
from core.execution_plan.domain.value_objects import ExecutionPlanStatus, PlanStepStatus


def test_execution_plan_defaults_to_active_status():
    plan = ExecutionPlan(case_id=5, recommendation_id=2)
    assert plan.status == ExecutionPlanStatus.ACTIVE
    assert plan.completed_at is None


def test_plan_step_defaults_to_pending_status():
    step = PlanStep(title="CV", description="Preparar CV", sequence=1, depends_on=[])
    assert step.status == PlanStepStatus.PENDING
    assert step.completed_at is None


def test_plan_step_depends_on_defaults_to_empty_list_not_none():
    step = PlanStep(title="CV", description="Preparar CV", sequence=1)
    assert step.depends_on == []


def test_plan_step_has_no_stored_blocked_field():
    """'Bloqueado/disponible' es una propiedad derivada (§4 del diseño),
    no un campo persistido -- si algún día aparece un campo `blocked` en
    PlanStep, es una desviación del diseño aprobado que amerita revisión."""
    step = PlanStep(title="CV", description="Preparar CV", sequence=1)
    assert not hasattr(step, "blocked")
    assert not hasattr(step, "is_blocked")


def test_execution_plan_status_has_exactly_two_states():
    assert {s.value for s in ExecutionPlanStatus} == {"ACTIVE", "COMPLETED"}


def test_plan_step_status_has_exactly_two_states():
    assert {s.value for s in PlanStepStatus} == {"PENDING", "COMPLETED"}

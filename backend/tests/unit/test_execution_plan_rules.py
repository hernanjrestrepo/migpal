"""
Execution Plan — domain rules (Sprint 2, Hito 4).

Funciones puras, sin DB -- confirma que `build_plan_steps`/`start_plan`/
`complete_step` implementan las invariantes 1, 2, 3, 5, 6, 7 de
docs/HITO_4_DESIGN.md §5.
"""

import pytest

from core.execution_plan.domain.aggregates import ExecutionPlan, PlanStep
from core.execution_plan.domain.rules import (
    ExecutionPlanInvariantError,
    ExecutionPlanTransitionError,
    build_plan_steps,
    complete_step,
    start_plan,
)
from core.execution_plan.domain.value_objects import ExecutionPlanStatus, PlanStepStatus
from core.recommendation.domain.rules import accept, build_recommendation, issue
from core.recommendation.domain.value_objects import MigrationRoute, NextStep, RouteEvaluation

ROUTE = MigrationRoute(visa_type="O-1", country="Estados Unidos", fit_score=82.0)
EVALUATION = RouteEvaluation(
    route=ROUTE, strengths=[], risks=[], required_documents=["CV detallado", "Cartas de recomendación"]
)
NEXT_STEP = NextStep(title="Solicitar visa", description="Presentar la solicitud O-1")


def _accepted_recommendation(case_id=5, rec_id=100):
    rec = build_recommendation(
        case_id=case_id,
        assessment_id=1,
        assessment_confidence=1.0,
        primary_evaluation=EVALUATION,
        next_step=NEXT_STEP,
        confidence=0.8,
        rationale=["Señal detectada: experience"],
    )
    rec = accept(issue(rec))
    rec.id = rec_id
    return rec


def _plan_with_steps():
    plan = ExecutionPlan(case_id=5, recommendation_id=100, status=ExecutionPlanStatus.ACTIVE)
    step_a = PlanStep(id=1, execution_plan_id=1, title="CV", description="CV", sequence=1, depends_on=[])
    step_b = PlanStep(id=2, execution_plan_id=1, title="Cartas", description="Cartas", sequence=2, depends_on=[])
    step_final = PlanStep(
        id=3, execution_plan_id=1, title="Visa", description="Visa", sequence=3, depends_on=[1, 2]
    )
    plan.steps = [step_a, step_b, step_final]
    return plan


# ---- build_plan_steps (invariante 7) ----


def test_build_plan_steps_creates_one_step_per_required_document_with_no_dependencies():
    document_steps, _final_step = build_plan_steps(EVALUATION, NEXT_STEP)
    assert [s.title for s in document_steps] == ["CV detallado", "Cartas de recomendación"]
    assert all(s.depends_on == [] for s in document_steps)


def test_build_plan_steps_final_step_derives_from_next_step_and_leaves_depends_on_unresolved():
    _document_steps, final_step = build_plan_steps(EVALUATION, NEXT_STEP)
    assert final_step.title == "Solicitar visa"
    assert final_step.description == "Presentar la solicitud O-1"
    assert final_step.depends_on == []  # se resuelve en application/, no acá (ver docstring del módulo)


def test_build_plan_steps_is_deterministic():
    first_docs, first_final = build_plan_steps(EVALUATION, NEXT_STEP)
    second_docs, second_final = build_plan_steps(EVALUATION, NEXT_STEP)
    assert [s.title for s in first_docs] == [s.title for s in second_docs]
    assert first_final.title == second_final.title


def test_build_plan_steps_with_no_required_documents_produces_only_the_final_step():
    empty_evaluation = RouteEvaluation(route=ROUTE, strengths=[], risks=[], required_documents=[])
    document_steps, final_step = build_plan_steps(empty_evaluation, NEXT_STEP)
    assert document_steps == []
    assert final_step.sequence == 1


# ---- start_plan (invariantes 1, 2) ----


def test_start_plan_raises_if_recommendation_not_accepted():
    rec = issue(
        build_recommendation(
            case_id=5,
            assessment_id=1,
            assessment_confidence=1.0,
            primary_evaluation=EVALUATION,
            next_step=NEXT_STEP,
            confidence=0.8,
            rationale=["x"],
        )
    )
    with pytest.raises(ExecutionPlanInvariantError):
        start_plan(rec, existing_active=None)


def test_start_plan_raises_if_case_already_has_active_plan():
    rec = _accepted_recommendation()
    existing = ExecutionPlan(case_id=rec.case_id, recommendation_id=rec.id)
    with pytest.raises(ExecutionPlanInvariantError):
        start_plan(rec, existing_active=existing)


def test_start_plan_succeeds_with_accepted_recommendation_and_no_active_plan():
    rec = _accepted_recommendation()
    plan = start_plan(rec, existing_active=None)
    assert plan.case_id == rec.case_id
    assert plan.recommendation_id == rec.id
    assert plan.status == ExecutionPlanStatus.ACTIVE
    assert list(plan.steps) == []


# ---- complete_step (invariantes 3, 5, 6) ----


def test_complete_step_marks_step_completed():
    plan = _plan_with_steps()
    complete_step(plan, 1)
    assert plan.steps[0].status == PlanStepStatus.COMPLETED
    assert plan.steps[0].completed_at is not None


def test_complete_step_raises_if_dependency_not_completed():
    plan = _plan_with_steps()
    with pytest.raises(ExecutionPlanInvariantError):
        complete_step(plan, 3)  # depende de 1 y 2, ninguno completado todavía


def test_complete_step_succeeds_once_dependencies_completed():
    plan = _plan_with_steps()
    complete_step(plan, 1)
    complete_step(plan, 2)
    complete_step(plan, 3)  # ya no está bloqueado
    assert plan.steps[2].status == PlanStepStatus.COMPLETED


def test_complete_step_auto_completes_plan_when_last_step_done():
    plan = _plan_with_steps()
    complete_step(plan, 1)
    complete_step(plan, 2)
    assert plan.status == ExecutionPlanStatus.ACTIVE
    complete_step(plan, 3)
    assert plan.status == ExecutionPlanStatus.COMPLETED
    assert plan.completed_at is not None


def test_complete_step_raises_if_plan_already_completed():
    plan = _plan_with_steps()
    complete_step(plan, 1)
    complete_step(plan, 2)
    complete_step(plan, 3)
    with pytest.raises(ExecutionPlanTransitionError):
        complete_step(plan, 3)


def test_complete_step_raises_if_step_already_completed():
    plan = _plan_with_steps()
    complete_step(plan, 1)
    with pytest.raises(ExecutionPlanTransitionError):
        complete_step(plan, 1)


def test_complete_step_raises_if_step_id_not_in_plan():
    plan = _plan_with_steps()
    with pytest.raises(ExecutionPlanInvariantError):
        complete_step(plan, 999)

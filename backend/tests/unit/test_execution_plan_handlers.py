"""
Execution Plan — application handlers (Sprint 2, Hito 4).

Repositorios en memoria (cumplen el mismo contrato que las versiones reales
contra Postgres, incluida la asignación de ids en `add()`/`save()` -- eso es
justo lo que valida el flujo de dos llamadas de
`handle_generar_execution_plan`, ver su docstring) -- sin DB, mismo criterio
que `tests/unit/test_recommendation_handlers.py`. El adapter real se prueba
contra Postgres real en un sprint posterior (Sprint 3, API).
"""

import pytest

from core.execution_plan.application.commands import CompletarPasoCommand, GenerarExecutionPlanCommand
from core.execution_plan.application.handlers import handle_completar_paso, handle_generar_execution_plan
from core.execution_plan.application.queries import ConsultarMiPlanQuery, handle_consultar_mi_plan
from core.execution_plan.domain.rules import ExecutionPlanInvariantError
from core.execution_plan.domain.value_objects import ExecutionPlanStatus, PlanStepStatus
from core.recommendation.domain.rules import accept, build_recommendation, issue
from core.recommendation.domain.value_objects import MigrationRoute, NextStep, RouteEvaluation
from core.shared.exceptions import ExecutionPlanNotFound

ROUTE = MigrationRoute(visa_type="O-1", country="Estados Unidos", fit_score=82.0)
EVALUATION = RouteEvaluation(
    route=ROUTE, strengths=[], risks=[], required_documents=["CV detallado", "Cartas de recomendación"]
)
NEXT_STEP = NextStep(title="Solicitar visa", description="Presentar la solicitud O-1")


class _InMemoryRecommendationRepository:
    """Mismo Protocol que la versión real -- ver
    tests/unit/test_recommendation_handlers.py, misma implementación."""

    def __init__(self):
        self._by_id = {}
        self._next_id = 1

    def add(self, recommendation):
        recommendation.id = self._next_id
        self._next_id += 1
        self._by_id[recommendation.id] = recommendation
        return recommendation

    def save(self, recommendation):
        if recommendation.id is None:
            return self.add(recommendation)
        self._by_id[recommendation.id] = recommendation
        return recommendation

    def get_latest_for_case(self, case_id):
        matches = [r for r in self._by_id.values() if r.case_id == case_id]
        return max(matches, key=lambda r: r.id) if matches else None

    def get_by_id(self, recommendation_id):
        return self._by_id.get(recommendation_id)

    def get_accepted_for_case(self, case_id):
        for r in self._by_id.values():
            if r.case_id == case_id and r.status.value == "ACCEPTED":
                return r
        return None


class _InMemoryExecutionPlanRepository:
    """Mismo Protocol que `core/execution_plan/domain/repository.py` --
    asigna ids incrementales a plan y pasos en `add()`/`save()`, igual que
    lo haría Postgres al insertar (necesario para probar el flujo de dos
    llamadas de `handle_generar_execution_plan`)."""

    def __init__(self):
        self._plans = {}
        self._next_plan_id = 1
        self._next_step_id = 1

    def add(self, plan):
        plan.id = self._next_plan_id
        self._next_plan_id += 1
        for step in plan.steps:
            step.id = self._next_step_id
            self._next_step_id += 1
            step.execution_plan_id = plan.id
        self._plans[plan.id] = plan
        return plan

    def save(self, plan, *, completed_step_id=None):
        for step in plan.steps:
            if step.id is None:
                step.id = self._next_step_id
                self._next_step_id += 1
                step.execution_plan_id = plan.id
        self._plans[plan.id] = plan
        return plan

    def get_active_for_case(self, case_id):
        return next(
            (p for p in self._plans.values() if p.case_id == case_id and p.status == ExecutionPlanStatus.ACTIVE),
            None,
        )

    def get_latest_for_case(self, case_id):
        matches = [p for p in self._plans.values() if p.case_id == case_id]
        return max(matches, key=lambda p: p.id) if matches else None

    def get_by_id(self, execution_plan_id):
        return self._plans.get(execution_plan_id)


def _accepted_recommendation(repo, case_id=5):
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
    return repo.add(rec)


# ---- handle_generar_execution_plan ----


def test_handle_generar_execution_plan_persists_plan_with_steps_derived_from_recommendation():
    rec_repo = _InMemoryRecommendationRepository()
    plan_repo = _InMemoryExecutionPlanRepository()
    rec = _accepted_recommendation(rec_repo, case_id=5)

    plan = handle_generar_execution_plan(GenerarExecutionPlanCommand(case_id=5), plan_repo, rec_repo)

    assert plan.id is not None
    assert plan.case_id == 5
    assert plan.recommendation_id == rec.id
    assert plan.status == ExecutionPlanStatus.ACTIVE
    assert {s.title for s in plan.steps} == {"CV detallado", "Cartas de recomendación", "Solicitar visa"}
    assert all(s.id is not None for s in plan.steps)


def test_handle_generar_execution_plan_final_step_depends_on_real_document_step_ids():
    rec_repo = _InMemoryRecommendationRepository()
    plan_repo = _InMemoryExecutionPlanRepository()
    _accepted_recommendation(rec_repo, case_id=5)

    plan = handle_generar_execution_plan(GenerarExecutionPlanCommand(case_id=5), plan_repo, rec_repo)

    final_step = next(s for s in plan.steps if s.title == "Solicitar visa")
    document_ids = {s.id for s in plan.steps if s.title != "Solicitar visa"}
    assert set(final_step.depends_on) == document_ids


def test_handle_generar_execution_plan_raises_if_no_accepted_recommendation():
    rec_repo = _InMemoryRecommendationRepository()
    plan_repo = _InMemoryExecutionPlanRepository()

    with pytest.raises(ExecutionPlanInvariantError):
        handle_generar_execution_plan(GenerarExecutionPlanCommand(case_id=5), plan_repo, rec_repo)


def test_handle_generar_execution_plan_raises_if_case_already_has_active_plan():
    rec_repo = _InMemoryRecommendationRepository()
    plan_repo = _InMemoryExecutionPlanRepository()
    _accepted_recommendation(rec_repo, case_id=5)
    handle_generar_execution_plan(GenerarExecutionPlanCommand(case_id=5), plan_repo, rec_repo)

    with pytest.raises(ExecutionPlanInvariantError):
        handle_generar_execution_plan(GenerarExecutionPlanCommand(case_id=5), plan_repo, rec_repo)


# ---- handle_completar_paso ----


def test_handle_completar_paso_completes_available_step():
    rec_repo = _InMemoryRecommendationRepository()
    plan_repo = _InMemoryExecutionPlanRepository()
    _accepted_recommendation(rec_repo, case_id=5)
    plan = handle_generar_execution_plan(GenerarExecutionPlanCommand(case_id=5), plan_repo, rec_repo)
    document_step = next(s for s in plan.steps if s.title == "CV detallado")

    result = handle_completar_paso(
        CompletarPasoCommand(execution_plan_id=plan.id, step_id=document_step.id, case_id=5), plan_repo
    )

    completed = next(s for s in result.steps if s.id == document_step.id)
    assert completed.status == PlanStepStatus.COMPLETED


def test_handle_completar_paso_raises_for_wrong_case_id():
    rec_repo = _InMemoryRecommendationRepository()
    plan_repo = _InMemoryExecutionPlanRepository()
    _accepted_recommendation(rec_repo, case_id=5)
    plan = handle_generar_execution_plan(GenerarExecutionPlanCommand(case_id=5), plan_repo, rec_repo)
    document_step = plan.steps[0]

    with pytest.raises(ExecutionPlanNotFound):
        handle_completar_paso(
            CompletarPasoCommand(execution_plan_id=plan.id, step_id=document_step.id, case_id=999), plan_repo
        )


def test_handle_completar_paso_raises_for_blocked_step():
    rec_repo = _InMemoryRecommendationRepository()
    plan_repo = _InMemoryExecutionPlanRepository()
    _accepted_recommendation(rec_repo, case_id=5)
    plan = handle_generar_execution_plan(GenerarExecutionPlanCommand(case_id=5), plan_repo, rec_repo)
    final_step = next(s for s in plan.steps if s.title == "Solicitar visa")

    with pytest.raises(ExecutionPlanInvariantError):
        handle_completar_paso(
            CompletarPasoCommand(execution_plan_id=plan.id, step_id=final_step.id, case_id=5), plan_repo
        )


# ---- handle_consultar_mi_plan ----


def test_handle_consultar_mi_plan_returns_view_with_blocked_computed():
    rec_repo = _InMemoryRecommendationRepository()
    plan_repo = _InMemoryExecutionPlanRepository()
    _accepted_recommendation(rec_repo, case_id=5)
    plan = handle_generar_execution_plan(GenerarExecutionPlanCommand(case_id=5), plan_repo, rec_repo)

    view = handle_consultar_mi_plan(ConsultarMiPlanQuery(case_id=5), plan_repo)

    assert view is not None
    assert view.total_count == 3
    assert view.completed_count == 0
    final_view = next(s for s in view.steps if s.title == "Solicitar visa")
    assert final_view.blocked is True
    assert set(final_view.blocked_by) == {s.id for s in plan.steps if s.title != "Solicitar visa"}
    document_view = next(s for s in view.steps if s.title == "CV detallado")
    assert document_view.blocked is False


def test_handle_consultar_mi_plan_returns_none_if_no_plan_exists():
    plan_repo = _InMemoryExecutionPlanRepository()
    assert handle_consultar_mi_plan(ConsultarMiPlanQuery(case_id=5), plan_repo) is None

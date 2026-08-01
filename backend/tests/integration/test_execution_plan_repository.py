"""
Execution Plan — repositorio contra Postgres real (Sprint 1, Hito 4).

Alcance exacto de Sprint 1 (docs/HITO_4_DESIGN.md): Aggregate, entidad,
repositorio, persistencia, eventos. Sin reglas de dominio (eso es Sprint
2) -- estos tests construyen ExecutionPlan/PlanStep directamente, sin pasar
por ninguna función de invariantes (no existen todavía a propósito).
"""

import uuid

import pytest
from sqlmodel import Session

from app.db.session import engine
from app.models.user import User
from app.utils.password import get_password_hash
from core.case_engine.domain.aggregates import MigrationCase
from core.decision_engine.domain.aggregates import Assessment
from core.execution_plan.domain.aggregates import ExecutionPlan, PlanStep
from core.execution_plan.domain.value_objects import ExecutionPlanStatus, PlanStepStatus
from core.execution_plan.infrastructure.repository import ExecutionPlanRepository
from core.recommendation.domain.rules import accept, build_recommendation, issue
from core.recommendation.domain.value_objects import MigrationRoute, NextStep, RouteEvaluation
from core.recommendation.infrastructure.repository import RecommendationRepository
from core.shared.event_log import get_event_log

ROUTE = MigrationRoute(visa_type="O-1", country="Estados Unidos", fit_score=82.0)
EVALUATION = RouteEvaluation(
    route=ROUTE, strengths=[], risks=[], required_documents=["CV detallado", "Cartas de recomendación"]
)
NEXT_STEP = NextStep(title="Solicitar visa", description="Presentar la solicitud O-1")


@pytest.fixture
def accepted_recommendation():
    """Crea User -> MigrationCase -> Assessment -> Recommendation ACCEPTED
    reales en Postgres -- las FKs obligatorias de ExecutionPlan (invariante
    1 del diseño, aunque no se valide todavía en código -- Sprint 2)."""
    with Session(engine) as session:
        suffix = uuid.uuid4().hex[:8]
        user = User(
            email=f"exec_plan_test_{suffix}@example.com",
            username=f"exec_plan_test_{suffix}",
            hashed_password=get_password_hash("Passw0rd!"),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        case = MigrationCase(user_id=user.id)
        session.add(case)
        session.commit()
        session.refresh(case)

        assessment = Assessment(
            case_id=case.id, score=100.0, confidence=1.0, findings=["Señal detectada: experience"], recommendations=[]
        )
        session.add(assessment)
        session.commit()
        session.refresh(assessment)

        rec_repo = RecommendationRepository(session)
        rec = rec_repo.add(
            build_recommendation(
                case_id=case.id,
                assessment_id=assessment.id,
                assessment_confidence=assessment.confidence,
                primary_evaluation=EVALUATION,
                next_step=NEXT_STEP,
                confidence=0.8,
                rationale=["Señal detectada: experience"],
            )
        )
        rec = issue(rec)
        rec = accept(rec)
        rec = rec_repo.save(rec)

        yield case, rec


def _new_plan_with_steps(case_id: int, recommendation_id: int) -> ExecutionPlan:
    plan = ExecutionPlan(case_id=case_id, recommendation_id=recommendation_id)
    plan.steps = [
        PlanStep(title="CV detallado", description="Preparar CV", sequence=1, depends_on=[]),
        PlanStep(title="Cartas de recomendación", description="Conseguir cartas", sequence=2, depends_on=[]),
        PlanStep(title="Solicitar visa", description="Presentar la solicitud O-1", sequence=3, depends_on=[]),
    ]
    return plan


def test_add_persists_plan_with_its_steps_and_emits_execution_plan_created(accepted_recommendation):
    case, rec = accepted_recommendation
    with Session(engine) as session:
        repo = ExecutionPlanRepository(session)
        saved = repo.add(_new_plan_with_steps(case.id, rec.id))

        assert saved.id is not None
        assert saved.status == ExecutionPlanStatus.ACTIVE

        fetched = repo.get_by_id(saved.id)
        assert fetched is not None
        assert len(fetched.steps) == 3
        assert {s.title for s in fetched.steps} == {"CV detallado", "Cartas de recomendación", "Solicitar visa"}

        events = get_event_log(session, name="ExecutionPlanCreated", limit=50)
        matching = [e for e in events if e.payload and f'"execution_plan_id": {saved.id}' in e.payload]
        assert len(matching) == 1


def test_get_active_for_case_finds_the_active_plan(accepted_recommendation):
    case, rec = accepted_recommendation
    with Session(engine) as session:
        repo = ExecutionPlanRepository(session)
        saved = repo.add(_new_plan_with_steps(case.id, rec.id))

        active = repo.get_active_for_case(case.id)
        assert active is not None
        assert active.id == saved.id


def test_get_latest_for_case_returns_the_most_recent_plan(accepted_recommendation):
    case, rec = accepted_recommendation
    with Session(engine) as session:
        repo = ExecutionPlanRepository(session)
        first = repo.add(_new_plan_with_steps(case.id, rec.id))
        second = repo.add(_new_plan_with_steps(case.id, rec.id))

        latest = repo.get_latest_for_case(case.id)
        assert latest.id == second.id
        assert latest.id != first.id


def test_save_with_completed_step_id_emits_plan_step_completed_only(accepted_recommendation):
    case, rec = accepted_recommendation
    with Session(engine) as session:
        repo = ExecutionPlanRepository(session)
        plan = repo.add(_new_plan_with_steps(case.id, rec.id))

        step = plan.steps[0]
        step.status = PlanStepStatus.COMPLETED
        repo.save(plan, completed_step_id=step.id)

        step_events = get_event_log(session, name="PlanStepCompleted", limit=50)
        matching_step = [e for e in step_events if e.payload and f'"step_id": {step.id}' in e.payload]
        assert len(matching_step) == 1

        plan_completed_events = get_event_log(session, name="ExecutionPlanCompleted", limit=50)
        matching_plan = [
            e for e in plan_completed_events if e.payload and f'"execution_plan_id": {plan.id}' in e.payload
        ]
        assert matching_plan == []  # el plan sigue ACTIVE -- no todos los pasos están completos


def test_save_with_plan_completed_emits_execution_plan_completed_too(accepted_recommendation):
    case, rec = accepted_recommendation
    with Session(engine) as session:
        repo = ExecutionPlanRepository(session)
        plan = repo.add(_new_plan_with_steps(case.id, rec.id))

        last_step = plan.steps[-1]
        last_step.status = PlanStepStatus.COMPLETED
        plan.status = ExecutionPlanStatus.COMPLETED
        repo.save(plan, completed_step_id=last_step.id)

        reread = repo.get_by_id(plan.id)
        assert reread.status == ExecutionPlanStatus.COMPLETED

        events = get_event_log(session, name="ExecutionPlanCompleted", limit=50)
        matching = [e for e in events if e.payload and f'"execution_plan_id": {plan.id}' in e.payload]
        assert len(matching) == 1


def test_save_without_completed_step_id_emits_no_step_event(accepted_recommendation):
    """`save()` es genérico -- si nadie le dice que se completó un paso, no
    inventa un evento (Sprint 1 no decide negocio, solo persiste lo que se
    le pide)."""
    case, rec = accepted_recommendation
    with Session(engine) as session:
        repo = ExecutionPlanRepository(session)
        plan = repo.add(_new_plan_with_steps(case.id, rec.id))

        repo.save(plan)

        events = get_event_log(session, name="PlanStepCompleted", limit=200)
        matching = [e for e in events if e.payload and f'"execution_plan_id": {plan.id}' in e.payload]
        assert matching == []

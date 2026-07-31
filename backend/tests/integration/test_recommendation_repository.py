"""
Recommendation — repositorio contra Postgres real (Sprint 2, Hito 3).

A diferencia de tests/unit/test_recommendation_domain.py (sin DB), estos
tests usan `app.db.session.engine` real -- el mismo motor que usa la app
(Postgres en docker-compose, ver conftest.py). Verifican persistencia,
consultas y que `save()` dispara el evento correcto según el status.
"""

import uuid

import pytest
from sqlmodel import Session

from app.db.session import engine
from app.models.user import User
from app.utils.password import get_password_hash
from core.case_engine.domain.aggregates import MigrationCase
from core.decision_engine.domain.aggregates import Assessment
from core.recommendation.domain.rules import accept, build_recommendation, discard, issue
from core.recommendation.domain.value_objects import MigrationRoute, NextStep, RouteEvaluation
from core.recommendation.infrastructure.repository import RecommendationRepository
from core.shared.event_log import get_event_log

ROUTE = MigrationRoute(visa_type="O-1", country="Estados Unidos", fit_score=82.0)
EVALUATION = RouteEvaluation(route=ROUTE, strengths=["Experiencia sólida"], risks=[], required_documents=["CV"])
NEXT_STEP = NextStep(title="Perfilamiento completo", description="Documentar logros para O-1")


@pytest.fixture
def case_and_assessment():
    """Crea User -> MigrationCase -> Assessment reales en Postgres -- las
    FKs obligatorias de Recommendation (invariante 1 del diseño)."""
    with Session(engine) as session:
        suffix = uuid.uuid4().hex[:8]
        user = User(
            email=f"repo_test_{suffix}@example.com",
            username=f"repo_test_{suffix}",
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
            case_id=case.id,
            score=100.0,
            confidence=0.9,
            findings=["Señal detectada: experience"],
            recommendations=["Continuar con el Perfilamiento."],
        )
        session.add(assessment)
        session.commit()
        session.refresh(assessment)

        yield case, assessment


def _new_recommendation(case, assessment):
    return build_recommendation(
        case_id=case.id,
        assessment_id=assessment.id,
        assessment_confidence=assessment.confidence,
        primary_evaluation=EVALUATION,
        next_step=NEXT_STEP,
        confidence=0.8,
        rationale=["Señal detectada: experience"],
    )


def test_add_persists_and_get_by_id_reads_it_back(case_and_assessment):
    case, assessment = case_and_assessment
    with Session(engine) as session:
        repo = RecommendationRepository(session)
        saved = repo.add(_new_recommendation(case, assessment))

        assert saved.id is not None
        fetched = repo.get_by_id(saved.id)
        assert fetched is not None
        assert fetched.case_id == case.id
        assert fetched.assessment_id == assessment.id
        assert fetched.primary_route_evaluation() == EVALUATION
        assert fetched.next_step_detail() == NEXT_STEP


def test_get_latest_for_case_returns_the_most_recent_one(case_and_assessment):
    case, assessment = case_and_assessment
    with Session(engine) as session:
        repo = RecommendationRepository(session)
        first = repo.add(_new_recommendation(case, assessment))
        second = repo.add(_new_recommendation(case, assessment))

        latest = repo.get_latest_for_case(case.id)
        assert latest.id == second.id
        assert latest.id != first.id


def test_save_on_issued_persists_status_and_appends_recommendation_issued_event(case_and_assessment):
    case, assessment = case_and_assessment
    with Session(engine) as session:
        repo = RecommendationRepository(session)
        rec = repo.add(_new_recommendation(case, assessment))
        issued = issue(rec)
        repo.save(issued)

        reread = repo.get_by_id(issued.id)
        assert reread.status.value == "ISSUED"

        events = get_event_log(session, name="RecommendationIssued", limit=50)
        matching = [e for e in events if e.payload and f'"recommendation_id": {issued.id}' in e.payload]
        assert len(matching) == 1, "debe existir exactamente un RecommendationIssued para este id"


def test_save_on_accepted_appends_recommendation_accepted_event_and_get_accepted_for_case_finds_it(
    case_and_assessment,
):
    case, assessment = case_and_assessment
    with Session(engine) as session:
        repo = RecommendationRepository(session)
        rec = repo.add(_new_recommendation(case, assessment))
        repo.save(issue(rec))
        repo.save(accept(rec))

        found = repo.get_accepted_for_case(case.id)
        assert found is not None
        assert found.id == rec.id
        assert found.decided_at is not None

        events = get_event_log(session, name="RecommendationAccepted", limit=50)
        matching = [e for e in events if e.payload and f'"recommendation_id": {rec.id}' in e.payload]
        assert len(matching) == 1


def test_save_on_discarded_appends_recommendation_discarded_event(case_and_assessment):
    case, assessment = case_and_assessment
    with Session(engine) as session:
        repo = RecommendationRepository(session)
        rec = repo.add(_new_recommendation(case, assessment))
        repo.save(issue(rec))
        repo.save(discard(rec))

        reread = repo.get_by_id(rec.id)
        assert reread.status.value == "DISCARDED"

        events = get_event_log(session, name="RecommendationDiscarded", limit=50)
        matching = [e for e in events if e.payload and f'"recommendation_id": {rec.id}' in e.payload]
        assert len(matching) == 1


def test_add_does_not_emit_any_event_while_still_in_draft(case_and_assessment):
    """`add()` persiste el DRAFT inicial sin evento -- los eventos existen
    para ISSUED/ACCEPTED/DISCARDED (§8 del diseño), no para el estado
    interno transitorio."""
    case, assessment = case_and_assessment
    with Session(engine) as session:
        repo = RecommendationRepository(session)
        rec = repo.add(_new_recommendation(case, assessment))

        events = get_event_log(session, limit=200)
        matching = [e for e in events if e.payload and f'"recommendation_id": {rec.id}' in e.payload]
        assert matching == []

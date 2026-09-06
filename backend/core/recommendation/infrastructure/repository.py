"""
Recommendation — infrastructure: persistencia (Sprint 2, Hito 3).

Implementa `core.recommendation.domain.repository.RecommendationRepository`
contra Postgres real -- mismo patrón que `AssessmentRepository`
(core/decision_engine/infrastructure/repository.py).

`save()` es distinto de `add()`: `add()` persiste una Recommendation nueva
(normalmente en DRAFT, sin evento todavía); `save()` persiste una transición
de estado ya aplicada por `domain.rules` (issue/accept/discard) y dispara el
evento correspondiente -- solo entonces, nunca en DRAFT (§8 del diseño: los
eventos existen para ISSUED/ACCEPTED/DISCARDED, no para el estado interno
transitorio).
"""

from __future__ import annotations

from sqlmodel import Session, select

from core.recommendation.domain.aggregates import Recommendation
from core.recommendation.domain.value_objects import RecommendationStatus
from core.shared.event_log import persist_event

_EVENT_BY_STATUS = {
    RecommendationStatus.ISSUED: "RecommendationIssued",
    RecommendationStatus.ACCEPTED: "RecommendationAccepted",
    RecommendationStatus.DISCARDED: "RecommendationDiscarded",
}


class RecommendationRepository:
    """Implementación concreta del Protocol homónimo en domain/repository.py."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, recommendation: Recommendation) -> Recommendation:
        self._session.add(recommendation)
        self._session.commit()
        self._session.refresh(recommendation)
        return recommendation

    def save(self, recommendation: Recommendation) -> Recommendation:
        self._session.add(recommendation)
        self._session.commit()
        self._session.refresh(recommendation)

        event_name = _EVENT_BY_STATUS.get(recommendation.status)
        if event_name:
            persist_event(
                self._session,
                name=event_name,
                payload={
                    "case_id": recommendation.case_id,
                    "assessment_id": recommendation.assessment_id,
                    "recommendation_id": recommendation.id,
                    "status": recommendation.status.value,
                },
            )
        return recommendation

    def save_route_selection(self, recommendation: Recommendation) -> Recommendation:
        """Persiste una Recommendation tras `domain.rules.select_route`
        (A-ADR-009). No reutiliza `save()`: la Recommendation sigue en
        ISSUED (no hay transición de estado), y `_EVENT_BY_STATUS` mapea
        ISSUED a "RecommendationIssued" -- reusar `save()` acá emitiría ese
        evento de nuevo como si se hubiera vuelto a emitir la Recommendation,
        lo cual no es lo que pasó. Se dispara "RecommendationRouteSelected"
        explícitamente en su lugar."""
        self._session.add(recommendation)
        self._session.commit()
        self._session.refresh(recommendation)

        primary = recommendation.primary_route_evaluation()
        persist_event(
            self._session,
            name="RecommendationRouteSelected",
            payload={
                "case_id": recommendation.case_id,
                "recommendation_id": recommendation.id,
                "chosen_route": {"visa_type": primary.route.visa_type, "country": primary.route.country},
            },
        )
        return recommendation

    def get_latest_for_case(self, case_id: int) -> Recommendation | None:
        return self._session.exec(
            select(Recommendation)
            .where(Recommendation.case_id == case_id)
            .order_by(Recommendation.id.desc())
        ).first()

    def get_by_id(self, recommendation_id: int) -> Recommendation | None:
        return self._session.get(Recommendation, recommendation_id)

    def get_accepted_for_case(self, case_id: int) -> Recommendation | None:
        return self._session.exec(
            select(Recommendation).where(
                Recommendation.case_id == case_id,
                Recommendation.status == RecommendationStatus.ACCEPTED,
            )
        ).first()

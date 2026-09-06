"""
Recommendation — domain: interfaz del repositorio (Sprint 1, Hito 3).

Protocol, no ABC -- consistente con que el resto del proyecto tipa contra
estructura, no contra herencia. Sin implementación acá: `AssessmentRepository`
(Sprint 2) implementará este contrato contra Postgres real; los tests de
Sprint 1 pueden usar cualquier objeto que cumpla este Protocol (p. ej. un
repositorio en memoria) sin tocar la base de datos.
"""

from __future__ import annotations

from typing import Protocol

from core.recommendation.domain.aggregates import Recommendation


class RecommendationRepository(Protocol):
    def add(self, recommendation: Recommendation) -> Recommendation:
        """Persiste una Recommendation nueva (normalmente en DRAFT, sin
        disparar evento). Ver `save()` para persistir una transición de
        estado ya aplicada."""
        ...

    def save(self, recommendation: Recommendation) -> Recommendation:
        """Persiste una Recommendation ya transicionada (issue/accept/discard)
        y dispara el evento de dominio correspondiente según su `status`
        (`RecommendationIssued`/`Accepted`/`Discarded`) -- nunca en DRAFT.
        Ver `infrastructure/repository.py::save()` para la implementación
        real contra Postgres. Agregado explícitamente al Protocol (auditoría
        de cierre de Hito 3, 2026-07-31): `application/handlers.py` depende
        de este método para toda transición de estado -- el contrato de
        dominio debe declararlo, no solo `add()`."""
        ...

    def save_route_selection(self, recommendation: Recommendation) -> Recommendation:
        """Persiste una Recommendation tras `domain.rules.select_route`
        (A-ADR-009) y dispara `RecommendationRouteSelected`. Separado de
        `save()` porque la Recommendation sigue en ISSUED (no hay transición
        de estado que `_EVENT_BY_STATUS` pueda mapear correctamente)."""
        ...

    def get_latest_for_case(self, case_id: int) -> Recommendation | None:
        """Última Recommendation del caso, sin importar su status."""
        ...

    def get_by_id(self, recommendation_id: int) -> Recommendation | None: ...

    def get_accepted_for_case(self, case_id: int) -> Recommendation | None:
        """La Recommendation ACCEPTED del caso, si existe -- usado para
        validar la invariante 6 (una sola ACCEPTED por caso) antes de
        llamar a `domain.rules.accept()`."""
        ...

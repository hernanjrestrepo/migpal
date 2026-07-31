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
        """Persiste (o actualiza) la Recommendation y devuelve la instancia persistida."""
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

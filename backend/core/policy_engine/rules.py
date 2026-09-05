"""
Policy Engine — filtrado y enriquecimiento de rutas candidatas (Sprint 3, Hito 3).

Determinístico, sin LLM (regla obligatoria 08, heredada por Recommendation
como invariante 7 -- ver docs/RECOMMENDATION_DESIGN.md §2). Calcula el
`fit_score` de cada ruta vía Decision Engine (`score_route_fit`), aplica la
única regla de negocio de este sprint, y enriquece con los datos de
"Knowledge" (hoy: el catálogo placeholder de `policy_engine/catalog.py`).

Regla de negocio: se excluye una ruta candidata si el perfil no tiene
NINGUNA de las señales que esa ruta requiere (`signal_hits == 0`) -- no
tiene sentido proponer una ruta sin ningún indicio de que el perfil la
sustente. Si esa regla dejaría CERO rutas (perfil sin señales detectadas en
absoluto), se desactiva para ese caso puntual y se devuelven todas sin
filtrar, ordenadas por fit_score -- Recommendation siempre necesita al
menos una `primary_evaluation` (invariante 2 del aggregate); no hay un
estado "sin recomendación posible" en el diseño actual.
"""

from __future__ import annotations

from core.decision_engine.infrastructure.scoring import score_route_fit
from core.policy_engine.catalog import ROUTE_CATALOG
from core.recommendation.domain.value_objects import MigrationRoute, RouteEvaluation, RouteSource


def evaluate_candidate_routes(
    *, matched_signals: set[str], objective_country: str | None
) -> list[RouteEvaluation]:
    """Devuelve las rutas candidatas evaluadas, ordenadas por fit_score
    descendente (primera = mejor candidata). Nunca vacío mientras
    ROUTE_CATALOG no lo esté."""

    scored: list[tuple[RouteEvaluation, int]] = []
    for entry in ROUTE_CATALOG:
        fit = score_route_fit(
            matched_signals=matched_signals,
            required_signals=entry["required_signals"],
            route_country=entry["country"],
            objective_country=objective_country,
        )
        signal_hits = sum(1 for signal in entry["required_signals"] if signal in matched_signals)

        route = MigrationRoute(visa_type=entry["visa_type"], country=entry["country"], fit_score=fit)
        evaluation = RouteEvaluation(
            route=route,
            strengths=[entry["strengths_hint"]],
            risks=[entry["risks_hint"]],
            required_documents=list(entry["required_documents"]),
            # Procedencia del dato, hasta el usuario final (A-ADR-008).
            source=RouteSource(
                name=entry["source_name"],
                url=entry["source_url"],
                verified_at=entry["verified_at"],
            ),
        )
        scored.append((evaluation, signal_hits))

    with_any_signal = [ev for ev, hits in scored if hits > 0]
    qualifying = with_any_signal if with_any_signal else [ev for ev, _ in scored]

    return sorted(qualifying, key=lambda ev: ev.route.fit_score, reverse=True)

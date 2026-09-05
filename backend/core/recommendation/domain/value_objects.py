"""
Recommendation — domain: Value Objects + estados.

Ver docs/RECOMMENDATION_DESIGN.md §2 (baseline aprobado 2026-07-30) -- este
módulo es la implementación literal de esa sección, no una reinterpretación.
No modificar la forma de estos VOs sin antes actualizar el diseño (regla del
Hito 3: el diseño solo cambia ante una contradicción objetiva demostrable).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class RecommendationStatus(StrEnum):
    """Ciclo de vida (§2): DRAFT -> ISSUED -> ACCEPTED | DISCARDED. Sin
    estado FAILED -- si el LLM falla, solo se degrada narrative_summary,
    nunca la Recommendation completa (§2, §5)."""

    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    ACCEPTED = "ACCEPTED"
    DISCARDED = "DISCARDED"


class MigrationRoute(BaseModel):
    """VO inmutable -- describe únicamente la alternativa migratoria,
    independiente del caso (§2, refinamiento post-revisión). No lleva
    strengths/risks/required_documents: eso es RouteEvaluation."""

    model_config = ConfigDict(frozen=True)

    visa_type: str
    country: str
    fit_score: float  # [0, 100]


class RouteSource(BaseModel):
    """VO inmutable -- de dónde salió la información de esta ruta y cuándo se
    verificó por última vez contra la fuente oficial (A-ADR-008).

    `verified_at` en `None` significa explícitamente "no se pudo verificar
    contra la fuente": el producto lo muestra distinto a una ruta verificada,
    en vez de presentar ambas como igual de confiables."""

    model_config = ConfigDict(frozen=True)

    name: str
    url: str
    verified_at: str | None = None

    @property
    def is_verified(self) -> bool:
        return bool(self.verified_at)


class RouteEvaluation(BaseModel):
    """VO inmutable -- lo que Recommendation determinó sobre una ruta, para
    este caso, con este Assessment y esta versión de Policy/Knowledge (§2).

    `source` es opcional y aditivo (A-ADR-008): las Recommendation ya
    persistidas, cuyo JSON no tiene la clave, siguen validando sin migración.
    No participa de ninguna decisión -- es metadato de procedencia, no entra
    en `fit_score` ni en `confidence`."""

    model_config = ConfigDict(frozen=True)

    route: MigrationRoute
    strengths: list[str] = []
    risks: list[str] = []
    required_documents: list[str] = []
    source: RouteSource | None = None


class NextStep(BaseModel):
    """VO inmutable -- superficie ampliada a propósito para no romper
    compatibilidad cuando exista un futuro contexto `Plan`/`Task` (§2). Los
    campos marcados como no usados en Hito 3 quedan en su default vacío;
    no se implementa su lógica todavía."""

    model_config = ConfigDict(frozen=True)

    title: str
    description: str
    priority: str | None = None  # no se calcula en Hito 3
    estimated_effort: str | None = None  # no se calcula en Hito 3
    estimated_cost_usd: float | None = None
    blocking: bool = True
    depends_on: list[str] = []  # no se usa en Hito 3 (sin pasos encadenados)

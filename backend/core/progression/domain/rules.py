"""
Progression — domain: niveles, XP e insignias (Sprint 7, Hito 5).

Funciones puras, sin DB -- reciben qué hitos ya ocurrieron (un `set` de
nombres) y devuelven el cálculo. Quien resuelve *si* un hito ocurrió es
`application/handlers.py`, consultando el event log compartido
(`core/shared/event_log.py`) más, para "trámites 100%", el estado real de
Settlement -- no hay un evento por cada avance porcentual, así que ese
hito puntual se resuelve con una consulta de estado, no de historial.

Principio de diseño explícito (Blueprint v2.2, sección de gamificación):
el XP se gana completando algo de valor real -- nunca por abrir la app,
nunca por una racha. Por eso cada hito es un logro de una sola vez (estar
en el set lo activa, repetir el evento no suma XP de nuevo) y no existe
ningún concepto de "días consecutivos" en este módulo."""

from __future__ import annotations

from dataclasses import dataclass

# Nombre sintético para el único hito que no viene de un evento del log,
# sino de una consulta de estado a Settlement (ver docstring del módulo).
SETTLEMENT_COMPLETE_MILESTONE_KEY = "__settlement_complete__"


@dataclass(frozen=True)
class Milestone:
    key: str
    xp: int
    badge_id: str
    badge_label: str


MILESTONES: list[Milestone] = [
    Milestone("AssessmentCompleted", 50, "evaluacion_completa", "Evaluación completa"),
    Milestone("RecommendationAccepted", 100, "ruta_elegida", "Ruta elegida"),
    Milestone("BudgetEstimateCalculated", 30, "presupuesto_calculado", "Presupuesto calculado"),
    Milestone("SettlementChecklistCreated", 20, "tramites_iniciados", "Trámites iniciados"),
    Milestone(SETTLEMENT_COMPLETE_MILESTONE_KEY, 100, "tramites_completos", "Trámites 100% completos"),
    Milestone("GeographicSelectionUpdated", 20, "pais_elegido", "País de destino elegido"),
    Milestone("FamilySurveyResponseSubmitted", 40, "encuesta_familiar", "Encuesta familiar respondida"),
    Milestone("ExecutionPlanCreated", 50, "plan_generado", "Plan de ejecución generado"),
    Milestone("ExecutionPlanCompleted", 150, "plan_completado", "Plan de ejecución completado"),
    Milestone("CommunityPostPublished", 30, "comunidad_activa", "Primera publicación en la comunidad"),
    Milestone("MarketplaceTransactionCompleted", 30, "primera_transaccion", "Primera transacción en el Mercado"),
]

# (umbral de XP acumulado, nombre del nivel) -- ordenado ascendente.
LEVELS: list[tuple[int, str]] = [
    (0, "Nivel 1 · Primeros pasos"),
    (50, "Nivel 2 · Rumbo trazado"),
    (150, "Nivel 3 · Ruta elegida"),
    (250, "Nivel 4 · Instalación en marcha"),
    (400, "Nivel 5 · Casi listo"),
    (600, "Nivel 6 · Listo para radicar"),
]


def level_for_xp(xp: int) -> str:
    current = LEVELS[0][1]
    for threshold, name in LEVELS:
        if xp >= threshold:
            current = name
        else:
            break
    return current


def next_level(xp: int) -> tuple[str, int] | None:
    """Nombre del próximo nivel y cuánto XP falta -- `None` si ya se
    alcanzó el nivel más alto definido."""

    for threshold, name in LEVELS:
        if xp < threshold:
            return name, threshold - xp
    return None


@dataclass(frozen=True)
class Badge:
    badge_id: str
    label: str
    earned: bool


@dataclass(frozen=True)
class ProgressResult:
    xp: int
    level: str
    next_level_name: str | None
    xp_to_next_level: int | None
    badges: list[Badge]


def compute_progress(*, achieved_keys: set[str]) -> ProgressResult:
    earned_milestones = [m for m in MILESTONES if m.key in achieved_keys]
    total_xp = sum(m.xp for m in earned_milestones)
    upcoming = next_level(total_xp)

    return ProgressResult(
        xp=total_xp,
        level=level_for_xp(total_xp),
        next_level_name=upcoming[0] if upcoming else None,
        xp_to_next_level=upcoming[1] if upcoming else None,
        badges=[
            Badge(badge_id=m.badge_id, label=m.badge_label, earned=m.key in achieved_keys) for m in MILESTONES
        ],
    )

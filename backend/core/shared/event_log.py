"""
Event Log persistido (Hito 2, regla 5).

Hasta ahora `core/shared/events.py` (EventBus) solo mantenía el historial en
memoria de un proceso -- útil para desacoplar publishers de subscribers,
inútil para auditoría real (se pierde al reiniciar). Este módulo agrega una
tabla real. No reemplaza EventBus -- se suscribe a él y persiste cada
evento que decide guardar (Hito 2-4: CaseCreated, AssessmentCompleted,
RecommendationIssued, RecommendationAccepted, RecommendationDiscarded,
ExecutionPlanCreated, PlanStepCompleted, ExecutionPlanCompleted. Hito 5:
BudgetEstimateCalculated, SettlementChecklistCreated,
SettlementItemStatusUpdated, GeographicSelectionUpdated,
FamilySurveyResponseSubmitted, CommunityPostPublished,
MarketplaceTransactionCompleted -- Sprint 7 los consume para calcular
niveles/XP, ver core/progression/).

Regla 10 (Constitución): un evento nunca se modifica, solo se agrega uno
nuevo. Esta tabla es append-only por diseño -- no hay UPDATE ni DELETE en
ningún código de este proyecto sobre `domain_events`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, Session, SQLModel, select

PERSISTED_EVENT_NAMES = {
    "CaseCreated",
    "AssessmentCompleted",
    "RecommendationIssued",
    "RecommendationAccepted",
    "RecommendationDiscarded",
    "ExecutionPlanCreated",
    "PlanStepCompleted",
    "ExecutionPlanCompleted",
    "BudgetEstimateCalculated",
    "SettlementChecklistCreated",
    "SettlementItemStatusUpdated",
    "GeographicSelectionUpdated",
    "FamilySurveyResponseSubmitted",
    "CommunityPostPublished",
    "MarketplaceTransactionCompleted",
}


class PersistedDomainEvent(SQLModel, table=True):
    __tablename__ = "domain_events"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    payload: str  # JSON serializado -- sin tabla de payload tipado todavía (Hito 2)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)


def persist_event(session: Session, *, name: str, payload: dict) -> PersistedDomainEvent:
    import json

    row = PersistedDomainEvent(name=name, payload=json.dumps(payload, default=str))
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def get_event_log(
    session: Session, *, name: str | None = None, limit: int = 100
) -> list[PersistedDomainEvent]:
    query = select(PersistedDomainEvent).order_by(PersistedDomainEvent.id.desc()).limit(limit)
    if name:
        query = query.where(PersistedDomainEvent.name == name)
    return list(session.exec(query))

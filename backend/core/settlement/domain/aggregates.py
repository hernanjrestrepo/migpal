"""
Settlement — domain: Aggregate Root SettlementChecklist + entidad
SettlementItem (Sprint 2, Hito 5).

Mismo patrón que ExecutionPlan/PlanStep (ver
core/execution_plan/domain/aggregates.py): `SettlementItem` es una entidad,
no un Value Object, porque se actualiza uno por uno vía
`PATCH /v1/settlement/items/{item_id}`. `typing.List` (no `list`) en la
Relationship y sin `from __future__ import annotations` en este archivo --
misma razón documentada en execution_plan/domain/aggregates.py (SQLAlchemy
2.0 no resuelve `Relationship(List["X"])` con ese import activo).
"""

from datetime import UTC, datetime
from typing import List  # noqa: UP035 -- ver docstring del módulo

from sqlmodel import Field, Relationship, SQLModel

from core.settlement.domain.value_objects import SettlementItemStatus


class SettlementChecklist(SQLModel, table=True):
    """Nace del país de la Recommendation ACCEPTED del caso -- un solo
    checklist por caso (invariante 1, ver domain/rules.py::start_checklist)."""

    __tablename__ = "settlement_checklists"

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="migration_cases.id", index=True, unique=True)
    country: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    items: List["SettlementItem"] = Relationship(back_populates="checklist")  # noqa: UP006, UP035


class SettlementItem(SQLModel, table=True):
    __tablename__ = "settlement_items"

    id: int | None = Field(default=None, primary_key=True)
    checklist_id: int = Field(foreign_key="settlement_checklists.id", index=True)

    title: str
    description: str
    sequence: int

    status: SettlementItemStatus = Field(default=SettlementItemStatus.PENDING, index=True)
    updated_at: datetime | None = Field(default=None)

    checklist: SettlementChecklist | None = Relationship(back_populates="items")

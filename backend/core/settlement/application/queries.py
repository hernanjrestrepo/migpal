"""Settlement — application: consultas (Sprint 2, Hito 5)."""

from __future__ import annotations

from dataclasses import dataclass

from core.settlement.domain.aggregates import SettlementChecklist, SettlementItem
from core.settlement.domain.value_objects import SettlementItemStatus
from core.settlement.infrastructure.repository import SettlementRepository


@dataclass(frozen=True)
class ConsultarMiChecklistQuery:
    case_id: int


@dataclass(frozen=True)
class SettlementItemView:
    id: int
    title: str
    description: str
    sequence: int
    status: SettlementItemStatus
    updated_at: str | None


@dataclass(frozen=True)
class SettlementChecklistView:
    id: int
    case_id: int
    country: str
    items: list[SettlementItemView]
    done_count: int
    total_count: int


def _item_view(item: SettlementItem) -> SettlementItemView:
    return SettlementItemView(
        id=item.id,
        title=item.title,
        description=item.description,
        sequence=item.sequence,
        status=item.status,
        updated_at=item.updated_at.isoformat() if item.updated_at else None,
    )


def build_checklist_view(checklist: SettlementChecklist) -> SettlementChecklistView:
    items = sorted(checklist.items, key=lambda i: i.sequence)
    done = sum(1 for i in items if i.status == SettlementItemStatus.DONE)
    return SettlementChecklistView(
        id=checklist.id,
        case_id=checklist.case_id,
        country=checklist.country,
        items=[_item_view(i) for i in items],
        done_count=done,
        total_count=len(items),
    )


def handle_consultar_mi_checklist(
    query: ConsultarMiChecklistQuery, repo: SettlementRepository
) -> SettlementChecklistView | None:
    checklist = repo.get_for_case(query.case_id)
    if checklist is None:
        return None
    return build_checklist_view(checklist)

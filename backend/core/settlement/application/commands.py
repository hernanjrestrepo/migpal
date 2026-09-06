"""Settlement — application: comandos (Sprint 2, Hito 5)."""

from dataclasses import dataclass

from core.settlement.domain.value_objects import SettlementItemStatus


@dataclass(frozen=True)
class GenerarChecklistCommand:
    case_id: int


@dataclass(frozen=True)
class ActualizarItemCommand:
    checklist_id: int
    item_id: int
    case_id: int
    status: SettlementItemStatus

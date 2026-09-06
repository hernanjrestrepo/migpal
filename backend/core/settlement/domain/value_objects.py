"""Settlement — domain: estados (Sprint 2, Hito 5)."""

from __future__ import annotations

from enum import StrEnum


class SettlementItemStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    NOT_APPLICABLE = "NOT_APPLICABLE"

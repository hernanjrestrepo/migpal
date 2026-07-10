"""Case Engine — value objects (Anexo A, Domain Model)."""

from enum import Enum


class CaseStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"

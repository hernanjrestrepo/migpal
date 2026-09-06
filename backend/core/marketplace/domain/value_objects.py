"""Marketplace — domain: estados y categorías (Sprint 6, Hito 5)."""

from __future__ import annotations

from enum import StrEnum


class ServiceCategory(StrEnum):
    PLOMERIA = "PLOMERIA"
    PINTURA = "PINTURA"
    CUIDADO_INFANTIL = "CUIDADO_INFANTIL"
    MUDANZAS = "MUDANZAS"
    CLASES = "CLASES"
    BELLEZA = "BELLEZA"
    ELECTRICIDAD = "ELECTRICIDAD"
    OTRO = "OTRO"


class TransactionStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

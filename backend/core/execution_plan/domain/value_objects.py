"""
Execution Plan — domain: estados (Sprint 1, Hito 4).

Ver docs/HITO_4_DESIGN.md §4 -- no hay Value Objects compuestos en este
bounded context (a diferencia de Recommendation), solo estos dos enums.
"Bloqueado"/"disponible" NO es un tercer estado acá -- es una propiedad
derivada de `PlanStep.depends_on` + qué está COMPLETED (ver §4 del diseño),
calculada en application/, no almacenada.
"""

from __future__ import annotations

from enum import StrEnum


class ExecutionPlanStatus(StrEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


class PlanStepStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"

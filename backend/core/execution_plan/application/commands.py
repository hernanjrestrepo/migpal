"""Execution Plan — application: comandos (Sprint 2, Hito 4)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerarExecutionPlanCommand:
    case_id: int


@dataclass(frozen=True)
class CompletarPasoCommand:
    execution_plan_id: int
    step_id: int
    case_id: int

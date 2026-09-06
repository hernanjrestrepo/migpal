"""Negocio — application: comandos (Sprint 10, Hito 5)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConectarNegocioCommand:
    case_id: int
    idea_name: str
    idea_description: str
    industry: str | None = None
    country: str | None = None


@dataclass(frozen=True)
class ConsultarJuntaCommand:
    case_id: int
    message: str

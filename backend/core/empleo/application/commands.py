"""Empleo — application: comandos (Sprint 10b, Hito 5)."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConectarEmpleoCommand:
    case_id: int
    name: str
    target_roles: list[str] = field(default_factory=list)
    target_industries: list[str] = field(default_factory=list)
    location_preference: str | None = None
    experience_level: str | None = None
    skills: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BuscarEmpleosCommand:
    case_id: int

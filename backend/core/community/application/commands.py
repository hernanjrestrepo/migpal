"""Community — application: comandos (Sprint 5, Hito 5)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CrearGrupoCommand:
    name: str
    created_by_user_id: int
    description: str | None = None
    city: str | None = None
    country: str | None = None


@dataclass(frozen=True)
class UnirseAGrupoCommand:
    group_id: int
    user_id: int


@dataclass(frozen=True)
class PublicarCommand:
    group_id: int
    author_user_id: int
    body: str


@dataclass(frozen=True)
class ComentarCommand:
    post_id: int
    author_user_id: int
    body: str


@dataclass(frozen=True)
class DarMeGustaCommand:
    post_id: int
    user_id: int


@dataclass(frozen=True)
class QuitarMeGustaCommand:
    post_id: int
    user_id: int

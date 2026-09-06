"""
Community — domain: invariantes (Sprint 5, Hito 5).

Todas son funciones de validación (guard clauses), no transiciones de
estado -- este bounded context no tiene un aggregate con status como
ExecutionPlan/Settlement, son operaciones de alta/baja simples. La razón
para tenerlas en `domain/` igual, en vez de chequearlas directo en
`application/handlers.py`, es la misma de siempre en este repo: que la
regla de negocio sea testeable sin DB y esté en un solo lugar.

Nota de alcance explícita (ver Blueprint v2.1, sección de requisitos duros
para producción): este sprint NO incluye moderación de contenido, ni
humana ni por IA. Un post ofensivo hoy queda visible hasta que alguien lo
borre a mano -- es un backlog real, no un olvido."""

from __future__ import annotations


class CommunityInvariantError(ValueError):
    """Se violó una invariante de Community."""


def validate_can_join(*, already_member: bool) -> None:
    if already_member:
        raise CommunityInvariantError("Ya sos miembro de este grupo.")


def validate_can_post(*, is_member: bool) -> None:
    if not is_member:
        raise CommunityInvariantError("Tenés que unirte al grupo antes de publicar en él.")


def validate_can_comment(*, is_member: bool) -> None:
    if not is_member:
        raise CommunityInvariantError("Tenés que ser miembro del grupo para comentar.")


def validate_can_like(*, is_member: bool, already_liked: bool) -> None:
    if not is_member:
        raise CommunityInvariantError("Tenés que ser miembro del grupo para darle me gusta a una publicación.")
    if already_liked:
        raise CommunityInvariantError("Ya le diste me gusta a esta publicación.")


def validate_can_unlike(*, already_liked: bool) -> None:
    if not already_liked:
        raise CommunityInvariantError("Todavía no le diste me gusta a esta publicación.")

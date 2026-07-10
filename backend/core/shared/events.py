"""
Bus de eventos de dominio (Sprint 1, primer slice).

Implementación en memoria del despachador descrito en el Engineering Handbook
y el Anexo D (Persistence Strategy — outbox pattern): cada evento se
registra aquí; migrar a Redis/una cola real no cambia el contrato
(nombre + payload), solo la implementación de `publish`.

Regla obligatoria 10 (Constitución): un evento nunca se modifica, solo se
agrega uno nuevo. Este módulo no expone ninguna forma de editar un evento
ya publicado -- solo `publish` (agrega) y `subscribe` (escucha).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class DomainEvent:
    """Evento de dominio inmutable. Ver Anexo B (Event Catalog) para la
    clasificación Domain / Integration / Technical de cada nombre."""

    name: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class EventBus:
    """Despachador en memoria. Un proceso, sin garantías de entrega entre
    reinicios -- suficiente para Sprint 1; se reemplaza por una cola real
    sin tocar el código de dominio que llama a `publish`."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[DomainEvent], None]]] = defaultdict(list)
        self._log: list[DomainEvent] = []

    def publish(self, name: str, payload: dict[str, Any]) -> DomainEvent:
        event = DomainEvent(name=name, payload=payload)
        self._log.append(event)
        for handler in self._subscribers.get(name, []):
            handler(event)
        return event

    def subscribe(self, name: str, handler: Callable[[DomainEvent], None]) -> None:
        self._subscribers[name].append(handler)

    def history(self) -> list[DomainEvent]:
        """Solo lectura -- el log es append-only (regla 10)."""
        return list(self._log)


# Instancia única del proceso -- equivalente al "platform/event_bus"
# de la estructura de repositorio del Anexo A.
event_bus = EventBus()

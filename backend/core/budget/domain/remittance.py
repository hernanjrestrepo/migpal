"""
Budget — domain: comparación de remesas (Sprint 3, Hito 5).

Mismo principio que `relocation.py`: las comisiones y el spread cambiario
de cada proveedor (Wise, Remitly, Western Union, banco tradicional...)
cambian todo el tiempo y varían por corredor de envío -- no se hardcodea
ninguna tarifa "real" acá. Quien llama aporta las cotizaciones (a mano hoy,
vía una API de tipo de cambio mañana); este módulo solo calcula cuánto
llega efectivamente a destino y ordena de mejor a peor.

Nota de producto (ver el mock y la conversación con Hernán): la comisión
visible casi nunca es el costo real -- el margen sobre la tasa de cambio
(`spread_percent`) suele pesar más. Por eso el cálculo aplica ambos, no
solo la comisión.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.budget.domain.rules import BudgetInvariantError


@dataclass(frozen=True)
class RemittanceQuote:
    provider_name: str
    fee: float
    spread_percent: float


@dataclass(frozen=True)
class RemittanceResult:
    provider_name: str
    amount_received: float


def estimate_amount_received(*, amount: float, fee: float, spread_percent: float) -> float:
    if amount < 0:
        raise BudgetInvariantError("amount no puede ser negativo.")
    if fee < 0:
        raise BudgetInvariantError("fee no puede ser negativo.")
    if spread_percent < 0:
        raise BudgetInvariantError("spread_percent no puede ser negativo.")
    if fee > amount:
        raise BudgetInvariantError("fee no puede ser mayor que el monto a enviar.")

    after_fee = amount - fee
    return after_fee * (1 - spread_percent / 100)


def compare_remittance_quotes(*, amount: float, quotes: list[RemittanceQuote]) -> list[RemittanceResult]:
    """Ordenado de mayor a menor `amount_received` -- la mejor opción
    primero, no el orden en que se recibieron las cotizaciones."""

    if not quotes:
        raise BudgetInvariantError("Hace falta al menos una cotización para comparar.")

    results = [
        RemittanceResult(
            provider_name=q.provider_name,
            amount_received=estimate_amount_received(amount=amount, fee=q.fee, spread_percent=q.spread_percent),
        )
        for q in quotes
    ]
    return sorted(results, key=lambda r: r.amount_received, reverse=True)

"""
Settlement — domain: plantillas por país e invariantes (Sprint 2, Hito 5).

Cuatro configuraciones fijas, no un motor genérico -- el catálogo de rutas
del piloto está congelado en 4 países (ver docs/HITO_5_DESIGN.md §0 y el
Blueprint v2.0). `COUNTRY_TEMPLATES` usa exactamente los mismos strings de
`country` que `policy_engine/catalog.py` ("Estados Unidos", "Canadá",
"Australia", "España") para poder indexar directo por
`recommendation.primary_route_evaluation().route.country`.

Cada item nombra la institución real que administra el trámite (SSA/IRS,
Service Canada/CRA, ATO, Extranjería/Agencia Tributaria) -- son hechos de
dominio público estables, no cifras que cambien con frecuencia como las
tasas de gobierno (por eso sí se hardcodean acá, a diferencia de
`core/budget`, que deliberadamente no fija esos montos)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from core.settlement.domain.aggregates import SettlementChecklist, SettlementItem
from core.settlement.domain.value_objects import SettlementItemStatus


class SettlementInvariantError(ValueError):
    """Se violó una invariante de SettlementChecklist."""


@dataclass(frozen=True)
class SettlementItemSpec:
    title: str
    description: str


COUNTRY_TEMPLATES: dict[str, list[SettlementItemSpec]] = {
    "Estados Unidos": [
        SettlementItemSpec("Cuenta bancaria", "Abrir una cuenta bancaria en EE. UU."),
        SettlementItemSpec(
            "Social Security Number (SSN)",
            "Tramitar el SSN ante la Social Security Administration (SSA) -- necesario para cobrar tu salario.",
        ),
        SettlementItemSpec(
            "Permiso de trabajo",
            "Con O-1A la autorización de trabajo viene incluida en la aprobación de la visa -- no es un trámite aparte.",
        ),
        SettlementItemSpec(
            "Acceso a salud",
            "No hay cobertura pública universal -- gestionar un seguro propio o de tu empleador.",
        ),
        SettlementItemSpec(
            "Licencia de conducir", "Tramitarla ante el DMV/DPS del estado donde te instalás."
        ),
        SettlementItemSpec(
            "Impuestos", "Declaración federal ante el IRS y, según el estado, declaración estatal."
        ),
    ],
    "Canadá": [
        SettlementItemSpec("Cuenta bancaria", "Abrir una cuenta bancaria en Canadá."),
        SettlementItemSpec(
            "Social Insurance Number (SIN)",
            "Tramitar el SIN ante Service Canada -- necesario para trabajar y para trámites de gobierno.",
        ),
        SettlementItemSpec(
            "Permiso de trabajo",
            "Bajo Express Entry, la residencia permanente aprobada no requiere un permiso de trabajo separado.",
        ),
        SettlementItemSpec(
            "Acceso a salud", "Inscribirte al sistema público provincial de salud -- el tiempo de espera varía por provincia."
        ),
        SettlementItemSpec("Licencia de conducir", "Canje o trámite según la provincia donde te instalás."),
        SettlementItemSpec(
            "Impuestos", "Declaración anual ante la Canada Revenue Agency (CRA)."
        ),
    ],
    "Australia": [
        SettlementItemSpec("Cuenta bancaria", "Abrir una cuenta bancaria en Australia."),
        SettlementItemSpec(
            "Tax File Number (TFN)",
            "Tramitar el TFN ante la Australian Taxation Office (ATO) -- necesario para trabajar y pagar impuestos.",
        ),
        SettlementItemSpec(
            "Permiso de trabajo",
            "La autorización de trabajo viene incluida en la visa Subclass 189 -- no es un trámite aparte.",
        ),
        SettlementItemSpec(
            "Acceso a salud", "Verificar elegibilidad a Medicare según tu tipo de visa."
        ),
        SettlementItemSpec(
            "Licencia de conducir", "Trámite ante la autoridad de tránsito del estado donde te instalás."
        ),
        SettlementItemSpec(
            "Impuestos",
            "Declaración ante la Australian Taxation Office (ATO) -- el año fiscal va de julio a junio.",
        ),
    ],
    "España": [
        SettlementItemSpec("Cuenta bancaria", "Abrir una cuenta bancaria en España."),
        SettlementItemSpec(
            "Número de Identidad de Extranjero (NIE)",
            "Tramitarlo ante la Oficina de Extranjería o la Policía Nacional -- necesario para casi todo trámite.",
        ),
        SettlementItemSpec(
            "Permiso de trabajo",
            "La autorización inicial queda vinculada al empleador que presentó tu solicitud (LO 4/2000).",
        ),
        SettlementItemSpec(
            "Acceso a salud",
            "Acceso al Sistema Nacional de Salud tras tu afiliación a la Seguridad Social.",
        ),
        SettlementItemSpec(
            "Licencia de conducir", "Canje según convenio bilateral con tu país de origen, o examen ante la DGT."
        ),
        SettlementItemSpec("Impuestos", "Declaración de la renta (IRPF) ante la Agencia Tributaria."),
    ],
}


def build_checklist_items(country: str) -> list[SettlementItem]:
    """Invariante 2: solo hay plantilla para los 4 países del catálogo del
    piloto -- un país fuera de esa lista es un error de datos aguas arriba
    (la Recommendation nunca debería producir un país sin ruta en el
    catálogo), no una entrada de usuario a validar con un mensaje amable."""

    template = COUNTRY_TEMPLATES.get(country)
    if template is None:
        raise SettlementInvariantError(
            f"No hay checklist de instalación definido para '{country}' -- el piloto cubre "
            f"{sorted(COUNTRY_TEMPLATES.keys())}."
        )

    return [
        SettlementItem(title=spec.title, description=spec.description, sequence=index)
        for index, spec in enumerate(template, start=1)
    ]


def start_checklist(*, case_id: int, country: str, existing: SettlementChecklist | None) -> SettlementChecklist:
    """Invariante 1: un solo SettlementChecklist por caso -- no tiene
    sentido regenerarlo (a diferencia de Budget, acá no hay "recalcular",
    los trámites que ya marcaste no deberían perderse)."""

    if existing is not None:
        raise SettlementInvariantError(f"El caso {case_id} ya tiene un checklist de instalación.")

    return SettlementChecklist(case_id=case_id, country=country)


def update_item_status(
    checklist: SettlementChecklist, item_id: int, new_status: SettlementItemStatus
) -> SettlementChecklist:
    item = next((i for i in checklist.items if i.id == item_id), None)
    if item is None:
        raise SettlementInvariantError(f"El checklist no tiene ningún item con id {item_id}.")

    item.status = new_status
    item.updated_at = datetime.now(UTC)
    return checklist

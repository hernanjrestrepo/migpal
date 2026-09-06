"""Family Planning — application: comandos (Sprint 4, Hito 5)."""

from dataclasses import dataclass

from core.family_planning.domain.value_objects import PlaceOptionType


@dataclass(frozen=True)
class SeleccionarPaisCommand:
    case_id: int
    country: str


@dataclass(frozen=True)
class SeleccionarEstadoCommand:
    case_id: int
    state: str


@dataclass(frozen=True)
class SeleccionarCiudadCommand:
    case_id: int
    city: str


@dataclass(frozen=True)
class SeleccionarBarrioCommand:
    case_id: int
    neighborhood: str


@dataclass(frozen=True)
class ResponderEncuestaCommand:
    case_id: int
    case_family_member_id: int | None
    is_primary_applicant: bool
    climate_preference: str | None = None
    top_priority: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class AgregarOpcionCommand:
    case_id: int
    option_type: PlaceOptionType
    name: str
    website: str | None = None
    phone: str | None = None
    requirements: str | None = None
    cost_amount: float | None = None
    cost_period: str | None = None
    image_url: str | None = None

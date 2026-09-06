"""
Family Planning — domain (Sprint 4, Hito 5): tres aggregates independientes
bajo el mismo `case_id`, ninguno posee a los otros (mismo principio que
Assessment/Recommendation/ExecutionPlan bajo MigrationCase -- el caso es
operado sobre, no posee).

`GeographicSelection`: un registro por caso, país/estado/ciudad/barrio se
completan en cascada (ver domain/rules.py -- no podés fijar `state` sin
`country`, etc.).

`FamilySurveyResponse`: uno por integrante de la familia que responde,
identificado por `case_family_member_id` (FK a
`core.case_engine.domain.aggregates.CaseFamilyMember`) o, para el titular
del caso (que no aparece como CaseFamilyMember -- ver ese módulo), con
`is_primary_applicant=True` y `case_family_member_id=None`.

`PlaceOption`: colegios o vivienda sugeridos para el caso, con el detalle
que pidió Hernán explícitamente (sitio web, teléfono, requisitos, costo) --
sin foto real todavía (`image_url` queda nullable a propósito: la fuente de
imágenes reales vía API es un requisito de producción confirmado, no algo
que este backend pueda resolver por sí solo, ver docs/HITO_5_DESIGN.md §9
del Blueprint)."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel

from core.family_planning.domain.value_objects import PlaceOptionType


class GeographicSelection(SQLModel, table=True):
    __tablename__ = "geographic_selections"

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="migration_cases.id", index=True, unique=True)

    country: str | None = Field(default=None)
    state: str | None = Field(default=None)
    city: str | None = Field(default=None)
    neighborhood: str | None = Field(default=None)

    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FamilySurveyResponse(SQLModel, table=True):
    __tablename__ = "family_survey_responses"

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="migration_cases.id", index=True)
    case_family_member_id: int | None = Field(default=None, foreign_key="case_family_members.id")
    is_primary_applicant: bool = Field(default=False)

    climate_preference: str | None = Field(default=None)
    top_priority: str | None = Field(default=None)
    notes: str | None = Field(default=None)

    completed: bool = Field(default=False)
    submitted_at: datetime | None = Field(default=None)


class PlaceOption(SQLModel, table=True):
    __tablename__ = "place_options"

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="migration_cases.id", index=True)
    option_type: PlaceOptionType = Field(index=True)

    name: str
    website: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    requirements: str | None = Field(default=None)
    cost_amount: float | None = Field(default=None)
    cost_period: str | None = Field(default=None)  # "anual", "mensual", etc.
    image_url: str | None = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

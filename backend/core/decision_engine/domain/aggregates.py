"""
Decision Engine — domain: Assessment (Hito 2, regla 3).

"Assessment debe convertirse inmediatamente en un Aggregate del Core.
No quiero un JSON perdido." -- persistido, no un dict en memoria.

Regla 4: toda recomendación guarda las versiones que la produjeron, incluso
si hoy son "1.0" -- Policy Engine y Knowledge no existen todavía como
bounded contexts (eso es trabajo futuro), pero el CAMPO existe desde ahora
para que ningún Assessment nazca sin esa trazabilidad.
"""

from datetime import UTC, datetime

from sqlmodel import JSON as SQLModelJSON
from sqlmodel import Column, Field, SQLModel


class Assessment(SQLModel, table=True):
    """Aggregate Root. Vinculado a un MigrationCase, nunca al revés
    (Anexo A: Decision Engine opera sobre el caso, no lo posee)."""

    __tablename__ = "assessments"

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="migration_cases.id", index=True)

    score: float
    confidence: float

    # Listas de strings -- JSON nativo de Postgres, no un campo de texto libre.
    findings: list[str] = Field(sa_column=Column(SQLModelJSON))
    recommendations: list[str] = Field(sa_column=Column(SQLModelJSON))

    # Regla 4 -- trazabilidad de versión, presente desde el primer Assessment.
    decision_engine_version: str = Field(default="1.0")
    policy_version: str = Field(default="1.0")
    knowledge_version: str = Field(default="1.0")

    version: int = Field(default=1)  # reasessments futuros incrementan esto
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

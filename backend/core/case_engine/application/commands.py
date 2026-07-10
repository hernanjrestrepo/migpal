"""Case Engine — application: comandos (DTOs de intención, sin lógica)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OpenCaseCommand:
    user_id: int


@dataclass(frozen=True)
class UpdateObjectiveCommand:
    user_id: int
    objective_country: str | None
    objective_visa_type: str | None


@dataclass(frozen=True)
class AddFamilyMemberCommand:
    user_id: int
    full_name: str
    relationship_type: str

"""Case Engine — application: queries (lectura, sin efectos secundarios)."""

from dataclasses import dataclass

from core.case_engine.domain.aggregates import MigrationCase
from core.case_engine.infrastructure.repository import CaseRepository
from core.shared.exceptions import CaseNotFound


@dataclass(frozen=True)
class GetCaseForUserQuery:
    user_id: int


def handle_get_case_for_user(query: GetCaseForUserQuery, repo: CaseRepository) -> MigrationCase:
    case = repo.get_by_user_id(query.user_id)
    if not case:
        raise CaseNotFound(f"No hay MigrationCase para user_id={query.user_id}")
    return case

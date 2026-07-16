"""Decision Engine — application: queries."""

from dataclasses import dataclass

from core.decision_engine.domain.aggregates import Assessment
from core.decision_engine.infrastructure.repository import AssessmentRepository


@dataclass(frozen=True)
class GetLatestAssessmentQuery:
    case_id: int


def handle_get_latest_assessment(
    query: GetLatestAssessmentQuery, repo: AssessmentRepository
) -> Assessment | None:
    return repo.get_latest_for_case(query.case_id)

"""Recommendation — application: queries."""

from dataclasses import dataclass

from core.recommendation.domain.aggregates import Recommendation
from core.recommendation.infrastructure.repository import RecommendationRepository


@dataclass(frozen=True)
class GetLatestRecommendationQuery:
    case_id: int


def handle_get_latest_recommendation(
    query: GetLatestRecommendationQuery, repo: RecommendationRepository
) -> Recommendation | None:
    return repo.get_latest_for_case(query.case_id)

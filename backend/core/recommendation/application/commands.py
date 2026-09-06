"""Recommendation — application: comandos."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AcceptRecommendationCommand:
    recommendation_id: int
    case_id: int


@dataclass(frozen=True)
class DiscardRecommendationCommand:
    recommendation_id: int
    case_id: int


@dataclass(frozen=True)
class SelectRouteCommand:
    recommendation_id: int
    case_id: int
    alternative_index: int

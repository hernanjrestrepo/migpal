"""
Decision Engine — application: handlers.

`handle_generate_assessment` es puramente determinístico: el mismo
`profile_text` produce siempre el mismo score/confidence/recommendations
(regla obligatoria 08). No importa `core.conversation` ni ningún AI Adapter
-- viola la dirección de dependencias del Handbook (Decision Engine es
Capa 1, Conversation es Capa 2; Capa 1 nunca depende de Capa 2).
"""

from __future__ import annotations

from core.decision_engine.application.commands import GenerateAssessmentCommand
from core.decision_engine.domain.aggregates import Assessment
from core.decision_engine.infrastructure.repository import AssessmentRepository
from core.decision_engine.infrastructure.scoring import recommend_from_score, score_profile_text
from core.shared.events import event_bus


def handle_generate_assessment(cmd: GenerateAssessmentCommand, repo: AssessmentRepository) -> Assessment:
    score, confidence, findings = score_profile_text(cmd.profile_text)
    recommendations = recommend_from_score(score)

    assessment = Assessment(
        case_id=cmd.case_id,
        score=score,
        confidence=confidence,
        findings=findings,
        recommendations=recommendations,
        decision_engine_version="1.0",
        policy_version="1.0",
        knowledge_version="1.0",
    )
    assessment = repo.add(assessment)

    event_bus.publish(
        "AssessmentCompleted",
        {"case_id": cmd.case_id, "assessment_id": assessment.id, "score": score, "confidence": confidence},
    )
    return assessment

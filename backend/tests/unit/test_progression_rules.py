"""Progression — domain rules (Sprint 7, Hito 5). Funciones puras, sin DB."""

from core.progression.domain.rules import (
    SETTLEMENT_COMPLETE_MILESTONE_KEY,
    compute_progress,
    level_for_xp,
    next_level,
)


def test_compute_progress_with_no_milestones_is_level_one_zero_xp():
    result = compute_progress(achieved_keys=set())
    assert result.xp == 0
    assert result.level == "Nivel 1 · Primeros pasos"
    assert all(not b.earned for b in result.badges)


def test_compute_progress_sums_xp_only_for_achieved_milestones():
    result = compute_progress(achieved_keys={"AssessmentCompleted", "RecommendationAccepted"})
    assert result.xp == 150  # 50 + 100
    badge_ids_earned = {b.badge_id for b in result.badges if b.earned}
    assert badge_ids_earned == {"evaluacion_completa", "ruta_elegida"}


def test_compute_progress_ignores_unknown_keys():
    result = compute_progress(achieved_keys={"AlgoQueNoExiste"})
    assert result.xp == 0


def test_compute_progress_includes_settlement_complete_synthetic_milestone():
    result = compute_progress(achieved_keys={SETTLEMENT_COMPLETE_MILESTONE_KEY})
    assert result.xp == 100
    badge = next(b for b in result.badges if b.badge_id == "tramites_completos")
    assert badge.earned is True


def test_compute_progress_repeating_a_milestone_key_does_not_double_count():
    # achieved_keys es un set -- no hay forma de "repetir" una key, lo cual
    # es justamente la garantía que se está probando (una sola vez, nunca más).
    result_once = compute_progress(achieved_keys={"BudgetEstimateCalculated"})
    result_again = compute_progress(achieved_keys={"BudgetEstimateCalculated"})
    assert result_once.xp == result_again.xp == 30


def test_level_for_xp_returns_highest_threshold_reached():
    assert level_for_xp(0) == "Nivel 1 · Primeros pasos"
    assert level_for_xp(49) == "Nivel 1 · Primeros pasos"
    assert level_for_xp(50) == "Nivel 2 · Rumbo trazado"
    assert level_for_xp(150) == "Nivel 3 · Ruta elegida"
    assert level_for_xp(10_000) == "Nivel 6 · Listo para radicar"


def test_next_level_reports_name_and_remaining_xp():
    name, remaining = next_level(30)
    assert name == "Nivel 2 · Rumbo trazado"
    assert remaining == 20


def test_next_level_is_none_at_max_level():
    assert next_level(10_000) is None


def test_all_milestones_produce_a_full_progress_when_all_achieved():
    from core.progression.domain.rules import MILESTONES

    all_keys = {m.key for m in MILESTONES}
    result = compute_progress(achieved_keys=all_keys)
    assert result.xp == sum(m.xp for m in MILESTONES)
    assert all(b.earned for b in result.badges)
    assert result.next_level_name is None

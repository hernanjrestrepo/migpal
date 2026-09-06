"""
Decision Engine — casos dorados (Handbook, Testing Strategy: "mismo caso,
mismos datos, mismo resultado", regla obligatoria 08).

Sin red, sin IA -- `score_profile_text`/`recommend_from_score` son funciones
puras. Si esto se rompe, se rompió la reproducibilidad del scoring, no un
detalle de UI.
"""

from core.decision_engine.infrastructure.scoring import recommend_from_score, score_profile_text


def test_same_text_always_produces_same_score():
    text = "Soy ingeniero con 6 años de experiencia, quiero migrar a Canada con mi familia."

    first = score_profile_text(text)
    second = score_profile_text(text)
    third = score_profile_text(text)

    assert first == second == third


def test_rich_profile_scores_high_with_high_confidence():
    text = (
        "Soy médico con maestría y 8 años de experiencia. Quiero migrar a Canada "
        "con mi esposa e hijos. Tenemos ahorros para el proceso."
    )
    score, confidence, findings = score_profile_text(text)

    assert score == 100.0  # 5/5 señales: experience, education, destination, family, financial
    assert confidence == 1.0
    assert len(findings) == 5


def test_empty_profile_scores_at_base_with_no_signals():
    score, confidence, findings = score_profile_text("Hola")

    assert score == 20.0  # BASE_SCORE, cero señales
    assert confidence == 0.0
    assert findings[0] == "No se detectaron señales claras de perfil en el mensaje."
    # A-ADR-009: explicabilidad -- cero señales detectadas implica las 5
    # categorías reportadas como faltantes.
    assert len(findings) == 1 + 5
    assert all(f.startswith("Señal no detectada:") for f in findings[1:])


def test_missing_signals_are_reported_for_explicability():
    """A-ADR-009 -- `findings` ahora expone también lo que NO se detectó,
    no solo lo detectado (antes, el usuario no tenía forma de saber qué le
    faltaba para mejorar su score)."""
    text = "Soy ingeniero con 6 años de experiencia."
    _, _, findings = score_profile_text(text)

    assert "Señal detectada: experience" in findings
    assert "Señal no detectada: education" in findings
    assert "Señal no detectada: destination" in findings
    assert "Señal no detectada: family" in findings
    assert "Señal no detectada: financial" in findings


def test_missing_signals_from_findings_is_symmetric_to_matched():
    from core.decision_engine.infrastructure.scoring import missing_signals_from_findings

    findings = [
        "Señal detectada: experience",
        "Señal no detectada: education",
        "Señal no detectada: family",
    ]
    assert missing_signals_from_findings(findings) == {"education", "family"}


def test_recommendation_thresholds_are_deterministic():
    assert "Perfilamiento completo" in recommend_from_score(100.0)[0]
    assert "información parcial" in recommend_from_score(60.0)[0]
    assert "más información" in recommend_from_score(20.0)[0]

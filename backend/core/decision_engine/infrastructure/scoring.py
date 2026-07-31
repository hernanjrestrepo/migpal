"""
Decision Engine — scoring determinístico (Hito 2).

Regla obligatoria 08 (Constitución/Handbook): "Toda decisión de negocio
debe ser reproducible: mismo caso, mismos datos, mismo resultado." Estas
funciones son puras -- mismo texto de entrada, siempre el mismo score.
NO llaman a ningún modelo de IA (eso violaría la regla 2: "el Decision
Engine nunca depende del LLM"). Son un placeholder deliberadamente simple
(keyword matching) -- Policy Engine y un modelo de scoring real las
reemplazan más adelante sin cambiar el contrato de `score_profile_text`.

Candidato directo a "caso dorado" (Handbook, Testing Strategy): mismo
texto -> mismo score, en cualquier build futuro.
"""

from __future__ import annotations

SIGNAL_KEYWORDS: dict[str, list[str]] = {
    "experience": [
        "experiencia",
        "años trabajando",
        "trabajo como",
        "profesión",
        "profesion",
        "ingeniero",
        "médico",
        "medico",
        "abogado",
        "desarrollador",
        "años de experiencia",
    ],
    "education": [
        "título",
        "titulo",
        "universidad",
        "maestría",
        "maestria",
        "licenciatura",
        "grado",
        "carrera",
    ],
    "destination": [
        "canadá",
        "canada",
        "españa",
        "espana",
        "estados unidos",
        "usa",
        "alemania",
        "australia",
        "migrar a",
        "quiero ir a",
        "quiero vivir en",
    ],
    "family": ["familia", "esposa", "esposo", "hijos", "pareja"],
    "financial": ["ahorro", "capital", "presupuesto", "dinero", "invertir"],
}

BASE_SCORE = 20.0
POINTS_PER_SIGNAL = 16.0


def score_profile_text(text: str) -> tuple[float, float, list[str]]:
    """Devuelve (score 0-100, confidence 0-1, findings) -- determinístico."""
    text_lower = text.lower()
    matched = [
        category for category, keywords in SIGNAL_KEYWORDS.items() if any(kw in text_lower for kw in keywords)
    ]

    score = min(100.0, BASE_SCORE + POINTS_PER_SIGNAL * len(matched))
    confidence = round(len(matched) / len(SIGNAL_KEYWORDS), 2)

    findings = [f"Señal detectada: {category}" for category in matched]
    if not findings:
        findings = ["No se detectaron señales claras de perfil en el mensaje."]

    return score, confidence, findings


def recommend_from_score(score: float) -> list[str]:
    if score >= 80:
        return ["Tu perfil muestra señales sólidas. Te recomendamos continuar con el Perfilamiento completo."]
    if score >= 50:
        return ["Tu perfil tiene información parcial. Cuéntanos más sobre tu experiencia y destino deseado."]
    return [
        "Necesitamos más información para una evaluación confiable: experiencia, educación y destino deseado."
    ]


def matched_signals_from_findings(findings: list[str]) -> set[str]:
    """Recommendation (Sprint 3, Hito 3) no tiene acceso al `profile_text`
    crudo -- Assessment no lo persiste (regla del diseño §3: "Conversation
    no entra directamente" a Recommendation). Se reconstruyen las señales ya
    detectadas a partir de `Assessment.findings` (formato "Señal detectada:
    {categoría}", ver `score_profile_text`), sin volver a tocar texto libre."""
    return {f.split(":", 1)[1].strip() for f in findings if f.startswith("Señal detectada:")}


DESTINATION_BONUS = 20.0
FIT_SCORE_PER_SIGNAL_RATIO = 80.0


def score_route_fit(
    *, matched_signals: set[str], required_signals: list[str], route_country: str, objective_country: str | None
) -> float:
    """Fit determinístico de UNA ruta candidata contra las señales ya
    detectadas del Assessment + el país objetivo declarado en el
    MigrationCase (§3 del diseño -- ambos son entradas legítimas; el texto
    crudo de Conversation no lo es). Mismo input, siempre el mismo output
    (regla obligatoria 08)."""

    signal_hits = sum(1 for signal in required_signals if signal in matched_signals)
    signal_ratio = (signal_hits / len(required_signals)) if required_signals else 1.0

    destination_bonus = 0.0
    if objective_country and objective_country.strip().lower() == route_country.strip().lower():
        destination_bonus = DESTINATION_BONUS

    return min(100.0, signal_ratio * FIT_SCORE_PER_SIGNAL_RATIO + destination_bonus)

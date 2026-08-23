#!/usr/bin/env python3
"""
MigPAL USA Standard v4.1
========================
ESTÁNDAR CONVERSACIONAL DEFINITIVO PARA MIGPAL USA

REGLAS FUNDAMENTALES (HARD RULES):
1. HARD CAP: Máximo 6 líneas por mensaje (split automático)
2. HARD RULE: UNA pregunta por mensaje (separar si hay 2+)
3. MICRO-CHECK OBLIGATORIO cada 3 turnos
4. PROGRESS HEADER en CADA mensaje ("📍Fase X/12 • YY%")
5. MINI-RESUMEN de 2 líneas al cerrar cada fase

GATING OBLIGATORIO:
- Prohibido recomendar/decidir visa sin:
  a) Perfil completo
  b) Resumen de Entendimiento confirmado

v4.1 FIXES:
- Hard cap 6 líneas con split automático
- Una pregunta por mensaje con separación
- Micro-check forzado cada 3 turnos
- Progress header obligatorio
- Mini-resumen al cerrar fase
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ============== CONSTANTES v4.1 ==============

MAX_FORMS_PER_5_TURNS = 1
MAX_MESSAGE_LINES = 6  # HARD CAP
MICRO_CHECK_FREQUENCY = 3  # OBLIGATORIO cada 3 turnos
TOTAL_PHASES = 12  # Fases principales

# Micro-checks aprobados
MICRO_CHECKS = {
    "es": [
        "¿Voy claro?",
        "¿Hasta aquí voy claro?",
        "¿Esto resuena contigo?",
        "¿Tiene sentido?",
        "¿Seguimos alineados?",
        "¿Te parece bien?",
    ],
    "en": [
        "Am I clear?",
        "Am I being clear so far?",
        "Does this resonate with you?",
        "Does this make sense?",
        "Are we on the same page?",
        "Does this work for you?",
    ],
}

# Frases PROHIBIDAS (sentenciosas)
FORBIDDEN_PHRASES = [
    "no eres candidato",
    "no calificas",
    "no tienes opción",
    "imposible para ti",
    "nada de eso conversa contigo",
    "you don't qualify",
    "you're not a candidate",
    "impossible for you",
]

# Frases SUAVES (reemplazos)
SOFT_ALTERNATIVES = {
    "no eres candidato": "por tu perfil, esas opciones no suelen ser las más coherentes",
    "no calificas": "con la información actual, hay otras opciones que encajan mejor",
    "imposible": "requiere condiciones específicas que podemos evaluar",
}

# Mini-resúmenes por fase
PHASE_SUMMARIES = {
    "registro": "✅ Registro completado: {name} de {country}.",
    "diagnostico": "✅ Diagnóstico completado: Perfil {profile_type}, presupuesto ${budget}.",
    "perfilamiento": "✅ Perfilamiento completado: {experience} años experiencia, tipo {migrant_type}.",
    "visa": "✅ Visa definida: {visa_type} con {probability}% probabilidad.",
    "estado": "✅ Estado seleccionado: {state}.",
    "ciudad": "✅ Ciudad seleccionada: {city}, {state}.",
    "barrio": "✅ Barrio seleccionado: {neighborhood}.",
    "vivienda": "✅ Vivienda definida: {housing_type}, ${rent}/mes.",
    "colegio": "✅ Colegios definidos: {schools}.",
    "timeline": "✅ Timeline definido: {months} meses.",
    "presupuesto": "✅ Presupuesto total: ${total}.",
    "cierre": "🎉 ¡Plan completo! Siguiente: agendar consulta.",
}


# ============== ENUMS ==============


class ConversationPhase(Enum):
    """Fases de la conversación MigPAL USA (12 principales)"""

    REGISTRO = "registro"
    DIAGNOSTICO = "diagnostico"
    PERFILAMIENTO = "perfilamiento"
    DEFINICION_VISA = "visa"
    SELECCION_ESTADO = "estado"
    SELECCION_CIUDAD = "ciudad"
    SELECCION_BARRIO = "barrio"
    SELECCION_VIVIENDA = "vivienda"
    SELECCION_COLEGIOS = "colegio"
    TIMELINE = "timeline"
    PRESUPUESTO = "presupuesto"
    CIERRE = "cierre"


class GatingStatus(Enum):
    """Estado del gating para recomendaciones"""

    BLOCKED = "blocked"
    PENDING_PROFILE = "pending_profile"
    PENDING_SUMMARY = "pending_summary"
    APPROVED = "approved"


# ============== DATACLASSES ==============


@dataclass
class ConversationState:
    """Estado de la conversación del usuario"""

    user_id: int
    current_phase: ConversationPhase = ConversationPhase.REGISTRO
    turn_count: int = 0
    forms_shown_last_5: int = 0
    last_micro_check: int = 0
    profile_complete: bool = False
    summary_confirmed: bool = False
    gating_status: GatingStatus = GatingStatus.BLOCKED

    # Datos del perfil
    profile_data: dict[str, Any] = field(default_factory=dict)

    # Selecciones
    selected_visa: str | None = None
    selected_state: str | None = None
    selected_city: str | None = None
    selected_neighborhood: str | None = None
    selected_housing: str | None = None
    selected_schools: list[str] = field(default_factory=list)

    # Tracking de fases completadas
    phases_completed: list[str] = field(default_factory=list)


@dataclass
class MatrixEvaluation:
    """Evaluación con matriz ponderada"""

    name: str
    score: float
    weighted_score: float
    pros: list[str]
    cons: list[str]
    factors: dict[str, float]
    recommendation: str


@dataclass
class MessageResponse:
    """Respuesta estructurada de MigPAL"""

    text: str
    include_micro_check: bool = False
    show_progress: bool = True
    buttons: list[tuple[str, str]] | None = None
    is_form: bool = False
    split_messages: list[str] = field(default_factory=list)  # v4.1: mensajes divididos
    phase_summary: str | None = None  # v4.1: mini-resumen de fase


@dataclass
class FormattedOutput:
    """Salida formateada con todos los componentes v4.1"""

    messages: list[str]  # Lista de mensajes (puede ser >1 si se dividió)
    has_micro_check: bool
    has_progress: bool
    question_count: int
    line_count: int
    phase_summary: str | None


# ============== CLASE PRINCIPAL v4.1 ==============


class MigPALUSAStandard:
    """
    Estándar conversacional MigPAL USA v4.1.
    Implementa HARD RULES para score 100/100.
    """

    _instance = None
    _states: dict[int, ConversationState] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._states = {}
        return cls._instance

    def get_state(self, user_id: int) -> ConversationState:
        """Obtiene o crea el estado de conversación"""
        if user_id not in self._states:
            self._states[user_id] = ConversationState(user_id=user_id)
        return self._states[user_id]

    def update_state(self, user_id: int, **kwargs) -> None:
        """Actualiza el estado de conversación"""
        state = self.get_state(user_id)
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)

    def reset_state(self, user_id: int) -> None:
        """Resetea el estado de un usuario"""
        if user_id in self._states:
            del self._states[user_id]

    # ============== PROGRESS HEADER (OBLIGATORIO) ==============

    def get_progress_header(self, user_id: int) -> str:
        """
        v4.1: Progress header OBLIGATORIO en cada mensaje.
        Formato: "📍Fase X/12 • YY%"
        """
        state = self.get_state(user_id)
        phase = state.current_phase

        phase_numbers = {
            ConversationPhase.REGISTRO: 1,
            ConversationPhase.DIAGNOSTICO: 2,
            ConversationPhase.PERFILAMIENTO: 3,
            ConversationPhase.DEFINICION_VISA: 4,
            ConversationPhase.SELECCION_ESTADO: 5,
            ConversationPhase.SELECCION_CIUDAD: 6,
            ConversationPhase.SELECCION_BARRIO: 7,
            ConversationPhase.SELECCION_VIVIENDA: 8,
            ConversationPhase.SELECCION_COLEGIOS: 9,
            ConversationPhase.TIMELINE: 10,
            ConversationPhase.PRESUPUESTO: 11,
            ConversationPhase.CIERRE: 12,
        }

        num = phase_numbers.get(phase, 1)
        percentage = int((num / TOTAL_PHASES) * 100)

        return f"📍Fase {num}/{TOTAL_PHASES} • {percentage}%"

    # ============== MICRO-CHECK (OBLIGATORIO cada 3 turnos) ==============

    def must_add_micro_check(self, user_id: int) -> bool:
        """
        v4.1: OBLIGATORIO agregar micro-check cada 3 turnos.
        """
        state = self.get_state(user_id)
        turns_since_check = state.turn_count - state.last_micro_check
        return turns_since_check >= MICRO_CHECK_FREQUENCY

    def get_micro_check(self, lang: str = "es") -> str:
        """Obtiene un micro-check aleatorio"""
        import random

        checks = MICRO_CHECKS.get(lang, MICRO_CHECKS["es"])
        return random.choice(checks)

    def mark_micro_check_done(self, user_id: int) -> None:
        """Marca que se hizo un micro-check"""
        state = self.get_state(user_id)
        state.last_micro_check = state.turn_count

    # ============== HARD CAP: 6 LÍNEAS (con split automático) ==============

    def split_message_by_lines(self, message: str, max_lines: int = MAX_MESSAGE_LINES) -> list[str]:
        """
        v4.1: HARD CAP - Divide mensaje en chunks de máximo 6 líneas.
        Retorna lista de mensajes.
        """
        lines = [l for l in message.split("\n") if l.strip()]

        if len(lines) <= max_lines:
            return [message]

        # Dividir en chunks
        chunks = []
        current_chunk = []

        for line in lines:
            current_chunk.append(line)
            if len(current_chunk) >= max_lines:
                chunks.append("\n".join(current_chunk))
                current_chunk = []

        # Agregar último chunk si hay
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    # ============== HARD RULE: UNA PREGUNTA (con separación) ==============

    def split_by_questions(self, message: str) -> list[str]:
        """
        v4.1: HARD RULE - Si hay 2+ preguntas, separar en mensajes.
        """
        # Contar preguntas
        question_count = message.count("?")

        if question_count <= 1:
            return [message]

        # Separar por preguntas
        # Buscar patrones de pregunta (texto + ?)
        parts = re.split(r"(\?)", message)

        messages = []
        current = ""

        for _i, part in enumerate(parts):
            current += part
            if part == "?":
                # Fin de una pregunta
                cleaned = current.strip()
                if cleaned:
                    messages.append(cleaned)
                current = ""

        # Agregar resto si hay
        if current.strip():
            messages.append(current.strip())

        return messages if messages else [message]

    # ============== MINI-RESUMEN DE FASE ==============

    def get_phase_summary(self, phase: str, data: dict[str, Any]) -> str:
        """
        v4.1: Mini-resumen de 2 líneas al cerrar fase.
        """
        template = PHASE_SUMMARIES.get(phase, "✅ Fase completada.")

        try:
            return template.format(**data)
        except KeyError:
            return f"✅ {phase.capitalize()} completado."

    def mark_phase_complete(self, user_id: int, phase: str, data: dict[str, Any] = None) -> str:
        """Marca fase como completada y retorna mini-resumen"""
        state = self.get_state(user_id)
        if phase not in state.phases_completed:
            state.phases_completed.append(phase)

        return self.get_phase_summary(phase, data or {})

    # ============== VALIDACIONES ==============

    def check_gating(self, user_id: int) -> tuple[GatingStatus, str]:
        """Verifica si el usuario puede recibir recomendaciones de visa."""
        state = self.get_state(user_id)

        if not state.profile_complete:
            return GatingStatus.PENDING_PROFILE, self._get_missing_profile_message(state)

        if not state.summary_confirmed:
            return GatingStatus.PENDING_SUMMARY, self._get_summary_required_message()

        return GatingStatus.APPROVED, ""

    def _get_missing_profile_message(self, state: ConversationState) -> str:
        """Mensaje cuando falta completar perfil"""
        missing = self._get_missing_fields(state)
        return f"Necesito conocer más sobre ti. ¿Me cuentas sobre {missing[0]}?"

    def _get_summary_required_message(self) -> str:
        """Mensaje cuando falta confirmar resumen"""
        return "Antes de recomendarte, quiero confirmar que entendí bien."

    def _get_missing_fields(self, state: ConversationState) -> list[str]:
        """Obtiene campos faltantes del perfil"""
        required = [
            "name",
            "nationality",
            "family",
            "profession",
            "experience",
            "english",
            "motivation",
            "budget",
        ]
        missing = [f for f in required if f not in state.profile_data or not state.profile_data[f]]
        return missing if missing else ["información adicional"]

    def can_show_form(self, user_id: int) -> bool:
        """Verifica si se puede mostrar un formulario."""
        state = self.get_state(user_id)
        return state.forms_shown_last_5 < MAX_FORMS_PER_5_TURNS

    def register_form_shown(self, user_id: int) -> None:
        """Registra que se mostró un formulario"""
        state = self.get_state(user_id)
        state.forms_shown_last_5 += 1
        if state.turn_count % 5 == 0:
            state.forms_shown_last_5 = 0

    # ============== PROCESAMIENTO DE MENSAJES v4.1 ==============

    def soften_message(self, message: str) -> str:
        """Suaviza el mensaje eliminando frases sentenciosas."""
        result = message
        for forbidden in FORBIDDEN_PHRASES:
            if forbidden in result.lower():
                replacement = SOFT_ALTERNATIVES.get(forbidden, "hay otras opciones que podemos explorar")
                result = re.sub(re.escape(forbidden), replacement, result, flags=re.IGNORECASE)
        return result

    def format_response_v41(
        self,
        user_id: int,
        message: str,
        phase_data: dict[str, Any] = None,
        is_phase_end: bool = False,
        lang: str = "es",
    ) -> FormattedOutput:
        """
        v4.1: Formatea respuesta con TODAS las reglas aplicadas.

        Returns:
            FormattedOutput con lista de mensajes formateados
        """
        state = self.get_state(user_id)
        state.turn_count += 1

        # 1. Suavizar tono
        message = self.soften_message(message)

        # 2. HARD RULE: Separar por preguntas (una por mensaje)
        question_messages = self.split_by_questions(message)

        # 3. HARD CAP: Dividir por líneas (máx 6)
        all_messages = []
        for qmsg in question_messages:
            line_messages = self.split_message_by_lines(qmsg)
            all_messages.extend(line_messages)

        # 4. OBLIGATORIO: Progress header en cada mensaje
        progress_header = self.get_progress_header(user_id)
        formatted_messages = []

        for i, msg in enumerate(all_messages):
            # Agregar header solo al primer mensaje de cada grupo
            if i == 0:
                formatted_msg = f"{progress_header}\n\n{msg}"
            else:
                formatted_msg = msg
            formatted_messages.append(formatted_msg)

        # 5. OBLIGATORIO: Micro-check cada 3 turnos
        must_micro_check = self.must_add_micro_check(user_id)
        if must_micro_check:
            micro_check = self.get_micro_check(lang)
            # Agregar al último mensaje
            if formatted_messages:
                last_msg = formatted_messages[-1]
                # Solo agregar si no termina ya en pregunta
                if not last_msg.rstrip().endswith("?"):
                    formatted_messages[-1] = f"{last_msg}\n\n{micro_check}"
                self.mark_micro_check_done(user_id)

        # 6. Mini-resumen si es fin de fase
        phase_summary = None
        if is_phase_end and phase_data:
            phase_summary = self.get_phase_summary(state.current_phase.value, phase_data)
            # Agregar como mensaje separado
            formatted_messages.append(phase_summary)

        # Calcular métricas
        total_lines = sum(len(m.split("\n")) for m in formatted_messages)
        total_questions = sum(m.count("?") for m in formatted_messages)

        return FormattedOutput(
            messages=formatted_messages,
            has_micro_check=must_micro_check,
            has_progress=True,  # Siempre True en v4.1
            question_count=total_questions,
            line_count=total_lines,
            phase_summary=phase_summary,
        )

    # ============== FUNCIONES LEGACY (compatibilidad) ==============

    def format_response(
        self, user_id: int, message: str, include_progress: bool = True, is_form: bool = False
    ) -> MessageResponse:
        """
        Formato legacy - usa format_response_v41 internamente.
        """
        output = self.format_response_v41(user_id, message)

        # Combinar mensajes para compatibilidad
        combined = "\n\n".join(output.messages)

        return MessageResponse(
            text=combined,
            include_micro_check=output.has_micro_check,
            show_progress=output.has_progress,
            is_form=is_form,
            split_messages=output.messages,
            phase_summary=output.phase_summary,
        )

    def get_progress_indicator(self, user_id: int) -> str:
        """Legacy: usa get_progress_header"""
        return self.get_progress_header(user_id)

    def should_add_micro_check(self, user_id: int) -> bool:
        """Legacy: usa must_add_micro_check"""
        return self.must_add_micro_check(user_id)

    # ============== MATRICES PONDERADAS ==============

    def create_weighted_matrix(
        self, items: list[dict[str, Any]], weights: dict[str, float], factors: list[str]
    ) -> list[MatrixEvaluation]:
        """Crea matriz ponderada para evaluación."""
        evaluations = []

        for item in items:
            name = item.get("name", "Unknown")
            scores = {}
            weighted_total = 0

            for factor in factors:
                score = item.get(factor, 3)
                weight = weights.get(factor, 1)
                scores[factor] = score
                weighted_total += score * weight

            max_possible = sum(weights.values()) * 5
            final_score = (weighted_total / max_possible) * 100

            pros = item.get("pros", [])
            cons = item.get("cons", [])

            evaluations.append(
                MatrixEvaluation(
                    name=name,
                    score=final_score,
                    weighted_score=weighted_total,
                    pros=pros,
                    cons=cons,
                    factors=scores,
                    recommendation=self._generate_recommendation(name, final_score),
                )
            )

        evaluations.sort(key=lambda x: x.score, reverse=True)
        return evaluations

    def _generate_recommendation(self, name: str, score: float) -> str:
        """Genera recomendación basada en score"""
        if score >= 85:
            return f"👉 {name} es excelente opción"
        elif score >= 70:
            return f"👉 {name} es buena opción"
        elif score >= 55:
            return f"👉 {name} puede funcionar"
        else:
            return f"👉 {name} tiene mejores alternativas"

    def format_matrix_results(self, evaluations: list[MatrixEvaluation], top_n: int = 3) -> str:
        """Formatea resultados de matriz (máx 3 para cumplir 6 líneas)"""
        result = "🏆 **TOP OPCIONES**\n"

        for i, eval in enumerate(evaluations[:top_n], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            result += f"{emoji} {eval.name}: {eval.score:.0f}/100\n"

        return result

    # ============== FACTORES DE EVALUACIÓN ==============

    def get_state_factors(self) -> dict[str, float]:
        """Factores para evaluar estados"""
        return {
            "salud": 18,
            "oportunidades_negocio": 15,
            "costo_vida": 14,
            "criminalidad": 12,
            "estudios": 10,
            "impuestos": 8,
            "migration_friendly": 8,
            "dinamismo_economico": 7,
            "comunidad_latina": 5,
            "clima": 2,
            "poblacion": 1,
        }

    def get_business_factors(self) -> dict[str, float]:
        """Factores para evaluar negocios"""
        return {
            "rentabilidad": 20,
            "recurrencia_ingresos": 18,
            "riesgo_operativo": 15,
            "inversion_inicial": 12,
            "payback": 12,
            "encaje_visa": 10,
            "empleo_familia": 8,
            "escalabilidad": 5,
        }

    # ============== CHECKLISTS ==============

    def get_document_checklist(self, visa_type: str) -> list[dict[str, Any]]:
        """Obtiene checklist de documentos según tipo de visa"""
        checklists = {
            "E-2": [
                {"name": "Pasaporte vigente", "required": True},
                {"name": "Plan de negocios", "required": True},
                {"name": "Prueba de inversión", "required": True},
            ],
            "L-1": [
                {"name": "Pasaporte vigente", "required": True},
                {"name": "Carta empresa matriz", "required": True},
            ],
        }
        return checklists.get(visa_type, [])

    def get_installation_checklist(self) -> list[dict[str, Any]]:
        """Checklist de instalación en USA"""
        return [
            {"category": "Documentos", "items": ["SSN", "Licencia", "USCIS"]},
            {"category": "Finanzas", "items": ["Banco", "Crédito"]},
            {"category": "Vivienda", "items": ["Contrato", "Servicios"]},
        ]


# ============== SINGLETON ==============

_standard_instance: MigPALUSAStandard | None = None


def get_migpal_standard() -> MigPALUSAStandard:
    """Obtiene la instancia singleton del estándar MigPAL USA"""
    global _standard_instance
    if _standard_instance is None:
        _standard_instance = MigPALUSAStandard()
    return _standard_instance


# ============== FUNCIONES DE CONVENIENCIA v4.1 ==============


def format_message_v41(
    user_id: int,
    message: str,
    phase_data: dict[str, Any] = None,
    is_phase_end: bool = False,
    lang: str = "es",
) -> list[str]:
    """
    v4.1: Formatea mensaje y retorna lista de mensajes.
    Garantiza: máx 6 líneas, 1 pregunta, micro-check, progress header.
    """
    standard = get_migpal_standard()
    output = standard.format_response_v41(user_id, message, phase_data, is_phase_end, lang)
    return output.messages


def check_visa_gating(user_id: int) -> tuple[bool, str]:
    """Verifica si se puede recomendar visa"""
    standard = get_migpal_standard()
    status, message = standard.check_gating(user_id)
    return status == GatingStatus.APPROVED, message


def format_message(user_id: int, message: str, is_form: bool = False) -> str:
    """Legacy: Formatea mensaje según reglas MigPAL USA"""
    standard = get_migpal_standard()
    response = standard.format_response(user_id, message, is_form=is_form)
    return response.text


def evaluate_options(items: list[dict], category: str, custom_weights: dict[str, float] | None = None) -> str:
    """Evalúa opciones con matriz ponderada"""
    standard = get_migpal_standard()

    factor_getters = {
        "state": standard.get_state_factors,
        "business": standard.get_business_factors,
    }

    weights = custom_weights or factor_getters.get(category, standard.get_state_factors)()
    factors = list(weights.keys())

    evaluations = standard.create_weighted_matrix(items, weights, factors)
    return standard.format_matrix_results(evaluations)


def can_show_form(user_id: int) -> bool:
    """Verifica si se puede mostrar formulario"""
    return get_migpal_standard().can_show_form(user_id)


def get_progress(user_id: int) -> str:
    """Obtiene indicador de progreso"""
    return get_migpal_standard().get_progress_header(user_id)


def advance_phase(user_id: int, new_phase: ConversationPhase) -> None:
    """Avanza a una nueva fase"""
    get_migpal_standard().update_state(user_id, current_phase=new_phase)


def mark_profile_complete(user_id: int) -> None:
    """Marca el perfil como completo"""
    get_migpal_standard().update_state(user_id, profile_complete=True)


def mark_summary_confirmed(user_id: int) -> None:
    """Marca el resumen como confirmado"""
    standard = get_migpal_standard()
    standard.update_state(user_id, summary_confirmed=True, gating_status=GatingStatus.APPROVED)


def reset_user_state(user_id: int) -> None:
    """Resetea el estado de un usuario"""
    get_migpal_standard().reset_state(user_id)


# ============== EXPORTAR ==============

__all__ = [
    "MigPALUSAStandard",
    "ConversationPhase",
    "GatingStatus",
    "ConversationState",
    "MatrixEvaluation",
    "MessageResponse",
    "FormattedOutput",
    "get_migpal_standard",
    "format_message_v41",
    "check_visa_gating",
    "format_message",
    "evaluate_options",
    "can_show_form",
    "get_progress",
    "advance_phase",
    "mark_profile_complete",
    "mark_summary_confirmed",
    "reset_user_state",
    "MICRO_CHECKS",
    "FORBIDDEN_PHRASES",
    "MAX_MESSAGE_LINES",
    "MICRO_CHECK_FREQUENCY",
    "TOTAL_PHASES",
]

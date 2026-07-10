#!/usr/bin/env python3
"""
🎯 STATE & VALIDATION LAYER - MigPAL USA
=========================================

PRINCIPIO FUNDAMENTAL:
    El LLM conversa LIBREMENTE.
    El SISTEMA gobierna el PROGRESO.

Este módulo implementa una capa de validación EXTERNA al modelo de IA.
NO limita el lenguaje ni la conversación. Solo controla:
- Cuándo se guarda información
- Cuándo se pide confirmación
- Cuándo se avanza de estado
- Cuándo se queda explorando

REGLA MADRE:
    El modelo piensa libre, el sistema gobierna el progreso.

NO HACER:
- Forzar formularios
- Limitar la empatía del LLM
- Restringir el lenguaje
- Bloquear la exploración

SÍ HACER:
- Sugerir formularios cuando falte info crítica (si el usuario acepta)
- Validar antes de avanzar de estado
- Bloquear recomendaciones de visa sin Resumen validado
- Permitir que el LLM explore libremente
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Estados de la conversación - el sistema los controla, no el LLM"""

    EXPLORING = "exploring"  # LLM explorando libremente
    GATHERING_INFO = "gathering_info"  # Sistema detectó info útil
    AWAITING_CONFIRMATION = "awaiting_confirmation"  # Esperando confirmación
    READY_TO_ADVANCE = "ready_to_advance"  # Listo para avanzar
    BLOCKED = "blocked"  # Bloqueado por regla dura


class ProgressPhase(Enum):
    """Fases de progreso - controladas por el sistema"""

    INITIAL_CONTACT = "initial_contact"
    UNDERSTANDING_MOTIVATION = "understanding_motivation"
    UNDERSTANDING_FAMILY = "understanding_family"
    UNDERSTANDING_SITUATION = "understanding_situation"
    UNDERSTANDING_DESIRES = "understanding_desires"
    UNDERSTANDING_CONSTRAINTS = "understanding_constraints"
    SUMMARY_PENDING = "summary_pending"
    SUMMARY_CONFIRMED = "summary_confirmed"
    OPTIONS_EXPLORATION = "options_exploration"


@dataclass
class ValidationResult:
    """Resultado de validación del sistema"""

    can_proceed: bool
    reason: str = ""
    suggestion: str | None = None
    missing_info: list[str] = field(default_factory=list)
    should_save_info: bool = False
    info_to_save: dict[str, Any] = field(default_factory=dict)


@dataclass
class StateDecision:
    """Decisión del sistema sobre el estado"""

    action: str  # "stay", "advance", "save_info", "request_confirmation", "suggest_form"
    current_state: ConversationState
    current_phase: ProgressPhase
    next_phase: ProgressPhase | None = None
    message_to_user: str | None = None
    internal_note: str = ""


class StateValidationLayer:
    """
    🎯 CAPA DE VALIDACIÓN DE ESTADO

    Separa la libertad del LLM del control de progreso.

    El LLM puede:
    - Conversar libremente
    - Empatizar sin límites
    - Explorar temas
    - Adaptarse al usuario

    El Sistema controla:
    - Cuándo guardar información
    - Cuándo pedir confirmación
    - Cuándo avanzar de fase
    - Cuándo bloquear (solo para visas sin resumen)
    """

    # Información mínima para cada fase (NO obligatoria para conversar)
    PHASE_INFO_HINTS = {
        ProgressPhase.UNDERSTANDING_MOTIVATION: ["deep_motivation"],
        ProgressPhase.UNDERSTANDING_FAMILY: ["migrating_alone", "family_members"],
        ProgressPhase.UNDERSTANDING_SITUATION: ["current_profession", "current_income"],
        ProgressPhase.UNDERSTANDING_DESIRES: ["desired_lifestyle", "desired_location"],
        ProgressPhase.UNDERSTANDING_CONSTRAINTS: ["available_savings", "timeline_urgency"],
    }

    # Información CRÍTICA para el resumen (sugerir si falta)
    CRITICAL_FOR_SUMMARY = [
        "deep_motivation",
        "family_situation",  # migrating_alone OR family_members
        "work_situation",  # current_profession OR current_income
        "desired_life",  # desired_lifestyle
    ]

    def __init__(self):
        self.current_state = ConversationState.EXPLORING
        self.current_phase = ProgressPhase.INITIAL_CONTACT
        self.understanding = {}
        self.summary_confirmed = False
        self.interaction_count = 0
        self.last_form_interaction = 0
        self.form_count = 0

    def process_interaction(
        self, user_message: str, llm_response: str, extracted_info: dict[str, Any]
    ) -> StateDecision:
        """
        Procesar una interacción y decidir qué hacer.

        El LLM ya respondió libremente. Ahora el sistema decide:
        - ¿Guardar información extraída?
        - ¿Pedir confirmación?
        - ¿Avanzar de fase?
        - ¿Quedarse explorando?

        Args:
            user_message: Lo que dijo el usuario
            llm_response: Lo que respondió el LLM (ya generado)
            extracted_info: Información extraída por NLU

        Returns:
            StateDecision con la acción a tomar
        """
        self.interaction_count += 1

        # 1. ¿Hay información nueva para guardar?
        if extracted_info:
            self._save_extracted_info(extracted_info)

        # 2. ¿El usuario confirmó algo?
        if self._detect_confirmation(user_message):
            return self._handle_confirmation(user_message)

        # 3. ¿El usuario corrigió algo?
        if self._detect_correction(user_message):
            return self._handle_correction(user_message)

        # 4. ¿Hay suficiente info para avanzar de fase?
        if self._can_advance_phase():
            return self._decide_advance()

        # 5. ¿Falta info crítica y es buen momento para sugerir?
        if self._should_suggest_info_gathering():
            return self._suggest_info_gathering()

        # 6. Por defecto: seguir explorando
        return StateDecision(
            action="stay",
            current_state=ConversationState.EXPLORING,
            current_phase=self.current_phase,
            internal_note="LLM explorando libremente",
        )

    def _save_extracted_info(self, info: dict[str, Any]):
        """Guardar información extraída sin interrumpir la conversación"""
        for key, value in info.items():
            if value is not None and value != "":
                self.understanding[key] = value
                logger.info(f"📝 Info guardada: {key} = {value}")

    def _detect_confirmation(self, user_message: str) -> bool:
        """Detectar si el usuario confirmó algo"""
        import re

        text_lower = user_message.lower()

        confirmation_patterns = [
            r"^sí[,.]?\s*",
            r"^si[,.]?\s*",
            r"^correcto",
            r"^exacto",
            r"^así es",
            r"^eso es",
            r"^perfecto",
            r"está bien",
            r"es correcto",
            r"entendiste bien",
        ]

        return any(re.search(p, text_lower) for p in confirmation_patterns)

    def _detect_correction(self, user_message: str) -> bool:
        """Detectar si el usuario está corrigiendo"""
        import re

        text_lower = user_message.lower()

        correction_patterns = [
            r"no,?\s*(en realidad|quise decir)",
            r"corrijo",
            r"no es así",
            r"me equivoqué",
            r"en realidad",
        ]

        return any(re.search(p, text_lower) for p in correction_patterns)

    def _handle_confirmation(self, user_message: str) -> StateDecision:
        """Manejar confirmación del usuario"""

        # Si estamos esperando confirmación del resumen
        if self.current_phase == ProgressPhase.SUMMARY_PENDING:
            self.summary_confirmed = True
            self.current_phase = ProgressPhase.SUMMARY_CONFIRMED

            return StateDecision(
                action="advance",
                current_state=ConversationState.READY_TO_ADVANCE,
                current_phase=ProgressPhase.SUMMARY_CONFIRMED,
                next_phase=ProgressPhase.OPTIONS_EXPLORATION,
                internal_note="✅ Resumen confirmado. Ahora se pueden explorar opciones.",
            )

        # Confirmación general - avanzar si es posible
        if self._can_advance_phase():
            return self._decide_advance()

        return StateDecision(
            action="stay",
            current_state=ConversationState.EXPLORING,
            current_phase=self.current_phase,
            internal_note="Confirmación recibida, continuando exploración",
        )

    def _handle_correction(self, user_message: str) -> StateDecision:
        """Manejar corrección del usuario - NO avanzar"""
        return StateDecision(
            action="stay",
            current_state=ConversationState.EXPLORING,
            current_phase=self.current_phase,
            internal_note="🔄 Usuario corrigiendo. LLM debe reinterpretar.",
        )

    def _can_advance_phase(self) -> bool:
        """Verificar si hay suficiente info para avanzar de fase"""
        hints = self.PHASE_INFO_HINTS.get(self.current_phase, [])

        if not hints:
            return True  # Fases sin requisitos pueden avanzar

        # Verificar si al menos uno de los hints está presente
        for hint in hints:
            if hint in self.understanding and self.understanding[hint]:
                return True

        return False

    def _decide_advance(self) -> StateDecision:
        """Decidir si avanzar de fase"""
        phase_order = list(ProgressPhase)
        current_idx = phase_order.index(self.current_phase)

        if current_idx < len(phase_order) - 1:
            next_phase = phase_order[current_idx + 1]

            # Si vamos a OPTIONS, verificar resumen confirmado
            if next_phase == ProgressPhase.OPTIONS_EXPLORATION:
                if not self.summary_confirmed:
                    return StateDecision(
                        action="request_confirmation",
                        current_state=ConversationState.AWAITING_CONFIRMATION,
                        current_phase=ProgressPhase.SUMMARY_PENDING,
                        internal_note="🚨 Necesita resumen confirmado antes de opciones",
                    )

            self.current_phase = next_phase
            return StateDecision(
                action="advance",
                current_state=ConversationState.EXPLORING,
                current_phase=self.current_phase,
                next_phase=next_phase,
                internal_note=f"Avanzando a {next_phase.value}",
            )

        return StateDecision(
            action="stay",
            current_state=ConversationState.EXPLORING,
            current_phase=self.current_phase,
            internal_note="Ya en fase final",
        )

    def _should_suggest_info_gathering(self) -> bool:
        """
        ¿Es buen momento para SUGERIR (no forzar) recopilar info?

        Solo sugerir si:
        - Han pasado varias interacciones
        - Falta info crítica
        - No hemos sugerido recientemente
        """
        # No sugerir en las primeras interacciones
        if self.interaction_count < 5:
            return False

        # No sugerir si ya sugerimos recientemente
        if self.interaction_count - self.last_form_interaction < 5:
            return False

        # Verificar si falta info crítica
        missing = self._get_missing_critical_info()

        return len(missing) > 0

    def _get_missing_critical_info(self) -> list[str]:
        """Obtener lista de info crítica faltante"""
        missing = []

        for info_key in self.CRITICAL_FOR_SUMMARY:
            if info_key == "family_situation":
                if not self.understanding.get("migrating_alone") and not self.understanding.get(
                    "family_members"
                ):
                    missing.append("situación familiar")
            elif info_key == "work_situation":
                if not self.understanding.get("current_profession") and not self.understanding.get(
                    "current_income"
                ):
                    missing.append("situación laboral")
            elif info_key == "desired_life":
                if not self.understanding.get("desired_lifestyle"):
                    missing.append("vida deseada")
            else:
                if not self.understanding.get(info_key):
                    missing.append(info_key.replace("_", " "))

        return missing

    def _suggest_info_gathering(self) -> StateDecision:
        """Sugerir (no forzar) recopilar información faltante"""
        missing = self._get_missing_critical_info()

        self.last_form_interaction = self.interaction_count

        return StateDecision(
            action="suggest_form",
            current_state=ConversationState.GATHERING_INFO,
            current_phase=self.current_phase,
            message_to_user=self._build_gentle_suggestion(missing),
            internal_note=f"Sugiriendo info faltante: {missing}",
        )

    def _build_gentle_suggestion(self, missing: list[str]) -> str:
        """Construir sugerencia amable (no formulario forzado)"""
        if len(missing) == 1:
            return f"Por cierto, me ayudaría saber un poco más sobre tu {missing[0]}. ¿Me cuentas?"
        else:
            items = ", ".join(missing[:-1]) + f" y {missing[-1]}"
            return f"Para entenderte mejor, me gustaría saber sobre tu {items}. ¿Qué me puedes contar?"

    def can_show_visa_options(self) -> tuple[bool, str]:
        """
        🚨 REGLA CRÍTICA: No recomendar visas sin Resumen validado.

        Returns:
            (can_show, reason)
        """
        if not self.summary_confirmed:
            return False, "🚨 No se pueden mostrar opciones de visa sin Resumen de Entendimiento confirmado."

        return True, "OK"

    def can_recommend_visa(self) -> tuple[bool, str]:
        """
        🚨 REGLA CRÍTICA: No recomendar caminos sin Resumen validado.
        """
        return self.can_show_visa_options()

    def get_summary_for_confirmation(self) -> str | None:
        """
        Generar resumen para confirmación del usuario.

        Solo se genera si hay suficiente información.
        """
        if not self._has_minimum_for_summary():
            return None

        parts = []

        # Motivación
        if self.understanding.get("deep_motivation"):
            parts.append(f"Quieres migrar porque {self.understanding['deep_motivation']}")

        # Familia
        if self.understanding.get("migrating_alone"):
            parts.append("Viajarías solo/a")
        elif self.understanding.get("family_members"):
            family = self.understanding["family_members"]
            if isinstance(family, list):
                parts.append(f"Viajarías con {len(family)} persona(s)")
            else:
                parts.append("Viajarías con tu familia")

        # Trabajo
        if self.understanding.get("current_profession"):
            parts.append(f"Trabajas como {self.understanding['current_profession']}")

        # Vida deseada
        if self.understanding.get("desired_lifestyle"):
            parts.append(f"Buscas {self.understanding['desired_lifestyle']}")

        # Restricciones
        if self.understanding.get("available_savings"):
            parts.append(f"Cuentas con aproximadamente ${self.understanding['available_savings']}")

        if not parts:
            return None

        summary = "Déjame ver si entendí bien:\n\n"
        summary += "\n".join(f"• {p}" for p in parts)
        summary += "\n\n¿Es correcto o hay algo que deba ajustar?"

        return summary

    def _has_minimum_for_summary(self) -> bool:
        """Verificar si hay mínimo para generar resumen"""
        has_motivation = bool(self.understanding.get("deep_motivation"))
        has_family = bool(
            self.understanding.get("migrating_alone") or self.understanding.get("family_members")
        )

        return has_motivation or has_family

    def get_state_info(self) -> dict[str, Any]:
        """Obtener información del estado actual"""
        return {
            "conversation_state": self.current_state.value,
            "progress_phase": self.current_phase.value,
            "summary_confirmed": self.summary_confirmed,
            "interaction_count": self.interaction_count,
            "understanding_keys": list(self.understanding.keys()),
            "missing_critical": self._get_missing_critical_info(),
            "can_show_visa_options": self.can_show_visa_options()[0],
        }


# =========================================================================
# FUNCIONES DE CONVENIENCIA
# =========================================================================


def create_state_layer() -> StateValidationLayer:
    """Crear nueva instancia del State Layer"""
    return StateValidationLayer()


def process_llm_response(
    layer: StateValidationLayer, user_message: str, llm_response: str, extracted_info: dict[str, Any] = None
) -> StateDecision:
    """
    Procesar respuesta del LLM y obtener decisión del sistema.

    El LLM ya respondió libremente. Esta función decide qué hacer después.
    """
    return layer.process_interaction(
        user_message=user_message, llm_response=llm_response, extracted_info=extracted_info or {}
    )


def can_proceed_to_visa_options(layer: StateValidationLayer) -> tuple[bool, str]:
    """Verificar si se puede proceder a opciones de visa"""
    return layer.can_show_visa_options()

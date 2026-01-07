#!/usr/bin/env python3
"""
🔒 REGLAS DURAS DE SISTEMA - MigPAL USA
=======================================

Este módulo contiene las RESTRICCIONES OBLIGATORIAS del motor conversacional.
NO son sugerencias ni UX. Son reglas inviolables.

Si una regla se viola → el flujo NO puede avanzar.
Si hay conflicto código vs regla → LA REGLA PREVALECE.

SEGMENTOS:
1/4 - Principios Inviolables (Core) ✅
2/4 - Control de Flujo (Bloqueos) ✅
3/4 - Inteligencia Conversacional ✅
4/4 - (Pendiente)
"""

import logging
from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RuleViolation(Enum):
    """Tipos de violaciones de reglas duras"""
    # Segmento 1/4 - Principios Inviolables
    PERSONAL_DATA_TOO_EARLY = "personal_data_too_early"
    VISA_WITHOUT_PROFILE = "visa_without_profile"
    OPTIONS_WITHOUT_SUMMARY = "options_without_summary"
    TOO_MANY_FORMS = "too_many_forms"
    ADVANCE_ON_DOUBT = "advance_on_doubt"
    
    # Segmento 2/4 - Control de Flujo (Bloqueos)
    SKIPPED_MANDATORY_STATE = "skipped_mandatory_state"
    UNDERSTANDING_NOT_CONFIRMED = "understanding_not_confirmed"
    INVALID_STATE_TRANSITION = "invalid_state_transition"
    MISSING_REQUIRED_DATA = "missing_required_data"
    
    # Segmento 2/4 - Conversación vs Formularios
    FORM_WITHOUT_DIALOGUE = "form_without_dialogue"
    CHECKLIST_QUESTIONS = "checklist_questions"
    IGNORED_USER_INPUT = "ignored_user_input"
    BOT_LIKE_BEHAVIOR = "bot_like_behavior"
    
    # Segmento 3/4 - Inteligencia Conversacional
    CORRECTION_NOT_HANDLED = "correction_not_handled"
    OFF_TOPIC_IGNORED = "off_topic_ignored"
    AUDIO_NOT_CONFIRMED = "audio_not_confirmed"
    NO_EXPLANATION_WHY = "no_explanation_why"


@dataclass
class RuleCheckResult:
    """Resultado de verificación de reglas"""
    passed: bool
    violation: Optional[RuleViolation] = None
    message: str = ""
    should_rollback: bool = False
    rollback_to_phase: Optional[str] = None


class HardRulesGuardian:
    """
    🔒 GUARDIÁN DE REGLAS DURAS
    
    Verifica que todas las reglas inviolables se cumplan.
    Si alguna se viola, bloquea el avance y puede hacer rollback.
    """
    
    # =========================================================================
    # SEGMENTO 1/4 — PRINCIPIOS INVIOLABLES (CORE)
    # =========================================================================
    
    # Fases donde NO se pueden pedir datos personales
    EARLY_PHASES = ["greeting", "deep_motivation"]
    
    # Fases que requieren perfil completo para hablar de visas
    VISA_TALK_REQUIRES = ["options", "plan_creation"]
    
    # Campos mínimos para considerar perfil "completo"
    MINIMUM_PROFILE_FIELDS = [
        "deep_motivation",
        "migrating_alone",  # o family_members
        "current_profession",
        "desired_lifestyle",
    ]
    
    def __init__(self):
        self.violations_log: List[Dict] = []
    
    def check_all_rules(
        self,
        current_phase: str,
        next_phase: str,
        user_text: str,
        bot_response: str,
        context: Dict[str, Any],
        interaction_count: int,
        form_count: int,
        last_form_interaction: int,
    ) -> RuleCheckResult:
        """
        Verificar TODAS las reglas duras antes de permitir avance.
        
        Returns:
            RuleCheckResult con passed=False si alguna regla se viola
        """
        
        # REGLA 1: ❌ Prohibido pedir datos personales en primeros mensajes
        result = self._check_no_personal_data_early(current_phase, bot_response)
        if not result.passed:
            return result
        
        # REGLA 2: ❌ Prohibido recomendar visa sin perfil completo
        result = self._check_no_visa_without_profile(next_phase, context)
        if not result.passed:
            return result
        
        # REGLA 3: ❌ Prohibido saltar a "opciones" sin resumen confirmado
        result = self._check_no_options_without_summary(next_phase, context)
        if not result.passed:
            return result
        
        # REGLA 4: ❌ Prohibido más de 1 formulario cada 5 interacciones
        result = self._check_form_limit(interaction_count, form_count, last_form_interaction)
        if not result.passed:
            return result
        
        # REGLA 5: ❌ Prohibido avanzar si usuario expresa duda/corrección/confusión
        result = self._check_no_advance_on_doubt(user_text, current_phase, next_phase)
        if not result.passed:
            return result
        
        return RuleCheckResult(passed=True, message="Todas las reglas cumplidas")
    
    def _check_no_personal_data_early(
        self, 
        current_phase: str, 
        bot_response: str
    ) -> RuleCheckResult:
        """
        REGLA 1: ❌ Prohibido pedir datos personales en los primeros mensajes.
        """
        if current_phase not in self.EARLY_PHASES:
            return RuleCheckResult(passed=True)
        
        # Patrones de solicitud de datos personales
        personal_data_patterns = [
            r"tu nombre completo",
            r"tu número de",
            r"tu dirección",
            r"tu correo",
            r"tu email",
            r"tu teléfono",
            r"tu pasaporte",
            r"tu fecha de nacimiento",
            r"cuántos años tienes",
            r"tu edad exacta",
        ]
        
        import re
        response_lower = bot_response.lower()
        
        for pattern in personal_data_patterns:
            if re.search(pattern, response_lower):
                self._log_violation(RuleViolation.PERSONAL_DATA_TOO_EARLY, current_phase)
                return RuleCheckResult(
                    passed=False,
                    violation=RuleViolation.PERSONAL_DATA_TOO_EARLY,
                    message="No se pueden pedir datos personales en fases tempranas",
                    should_rollback=False
                )
        
        return RuleCheckResult(passed=True)
    
    def _check_no_visa_without_profile(
        self,
        next_phase: str,
        context: Dict[str, Any]
    ) -> RuleCheckResult:
        """
        REGLA 2: ❌ Prohibido recomendar visa sin perfil completo.
        """
        if next_phase not in self.VISA_TALK_REQUIRES:
            return RuleCheckResult(passed=True)
        
        understanding = context.get("understanding", {})
        
        # Verificar campos mínimos
        missing_fields = []
        for field in self.MINIMUM_PROFILE_FIELDS:
            value = understanding.get(field)
            if value is None or value == "" or value == []:
                missing_fields.append(field)
        
        # Excepción: si tiene family_members, no necesita migrating_alone
        if "migrating_alone" in missing_fields:
            if understanding.get("family_members"):
                missing_fields.remove("migrating_alone")
        
        if missing_fields:
            self._log_violation(RuleViolation.VISA_WITHOUT_PROFILE, next_phase)
            return RuleCheckResult(
                passed=False,
                violation=RuleViolation.VISA_WITHOUT_PROFILE,
                message=f"Perfil incompleto. Faltan: {', '.join(missing_fields)}",
                should_rollback=True,
                rollback_to_phase="real_constraints"
            )
        
        return RuleCheckResult(passed=True)
    
    def _check_no_options_without_summary(
        self,
        next_phase: str,
        context: Dict[str, Any]
    ) -> RuleCheckResult:
        """
        REGLA 3: ❌ Prohibido saltar a "opciones" sin resumen confirmado.
        """
        if next_phase != "options":
            return RuleCheckResult(passed=True)
        
        understanding = context.get("understanding", {})
        confirmed = understanding.get("confirmed_by_user", False)
        
        if not confirmed:
            self._log_violation(RuleViolation.OPTIONS_WITHOUT_SUMMARY, next_phase)
            return RuleCheckResult(
                passed=False,
                violation=RuleViolation.OPTIONS_WITHOUT_SUMMARY,
                message="No se puede ir a opciones sin resumen confirmado",
                should_rollback=True,
                rollback_to_phase="understanding"
            )
        
        return RuleCheckResult(passed=True)
    
    def _check_form_limit(
        self,
        interaction_count: int,
        form_count: int,
        last_form_interaction: int
    ) -> RuleCheckResult:
        """
        REGLA 4: ❌ Prohibido más de 1 formulario cada 5 interacciones.
        """
        if form_count == 0:
            return RuleCheckResult(passed=True)
        
        interactions_since_last_form = interaction_count - last_form_interaction
        
        if interactions_since_last_form < 5:
            self._log_violation(RuleViolation.TOO_MANY_FORMS, f"interaction_{interaction_count}")
            return RuleCheckResult(
                passed=False,
                violation=RuleViolation.TOO_MANY_FORMS,
                message=f"Demasiados formularios. Último hace {interactions_since_last_form} interacciones",
                should_rollback=False
            )
        
        return RuleCheckResult(passed=True)
    
    def _check_no_advance_on_doubt(
        self,
        user_text: str,
        current_phase: str,
        next_phase: str
    ) -> RuleCheckResult:
        """
        REGLA 5: ❌ Prohibido avanzar si usuario expresa duda/corrección/confusión.
        """
        if current_phase == next_phase:
            return RuleCheckResult(passed=True)  # No hay avance
        
        import re
        text_lower = user_text.lower()
        
        # Patrones de duda/corrección/confusión
        doubt_patterns = [
            r"no estoy segur[oa]",
            r"no sé si",
            r"tengo dudas",
            r"me confunde",
            r"no entiendo",
            r"espera",
            r"un momento",
            r"déjame pensar",
            r"no,?\s*(en realidad|quise decir|me equivoqué)",
            r"corrijo",
            r"no es así",
            r"cambiar",
            r"corregir",
        ]
        
        for pattern in doubt_patterns:
            if re.search(pattern, text_lower):
                self._log_violation(RuleViolation.ADVANCE_ON_DOUBT, current_phase)
                return RuleCheckResult(
                    passed=False,
                    violation=RuleViolation.ADVANCE_ON_DOUBT,
                    message="Usuario expresó duda/corrección. No se puede avanzar.",
                    should_rollback=True,
                    rollback_to_phase=current_phase
                )
        
        return RuleCheckResult(passed=True)
    
    # =========================================================================
    # SEGMENTO 2/4 — CONTROL DE FLUJO (BLOQUEOS)
    # =========================================================================
    
    # Estados OBLIGATORIOS y BLOQUEANTES - en orden estricto
    MANDATORY_STATES = [
        "greeting",              # Empatía + contención
        "deep_motivation",       # Por qué quiere migrar (MOTIVATION)
        "who_migrates",          # Quiénes, edades, familia
        "current_situation",     # Trabajo, dinero, situación real (CURRENT_CONTEXT)
        "desired_life",          # Vida deseada en USA (DESIRED_LIFE_USA)
        "real_constraints",      # Edad, idioma, dinero, estatus (CONSTRAINTS)
        "understanding",         # Resumen en lenguaje humano (UNDERSTANDING_SUMMARY)
        # CONFIRMATION está implícito en understanding con confirmed_by_user
    ]
    
    # Estados que requieren understanding_confirmed = true
    STATES_REQUIRING_CONFIRMATION = [
        "options",
        "plan_creation",
        "visa_analysis",
        "recommendations",
    ]
    
    # Datos requeridos por cada estado para poder avanzar
    STATE_REQUIRED_DATA = {
        "deep_motivation": [],  # Solo necesita interacción
        "who_migrates": ["deep_motivation"],
        "current_situation": ["migrating_alone"],  # o family_members
        "desired_life": ["current_profession"],
        "real_constraints": ["desired_lifestyle"],
        "understanding": ["available_savings"],  # o timeline_urgency
    }
    
    def check_state_transition(
        self,
        current_state: str,
        next_state: str,
        context: Dict[str, Any]
    ) -> RuleCheckResult:
        """
        Verificar que la transición de estado sea válida.
        
        REGLAS:
        1. No se puede saltar estados obligatorios
        2. Estados posteriores a CONFIRMATION requieren understanding_confirmed = true
        """
        
        # Verificar si se está saltando un estado obligatorio
        result = self._check_no_skipped_states(current_state, next_state)
        if not result.passed:
            return result
        
        # Verificar si el estado requiere confirmación
        result = self._check_confirmation_required(next_state, context)
        if not result.passed:
            return result
        
        # Verificar datos requeridos para el estado
        result = self._check_required_data_for_state(next_state, context)
        if not result.passed:
            return result
        
        return RuleCheckResult(passed=True)
    
    def _check_no_skipped_states(
        self,
        current_state: str,
        next_state: str
    ) -> RuleCheckResult:
        """
        Verificar que no se salten estados obligatorios.
        """
        if current_state not in self.MANDATORY_STATES:
            return RuleCheckResult(passed=True)
        
        if next_state not in self.MANDATORY_STATES:
            # Transición a estado no obligatorio (ej: options)
            # Verificar que se hayan completado todos los obligatorios
            current_idx = self.MANDATORY_STATES.index(current_state)
            if current_idx < len(self.MANDATORY_STATES) - 1:
                # No ha completado todos los estados obligatorios
                next_required = self.MANDATORY_STATES[current_idx + 1]
                self._log_violation(RuleViolation.SKIPPED_MANDATORY_STATE, next_state)
                return RuleCheckResult(
                    passed=False,
                    violation=RuleViolation.SKIPPED_MANDATORY_STATE,
                    message=f"Debe completar '{next_required}' antes de ir a '{next_state}'",
                    should_rollback=True,
                    rollback_to_phase=current_state
                )
            return RuleCheckResult(passed=True)
        
        current_idx = self.MANDATORY_STATES.index(current_state)
        next_idx = self.MANDATORY_STATES.index(next_state)
        
        # Solo puede avanzar al siguiente estado o quedarse
        if next_idx > current_idx + 1:
            skipped = self.MANDATORY_STATES[current_idx + 1]
            self._log_violation(RuleViolation.SKIPPED_MANDATORY_STATE, next_state)
            return RuleCheckResult(
                passed=False,
                violation=RuleViolation.SKIPPED_MANDATORY_STATE,
                message=f"No se puede saltar de '{current_state}' a '{next_state}'. Falta: '{skipped}'",
                should_rollback=True,
                rollback_to_phase=current_state
            )
        
        return RuleCheckResult(passed=True)
    
    def _check_confirmation_required(
        self,
        next_state: str,
        context: Dict[str, Any]
    ) -> RuleCheckResult:
        """
        🚨 REGLA CRÍTICA: Ningún estado posterior puede ejecutarse sin:
        understanding_confirmed = true
        """
        if next_state not in self.STATES_REQUIRING_CONFIRMATION:
            return RuleCheckResult(passed=True)
        
        understanding = context.get("understanding", {})
        confirmed = understanding.get("confirmed_by_user", False)
        
        if not confirmed:
            self._log_violation(RuleViolation.UNDERSTANDING_NOT_CONFIRMED, next_state)
            return RuleCheckResult(
                passed=False,
                violation=RuleViolation.UNDERSTANDING_NOT_CONFIRMED,
                message=f"🚨 BLOQUEADO: '{next_state}' requiere understanding_confirmed = true",
                should_rollback=True,
                rollback_to_phase="understanding"
            )
        
        return RuleCheckResult(passed=True)
    
    def _check_required_data_for_state(
        self,
        next_state: str,
        context: Dict[str, Any]
    ) -> RuleCheckResult:
        """
        Verificar que existan los datos requeridos para avanzar al estado.
        """
        required_fields = self.STATE_REQUIRED_DATA.get(next_state, [])
        
        if not required_fields:
            return RuleCheckResult(passed=True)
        
        understanding = context.get("understanding", {})
        
        for field in required_fields:
            value = understanding.get(field)
            
            # Caso especial: migrating_alone puede ser reemplazado por family_members
            if field == "migrating_alone" and value is None:
                if understanding.get("family_members"):
                    continue
            
            # Caso especial: available_savings puede ser reemplazado por timeline_urgency
            if field == "available_savings" and value is None:
                if understanding.get("timeline_urgency"):
                    continue
            
            if value is None or value == "" or value == []:
                self._log_violation(RuleViolation.MISSING_REQUIRED_DATA, next_state)
                return RuleCheckResult(
                    passed=False,
                    violation=RuleViolation.MISSING_REQUIRED_DATA,
                    message=f"Falta dato requerido '{field}' para avanzar a '{next_state}'",
                    should_rollback=False
                )
        
        return RuleCheckResult(passed=True)
    
    def get_next_mandatory_state(self, current_state: str) -> Optional[str]:
        """
        Obtener el siguiente estado obligatorio.
        """
        if current_state not in self.MANDATORY_STATES:
            return self.MANDATORY_STATES[0] if self.MANDATORY_STATES else None
        
        current_idx = self.MANDATORY_STATES.index(current_state)
        
        if current_idx < len(self.MANDATORY_STATES) - 1:
            return self.MANDATORY_STATES[current_idx + 1]
        
        return None  # Ya completó todos los estados obligatorios
    
    def is_understanding_confirmed(self, context: Dict[str, Any]) -> bool:
        """
        Verificar si el entendimiento está confirmado.
        """
        understanding = context.get("understanding", {})
        return understanding.get("confirmed_by_user", False)
    
    def get_completed_states(self, context: Dict[str, Any]) -> List[str]:
        """
        Obtener lista de estados completados.
        """
        topics = context.get("topics_discussed", [])
        completed = []
        
        for state in self.MANDATORY_STATES:
            # Mapear estados a topics
            topic_map = {
                "greeting": "greeting",
                "deep_motivation": "motivation",
                "who_migrates": "family",
                "current_situation": "current_situation",
                "desired_life": "desired_life",
                "real_constraints": "constraints",
                "understanding": "understanding",
            }
            
            topic = topic_map.get(state, state)
            if topic in topics or state in topics:
                completed.append(state)
        
        return completed
    
    # =========================================================================
    # CONVERSACIÓN VS FORMULARIOS (parte del Segmento 2/4)
    # =========================================================================
    
    def check_form_prerequisites(
        self,
        interaction_count: int,
        has_dialogue: bool,
        has_empathy: bool,
        has_explanation: bool
    ) -> RuleCheckResult:
        """
        Verificar que antes de un formulario exista:
        - Diálogo libre
        - Empatía
        - Explicación del porqué se pregunta
        """
        if not has_dialogue:
            return RuleCheckResult(
                passed=False,
                violation=RuleViolation.FORM_WITHOUT_DIALOGUE,
                message="Formulario sin diálogo previo"
            )
        
        if not has_empathy:
            return RuleCheckResult(
                passed=False,
                violation=RuleViolation.FORM_WITHOUT_DIALOGUE,
                message="Formulario sin empatía previa"
            )
        
        if not has_explanation:
            return RuleCheckResult(
                passed=False,
                violation=RuleViolation.FORM_WITHOUT_DIALOGUE,
                message="Formulario sin explicación del porqué"
            )
        
        return RuleCheckResult(passed=True)
    
    def check_not_checklist(self, bot_response: str) -> RuleCheckResult:
        """
        REGLA: Está prohibido encadenar preguntas tipo checklist.
        """
        import re
        
        # Detectar múltiples preguntas seguidas
        questions = re.findall(r'\?', bot_response)
        
        if len(questions) > 2:
            return RuleCheckResult(
                passed=False,
                violation=RuleViolation.CHECKLIST_QUESTIONS,
                message="Demasiadas preguntas encadenadas (checklist)"
            )
        
        return RuleCheckResult(passed=True)
    
    # =========================================================================
    # SEGMENTO 3/4 — INTELIGENCIA CONVERSACIONAL
    # =========================================================================
    
    # Patrones de corrección del usuario
    CORRECTION_PATTERNS = [
        r"no,?\s*(en realidad|quise decir|me equivoqué)",
        r"corrijo",
        r"no es así",
        r"cambiar",
        r"corregir",
        r"no,?\s*es",
        r"en realidad",
        r"me equivoqué",
        r"quería decir",
        r"no,?\s*lo que",
    ]
    
    # Patrones de respuesta fuera de tema
    OFF_TOPIC_INDICATORS = [
        r"otra cosa",
        r"cambiando de tema",
        r"por cierto",
        r"antes de eso",
        r"una pregunta",
        r"tengo una duda",
        r"\?",  # Pregunta del usuario
    ]
    
    def detect_user_correction(self, user_text: str) -> Tuple[bool, Optional[str]]:
        """
        Detectar si el usuario está corrigiendo algo.
        
        REGLA: Si el usuario corrige algo, el sistema:
        - NO avanza
        - Reinterpreta
        - Confirma nuevamente
        
        Returns:
            (is_correction, correction_type)
        """
        import re
        text_lower = user_text.lower()
        
        for pattern in self.CORRECTION_PATTERNS:
            if re.search(pattern, text_lower):
                # Determinar tipo de corrección basado en contenido
                if any(w in text_lower for w in ["familia", "solo", "esposa", "hijos", "pareja"]):
                    return True, "family_correction"
                elif any(w in text_lower for w in ["trabajo", "profesión", "ingeniero", "contador", "abogado", "médico"]):
                    return True, "profession_correction"
                elif any(w in text_lower for w in ["dinero", "ahorro", "$", "dólares", "pesos"]):
                    return True, "financial_correction"
                else:
                    return True, "general_correction"
        
        return False, None
    
    def detect_off_topic_response(
        self,
        user_text: str,
        expected_topic: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Detectar si el usuario respondió algo fuera de la pregunta.
        
        REGLA: Si el usuario responde algo fuera de la pregunta:
        - Interpretar intención
        - Ajustar contexto
        - NO ignorar el mensaje
        
        Returns:
            (is_off_topic, detected_intention)
        """
        import re
        text_lower = user_text.lower()
        
        # Detectar si es una pregunta del usuario
        if "?" in user_text:
            return True, "user_question"
        
        # Detectar cambio de tema explícito
        for pattern in self.OFF_TOPIC_INDICATORS:
            if re.search(pattern, text_lower):
                return True, "topic_change"
        
        # Detectar si habla de algo diferente al tema esperado
        topic_keywords = {
            "motivation": ["quiero", "necesito", "busco", "sueño", "deseo"],
            "family": ["familia", "esposa", "hijos", "solo", "pareja"],
            "profession": ["trabajo", "profesión", "experiencia", "años"],
            "lifestyle": ["vida", "vivir", "ciudad", "clima"],
            "constraints": ["dinero", "ahorro", "tiempo", "urgencia"],
        }
        
        expected_keywords = topic_keywords.get(expected_topic, [])
        
        # Si no menciona ninguna palabra clave del tema esperado
        if expected_keywords and not any(kw in text_lower for kw in expected_keywords):
            # Detectar qué tema sí mencionó
            for topic, keywords in topic_keywords.items():
                if topic != expected_topic and any(kw in text_lower for kw in keywords):
                    return True, f"talking_about_{topic}"
        
        return False, None
    
    def handle_correction(
        self,
        user_text: str,
        correction_type: str,
        current_understanding: Dict[str, Any],
        lang: str = "es"
    ) -> Dict[str, Any]:
        """
        Manejar una corrección del usuario.
        
        Returns:
            Dict con:
            - response: Mensaje de confirmación
            - should_reinterpret: True
            - field_to_update: Campo a actualizar
        """
        if lang == "es":
            responses = {
                "family_correction": (
                    "Entendido, gracias por la aclaración. 🙏\n\n"
                    "Entonces, ¿me confirmas quiénes migrarían contigo?"
                ),
                "profession_correction": (
                    "Gracias por corregirme. 📝\n\n"
                    "¿Cuál es tu profesión o trabajo actual?"
                ),
                "financial_correction": (
                    "Entiendo, actualizo esa información. 💰\n\n"
                    "¿Con cuánto cuentas aproximadamente?"
                ),
                "general_correction": (
                    "Gracias por la aclaración. 🙏\n\n"
                    "Cuéntame más para asegurarme de entenderte bien."
                ),
            }
        else:
            responses = {
                "family_correction": (
                    "Understood, thanks for the clarification. 🙏\n\n"
                    "So, can you confirm who would be migrating with you?"
                ),
                "general_correction": (
                    "Thanks for the clarification. 🙏\n\n"
                    "Tell me more so I can make sure I understand you correctly."
                ),
            }
        
        field_map = {
            "family_correction": "family_members",
            "profession_correction": "current_profession",
            "financial_correction": "available_savings",
            "general_correction": None,
        }
        
        return {
            "response": responses.get(correction_type, responses["general_correction"]),
            "should_reinterpret": True,
            "field_to_update": field_map.get(correction_type),
            "should_advance": False,  # NUNCA avanzar en corrección
        }
    
    def handle_off_topic(
        self,
        user_text: str,
        detected_intention: str,
        current_phase: str,
        lang: str = "es"
    ) -> Dict[str, Any]:
        """
        Manejar respuesta fuera de tema.
        
        REGLA: NO ignorar el mensaje, interpretar y ajustar.
        """
        if lang == "es":
            if detected_intention == "user_question":
                return {
                    "response": (
                        "Buena pregunta. 🤔\n\n"
                        "Déjame responderla y luego continuamos."
                    ),
                    "should_answer_question": True,
                    "should_advance": False,
                }
            elif detected_intention == "topic_change":
                return {
                    "response": (
                        "Entiendo que quieres hablar de eso. 💬\n\n"
                        "Cuéntame, te escucho."
                    ),
                    "should_adjust_context": True,
                    "should_advance": False,
                }
            elif detected_intention.startswith("talking_about_"):
                topic = detected_intention.replace("talking_about_", "")
                return {
                    "response": (
                        f"Veo que mencionas algo sobre {topic}. 📝\n\n"
                        "Eso es importante, lo tengo en cuenta."
                    ),
                    "should_store_info": True,
                    "detected_topic": topic,
                    "should_advance": False,
                }
        
        return {
            "response": "Entiendo. Cuéntame más.",
            "should_advance": False,
        }
    
    def handle_audio_message(
        self,
        transcription: str,
        lang: str = "es"
    ) -> Dict[str, Any]:
        """
        Manejar mensaje de audio.
        
        REGLA: Si llega audio:
        - Transcribir
        - Parafrasear
        - Confirmar comprensión
        """
        # Parafrasear el contenido
        paraphrase = self._paraphrase_text(transcription, lang)
        
        if lang == "es":
            response = (
                f"Escuché tu mensaje de voz. 🎤\n\n"
                f"Entiendo que: *{paraphrase}*\n\n"
                f"¿Es correcto o quieres que ajuste algo?"
            )
        else:
            response = (
                f"I heard your voice message. 🎤\n\n"
                f"I understand that: *{paraphrase}*\n\n"
                f"Is that correct or would you like me to adjust something?"
            )
        
        return {
            "response": response,
            "transcription": transcription,
            "paraphrase": paraphrase,
            "requires_confirmation": True,
            "should_advance": False,  # Esperar confirmación
        }
    
    def _paraphrase_text(self, text: str, lang: str = "es") -> str:
        """
        Parafrasear texto para confirmar comprensión.
        """
        # Simplificar y resumir el texto
        # Por ahora, una versión simple
        text = text.strip()
        
        if len(text) > 100:
            # Tomar las primeras oraciones
            sentences = text.split(".")
            if len(sentences) > 2:
                text = ". ".join(sentences[:2]) + "..."
        
        return text
    
    def check_response_has_explanation(
        self,
        bot_response: str,
        lang: str = "es"
    ) -> RuleCheckResult:
        """
        REGLA: MigPAL DEBE explicar lo que hace y por qué pregunta.
        
        Verificar que la respuesta incluya contexto/explicación.
        """
        import re
        response_lower = bot_response.lower()
        
        # Patrones que indican explicación
        explanation_patterns_es = [
            r"porque",
            r"para (poder|entender|conocer|ayudarte)",
            r"esto (me ayuda|es importante|sirve)",
            r"así (puedo|podré)",
            r"necesito (saber|entender|conocer)",
            r"quiero (asegurarme|entender)",
            r"es importante",
            r"me ayuda a",
        ]
        
        explanation_patterns_en = [
            r"because",
            r"so (i can|that i)",
            r"this (helps|is important)",
            r"i need to (know|understand)",
            r"i want to (make sure|understand)",
        ]
        
        patterns = explanation_patterns_es if lang == "es" else explanation_patterns_en
        
        # Verificar si hay alguna explicación
        has_explanation = any(
            re.search(pattern, response_lower)
            for pattern in patterns
        )
        
        # También es válido si es una respuesta empática o de confirmación
        empathy_patterns = [
            r"entiendo",
            r"gracias por",
            r"comprendo",
            r"me cuentas",
            r"cuéntame",
        ]
        
        has_empathy = any(
            re.search(pattern, response_lower)
            for pattern in empathy_patterns
        )
        
        if has_explanation or has_empathy:
            return RuleCheckResult(passed=True)
        
        # Si es una pregunta directa sin contexto, es violación
        if "?" in bot_response and not has_explanation and not has_empathy:
            self._log_violation(RuleViolation.NO_EXPLANATION_WHY, "bot_response")
            return RuleCheckResult(
                passed=False,
                violation=RuleViolation.NO_EXPLANATION_WHY,
                message="Respuesta sin explicación del porqué se pregunta"
            )
        
        return RuleCheckResult(passed=True)
    
    def _log_violation(self, violation: RuleViolation, context: str):
        """Registrar violación para análisis"""
        from datetime import datetime
        self.violations_log.append({
            "timestamp": datetime.now().isoformat(),
            "violation": violation.value,
            "context": context
        })
        logger.warning(f"🔒 REGLA VIOLADA: {violation.value} en {context}")
    
    def get_violations_summary(self) -> Dict[str, int]:
        """Obtener resumen de violaciones"""
        summary = {}
        for v in self.violations_log:
            key = v["violation"]
            summary[key] = summary.get(key, 0) + 1
        return summary


# Singleton
_guardian = None

def get_hard_rules_guardian() -> HardRulesGuardian:
    """Obtener instancia del guardián de reglas duras"""
    global _guardian
    if _guardian is None:
        _guardian = HardRulesGuardian()
    return _guardian


# =========================================================================
# FUNCIONES DE CONVENIENCIA
# =========================================================================

def can_advance_phase(
    current_phase: str,
    next_phase: str,
    user_text: str,
    context: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Verificar si se puede avanzar de fase.
    
    Returns:
        (can_advance, reason)
    """
    guardian = get_hard_rules_guardian()
    
    result = guardian.check_all_rules(
        current_phase=current_phase,
        next_phase=next_phase,
        user_text=user_text,
        bot_response="",  # No tenemos respuesta aún
        context=context,
        interaction_count=context.get("interaction_count", 0),
        form_count=context.get("form_count", 0),
        last_form_interaction=context.get("last_form_interaction", 0),
    )
    
    return result.passed, result.message


def can_show_visa_options(context: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Verificar si se pueden mostrar opciones de visa.
    
    Returns:
        (can_show, reason)
    """
    understanding = context.get("understanding", {})
    
    # Verificar perfil completo
    guardian = get_hard_rules_guardian()
    result = guardian._check_no_visa_without_profile("options", context)
    
    if not result.passed:
        return False, result.message
    
    # Verificar resumen confirmado
    result = guardian._check_no_options_without_summary("options", context)
    
    if not result.passed:
        return False, result.message
    
    return True, "OK"


def should_rollback_on_doubt(user_text: str) -> bool:
    """
    Verificar si el usuario expresó duda y se debe hacer rollback.
    """
    guardian = get_hard_rules_guardian()
    result = guardian._check_no_advance_on_doubt(user_text, "any", "different")
    return not result.passed

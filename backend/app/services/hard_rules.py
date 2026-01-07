#!/usr/bin/env python3
"""
🔒 REGLAS DURAS DE SISTEMA - MigPAL USA
=======================================

Este módulo contiene las RESTRICCIONES OBLIGATORIAS del motor conversacional.
NO son sugerencias ni UX. Son reglas inviolables.

Si una regla se viola → el flujo NO puede avanzar.
Si hay conflicto código vs regla → LA REGLA PREVALECE.

SEGMENTOS:
1/4 - Principios Inviolables (Core)
2/4 - Conversación vs Formularios
3/4 - (Pendiente)
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
    
    # Segmento 2/4 - Conversación vs Formularios
    FORM_WITHOUT_DIALOGUE = "form_without_dialogue"
    CHECKLIST_QUESTIONS = "checklist_questions"
    IGNORED_USER_INPUT = "ignored_user_input"
    BOT_LIKE_BEHAVIOR = "bot_like_behavior"


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
    # SEGMENTO 2/4 — CONVERSACIÓN VS FORMULARIOS
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

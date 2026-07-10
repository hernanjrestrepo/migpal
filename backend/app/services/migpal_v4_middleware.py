#!/usr/bin/env python3
"""
MigPAL V4 Middleware
====================
Middleware de integración del estándar MigPAL USA v4.0.

FEATURE FLAG: MIGPAL_USA_STANDARD_V4=1
- Si está activo, aplica todas las reglas del estándar v4.0
- Si falla, hace fallback al flujo actual sin interrumpir

FUNCIONES:
1. pre_process() - Antes de procesar el mensaje
2. post_process() - Después de generar la respuesta
3. check_gating() - Verificar gating de visa
4. format_response() - Formatear respuesta según reglas
"""

import logging
import os
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)

# ============== FEATURE FLAG ==============
MIGPAL_USA_STANDARD_V4 = os.getenv("MIGPAL_USA_STANDARD_V4", "1") == "1"

logger.info(f"🚀 MigPAL USA Standard V4: {'ENABLED' if MIGPAL_USA_STANDARD_V4 else 'DISABLED'}")


def is_v4_enabled() -> bool:
    """Verifica si el estándar v4.0 está habilitado"""
    return MIGPAL_USA_STANDARD_V4


def safe_v4_call(func):
    """Decorador para llamadas seguras al estándar v4.0 con fallback"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not MIGPAL_USA_STANDARD_V4:
            return None
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"V4 middleware error in {func.__name__}: {e}")
            return None

    return wrapper


# ============== IMPORTS CONDICIONALES ==============

_standard = None
_integration = None


def _load_v4_modules():
    """Carga los módulos v4.0 de forma lazy"""
    global _standard, _integration

    if not MIGPAL_USA_STANDARD_V4:
        return False

    if _standard is None:
        try:
            from . import migpal_usa_integration, migpal_usa_standard

            _standard = migpal_usa_standard
            _integration = migpal_usa_integration
            logger.info("✅ V4 modules loaded successfully")
            return True
        except ImportError as e:
            logger.error(f"Failed to load V4 modules: {e}")
            return False
    return True


# ============== MIDDLEWARE FUNCTIONS ==============


@safe_v4_call
def pre_process_message(
    user_id: int, text: str, state: str, user_data: dict[str, Any]
) -> dict[str, Any] | None:
    """
    Pre-procesa el mensaje antes del handler principal.

    Returns:
        Dict con información de pre-procesamiento o None si no aplica
    """
    if not _load_v4_modules():
        return None

    standard = _standard.get_migpal_standard()
    conv_state = standard.get_state(user_id)

    # Actualizar datos del perfil
    if user_data.get("profile"):
        conv_state.profile_data.update(user_data.get("profile", {}))

    # Verificar si se puede mostrar formulario
    can_form = standard.can_show_form(user_id)

    # Verificar si agregar micro-check
    should_micro_check = standard.should_add_micro_check(user_id)

    return {
        "can_show_form": can_form,
        "should_micro_check": should_micro_check,
        "current_phase": conv_state.current_phase.value if conv_state.current_phase else "unknown",
        "turn_count": conv_state.turn_count,
        "profile_complete": conv_state.profile_complete,
        "summary_confirmed": conv_state.summary_confirmed,
    }


@safe_v4_call
def post_process_response(user_id: int, response: str, is_form: bool = False) -> str:
    """
    Post-procesa la respuesta aplicando reglas del estándar v4.0.

    Args:
        user_id: ID del usuario
        response: Respuesta original
        is_form: Si la respuesta incluye un formulario

    Returns:
        Respuesta formateada según el estándar
    """
    if not _load_v4_modules():
        return response

    standard = _standard.get_migpal_standard()

    # Aplicar reglas de formato
    formatted = standard.format_response(user_id, response, is_form=is_form)

    result = formatted.text

    # Agregar micro-check si corresponde
    if formatted.include_micro_check:
        micro_check = standard.get_micro_check("es")
        result += f"\n\n{micro_check}"

    return result


@safe_v4_call
def check_visa_gating(user_id: int, user_data: dict[str, Any]) -> tuple[bool, str]:
    """
    Verifica si se puede recomendar visa.

    Returns:
        Tuple[bool, str]: (puede_recomendar, mensaje_bloqueo)
    """
    if not _load_v4_modules():
        return True, ""

    return _integration.check_and_enforce_gating(user_id, user_data, "recommend_visa")


@safe_v4_call
def get_progress_indicator(user_id: int) -> str | None:
    """
    Obtiene el indicador de progreso actual.
    """
    if not _load_v4_modules():
        return None

    return _integration.get_conversation_progress(user_id)


@safe_v4_call
def evaluate_states(user_id: int, custom_weights: dict[str, float] | None = None) -> str | None:
    """
    Genera evaluación ponderada de estados USA.
    """
    if not _load_v4_modules():
        return None

    return _integration.generate_state_evaluation(user_id, custom_weights)


@safe_v4_call
def evaluate_cities(state: str, user_id: int, custom_weights: dict[str, float] | None = None) -> str | None:
    """
    Genera evaluación ponderada de ciudades.
    """
    if not _load_v4_modules():
        return None

    return _integration.generate_city_evaluation(state, user_id, custom_weights)


@safe_v4_call
def evaluate_businesses(
    user_id: int, budget: float = 150000, custom_weights: dict[str, float] | None = None
) -> str | None:
    """
    Genera evaluación ponderada de negocios.
    """
    if not _load_v4_modules():
        return None

    return _integration.generate_business_evaluation(user_id, budget, custom_weights)


@safe_v4_call
def mark_profile_complete(user_id: int) -> None:
    """Marca el perfil como completo"""
    if not _load_v4_modules():
        return

    _integration.complete_profile(user_id)


@safe_v4_call
def mark_summary_confirmed(user_id: int) -> None:
    """Marca el resumen como confirmado"""
    if not _load_v4_modules():
        return

    _integration.confirm_summary(user_id)


@safe_v4_call
def advance_phase(user_id: int, phase_name: str) -> None:
    """Avanza a una nueva fase"""
    if not _load_v4_modules():
        return

    try:
        phase = _standard.ConversationPhase(phase_name)
        _integration.advance_to_phase(user_id, phase)
    except ValueError:
        logger.warning(f"Unknown phase: {phase_name}")


@safe_v4_call
def get_document_checklist(visa_type: str) -> str | None:
    """Obtiene checklist de documentos formateado"""
    if not _load_v4_modules():
        return None

    checklist = _integration.get_document_checklist_for_visa(visa_type)
    return _integration.format_checklist_message(checklist, f"Documentos para {visa_type}")


@safe_v4_call
def get_installation_checklist() -> str | None:
    """Obtiene checklist de instalación formateado"""
    if not _load_v4_modules():
        return None

    checklist = _integration.get_installation_checklist()
    return _integration.format_checklist_message(checklist, "Checklist de Instalación en USA")


@safe_v4_call
def get_interview_prep(visa_type: str) -> dict[str, Any] | None:
    """Obtiene preparación de entrevista"""
    if not _load_v4_modules():
        return None

    return _integration.get_interview_preparation(visa_type)


@safe_v4_call
def should_add_micro_check(user_id: int) -> bool:
    """Determina si agregar micro-check"""
    if not _load_v4_modules():
        return False

    return _integration.should_add_micro_check(user_id)


@safe_v4_call
def get_micro_check(lang: str = "es") -> str | None:
    """Obtiene un micro-check aleatorio"""
    if not _load_v4_modules():
        return None

    return _integration.get_micro_check(lang)


# ============== HANDLER WRAPPER ==============


def v4_message_handler(original_handler):
    """
    Decorador para wrappear handlers de mensaje con el estándar v4.0.

    Uso:
        @v4_message_handler
        async def _handle_message(self, update, context):
            ...
    """

    @wraps(original_handler)
    async def wrapper(self, update, context):
        user_id = update.effective_user.id
        text = update.message.text.strip() if update.message.text else ""

        # Pre-proceso v4
        pre_info = None
        if MIGPAL_USA_STANDARD_V4:
            try:
                user = self.get_user_data(user_id) if hasattr(self, "get_user_data") else {}
                state = self.get_state(user_id) if hasattr(self, "get_state") else "start"
                pre_info = pre_process_message(user_id, text, state, user)

                if pre_info:
                    logger.debug(f"V4 pre-process: {pre_info}")
            except Exception as e:
                logger.warning(f"V4 pre-process error: {e}")

        # Ejecutar handler original
        result = await original_handler(self, update, context)

        return result

    return wrapper


# ============== RESPONSE FORMATTER ==============


class V4ResponseFormatter:
    """
    Formateador de respuestas según el estándar v4.0.
    Uso como context manager para formatear respuestas automáticamente.
    """

    def __init__(self, user_id: int, include_progress: bool = True):
        self.user_id = user_id
        self.include_progress = include_progress
        self.original_response = ""
        self.formatted_response = ""

    def format(self, response: str, is_form: bool = False) -> str:
        """Formatea una respuesta"""
        self.original_response = response

        if not MIGPAL_USA_STANDARD_V4:
            self.formatted_response = response
            return response

        try:
            # Aplicar formato v4
            formatted = post_process_response(self.user_id, response, is_form)

            # Agregar indicador de progreso si corresponde
            if self.include_progress:
                progress = get_progress_indicator(self.user_id)
                if progress:
                    formatted = f"{progress}\n\n{formatted}"

            self.formatted_response = formatted
            return formatted
        except Exception as e:
            logger.warning(f"V4 format error: {e}")
            self.formatted_response = response
            return response


# ============== GATING ENFORCER ==============


class V4GatingEnforcer:
    """
    Enforcer de gating para recomendaciones de visa.
    """

    def __init__(self, user_id: int, user_data: dict[str, Any]):
        self.user_id = user_id
        self.user_data = user_data
        self.can_recommend = True
        self.blocking_message = ""

    def check(self) -> tuple[bool, str]:
        """Verifica si se puede recomendar visa"""
        if not MIGPAL_USA_STANDARD_V4:
            return True, ""

        try:
            self.can_recommend, self.blocking_message = check_visa_gating(self.user_id, self.user_data)
            return self.can_recommend, self.blocking_message
        except Exception as e:
            logger.warning(f"V4 gating check error: {e}")
            return True, ""

    def enforce(self) -> str | None:
        """
        Aplica el gating y retorna mensaje de bloqueo si aplica.
        Returns None si puede continuar.
        """
        can, msg = self.check()
        if not can:
            return msg
        return None


# ============== EXPORTAR ==============

__all__ = [
    "MIGPAL_USA_STANDARD_V4",
    "is_v4_enabled",
    "safe_v4_call",
    "pre_process_message",
    "post_process_response",
    "check_visa_gating",
    "get_progress_indicator",
    "evaluate_states",
    "evaluate_cities",
    "evaluate_businesses",
    "mark_profile_complete",
    "mark_summary_confirmed",
    "advance_phase",
    "get_document_checklist",
    "get_installation_checklist",
    "get_interview_prep",
    "should_add_micro_check",
    "get_micro_check",
    "v4_message_handler",
    "V4ResponseFormatter",
    "V4GatingEnforcer",
]

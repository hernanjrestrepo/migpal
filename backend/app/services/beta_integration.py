"""
MigPAL Beta Integration V3.0
============================
Integración del sistema de beta tracking con el bot de Telegram.

Este módulo conecta el beta_tracker con el flujo del bot para:
- Registrar eventos automáticamente
- Mostrar mensajes de beta
- Solicitar feedback al final
"""

import json
import logging
from pathlib import Path
from typing import Any

from .beta_tracker import (
    BETA_MODE,
    EventType,
    get_beta_tracker,
    process_feedback,
)
from .phase_manager import get_phase_manager
from .ux_helpers import get_progress_header

logger = logging.getLogger(__name__)

# Configuración
BETA_CONFIG_PATH = Path("data/beta_logs/beta_config.json")


def load_beta_config() -> dict[str, Any]:
    """Carga configuración de beta"""
    try:
        if BETA_CONFIG_PATH.exists():
            with open(BETA_CONFIG_PATH) as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading beta config: {e}")
    return {}


def save_beta_config(config: dict[str, Any]):
    """Guarda configuración de beta"""
    try:
        with open(BETA_CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving beta config: {e}")


def is_beta_user(user_id: int) -> bool:
    """Verifica si un usuario es parte del beta"""
    if not BETA_MODE:
        return False

    config = load_beta_config()
    return user_id in config.get("beta_users", [])


def add_beta_user(user_id: int, profile_type: str = "") -> bool:
    """Agrega usuario al beta"""
    config = load_beta_config()

    if user_id not in config.get("beta_users", []):
        if "beta_users" not in config:
            config["beta_users"] = []
        config["beta_users"].append(user_id)

        # Actualizar contador de perfil
        for profile in config.get("target_profiles", []):
            if profile["type"] == profile_type:
                profile["recruited"] += 1
                break

        save_beta_config(config)

        # Registrar evento
        tracker = get_beta_tracker()
        tracker.log_event(user_id, EventType.SESSION_START, "REGISTRO", {"profile_type": profile_type})

        # Actualizar métricas
        metrics = tracker._get_or_create_metrics(user_id)
        metrics.profile_type = profile_type
        tracker._save_metrics()

        logger.info(f"🧪 Beta user added: {user_id} ({profile_type})")
        return True

    return False


def get_beta_welcome_message() -> str:
    """Obtiene mensaje de bienvenida para beta"""
    config = load_beta_config()
    return config.get(
        "recruitment_message",
        """
🧪 ¡Bienvenido al Beta de MigPAL!

Eres parte de un grupo selecto probando nuestra nueva versión V3.0.

✅ **Beneficios:**
• Acceso gratuito al diagnóstico ($50 valor)
• Soporte prioritario
• Tu feedback moldea el producto

¿Listo para comenzar?
""",
    )


def get_beta_completion_message() -> str:
    """Obtiene mensaje de completación de beta"""
    config = load_beta_config()
    return config.get(
        "completion_bonus",
        """
🎉 ¡Gracias por completar el beta!

Como agradecimiento, recibirás **50% de descuento** en tu Plan Maestro.

Código: BETA50
""",
    )


# ============== HOOKS PARA EL BOT ==============


def on_message_received(user_id: int, message: str, phase: str):
    """Hook cuando se recibe un mensaje"""
    if not BETA_MODE:
        return

    tracker = get_beta_tracker()
    tracker.log_event(
        user_id,
        EventType.MESSAGE_RECEIVED,
        phase,
        {"message_length": len(message), "message_preview": message[:50]},
    )


def on_message_sent(user_id: int, message: str, phase: str):
    """Hook cuando se envía un mensaje"""
    if not BETA_MODE:
        return

    tracker = get_beta_tracker()
    tracker.log_event(user_id, EventType.MESSAGE_SENT, phase, {"message_length": len(message)})


def on_phase_start(user_id: int, phase: str):
    """Hook cuando inicia una fase"""
    if not BETA_MODE:
        return

    tracker = get_beta_tracker()
    tracker.log_event(user_id, EventType.PHASE_START, phase)
    logger.info(f"🧪 Phase started: {phase} for user {user_id}")


def on_phase_complete(user_id: int, phase: str):
    """Hook cuando se completa una fase"""
    if not BETA_MODE:
        return

    tracker = get_beta_tracker()
    tracker.log_event(user_id, EventType.PHASE_COMPLETE, phase)
    logger.info(f"🧪 Phase completed: {phase} for user {user_id}")


def on_question_asked(user_id: int, question: str, phase: str):
    """Hook cuando se hace una pregunta"""
    if not BETA_MODE:
        return

    tracker = get_beta_tracker()
    tracker.log_event(user_id, EventType.QUESTION_ASKED, phase, {"question": question})


def on_off_topic_detected(user_id: int, message: str, phase: str):
    """Hook cuando se detecta off-topic"""
    if not BETA_MODE:
        return

    tracker = get_beta_tracker()
    tracker.log_event(user_id, EventType.OFF_TOPIC_DETECTED, phase, {"message": message[:100]})


def on_frustration_detected(user_id: int, message: str, phase: str):
    """Hook cuando se detecta frustración"""
    if not BETA_MODE:
        return

    tracker = get_beta_tracker()
    tracker.log_event(user_id, EventType.FRUSTRATION_DETECTED, phase, {"message": message[:100]})


def on_fallback_used(user_id: int, fallback_type: str, phase: str):
    """Hook cuando se usa un fallback"""
    if not BETA_MODE:
        return

    tracker = get_beta_tracker()
    tracker.log_event(user_id, EventType.FALLBACK_USED, phase, {"fallback_type": fallback_type})


def on_data_extracted(user_id: int, field: str, value: str, phase: str):
    """Hook cuando se extrae un dato"""
    if not BETA_MODE:
        return

    tracker = get_beta_tracker()
    tracker.log_event(
        user_id, EventType.DATA_EXTRACTED, phase, {"field": field, "value_length": len(str(value))}
    )


def on_payment_prompted(user_id: int, amount: float, phase: str):
    """Hook cuando se invita al pago"""
    if not BETA_MODE:
        return

    tracker = get_beta_tracker()
    tracker.log_event(user_id, EventType.PAYMENT_PROMPTED, phase, {"amount": amount})


def on_payment_completed(user_id: int, amount: float, phase: str):
    """Hook cuando se completa un pago"""
    if not BETA_MODE:
        return

    tracker = get_beta_tracker()
    tracker.log_event(user_id, EventType.PAYMENT_COMPLETED, phase, {"amount": amount})


def on_deliverable_generated(user_id: int, deliverable_type: str, phase: str):
    """Hook cuando se genera un entregable"""
    if not BETA_MODE:
        return

    tracker = get_beta_tracker()
    tracker.log_event(user_id, EventType.DELIVERABLE_GENERATED, phase, {"deliverable_type": deliverable_type})


def on_error(user_id: int, error: str, phase: str):
    """Hook cuando ocurre un error"""
    if not BETA_MODE:
        return

    tracker = get_beta_tracker()
    tracker.log_event(user_id, EventType.ERROR_OCCURRED, phase, {"error": error[:200]})


# ============== FORMATO DE MENSAJES BETA ==============


def format_beta_message(user_id: int, message: str, phase: str) -> str:
    """Formatea mensaje con header de beta y progreso"""
    if not BETA_MODE:
        return message

    # Obtener header de progreso
    pm = get_phase_manager()
    header = get_progress_header(user_id, pm)

    # Agregar indicador de beta
    beta_indicator = "🧪 BETA"

    return f"{beta_indicator} | {header}\n\n{message}"


# ============== FEEDBACK ==============


def should_request_feedback(user_id: int, phase: str) -> bool:
    """Determina si se debe solicitar feedback"""
    if not BETA_MODE:
        return False

    # Solicitar feedback al completar CIERRE
    if phase == "CIERRE":
        tracker = get_beta_tracker()
        metrics = tracker.get_user_metrics(user_id)
        if metrics and not metrics.feedback_score:
            return True

    return False


def handle_feedback_response(user_id: int, message: str) -> str | None:
    """Maneja respuesta de feedback"""
    if not BETA_MODE:
        return None

    success, response = process_feedback(user_id, message)
    return response


# ============== REPORTE ==============


def get_beta_status() -> str:
    """Obtiene estado actual del beta"""
    config = load_beta_config()
    tracker = get_beta_tracker()

    total_users = len(config.get("beta_users", []))
    target = config.get("target_users", 10)

    # Contar por perfil
    profile_counts = {}
    for profile in config.get("target_profiles", []):
        profile_counts[profile["type"]] = {
            "target": profile["target_count"],
            "recruited": profile["recruited"],
        }

    # Métricas actuales
    completed = len(tracker.get_completed_users())
    active = len(tracker.get_active_users())

    status = f"""
📊 **ESTADO BETA MigPAL V3.0**

**Reclutamiento:** {total_users}/{target} usuarios

**Por perfil:**
"""
    for ptype, counts in profile_counts.items():
        status += f"• {ptype}: {counts['recruited']}/{counts['target']}\n"

    status += f"""
**Progreso:**
• Activos: {active}
• Completados: {completed}
• Tasa completación: {completed/total_users*100 if total_users > 0 else 0:.1f}%
"""

    return status


__all__ = [
    "is_beta_user",
    "add_beta_user",
    "get_beta_welcome_message",
    "get_beta_completion_message",
    "on_message_received",
    "on_message_sent",
    "on_phase_start",
    "on_phase_complete",
    "on_question_asked",
    "on_off_topic_detected",
    "on_frustration_detected",
    "on_fallback_used",
    "on_data_extracted",
    "on_payment_prompted",
    "on_payment_completed",
    "on_deliverable_generated",
    "on_error",
    "format_beta_message",
    "should_request_feedback",
    "handle_feedback_response",
    "get_beta_status",
]

"""
MigPAL UX Helpers V3.0
======================
Helpers para mejorar la experiencia de usuario en Telegram.

Incluye:
- Header de progreso visible en cada mensaje
- Formato consistente de mensajes
- Indicadores de fase y siguiente acción
"""

from .phase_manager import PHASE_CONFIG, Phase, get_phase_manager


def get_progress_header(user_id: int, phase_manager=None) -> str:
    """
    Genera el header de progreso para mostrar en cada mensaje.

    Formato:
    📍 Paso X de 6 | ▓▓▓░░ 33% | Siguiente: [acción]

    Args:
        user_id: ID del usuario
        phase_manager: Instancia del PhaseManager (opcional)

    Returns:
        String con el header de progreso
    """
    if phase_manager is None:
        phase_manager = get_phase_manager()

    current_phase = phase_manager.get_user_phase(user_id)
    PHASE_CONFIG[current_phase]

    # Número de paso (1-6)
    step_number = current_phase.value + 1
    total_steps = 6

    # Porcentaje de progreso
    progress_percent = int((current_phase.value / 5) * 100)

    # Barra de progreso compacta
    bar_width = 5
    filled = int(bar_width * progress_percent / 100)
    bar = "▓" * filled + "░" * (bar_width - filled)

    # Siguiente acción
    if current_phase == Phase.CIERRE:
        next_action = "¡Completado!"
    else:
        next_phase = Phase(current_phase.value + 1)
        next_config = PHASE_CONFIG[next_phase]
        if next_config.price > 0:
            next_action = f"{next_config.name} (${next_config.price})"
        else:
            next_action = next_config.name

    return f"📍 Paso {step_number} de {total_steps} | {bar} {progress_percent}% | Siguiente: {next_action}"


def get_phase_indicator(user_id: int, phase_manager=None) -> str:
    """
    Genera un indicador de fase más detallado.

    Args:
        user_id: ID del usuario
        phase_manager: Instancia del PhaseManager (opcional)

    Returns:
        String con el indicador de fase
    """
    if phase_manager is None:
        phase_manager = get_phase_manager()

    current_phase = phase_manager.get_user_phase(user_id)
    PHASE_CONFIG[current_phase]

    # Mostrar todas las fases con estado
    phases_display = []
    for phase in Phase:
        p_config = PHASE_CONFIG[phase]
        if phase.value < current_phase.value:
            status = "✅"
        elif phase == current_phase:
            status = "🔄"
        else:
            status = "⬜"
        phases_display.append(f"{status}{p_config.emoji}")

    return " ".join(phases_display)


def format_message_with_progress(
    user_id: int,
    message: str,
    show_header: bool = True,
    show_phase_indicator: bool = False,
    phase_manager=None,
) -> str:
    """
    Formatea un mensaje agregando el header de progreso.

    Args:
        user_id: ID del usuario
        message: Mensaje original
        show_header: Si mostrar el header de progreso
        show_phase_indicator: Si mostrar el indicador de fases
        phase_manager: Instancia del PhaseManager (opcional)

    Returns:
        Mensaje formateado con progreso
    """
    parts = []

    if show_header:
        header = get_progress_header(user_id, phase_manager)
        parts.append(header)

    if show_phase_indicator:
        indicator = get_phase_indicator(user_id, phase_manager)
        parts.append(indicator)

    if parts:
        parts.append("")  # Línea en blanco
        parts.append(message)
        return "\n".join(parts)

    return message


def get_payment_invitation(phase: Phase, user_name: str = "") -> str:
    """
    Genera una invitación natural al pago al cerrar una fase.

    Args:
        phase: Fase que se va a pagar
        user_name: Nombre del usuario (opcional)

    Returns:
        Mensaje de invitación al pago
    """
    config = PHASE_CONFIG[phase]

    if config.price == 0:
        return ""

    name_part = f", {user_name}" if user_name else ""

    # Mensajes naturales según la fase
    invitations = {
        Phase.DIAGNOSTICO: f"""
¡Excelente{name_part}! 🎉 Has completado tu registro.

Ahora viene lo importante: el **Diagnóstico** donde evaluaré tu viabilidad real y te diré exactamente qué visa te conviene.

💰 Inversión: **${config.price} USD**

Incluye:
• Análisis de todas las visas aplicables
• Tu probabilidad de éxito
• Obstáculos identificados
• Reporte PDF personalizado

¿Cómo prefieres pagar?
""",
        Phase.PERFILAMIENTO: f"""
¡Muy bien{name_part}! 📊 Tu diagnóstico está listo.

El siguiente paso es el **Perfilamiento Completo** donde recopilaré toda tu información para armar tu caso.

💰 Inversión: **${config.price} USD**

Incluye:
• Perfil migratorio completo (100+ campos)
• Checklist de documentos
• Estrategia de presentación
• Preparación para entrevista

¿Cómo prefieres pagar?
""",
        Phase.PLAN_MIGRACION: f"""
¡Perfecto{name_part}! 📑 Tu perfil está completo.

Ahora generaré tu **Plan Maestro de Migración** - el documento que consolida TODO tu plan.

💰 Inversión: **${config.price} USD**

Incluye:
• Visa + Ciudad + Empleo + Vivienda
• Presupuesto detallado
• Timeline de 12 meses
• Checklist de acciones

¿Cómo prefieres pagar?
""",
    }

    return invitations.get(
        phase,
        f"""
Para continuar con **{config.name}**, la inversión es de **${config.price} USD**.

¿Cómo prefieres pagar?
""",
    )


def get_payment_options_message() -> str:
    """
    Genera el mensaje con las opciones de pago disponibles.

    Returns:
        Mensaje con opciones de pago
    """
    return """
💳 **Tarjeta** (Visa, Mastercard, Amex)
🅿️ **PayPal**
📱 **Zelle** (USA)
🏦 **Transferencia bancaria**

Selecciona tu método preferido 👇
"""


def get_phase_completion_message(phase: Phase, user_name: str = "") -> str:
    """
    Genera mensaje de celebración al completar una fase.

    Args:
        phase: Fase completada
        user_name: Nombre del usuario (opcional)

    Returns:
        Mensaje de celebración
    """
    config = PHASE_CONFIG[phase]
    name_part = f" {user_name}" if user_name else ""

    messages = {
        Phase.REGISTRO: f"🎉 ¡Registro completado{name_part}! Ya eres parte de MigPAL.",
        Phase.DIAGNOSTICO: f"📊 ¡Diagnóstico listo{name_part}! Ya sé exactamente cómo ayudarte.",
        Phase.PERFILAMIENTO: f"📑 ¡Perfil completo{name_part}! Tengo toda tu información.",
        Phase.PLAN_MIGRACION: f"📋 ¡Plan Maestro generado{name_part}! Tu guía completa está lista.",
        Phase.EJECUCION: f"🚀 ¡Aplicación enviada{name_part}! Ahora a esperar.",
        Phase.CIERRE: f"🎊 ¡FELICIDADES{name_part}! Has completado tu proceso migratorio.",
    }

    return messages.get(phase, f"✅ Fase {config.name} completada.")


def get_missing_data_prompt(missing_fields: list, current_field: str = None) -> str:
    """
    Genera un prompt amigable para solicitar datos faltantes.

    Args:
        missing_fields: Lista de campos faltantes
        current_field: Campo actual que se está solicitando

    Returns:
        Mensaje solicitando el dato
    """
    field_prompts = {
        "name": "¿Cómo te llamas?",
        "origin_country": "¿De qué país eres?",
        "current_city": "¿En qué ciudad vives actualmente?",
        "migrant_type": "¿Qué tipo de migrante eres?",
        "family_composition": "¿Viajas solo o con familia?",
        "migration_reason": "¿Por qué quieres migrar a USA?",
        "education_level": "¿Cuál es tu nivel de estudios?",
        "profession": "¿Cuál es tu profesión?",
        "years_experience": "¿Cuántos años de experiencia tienes?",
        "english_level": "¿Cuál es tu nivel de inglés?",
        "visa_history": "¿Has tenido visas de USA antes?",
        "criminal_record": "¿Tienes antecedentes penales?",
        "savings_range": "¿Cuánto tienes ahorrado aproximadamente?",
    }

    if current_field and current_field in field_prompts:
        return field_prompts[current_field]

    if missing_fields:
        first_field = missing_fields[0]
        return field_prompts.get(first_field, f"Necesito saber tu {first_field}")

    return "¿En qué puedo ayudarte?"


__all__ = [
    "get_progress_header",
    "get_phase_indicator",
    "format_message_with_progress",
    "get_payment_invitation",
    "get_payment_options_message",
    "get_phase_completion_message",
    "get_missing_data_prompt",
]

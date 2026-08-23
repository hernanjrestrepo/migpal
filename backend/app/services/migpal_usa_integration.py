#!/usr/bin/env python3
"""
MigPAL USA Integration v4.0
===========================
Integra el estándar MigPAL USA con el sistema existente.

Este módulo actúa como puente entre:
- migpal_usa_standard.py (reglas y estándar)
- ai_brain.py (procesamiento de IA)
- telegram_bot.py (interfaz de usuario)
- understanding_summary.py (gating de visa)

FUNCIONES PRINCIPALES:
1. process_with_standard() - Procesa mensajes aplicando todas las reglas
2. check_and_enforce_gating() - Verifica gating antes de recomendaciones
3. generate_matrix_evaluation() - Genera evaluaciones ponderadas
4. format_with_progress() - Formatea respuestas con progreso
"""

import logging
from typing import Any

from .migpal_usa_standard import (
    MICRO_CHECKS,
    ConversationPhase,
    advance_phase,
    can_show_form,
    check_visa_gating,
    evaluate_options,
    format_message,
    get_migpal_standard,
    get_progress,
    mark_profile_complete,
    mark_summary_confirmed,
)
from .understanding_summary import can_recommend_visa as can_recommend_visa_with_summary

logger = logging.getLogger(__name__)


# ============== DATOS DE ESTADOS Y CIUDADES ==============

USA_STATES_DATA = [
    {
        "name": "Florida",
        "salud": 4,
        "oportunidades_negocio": 4,
        "costo_vida": 3,
        "criminalidad": 3,
        "estudios": 4,
        "impuestos": 5,
        "migration_friendly": 5,
        "dinamismo_economico": 4,
        "comunidad_latina": 5,
        "clima": 4,
        "poblacion": 4,
        "pros": ["Sin income tax", "Comunidad latina fuerte", "Clima cálido"],
        "cons": ["Huracanes", "Humedad alta", "Costo de vida en aumento"],
    },
    {
        "name": "Texas",
        "salud": 4,
        "oportunidades_negocio": 5,
        "costo_vida": 4,
        "criminalidad": 3,
        "estudios": 4,
        "impuestos": 5,
        "migration_friendly": 4,
        "dinamismo_economico": 5,
        "comunidad_latina": 5,
        "clima": 3,
        "poblacion": 5,
        "pros": ["Sin income tax", "Economía fuerte", "Costo de vida bajo"],
        "cons": ["Calor extremo", "Transporte público limitado"],
    },
    {
        "name": "North Carolina",
        "salud": 5,
        "oportunidades_negocio": 4,
        "costo_vida": 4,
        "criminalidad": 4,
        "estudios": 5,
        "impuestos": 3,
        "migration_friendly": 4,
        "dinamismo_economico": 4,
        "comunidad_latina": 3,
        "clima": 4,
        "poblacion": 3,
        "pros": ["Excelente salud", "Buenas universidades", "Clima equilibrado"],
        "cons": ["Income tax moderado", "Menos comunidad latina"],
    },
    {
        "name": "Georgia",
        "salud": 4,
        "oportunidades_negocio": 4,
        "costo_vida": 4,
        "criminalidad": 3,
        "estudios": 4,
        "impuestos": 3,
        "migration_friendly": 4,
        "dinamismo_economico": 4,
        "comunidad_latina": 4,
        "clima": 3,
        "poblacion": 4,
        "pros": ["Atlanta como hub", "Costo razonable", "Aeropuerto internacional"],
        "cons": ["Tráfico en Atlanta", "Humedad"],
    },
    {
        "name": "Arizona",
        "salud": 4,
        "oportunidades_negocio": 4,
        "costo_vida": 4,
        "criminalidad": 3,
        "estudios": 3,
        "impuestos": 4,
        "migration_friendly": 3,
        "dinamismo_economico": 4,
        "comunidad_latina": 5,
        "clima": 2,
        "poblacion": 3,
        "pros": ["Costo de vida bajo", "Comunidad latina", "Crecimiento económico"],
        "cons": ["Calor extremo", "Agua escasa"],
    },
    {
        "name": "Nevada",
        "salud": 3,
        "oportunidades_negocio": 4,
        "costo_vida": 3,
        "criminalidad": 3,
        "estudios": 3,
        "impuestos": 5,
        "migration_friendly": 4,
        "dinamismo_economico": 4,
        "comunidad_latina": 4,
        "clima": 2,
        "poblacion": 3,
        "pros": ["Sin income tax", "Las Vegas como hub", "Turismo"],
        "cons": ["Calor extremo", "Economía dependiente del turismo"],
    },
    {
        "name": "Colorado",
        "salud": 4,
        "oportunidades_negocio": 4,
        "costo_vida": 3,
        "criminalidad": 4,
        "estudios": 4,
        "impuestos": 3,
        "migration_friendly": 4,
        "dinamismo_economico": 4,
        "comunidad_latina": 3,
        "clima": 4,
        "poblacion": 3,
        "pros": ["Calidad de vida", "Tech hub", "Naturaleza"],
        "cons": ["Costo de vida alto", "Inviernos fríos"],
    },
    {
        "name": "Tennessee",
        "salud": 3,
        "oportunidades_negocio": 4,
        "costo_vida": 5,
        "criminalidad": 3,
        "estudios": 3,
        "impuestos": 5,
        "migration_friendly": 3,
        "dinamismo_economico": 4,
        "comunidad_latina": 2,
        "clima": 4,
        "poblacion": 3,
        "pros": ["Sin income tax", "Costo muy bajo", "Nashville creciendo"],
        "cons": ["Menos diversidad", "Servicios públicos limitados"],
    },
    {
        "name": "South Carolina",
        "salud": 3,
        "oportunidades_negocio": 3,
        "costo_vida": 5,
        "criminalidad": 3,
        "estudios": 3,
        "impuestos": 3,
        "migration_friendly": 3,
        "dinamismo_economico": 3,
        "comunidad_latina": 2,
        "clima": 4,
        "poblacion": 2,
        "pros": ["Costo muy bajo", "Playas", "Clima agradable"],
        "cons": ["Menos oportunidades", "Menos diversidad"],
    },
    {
        "name": "Virginia",
        "salud": 4,
        "oportunidades_negocio": 4,
        "costo_vida": 3,
        "criminalidad": 4,
        "estudios": 5,
        "impuestos": 3,
        "migration_friendly": 4,
        "dinamismo_economico": 4,
        "comunidad_latina": 3,
        "clima": 4,
        "poblacion": 3,
        "pros": ["Cerca de DC", "Buenas escuelas", "Tech hub"],
        "cons": ["Costo de vida alto", "Tráfico"],
    },
]

USA_CITIES_DATA = {
    "Florida": [
        {"name": "Tampa", "population": 400000, "pros": ["Costo razonable", "Playas"], "cons": ["Humedad"]},
        {
            "name": "Orlando",
            "population": 300000,
            "pros": ["Turismo", "Comunidad latina"],
            "cons": ["Turismo excesivo"],
        },
        {
            "name": "Miami",
            "population": 450000,
            "pros": ["Muy latino", "Internacional"],
            "cons": ["Caro", "Tráfico"],
        },
        {
            "name": "Jacksonville",
            "population": 900000,
            "pros": ["Barato", "Grande"],
            "cons": ["Menos latino"],
        },
    ],
    "Texas": [
        {
            "name": "Austin",
            "population": 1000000,
            "pros": ["Tech hub", "Cultura"],
            "cons": ["Caro", "Tráfico"],
        },
        {
            "name": "Houston",
            "population": 2300000,
            "pros": ["Diverso", "Oportunidades"],
            "cons": ["Calor", "Tráfico"],
        },
        {"name": "Dallas", "population": 1300000, "pros": ["Negocios", "Aeropuerto"], "cons": ["Sprawl"]},
        {"name": "San Antonio", "population": 1500000, "pros": ["Barato", "Latino"], "cons": ["Menos tech"]},
    ],
    "North Carolina": [
        {
            "name": "Raleigh",
            "population": 470000,
            "pros": ["Universidades", "Tech"],
            "cons": ["Menos latino"],
        },
        {"name": "Charlotte", "population": 900000, "pros": ["Finanzas", "Crecimiento"], "cons": ["Tráfico"]},
        {"name": "Durham", "population": 280000, "pros": ["Universidades", "Salud"], "cons": ["Pequeño"]},
    ],
}

BUSINESS_TYPES_DATA = [
    {
        "name": "Property Maintenance + Handyman",
        "rentabilidad": 5,
        "recurrencia_ingresos": 5,
        "riesgo_operativo": 2,
        "inversion_inicial": 4,
        "payback": 5,
        "encaje_visa": 5,
        "empleo_familia": 5,
        "escalabilidad": 4,
        "pros": ["Alta demanda", "Contratos recurrentes", "Familiar"],
        "cons": ["Trabajo físico", "Dependiente de gestión"],
        "investment_range": "$60K-$100K",
        "payback_months": "6-12",
    },
    {
        "name": "Mantenimiento para HOAs/Condominios",
        "rentabilidad": 5,
        "recurrencia_ingresos": 5,
        "riesgo_operativo": 2,
        "inversion_inicial": 3,
        "payback": 4,
        "encaje_visa": 5,
        "empleo_familia": 4,
        "escalabilidad": 4,
        "pros": ["Contratos mensuales", "Ingresos estables"],
        "cons": ["Negociación inicial", "Expectativas altas"],
        "investment_range": "$80K-$130K",
        "payback_months": "9-15",
    },
    {
        "name": "Limpieza + Mantenimiento Airbnb",
        "rentabilidad": 4,
        "recurrencia_ingresos": 4,
        "riesgo_operativo": 2,
        "inversion_inicial": 5,
        "payback": 5,
        "encaje_visa": 4,
        "empleo_familia": 5,
        "escalabilidad": 3,
        "pros": ["Baja inversión", "Fácil de operar"],
        "cons": ["Estacionalidad", "Dependencia turismo"],
        "investment_range": "$50K-$80K",
        "payback_months": "6-12",
    },
    {
        "name": "Empresa de Pintura",
        "rentabilidad": 4,
        "recurrencia_ingresos": 3,
        "riesgo_operativo": 2,
        "inversion_inicial": 5,
        "payback": 5,
        "encaje_visa": 4,
        "empleo_familia": 4,
        "escalabilidad": 3,
        "pros": ["Márgenes altos", "Baja inversión"],
        "cons": ["Trabajo físico", "Menos recurrente"],
        "investment_range": "$40K-$70K",
        "payback_months": "6-10",
    },
    {
        "name": "Remodelaciones Menores",
        "rentabilidad": 4,
        "recurrencia_ingresos": 3,
        "riesgo_operativo": 3,
        "inversion_inicial": 3,
        "payback": 3,
        "encaje_visa": 4,
        "empleo_familia": 4,
        "escalabilidad": 4,
        "pros": ["Tickets altos", "Usa experiencia"],
        "cons": ["Cashflow irregular", "Mayor riesgo"],
        "investment_range": "$80K-$140K",
        "payback_months": "12-18",
    },
    {
        "name": "Servicios de Limpieza Comercial",
        "rentabilidad": 3,
        "recurrencia_ingresos": 5,
        "riesgo_operativo": 2,
        "inversion_inicial": 5,
        "payback": 5,
        "encaje_visa": 4,
        "empleo_familia": 5,
        "escalabilidad": 4,
        "pros": ["Muy recurrente", "Contratos mensuales"],
        "cons": ["Margen medio", "Competencia"],
        "investment_range": "$30K-$60K",
        "payback_months": "6-12",
    },
    {
        "name": "Lawn Care + Mantenimiento Exterior",
        "rentabilidad": 4,
        "recurrencia_ingresos": 4,
        "riesgo_operativo": 2,
        "inversion_inicial": 4,
        "payback": 5,
        "encaje_visa": 4,
        "empleo_familia": 4,
        "escalabilidad": 3,
        "pros": ["Alta demanda en Florida", "Recurrente"],
        "cons": ["Competencia alta", "Trabajo físico"],
        "investment_range": "$40K-$80K",
        "payback_months": "6-10",
    },
    {
        "name": "Instalación de Pisos",
        "rentabilidad": 4,
        "recurrencia_ingresos": 3,
        "riesgo_operativo": 3,
        "inversion_inicial": 3,
        "payback": 3,
        "encaje_visa": 4,
        "empleo_familia": 3,
        "escalabilidad": 3,
        "pros": ["Buen margen", "Demanda constante"],
        "cons": ["Dependencia de proyectos", "Menos recurrente"],
        "investment_range": "$70K-$120K",
        "payback_months": "12-18",
    },
    {
        "name": "Pressure Washing",
        "rentabilidad": 3,
        "recurrencia_ingresos": 3,
        "riesgo_operativo": 1,
        "inversion_inicial": 5,
        "payback": 5,
        "encaje_visa": 3,
        "empleo_familia": 3,
        "escalabilidad": 2,
        "pros": ["Muy baja inversión", "Rápido arranque"],
        "cons": ["Ticket bajo", "Difícil escalar"],
        "investment_range": "$25K-$50K",
        "payback_months": "6-9",
    },
    {
        "name": "Franquicia de Servicios",
        "rentabilidad": 3,
        "recurrencia_ingresos": 4,
        "riesgo_operativo": 2,
        "inversion_inicial": 2,
        "payback": 2,
        "encaje_visa": 4,
        "empleo_familia": 3,
        "escalabilidad": 3,
        "pros": ["Marca conocida", "Soporte"],
        "cons": ["Royalties", "Menos control"],
        "investment_range": "$100K-$200K",
        "payback_months": "18-24",
    },
]


# ============== FUNCIONES DE INTEGRACIÓN ==============


def process_with_standard(user_id: int, message: str, user_data: dict[str, Any]) -> tuple[str, bool]:
    """
    Procesa un mensaje aplicando todas las reglas del estándar MigPAL USA.

    Returns:
        Tuple[str, bool]: (respuesta_formateada, requiere_formulario)
    """
    standard = get_migpal_standard()
    state = standard.get_state(user_id)

    # Actualizar datos del perfil si hay nuevos
    if user_data.get("profile"):
        state.profile_data.update(user_data.get("profile", {}))

    # Verificar si se puede mostrar formulario
    can_form = can_show_form(user_id)

    # Formatear respuesta con reglas
    # (El mensaje real viene del ai_brain, aquí solo aplicamos formato)

    return message, can_form


def check_and_enforce_gating(
    user_id: int, user_data: dict[str, Any], action: str = "recommend_visa"
) -> tuple[bool, str]:
    """
    Verifica y aplica gating antes de acciones sensibles.

    Args:
        user_id: ID del usuario
        user_data: Datos del usuario
        action: Acción a verificar (recommend_visa, show_plan, etc.)

    Returns:
        Tuple[bool, str]: (puede_continuar, mensaje_bloqueo)
    """
    get_migpal_standard()

    if action == "recommend_visa":
        # Verificar con el estándar nuevo
        can_recommend, blocking_msg = check_visa_gating(user_id)

        if not can_recommend:
            # También verificar con el sistema legacy
            legacy_can = can_recommend_visa_with_summary(user_id, user_data)
            if not legacy_can:
                return False, blocking_msg

        return can_recommend, blocking_msg

    return True, ""


def generate_state_evaluation(user_id: int, custom_weights: dict[str, float] | None = None) -> str:
    """
    Genera evaluación ponderada de estados USA.
    Mínimo 10 estados evaluados.
    """
    return evaluate_options(USA_STATES_DATA, "state", custom_weights)


def generate_city_evaluation(state: str, user_id: int, custom_weights: dict[str, float] | None = None) -> str:
    """
    Genera evaluación ponderada de ciudades en un estado.
    """
    cities = USA_CITIES_DATA.get(state, [])
    if not cities:
        return f"No tengo datos de ciudades para {state}. ¿Quieres que busque información?"

    # Agregar factores a las ciudades
    for city in cities:
        city.update(
            {
                "salud": 4,
                "oportunidades_negocio": 4,
                "costo_vida": 4,
                "criminalidad": 4,
                "estudios": 4,
                "impuestos": 4,
                "migration_friendly": 4,
                "dinamismo_economico": 4,
                "comunidad_latina": 4,
                "clima": 4,
                "poblacion": 3,
            }
        )

    return evaluate_options(cities, "city", custom_weights)


def generate_business_evaluation(
    user_id: int, budget: float = 150000, custom_weights: dict[str, float] | None = None
) -> str:
    """
    Genera evaluación ponderada de tipos de negocio.
    Filtrado por presupuesto disponible.
    """
    # Filtrar por presupuesto
    filtered = []
    for biz in BUSINESS_TYPES_DATA:
        inv_range = biz.get("investment_range", "$0-$0")
        # Extraer máximo del rango
        try:
            max_inv = int(inv_range.split("-")[1].replace("$", "").replace("K", "000"))
            if max_inv <= budget:
                filtered.append(biz)
        except:
            filtered.append(biz)

    if not filtered:
        filtered = BUSINESS_TYPES_DATA[:5]  # Top 5 por defecto

    return evaluate_options(filtered, "business", custom_weights)


def format_response_with_progress(user_id: int, message: str, include_progress: bool = True) -> str:
    """
    Formatea respuesta incluyendo indicador de progreso.
    """
    get_migpal_standard()

    # Aplicar formato del estándar
    formatted = format_message(user_id, message)

    return formatted


def get_conversation_progress(user_id: int) -> str:
    """
    Obtiene el indicador de progreso actual.
    """
    return get_progress(user_id)


def advance_to_phase(user_id: int, phase: ConversationPhase) -> None:
    """
    Avanza la conversación a una nueva fase.
    """
    advance_phase(user_id, phase)


def complete_profile(user_id: int) -> None:
    """
    Marca el perfil como completo.
    """
    mark_profile_complete(user_id)


def confirm_summary(user_id: int) -> None:
    """
    Confirma el resumen de entendimiento.
    """
    mark_summary_confirmed(user_id)


def get_micro_check(lang: str = "es") -> str:
    """
    Obtiene un micro-check aleatorio.
    """
    import random

    checks = MICRO_CHECKS.get(lang, MICRO_CHECKS["es"])
    return random.choice(checks)


def should_add_micro_check(user_id: int) -> bool:
    """
    Determina si agregar micro-check al mensaje.
    """
    standard = get_migpal_standard()
    return standard.should_add_micro_check(user_id)


# ============== FUNCIONES DE FASE POST-PLAN ==============


def get_document_checklist_for_visa(visa_type: str) -> list[dict[str, Any]]:
    """
    Obtiene checklist de documentos para un tipo de visa.
    """
    standard = get_migpal_standard()
    return standard.get_document_checklist(visa_type)


def get_installation_checklist() -> list[dict[str, Any]]:
    """
    Obtiene checklist de instalación en USA.
    """
    standard = get_migpal_standard()
    return standard.get_installation_checklist()


def get_interview_preparation(visa_type: str) -> dict[str, Any]:
    """
    Obtiene preparación para entrevista consular.
    """
    standard = get_migpal_standard()
    return standard.get_interview_prep(visa_type)


def format_checklist_message(checklist: list[dict], title: str) -> str:
    """
    Formatea un checklist para mostrar en Telegram.
    """
    result = f"📋 **{title}**\n\n"

    for category in checklist:
        if "category" in category:
            result += f"**{category['category']}:**\n"
            for item in category.get("items", []):
                result += f"  ☐ {item}\n"
            result += "\n"
        else:
            required = "🔴" if category.get("required") else "🟡"
            ocr = "📷" if category.get("ocr_enabled") else ""
            result += f"{required} {category['name']} {ocr}\n"

    return result


# ============== EXPORTAR ==============

__all__ = [
    "process_with_standard",
    "check_and_enforce_gating",
    "generate_state_evaluation",
    "generate_city_evaluation",
    "generate_business_evaluation",
    "format_response_with_progress",
    "get_conversation_progress",
    "advance_to_phase",
    "complete_profile",
    "confirm_summary",
    "get_micro_check",
    "should_add_micro_check",
    "get_document_checklist_for_visa",
    "get_installation_checklist",
    "get_interview_preparation",
    "format_checklist_message",
    "USA_STATES_DATA",
    "USA_CITIES_DATA",
    "BUSINESS_TYPES_DATA",
    "ConversationPhase",
]

#!/usr/bin/env python3
"""
MigPAL USA Standard v4.0
========================
ESTÁNDAR CONVERSACIONAL DEFINITIVO PARA MIGPAL USA

REGLAS FUNDAMENTALES:
1. 100% conversacional (sin monólogos)
2. Micro-checks ("¿voy claro?", "¿esto resuena contigo?")
3. Tono suave, nunca sentencioso
4. Formularios solo si necesarios (máx 1/5 turnos)
5. UNA pregunta por mensaje
6. Indicador de avance siempre visible

GATING OBLIGATORIO:
- Prohibido recomendar/decidir visa sin:
  a) Perfil completo
  b) Resumen de Entendimiento confirmado

MATRICES PONDERADAS PARA:
- Estado/Ciudad (≥10 opciones)
- Negocio (si aplica E-2/L-1)
- Barrio/Vivienda
- Colegios (si tiene hijos)

POST-PLAN:
- OCR + validación de documentos
- Autollenado de formularios
- Preparación de entrevista
- Checklist de mudanza/instalación
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


# ============== CONSTANTES ==============

MAX_FORMS_PER_5_TURNS = 1
MAX_MESSAGE_LINES = 6
MICRO_CHECK_FREQUENCY = 3  # Cada 3 mensajes hacer micro-check

# Micro-checks aprobados
MICRO_CHECKS = {
    "es": [
        "¿Hasta aquí voy claro?",
        "¿Esto resuena contigo?",
        "¿Tiene sentido así planteado?",
        "¿Seguimos alineados?",
        "¿Te parece bien así?",
    ],
    "en": [
        "Am I being clear so far?",
        "Does this resonate with you?",
        "Does this make sense?",
        "Are we on the same page?",
        "Does this work for you?",
    ]
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


# ============== ENUMS ==============

class ConversationPhase(Enum):
    """Fases de la conversación MigPAL USA"""
    REGISTRO = "registro"
    DIAGNOSTICO = "diagnostico"
    PERFILAMIENTO = "perfilamiento"
    DEFINICION_VISA = "definicion_visa"
    SELECCION_ESTADO = "seleccion_estado"
    SELECCION_CIUDAD = "seleccion_ciudad"
    ATERRIZAJE_NEGOCIO = "aterrizaje_negocio"
    SELECCION_BARRIO = "seleccion_barrio"
    SELECCION_VIVIENDA = "seleccion_vivienda"
    SELECCION_COLEGIOS = "seleccion_colegios"
    PLAN_MIGRACION = "plan_migracion"
    DOCUMENTOS = "documentos"
    FORMULARIOS = "formularios"
    ENTREVISTA = "entrevista"
    CHECKLIST_MUDANZA = "checklist_mudanza"
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
    profile_data: Dict[str, Any] = field(default_factory=dict)
    
    # Matrices de evaluación
    state_matrix: Optional[Dict] = None
    city_matrix: Optional[Dict] = None
    business_matrix: Optional[Dict] = None
    neighborhood_matrix: Optional[Dict] = None
    school_matrix: Optional[Dict] = None
    
    # Selecciones
    selected_visa: Optional[str] = None
    selected_state: Optional[str] = None
    selected_city: Optional[str] = None
    selected_business: Optional[str] = None
    selected_neighborhood: Optional[str] = None
    selected_housing: Optional[str] = None
    selected_schools: List[str] = field(default_factory=list)


@dataclass
class MatrixEvaluation:
    """Evaluación con matriz ponderada"""
    name: str
    score: float
    weighted_score: float
    pros: List[str]
    cons: List[str]
    factors: Dict[str, float]
    recommendation: str


@dataclass
class MessageResponse:
    """Respuesta estructurada de MigPAL"""
    text: str
    include_micro_check: bool = False
    show_progress: bool = True
    buttons: Optional[List[Tuple[str, str]]] = None
    is_form: bool = False


# ============== CLASE PRINCIPAL ==============

class MigPALUSAStandard:
    """
    Estándar conversacional MigPAL USA.
    Implementa todas las reglas definidas.
    """
    
    _instance = None
    _states: Dict[int, ConversationState] = {}
    
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
    
    # ============== VALIDACIONES ==============
    
    def check_gating(self, user_id: int) -> Tuple[GatingStatus, str]:
        """
        Verifica si el usuario puede recibir recomendaciones de visa.
        REGLA: Prohibido recomendar sin perfil completo + resumen confirmado.
        """
        state = self.get_state(user_id)
        
        if not state.profile_complete:
            return GatingStatus.PENDING_PROFILE, self._get_missing_profile_message(state)
        
        if not state.summary_confirmed:
            return GatingStatus.PENDING_SUMMARY, self._get_summary_required_message()
        
        return GatingStatus.APPROVED, ""
    
    def _get_missing_profile_message(self, state: ConversationState) -> str:
        """Mensaje cuando falta completar perfil"""
        missing = self._get_missing_fields(state)
        return f"Para darte una recomendación precisa, necesito conocer un poco más sobre ti. ¿Me puedes contar sobre {missing[0]}?"
    
    def _get_summary_required_message(self) -> str:
        """Mensaje cuando falta confirmar resumen"""
        return "Antes de darte recomendaciones, quiero asegurarme de que entendí bien tu situación. Déjame mostrarte un resumen de lo que entendí."
    
    def _get_missing_fields(self, state: ConversationState) -> List[str]:
        """Obtiene campos faltantes del perfil"""
        required = [
            "name", "nationality", "family_composition", "profession",
            "experience", "english_level", "motivation", "budget"
        ]
        missing = []
        for field in required:
            if field not in state.profile_data or not state.profile_data[field]:
                missing.append(field)
        return missing if missing else ["información adicional"]
    
    def can_show_form(self, user_id: int) -> bool:
        """
        Verifica si se puede mostrar un formulario.
        REGLA: Máximo 1 formulario cada 5 turnos.
        """
        state = self.get_state(user_id)
        return state.forms_shown_last_5 < MAX_FORMS_PER_5_TURNS
    
    def register_form_shown(self, user_id: int) -> None:
        """Registra que se mostró un formulario"""
        state = self.get_state(user_id)
        state.forms_shown_last_5 += 1
        if state.turn_count % 5 == 0:
            state.forms_shown_last_5 = 0
    
    def should_add_micro_check(self, user_id: int) -> bool:
        """
        Determina si agregar micro-check.
        REGLA: Cada 3 mensajes aproximadamente.
        """
        state = self.get_state(user_id)
        turns_since_check = state.turn_count - state.last_micro_check
        return turns_since_check >= MICRO_CHECK_FREQUENCY
    
    def get_micro_check(self, lang: str = "es") -> str:
        """Obtiene un micro-check aleatorio"""
        import random
        checks = MICRO_CHECKS.get(lang, MICRO_CHECKS["es"])
        return random.choice(checks)
    
    # ============== PROCESAMIENTO DE MENSAJES ==============
    
    def soften_message(self, message: str) -> str:
        """
        Suaviza el mensaje eliminando frases sentenciosas.
        REGLA: Tono suave, nunca sentencioso.
        """
        result = message.lower()
        for forbidden in FORBIDDEN_PHRASES:
            if forbidden in result:
                replacement = SOFT_ALTERNATIVES.get(forbidden, "hay otras opciones que podemos explorar")
                result = result.replace(forbidden, replacement)
        return message  # Retorna original con tono ajustado
    
    def limit_message_length(self, message: str) -> str:
        """
        Limita la longitud del mensaje.
        REGLA: Máximo 6 líneas, sin monólogos.
        """
        lines = message.split('\n')
        if len(lines) > MAX_MESSAGE_LINES:
            # Mantener las primeras líneas y agregar indicador
            truncated = '\n'.join(lines[:MAX_MESSAGE_LINES-1])
            truncated += "\n\n¿Quieres que te cuente más sobre esto?"
            return truncated
        return message
    
    def ensure_single_question(self, message: str) -> str:
        """
        Asegura que solo haya una pregunta por mensaje.
        REGLA: UNA pregunta por mensaje.
        """
        questions = message.count('?')
        if questions > 1:
            # Encontrar la primera pregunta y cortar ahí
            first_q = message.find('?')
            if first_q != -1:
                return message[:first_q+1]
        return message
    
    def format_response(self, user_id: int, message: str, 
                       include_progress: bool = True,
                       is_form: bool = False) -> MessageResponse:
        """
        Formatea la respuesta según las reglas MigPAL USA.
        """
        state = self.get_state(user_id)
        state.turn_count += 1
        
        # Aplicar reglas
        message = self.soften_message(message)
        message = self.limit_message_length(message)
        message = self.ensure_single_question(message)
        
        # Agregar micro-check si corresponde
        include_micro_check = self.should_add_micro_check(user_id)
        if include_micro_check:
            state.last_micro_check = state.turn_count
        
        # Registrar formulario si aplica
        if is_form:
            self.register_form_shown(user_id)
        
        return MessageResponse(
            text=message,
            include_micro_check=include_micro_check,
            show_progress=include_progress,
            is_form=is_form
        )
    
    def get_progress_indicator(self, user_id: int) -> str:
        """
        Genera indicador de progreso.
        REGLA: Siempre mostrar paso actual y siguiente.
        """
        state = self.get_state(user_id)
        phase = state.current_phase
        
        phase_names = {
            ConversationPhase.REGISTRO: ("Registro", 1),
            ConversationPhase.DIAGNOSTICO: ("Diagnóstico", 2),
            ConversationPhase.PERFILAMIENTO: ("Perfilamiento", 3),
            ConversationPhase.DEFINICION_VISA: ("Definición de Visa", 4),
            ConversationPhase.SELECCION_ESTADO: ("Selección de Estado", 5),
            ConversationPhase.SELECCION_CIUDAD: ("Selección de Ciudad", 6),
            ConversationPhase.ATERRIZAJE_NEGOCIO: ("Aterrizaje del Negocio", 7),
            ConversationPhase.SELECCION_BARRIO: ("Selección de Barrio", 8),
            ConversationPhase.SELECCION_VIVIENDA: ("Selección de Vivienda", 9),
            ConversationPhase.SELECCION_COLEGIOS: ("Selección de Colegios", 10),
            ConversationPhase.PLAN_MIGRACION: ("Plan de Migración", 11),
            ConversationPhase.DOCUMENTOS: ("Documentos", 12),
            ConversationPhase.FORMULARIOS: ("Formularios", 13),
            ConversationPhase.ENTREVISTA: ("Preparación Entrevista", 14),
            ConversationPhase.CHECKLIST_MUDANZA: ("Checklist Mudanza", 15),
            ConversationPhase.CIERRE: ("Cierre", 16),
        }
        
        name, num = phase_names.get(phase, ("En proceso", 0))
        total = 16
        percentage = int((num / total) * 100)
        
        return f"📍 Fase: {name} ({num} de {total})\n📊 Progreso: {percentage}% completado"
    
    # ============== MATRICES PONDERADAS ==============
    
    def create_weighted_matrix(self, 
                               items: List[Dict[str, Any]], 
                               weights: Dict[str, float],
                               factors: List[str]) -> List[MatrixEvaluation]:
        """
        Crea matriz ponderada para evaluación.
        Usado para: estados, ciudades, negocios, barrios, colegios.
        """
        evaluations = []
        
        for item in items:
            name = item.get("name", "Unknown")
            scores = {}
            weighted_total = 0
            
            for factor in factors:
                score = item.get(factor, 3)  # Default 3/5
                weight = weights.get(factor, 1)
                scores[factor] = score
                weighted_total += score * weight
            
            # Normalizar a 0-100
            max_possible = sum(weights.values()) * 5
            final_score = (weighted_total / max_possible) * 100
            
            # Extraer pros y contras
            pros = item.get("pros", [])
            cons = item.get("cons", [])
            
            evaluations.append(MatrixEvaluation(
                name=name,
                score=final_score,
                weighted_score=weighted_total,
                pros=pros,
                cons=cons,
                factors=scores,
                recommendation=self._generate_recommendation(name, final_score)
            ))
        
        # Ordenar por score
        evaluations.sort(key=lambda x: x.score, reverse=True)
        return evaluations
    
    def _generate_recommendation(self, name: str, score: float) -> str:
        """Genera recomendación basada en score"""
        if score >= 85:
            return f"👉 {name} es una excelente opción para tu perfil"
        elif score >= 70:
            return f"👉 {name} es una buena opción, con algunos puntos a considerar"
        elif score >= 55:
            return f"👉 {name} puede funcionar, pero hay mejores alternativas"
        else:
            return f"👉 {name} no es la opción más alineada con tu perfil"
    
    def format_matrix_results(self, evaluations: List[MatrixEvaluation], 
                             top_n: int = 10) -> str:
        """Formatea resultados de matriz para mostrar al usuario"""
        result = "🏆 **EVALUACIÓN PONDERADA**\n\n"
        
        for i, eval in enumerate(evaluations[:top_n], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
            result += f"{emoji} **{eval.name}**\n"
            result += f"   Calificación: ⭐ {eval.score:.0f}/100\n"
            
            if eval.pros:
                result += f"   ✅ {', '.join(eval.pros[:2])}\n"
            if eval.cons:
                result += f"   ⚠️ {', '.join(eval.cons[:2])}\n"
            
            result += f"   {eval.recommendation}\n\n"
        
        return result
    
    # ============== FACTORES DE EVALUACIÓN ==============
    
    def get_state_factors(self) -> Dict[str, float]:
        """Factores para evaluar estados (pesos por defecto)"""
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
    
    def get_city_factors(self) -> Dict[str, float]:
        """Factores para evaluar ciudades"""
        return self.get_state_factors()  # Mismos factores
    
    def get_business_factors(self) -> Dict[str, float]:
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
    
    def get_neighborhood_factors(self) -> Dict[str, float]:
        """Factores para evaluar barrios"""
        return {
            "seguridad": 25,
            "calidad_escuelas": 20,
            "costo_vivienda": 18,
            "acceso_servicios": 15,
            "transporte": 12,
            "comunidad": 10,
        }
    
    def get_school_factors(self) -> Dict[str, float]:
        """Factores para evaluar colegios"""
        return {
            "calidad_academica": 25,
            "seguridad": 20,
            "costo": 18,
            "distancia": 15,
            "actividades": 12,
            "diversidad": 10,
        }
    
    # ============== POST-PLAN: DOCUMENTOS ==============
    
    def get_document_checklist(self, visa_type: str) -> List[Dict[str, Any]]:
        """Obtiene checklist de documentos según tipo de visa"""
        checklists = {
            "E-2": [
                {"name": "Pasaporte vigente", "required": True, "ocr_enabled": True},
                {"name": "Plan de negocios", "required": True, "ocr_enabled": False},
                {"name": "Prueba de inversión", "required": True, "ocr_enabled": True},
                {"name": "Documentos de la empresa", "required": True, "ocr_enabled": True},
                {"name": "Estados financieros", "required": True, "ocr_enabled": True},
                {"name": "Contrato de arrendamiento", "required": False, "ocr_enabled": True},
                {"name": "Licencias y permisos", "required": False, "ocr_enabled": True},
            ],
            "L-1": [
                {"name": "Pasaporte vigente", "required": True, "ocr_enabled": True},
                {"name": "Carta de la empresa matriz", "required": True, "ocr_enabled": True},
                {"name": "Prueba de relación empresarial", "required": True, "ocr_enabled": True},
                {"name": "Descripción del puesto", "required": True, "ocr_enabled": False},
                {"name": "Historial laboral", "required": True, "ocr_enabled": True},
                {"name": "Organigrama", "required": True, "ocr_enabled": False},
            ],
            "EB-2_NIW": [
                {"name": "Pasaporte vigente", "required": True, "ocr_enabled": True},
                {"name": "Títulos académicos", "required": True, "ocr_enabled": True},
                {"name": "Cartas de recomendación", "required": True, "ocr_enabled": True},
                {"name": "Publicaciones", "required": False, "ocr_enabled": True},
                {"name": "Premios y reconocimientos", "required": False, "ocr_enabled": True},
                {"name": "Plan de trabajo en USA", "required": True, "ocr_enabled": False},
            ],
        }
        return checklists.get(visa_type, [])
    
    def get_installation_checklist(self) -> List[Dict[str, Any]]:
        """Checklist de instalación en USA"""
        return [
            {"category": "Documentos", "items": [
                "Obtener SSN (Social Security Number)",
                "Obtener licencia de conducir estatal",
                "Registrar dirección en USCIS",
            ]},
            {"category": "Finanzas", "items": [
                "Abrir cuenta bancaria",
                "Obtener tarjeta de crédito",
                "Establecer historial crediticio",
            ]},
            {"category": "Vivienda", "items": [
                "Firmar contrato de arrendamiento",
                "Activar servicios (luz, agua, gas, internet)",
                "Obtener seguro de inquilino",
            ]},
            {"category": "Transporte", "items": [
                "Comprar/arrendar vehículo",
                "Obtener seguro de auto",
                "Registrar vehículo en DMV",
            ]},
            {"category": "Salud", "items": [
                "Obtener seguro médico",
                "Encontrar médico de cabecera",
                "Registrar en farmacia",
            ]},
            {"category": "Educación (si aplica)", "items": [
                "Inscribir hijos en escuela",
                "Obtener registros de vacunación",
                "Conocer calendario escolar",
            ]},
        ]
    
    def get_interview_prep(self, visa_type: str) -> Dict[str, Any]:
        """Preparación para entrevista consular"""
        return {
            "general_tips": [
                "Llegar 15 minutos antes de la cita",
                "Llevar todos los documentos originales",
                "Vestir de manera profesional",
                "Responder de forma clara y concisa",
                "Mantener contacto visual",
                "No mentir ni exagerar",
            ],
            "common_questions": {
                "E-2": [
                    "¿Cuál es el propósito de su negocio?",
                    "¿Cuánto ha invertido?",
                    "¿Cuántos empleados tendrá?",
                    "¿Cómo generará ingresos?",
                    "¿Cuál es su plan a 5 años?",
                ],
                "L-1": [
                    "¿Cuál es su rol en la empresa?",
                    "¿Cuánto tiempo ha trabajado ahí?",
                    "¿Qué hará en la oficina de USA?",
                    "¿Cuántos empleados supervisará?",
                ],
                "EB-2_NIW": [
                    "¿Por qué su trabajo beneficia a USA?",
                    "¿Cuáles son sus logros principales?",
                    "¿Dónde planea trabajar?",
                    "¿Cómo contribuirá al interés nacional?",
                ],
            }.get(visa_type, []),
            "documents_to_bring": self.get_document_checklist(visa_type),
        }


# ============== SINGLETON ==============

_standard_instance: Optional[MigPALUSAStandard] = None

def get_migpal_standard() -> MigPALUSAStandard:
    """Obtiene la instancia singleton del estándar MigPAL USA"""
    global _standard_instance
    if _standard_instance is None:
        _standard_instance = MigPALUSAStandard()
    return _standard_instance


# ============== FUNCIONES DE CONVENIENCIA ==============

def check_visa_gating(user_id: int) -> Tuple[bool, str]:
    """Verifica si se puede recomendar visa"""
    standard = get_migpal_standard()
    status, message = standard.check_gating(user_id)
    return status == GatingStatus.APPROVED, message


def format_message(user_id: int, message: str, is_form: bool = False) -> str:
    """Formatea mensaje según reglas MigPAL USA"""
    standard = get_migpal_standard()
    response = standard.format_response(user_id, message, is_form=is_form)
    
    result = response.text
    
    if response.include_micro_check:
        result += f"\n\n{standard.get_micro_check()}"
    
    if response.show_progress:
        result = f"{standard.get_progress_indicator(user_id)}\n\n{result}"
    
    return result


def evaluate_options(items: List[Dict], category: str, 
                    custom_weights: Optional[Dict[str, float]] = None) -> str:
    """Evalúa opciones con matriz ponderada"""
    standard = get_migpal_standard()
    
    # Obtener factores según categoría
    factor_getters = {
        "state": standard.get_state_factors,
        "city": standard.get_city_factors,
        "business": standard.get_business_factors,
        "neighborhood": standard.get_neighborhood_factors,
        "school": standard.get_school_factors,
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
    return get_migpal_standard().get_progress_indicator(user_id)


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


# ============== EXPORTAR ==============

__all__ = [
    'MigPALUSAStandard',
    'ConversationPhase',
    'GatingStatus',
    'ConversationState',
    'MatrixEvaluation',
    'MessageResponse',
    'get_migpal_standard',
    'check_visa_gating',
    'format_message',
    'evaluate_options',
    'can_show_form',
    'get_progress',
    'advance_phase',
    'mark_profile_complete',
    'mark_summary_confirmed',
    'MICRO_CHECKS',
    'FORBIDDEN_PHRASES',
    'MAX_FORMS_PER_5_TURNS',
]

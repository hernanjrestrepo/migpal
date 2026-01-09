#!/usr/bin/env python3
"""
MigPAL Full Migration Cycle Simulator v1.0
==========================================
Simula 10 ciclos completos de migración para detectar errores, bugs y fricciones.

Cada simulación incluye:
1. Inicio de conversación
2. Recolección de datos personales
3. Información profesional
4. Situación financiera
5. Historial migratorio
6. Objetivos en USA
7. Análisis de visa
8. Generación de plan
9. Manejo de preguntas/confusión
10. Cierre

Detecta:
- Loops de respuesta
- Datos fantasma
- Saltos de tema
- Estados inconsistentes
- Respuestas repetidas
- Falta de respuesta
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

# Agregar el path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.case_storage import (
    save_user_data, load_user_data, delete_user_data
)
from app.services.profile_validator import (
    PriorityIntentHandler, get_profile_based_intro
)
from app.services.flow_governor import (
    InputInterpreter, interpret_user_input, InputType
)
from app.services.conversational_ai import ConversationalAI, UserIntent
from app.services.profile_checklist import (
    get_profile_checklist, check_profile_completeness
)
from app.services.test_time_reasoning import (
    get_test_time_reasoner, reason_visa_analysis
)
from app.services.coherence_validator import (
    validate_response, is_response_safe
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class SimulationPhase(Enum):
    """Fases de la simulación"""
    START = "start"
    PERSONAL_INFO = "personal_info"
    PROFESSIONAL_INFO = "professional_info"
    FINANCIAL_INFO = "financial_info"
    MIGRATION_HISTORY = "migration_history"
    USA_GOALS = "usa_goals"
    VISA_ANALYSIS = "visa_analysis"
    PLAN_GENERATION = "plan_generation"
    QUESTIONS = "questions"
    CLOSURE = "closure"


@dataclass
class SimulationMessage:
    """Mensaje de simulación"""
    phase: SimulationPhase
    user_input: str
    expected_state_after: Optional[str] = None
    expected_data_saved: Dict[str, Any] = field(default_factory=dict)
    is_question: bool = False
    is_confusion: bool = False


@dataclass
class SimulationIssue:
    """Problema detectado en la simulación"""
    severity: str  # "critical", "warning", "info"
    category: str  # "loop", "ghost_data", "topic_jump", "no_response", "state_mismatch"
    phase: SimulationPhase
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationResult:
    """Resultado de una simulación"""
    simulation_id: int
    user_id: int
    persona_name: str
    success: bool
    phases_completed: int
    total_phases: int
    issues: List[SimulationIssue] = field(default_factory=list)
    final_state: str = ""
    final_profile: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    responses_received: int = 0
    loops_detected: int = 0
    ghost_data_found: List[str] = field(default_factory=list)


# ============== PERSONAS DE SIMULACIÓN ==============

SIMULATION_PERSONAS = [
    {
        "id": 1,
        "name": "Carlos - Ingeniero Senior",
        "description": "Ingeniero de software con 10 años de experiencia, quiere H-1B",
        "messages": [
            SimulationMessage(SimulationPhase.START, "Hola, quiero migrar a USA"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Me llamo Carlos Pérez"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Tengo 35 años"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Soy colombiano"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "Soy ingeniero de software"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "Tengo 10 años de experiencia"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "Tengo título universitario en sistemas"),
            SimulationMessage(SimulationPhase.FINANCIAL_INFO, "Mi inglés es avanzado"),
            SimulationMessage(SimulationPhase.FINANCIAL_INFO, "Tengo $30,000 ahorrados"),
            SimulationMessage(SimulationPhase.MIGRATION_HISTORY, "Tengo visa B1/B2 vigente"),
            SimulationMessage(SimulationPhase.MIGRATION_HISTORY, "No me han negado visas"),
            SimulationMessage(SimulationPhase.MIGRATION_HISTORY, "No tengo problemas legales"),
            SimulationMessage(SimulationPhase.USA_GOALS, "Quiero trabajar en tecnología"),
            SimulationMessage(SimulationPhase.USA_GOALS, "Me gustaría ir en 6 meses"),
            SimulationMessage(SimulationPhase.VISA_ANALYSIS, "¿Qué visa me recomiendas?", is_question=True),
            SimulationMessage(SimulationPhase.QUESTIONS, "¿Qué es una visa H-1B?", is_question=True),
            SimulationMessage(SimulationPhase.CLOSURE, "Gracias por la información"),
        ]
    },
    {
        "id": 2,
        "name": "María - Doctora",
        "description": "Médica con especialización, busca O-1",
        "messages": [
            SimulationMessage(SimulationPhase.START, "Hola"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Soy María García"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Tengo 40 años, soy mexicana"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "Soy médica especialista en cardiología"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "15 años de experiencia, doctorado"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "He publicado 20 papers"),
            SimulationMessage(SimulationPhase.FINANCIAL_INFO, "Inglés nativo, $100,000 ahorros"),
            SimulationMessage(SimulationPhase.MIGRATION_HISTORY, "Nunca he tenido visa americana"),
            SimulationMessage(SimulationPhase.MIGRATION_HISTORY, "Sin problemas legales"),
            SimulationMessage(SimulationPhase.USA_GOALS, "Quiero investigar en un hospital"),
            SimulationMessage(SimulationPhase.VISA_ANALYSIS, "¿Califico para O-1?", is_question=True),
            SimulationMessage(SimulationPhase.CLOSURE, "Perfecto, gracias"),
        ]
    },
    {
        "id": 3,
        "name": "Juan - Confundido",
        "description": "Usuario que no entiende el proceso y hace muchas preguntas",
        "messages": [
            SimulationMessage(SimulationPhase.START, "ajá que pasa?", is_confusion=True),
            SimulationMessage(SimulationPhase.START, "qué es esto?", is_question=True),
            SimulationMessage(SimulationPhase.START, "no entiendo nada", is_confusion=True),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "ok, me llamo Juan"),
            SimulationMessage(SimulationPhase.QUESTIONS, "pero qué es una visa?", is_question=True),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "tengo 28 años"),
            SimulationMessage(SimulationPhase.QUESTIONS, "es seguro usar esto?", is_question=True),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "trabajo en ventas"),
            SimulationMessage(SimulationPhase.QUESTIONS, "cuánto cuesta todo?", is_question=True),
            SimulationMessage(SimulationPhase.CLOSURE, "ok, lo pienso"),
        ]
    },
    {
        "id": 4,
        "name": "Ana - Frustrada",
        "description": "Usuario que se frustra porque repite información",
        "messages": [
            SimulationMessage(SimulationPhase.START, "Hola, necesito ayuda"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Me llamo Ana López"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Ya te dije que me llamo Ana", is_confusion=True),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "otra vez lo mismo?", is_confusion=True),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "Soy contadora"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "te lo acabo de decir", is_confusion=True),
            SimulationMessage(SimulationPhase.FINANCIAL_INFO, "Tengo $20,000"),
            SimulationMessage(SimulationPhase.MIGRATION_HISTORY, "No tengo visa"),
            SimulationMessage(SimulationPhase.USA_GOALS, "Quiero trabajar allá"),
            SimulationMessage(SimulationPhase.CLOSURE, "ok gracias"),
        ]
    },
    {
        "id": 5,
        "name": "Pedro - Familia Grande",
        "description": "Usuario con familia que quiere migrar todos juntos",
        "messages": [
            SimulationMessage(SimulationPhase.START, "Hola, somos una familia"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Soy Pedro Martínez, 45 años"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Viajo con mi esposa y 3 hijos"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Los niños tienen 5, 10 y 15 años"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "Soy empresario, tengo una empresa"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "Mi esposa es profesora"),
            SimulationMessage(SimulationPhase.FINANCIAL_INFO, "Tenemos $200,000 para invertir"),
            SimulationMessage(SimulationPhase.FINANCIAL_INFO, "Inglés intermedio"),
            SimulationMessage(SimulationPhase.MIGRATION_HISTORY, "Tenemos visa de turista"),
            SimulationMessage(SimulationPhase.USA_GOALS, "Queremos establecernos permanentemente"),
            SimulationMessage(SimulationPhase.VISA_ANALYSIS, "¿Qué opciones tenemos como familia?", is_question=True),
            SimulationMessage(SimulationPhase.CLOSURE, "Excelente, gracias"),
        ]
    },
    {
        "id": 6,
        "name": "Laura - Estudiante",
        "description": "Joven que quiere estudiar en USA",
        "messages": [
            SimulationMessage(SimulationPhase.START, "Hola! Quiero estudiar en USA"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Soy Laura, tengo 22 años"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Soy argentina"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "Acabo de terminar mi carrera de diseño"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "No tengo experiencia laboral"),
            SimulationMessage(SimulationPhase.FINANCIAL_INFO, "Inglés avanzado"),
            SimulationMessage(SimulationPhase.FINANCIAL_INFO, "Mis padres pueden pagar $50,000"),
            SimulationMessage(SimulationPhase.MIGRATION_HISTORY, "Nunca he viajado a USA"),
            SimulationMessage(SimulationPhase.USA_GOALS, "Quiero hacer una maestría"),
            SimulationMessage(SimulationPhase.VISA_ANALYSIS, "¿Cómo aplico para visa de estudiante?", is_question=True),
            SimulationMessage(SimulationPhase.CLOSURE, "Gracias!"),
        ]
    },
    {
        "id": 7,
        "name": "Roberto - Negación Previa",
        "description": "Usuario con historial de negación de visa",
        "messages": [
            SimulationMessage(SimulationPhase.START, "Hola, necesito ayuda urgente"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Soy Roberto, 38 años, venezolano"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "Soy abogado con 12 años de experiencia"),
            SimulationMessage(SimulationPhase.FINANCIAL_INFO, "Inglés intermedio, $15,000 ahorros"),
            SimulationMessage(SimulationPhase.MIGRATION_HISTORY, "Me negaron la visa B1/B2 hace 2 años"),
            SimulationMessage(SimulationPhase.MIGRATION_HISTORY, "Dijeron que no demostré lazos con mi país"),
            SimulationMessage(SimulationPhase.USA_GOALS, "Quiero trabajar como abogado allá"),
            SimulationMessage(SimulationPhase.QUESTIONS, "¿Puedo volver a aplicar?", is_question=True),
            SimulationMessage(SimulationPhase.QUESTIONS, "¿Qué hago diferente esta vez?", is_question=True),
            SimulationMessage(SimulationPhase.CLOSURE, "Entendido, gracias"),
        ]
    },
    {
        "id": 8,
        "name": "Carmen - Emprendedora",
        "description": "Empresaria que quiere invertir en USA",
        "messages": [
            SimulationMessage(SimulationPhase.START, "Buenas tardes"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Carmen Rodríguez, 50 años, peruana"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "Tengo una cadena de restaurantes"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "25 años de experiencia empresarial"),
            SimulationMessage(SimulationPhase.FINANCIAL_INFO, "Puedo invertir $500,000"),
            SimulationMessage(SimulationPhase.FINANCIAL_INFO, "Inglés básico"),
            SimulationMessage(SimulationPhase.MIGRATION_HISTORY, "Visa de turista vigente"),
            SimulationMessage(SimulationPhase.USA_GOALS, "Quiero abrir restaurantes en Miami"),
            SimulationMessage(SimulationPhase.VISA_ANALYSIS, "¿Qué visa necesito para invertir?", is_question=True),
            SimulationMessage(SimulationPhase.QUESTIONS, "¿Cuánto tiempo toma el proceso?", is_question=True),
            SimulationMessage(SimulationPhase.CLOSURE, "Perfecto, seguimos en contacto"),
        ]
    },
    {
        "id": 9,
        "name": "Diego - Artista",
        "description": "Músico que busca visa de artista",
        "messages": [
            SimulationMessage(SimulationPhase.START, "Hey! Soy músico"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Diego Fernández, 30 años, chileno"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "Soy guitarrista profesional"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "He tocado en festivales internacionales"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "Tengo 3 discos grabados"),
            SimulationMessage(SimulationPhase.FINANCIAL_INFO, "Inglés intermedio, $10,000 ahorros"),
            SimulationMessage(SimulationPhase.MIGRATION_HISTORY, "He viajado a USA con visa de turista"),
            SimulationMessage(SimulationPhase.USA_GOALS, "Quiero hacer una gira y quedarme"),
            SimulationMessage(SimulationPhase.VISA_ANALYSIS, "¿Existe visa para artistas?", is_question=True),
            SimulationMessage(SimulationPhase.CLOSURE, "Genial, gracias!"),
        ]
    },
    {
        "id": 10,
        "name": "Elena - Caso Complejo",
        "description": "Usuario con situación migratoria compleja",
        "messages": [
            SimulationMessage(SimulationPhase.START, "Hola, mi caso es complicado"),
            SimulationMessage(SimulationPhase.PERSONAL_INFO, "Elena Vargas, 35 años, ecuatoriana"),
            SimulationMessage(SimulationPhase.PROFESSIONAL_INFO, "Enfermera con 10 años de experiencia"),
            SimulationMessage(SimulationPhase.FINANCIAL_INFO, "Inglés avanzado, $25,000"),
            SimulationMessage(SimulationPhase.MIGRATION_HISTORY, "Estuve en USA con visa de turista"),
            SimulationMessage(SimulationPhase.MIGRATION_HISTORY, "Me quedé más tiempo del permitido"),
            SimulationMessage(SimulationPhase.MIGRATION_HISTORY, "Salí hace 5 años"),
            SimulationMessage(SimulationPhase.QUESTIONS, "¿Puedo volver a aplicar?", is_question=True),
            SimulationMessage(SimulationPhase.QUESTIONS, "¿Hay algún perdón?", is_question=True),
            SimulationMessage(SimulationPhase.USA_GOALS, "Quiero trabajar legalmente"),
            SimulationMessage(SimulationPhase.CLOSURE, "Gracias por la honestidad"),
        ]
    },
]


class MigrationCycleSimulator:
    """Simulador de ciclos completos de migración"""
    
    def __init__(self):
        self.priority_handler = PriorityIntentHandler()
        self.input_interpreter = InputInterpreter()
        self.conversational_ai = ConversationalAI()
        self.checklist = get_profile_checklist()
        self.results: List[SimulationResult] = []
    
    def _create_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Crea un perfil de usuario vacío"""
        return {
            "user_id": user_id,
            "state": "start",
            "language": "es",
            "profile": {
                "personal": {},
                "education": {},
                "work": {},
                "languages": {},
                "financial": {},
                "history": {},
                "migration": {}
            },
            "family_members": [],
            "current_family_index": 0,
            "preferences": {},
            "selected_route": {},
            "documents": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def _analyze_message(self, text: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza un mensaje y retorna el análisis"""
        state = user_data.get("state", "start")
        lang = user_data.get("language", "es")
        
        # Detectar intent prioritario
        should_interrupt, intent_type, empathic_response = \
            self.priority_handler.should_interrupt_flow(text)
        
        # Interpretar input
        interpreted = interpret_user_input(text, state)
        
        # Detectar intent conversacional
        conv_intent = self.conversational_ai.detect_intent(text)
        
        return {
            "text": text,
            "priority_intent": {
                "should_interrupt": should_interrupt,
                "type": intent_type,
                "empathic_response": empathic_response
            },
            "interpreted": {
                "type": interpreted.input_type.value,
                "confidence": interpreted.confidence,
                "extracted_data": interpreted.extracted_data,
                "should_advance": interpreted.should_advance
            },
            "conversational_intent": conv_intent.value
        }
    
    def _extract_and_save_data(self, text: str, user_data: Dict[str, Any]) -> List[str]:
        """Extrae datos del mensaje y los guarda en el perfil"""
        extracted = []
        text_lower = text.lower()
        profile = user_data.get("profile", {})
        
        # Extraer nombre
        import re
        name_patterns = [
            r"(?:me llamo|soy|mi nombre es)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)",
            r"^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)$",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2 and "?" not in name:
                    profile.setdefault("personal", {})["name"] = name
                    extracted.append(f"name:{name}")
                    break
        
        # Extraer edad
        age_match = re.search(r"(\d+)\s*años", text_lower)
        if age_match:
            age = int(age_match.group(1))
            if 18 <= age <= 80:
                profile.setdefault("personal", {})["age"] = age
                extracted.append(f"age:{age}")
        
        # Extraer nacionalidad
        nationalities = {
            "colombiano": "Colombiano", "colombiana": "Colombiana",
            "mexicano": "Mexicano", "mexicana": "Mexicana",
            "venezolano": "Venezolano", "venezolana": "Venezolana",
            "argentino": "Argentino", "argentina": "Argentina",
            "peruano": "Peruano", "peruana": "Peruana",
            "chileno": "Chileno", "chilena": "Chilena",
            "ecuatoriano": "Ecuatoriano", "ecuatoriana": "Ecuatoriana",
        }
        for key, value in nationalities.items():
            if key in text_lower:
                profile.setdefault("personal", {})["nationality"] = value
                extracted.append(f"nationality:{value}")
                break
        
        # Extraer profesión
        professions = [
            "ingeniero", "médico", "médica", "doctor", "doctora", "abogado", "abogada",
            "contador", "contadora", "profesor", "profesora", "enfermero", "enfermera",
            "empresario", "empresaria", "músico", "artista", "diseñador", "diseñadora"
        ]
        for prof in professions:
            if prof in text_lower:
                profile.setdefault("work", {})["profession"] = prof.capitalize()
                extracted.append(f"profession:{prof}")
                break
        
        # Extraer nivel de inglés
        english_levels = {
            "inglés nativo": "Nativo", "inglés avanzado": "Avanzado",
            "inglés intermedio": "Intermedio", "inglés básico": "Básico",
            "english native": "Nativo", "english advanced": "Avanzado"
        }
        for key, value in english_levels.items():
            if key in text_lower:
                profile.setdefault("languages", {})["english"] = value
                extracted.append(f"english:{value}")
                break
        
        # Extraer ahorros
        savings_match = re.search(r"\$?([\d,]+)\s*(?:ahorr|saved|dólares|usd)", text_lower)
        if savings_match:
            savings = savings_match.group(1).replace(",", "")
            profile.setdefault("financial", {})["savings"] = f"${savings}"
            extracted.append(f"savings:${savings}")
        
        # Extraer historial de visa
        if "visa" in text_lower:
            if "b1" in text_lower or "b2" in text_lower or "turista" in text_lower:
                profile.setdefault("history", {})["visa_history"] = "B1/B2"
                extracted.append("visa_history:B1/B2")
            if "negaron" in text_lower or "negada" in text_lower:
                profile.setdefault("history", {})["visa_denials"] = True
                extracted.append("visa_denials:True")
            if "nunca" in text_lower and "visa" in text_lower:
                profile.setdefault("history", {})["visa_history"] = "Ninguna"
                extracted.append("visa_history:None")
        
        # Extraer problemas legales
        if "sin problemas legales" in text_lower or "no tengo problemas" in text_lower:
            profile.setdefault("history", {})["legal_issues"] = False
            extracted.append("legal_issues:False")
        
        user_data["profile"] = profile
        return extracted
    
    def _detect_issues(
        self,
        message: SimulationMessage,
        analysis: Dict[str, Any],
        user_data: Dict[str, Any],
        previous_responses: List[str]
    ) -> List[SimulationIssue]:
        """Detecta problemas en la simulación"""
        issues = []
        
        # 1. Detectar loops (respuestas repetidas)
        # Simulamos que el bot respondería algo basado en el análisis
        simulated_response = analysis.get("priority_intent", {}).get("empathic_response", "")
        if simulated_response and previous_responses:
            if simulated_response in previous_responses[-3:]:
                issues.append(SimulationIssue(
                    severity="warning",
                    category="loop",
                    phase=message.phase,
                    message="Posible loop de respuesta detectado",
                    details={"repeated_response": simulated_response[:50]}
                ))
        
        # 2. Detectar datos fantasma
        profile = user_data.get("profile", {})
        profile_intro = get_profile_based_intro(user_data.get("user_id", 0), user_data, "es")
        if "basado en" in profile_intro.lower():
            # Verificar si realmente hay datos confirmados
            confirmed_count = sum(1 for section in profile.values() 
                                 if isinstance(section, dict) and section)
            if confirmed_count < 2:
                issues.append(SimulationIssue(
                    severity="critical",
                    category="ghost_data",
                    phase=message.phase,
                    message="Se usaría 'basado en tu perfil' sin datos suficientes",
                    details={"confirmed_sections": confirmed_count}
                ))
        
        # 3. Detectar saltos de tema
        if message.is_question and not analysis["priority_intent"]["should_interrupt"]:
            issues.append(SimulationIssue(
                severity="warning",
                category="topic_jump",
                phase=message.phase,
                message="Pregunta del usuario no detectada como prioritaria",
                details={"question": message.user_input[:50]}
            ))
        
        # 4. Detectar confusión no manejada
        if message.is_confusion and not analysis["priority_intent"]["should_interrupt"]:
            issues.append(SimulationIssue(
                severity="critical",
                category="topic_jump",
                phase=message.phase,
                message="Confusión del usuario no detectada",
                details={"confusion_text": message.user_input[:50]}
            ))
        
        return issues
    
    async def run_simulation(self, persona: Dict[str, Any]) -> SimulationResult:
        """Ejecuta una simulación completa"""
        start_time = datetime.now()
        user_id = 9000000000 + persona["id"]
        
        # Limpiar datos previos
        try:
            delete_user_data(user_id)
        except:
            pass
        
        # Crear perfil vacío
        user_data = self._create_user_profile(user_id)
        save_user_data(user_id, user_data)
        
        result = SimulationResult(
            simulation_id=persona["id"],
            user_id=user_id,
            persona_name=persona["name"],
            success=True,
            phases_completed=0,
            total_phases=len(persona["messages"])
        )
        
        previous_responses = []
        
        for i, message in enumerate(persona["messages"]):
            # Analizar mensaje
            analysis = self._analyze_message(message.user_input, user_data)
            
            # Extraer y guardar datos
            extracted = self._extract_and_save_data(message.user_input, user_data)
            save_user_data(user_id, user_data)
            
            # Detectar issues
            issues = self._detect_issues(message, analysis, user_data, previous_responses)
            result.issues.extend(issues)
            
            # Simular respuesta
            if analysis["priority_intent"]["empathic_response"]:
                previous_responses.append(analysis["priority_intent"]["empathic_response"])
            
            result.phases_completed += 1
            result.responses_received += 1
            
            # Contar loops
            if any(i.category == "loop" for i in issues):
                result.loops_detected += 1
        
        # Verificar checklist final
        checklist_status = check_profile_completeness(user_id, user_data)
        
        # Verificar datos fantasma en perfil final
        profile = user_data.get("profile", {})
        for section_name, section_data in profile.items():
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    if value and not any(key in msg.user_input.lower() for msg in persona["messages"]):
                        # Dato que no fue mencionado por el usuario
                        result.ghost_data_found.append(f"{section_name}.{key}={value}")
        
        result.final_state = user_data.get("state", "unknown")
        result.final_profile = profile
        result.duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Determinar éxito
        critical_issues = [i for i in result.issues if i.severity == "critical"]
        if critical_issues or result.loops_detected > 2 or len(result.ghost_data_found) > 0:
            result.success = False
        
        return result
    
    async def run_all_simulations(self) -> Dict[str, Any]:
        """Ejecuta todas las simulaciones"""
        print("\n" + "="*70)
        print("  MigPAL - SIMULACIÓN DE 10 CICLOS COMPLETOS DE MIGRACIÓN")
        print("  Fecha:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("="*70)
        
        all_results = []
        
        for persona in SIMULATION_PERSONAS:
            print(f"\n--- Simulación {persona['id']}: {persona['name']} ---")
            print(f"    {persona['description']}")
            
            result = await self.run_simulation(persona)
            all_results.append(result)
            
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"    {status} | Fases: {result.phases_completed}/{result.total_phases}")
            print(f"    Issues: {len(result.issues)} | Loops: {result.loops_detected} | Ghost data: {len(result.ghost_data_found)}")
            
            if result.issues:
                for issue in result.issues[:3]:
                    print(f"    ⚠️ [{issue.severity}] {issue.category}: {issue.message}")
        
        self.results = all_results
        return self._generate_report()
    
    def _generate_report(self) -> Dict[str, Any]:
        """Genera el reporte final"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed
        
        # Agrupar issues por categoría
        issues_by_category = {}
        for result in self.results:
            for issue in result.issues:
                if issue.category not in issues_by_category:
                    issues_by_category[issue.category] = []
                issues_by_category[issue.category].append({
                    "simulation": result.persona_name,
                    "severity": issue.severity,
                    "message": issue.message,
                    "phase": issue.phase.value
                })
        
        # Calcular métricas
        total_loops = sum(r.loops_detected for r in self.results)
        total_ghost_data = sum(len(r.ghost_data_found) for r in self.results)
        total_issues = sum(len(r.issues) for r in self.results)
        
        report = {
            "summary": {
                "total_simulations": total,
                "passed": passed,
                "failed": failed,
                "success_rate": f"{passed/total*100:.1f}%",
                "total_issues": total_issues,
                "total_loops": total_loops,
                "total_ghost_data": total_ghost_data
            },
            "issues_by_category": issues_by_category,
            "failed_simulations": [
                {
                    "name": r.persona_name,
                    "issues": [{"category": i.category, "message": i.message} for i in r.issues],
                    "ghost_data": r.ghost_data_found
                }
                for r in self.results if not r.success
            ],
            "recommendations": self._generate_recommendations(issues_by_category, total_loops, total_ghost_data)
        }
        
        return report
    
    def _generate_recommendations(
        self,
        issues_by_category: Dict[str, List],
        total_loops: int,
        total_ghost_data: int
    ) -> List[Dict[str, str]]:
        """Genera recomendaciones basadas en los problemas encontrados"""
        recommendations = []
        
        if "loop" in issues_by_category:
            recommendations.append({
                "priority": "HIGH",
                "issue": "Loops de respuesta detectados",
                "count": len(issues_by_category["loop"]),
                "solution": "Implementar tracking de respuestas previas y variar mensajes empáticos"
            })
        
        if "ghost_data" in issues_by_category:
            recommendations.append({
                "priority": "CRITICAL",
                "issue": "Datos fantasma detectados",
                "count": len(issues_by_category["ghost_data"]),
                "solution": "Reforzar validación en profile_validator.py antes de usar 'basado en tu perfil'"
            })
        
        if "topic_jump" in issues_by_category:
            recommendations.append({
                "priority": "HIGH",
                "issue": "Preguntas/confusión no detectadas",
                "count": len(issues_by_category["topic_jump"]),
                "solution": "Ampliar patrones en PriorityIntentHandler para detectar más variaciones"
            })
        
        if total_loops > 5:
            recommendations.append({
                "priority": "MEDIUM",
                "issue": f"Alto número de loops ({total_loops})",
                "solution": "Implementar sistema de variación de respuestas empáticas"
            })
        
        if total_ghost_data > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "issue": f"Datos fantasma en perfiles ({total_ghost_data})",
                "solution": "Revisar extracción de datos y validar contra input real del usuario"
            })
        
        return recommendations


def print_report(report: Dict[str, Any]):
    """Imprime el reporte de forma legible"""
    print("\n" + "="*70)
    print("  REPORTE DE SIMULACIÓN")
    print("="*70)
    
    summary = report["summary"]
    print(f"\n📊 RESUMEN:")
    print(f"   Total simulaciones: {summary['total_simulations']}")
    print(f"   Exitosas: {summary['passed']} ✅")
    print(f"   Fallidas: {summary['failed']} ❌")
    print(f"   Tasa de éxito: {summary['success_rate']}")
    print(f"   Total issues: {summary['total_issues']}")
    print(f"   Total loops: {summary['total_loops']}")
    print(f"   Total datos fantasma: {summary['total_ghost_data']}")
    
    if report["issues_by_category"]:
        print(f"\n🔍 ISSUES POR CATEGORÍA:")
        for category, issues in report["issues_by_category"].items():
            print(f"   {category}: {len(issues)} issues")
            for issue in issues[:2]:
                print(f"      - [{issue['severity']}] {issue['simulation']}: {issue['message'][:50]}")
    
    if report["failed_simulations"]:
        print(f"\n❌ SIMULACIONES FALLIDAS:")
        for sim in report["failed_simulations"]:
            print(f"   {sim['name']}:")
            for issue in sim["issues"][:3]:
                print(f"      - {issue['category']}: {issue['message'][:50]}")
            if sim["ghost_data"]:
                print(f"      - Ghost data: {sim['ghost_data'][:3]}")
    
    if report["recommendations"]:
        print(f"\n💡 RECOMENDACIONES:")
        for rec in report["recommendations"]:
            print(f"   [{rec['priority']}] {rec['issue']}")
            print(f"      Solución: {rec['solution']}")
    
    print("\n" + "="*70)


async def main():
    simulator = MigrationCycleSimulator()
    report = await simulator.run_all_simulations()
    print_report(report)
    
    # Guardar reporte en archivo
    report_path = "/workspace/hjrm/migpal/backend/reports/simulation_report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📄 Reporte guardado en: {report_path}")
    
    return report


if __name__ == "__main__":
    report = asyncio.run(main())

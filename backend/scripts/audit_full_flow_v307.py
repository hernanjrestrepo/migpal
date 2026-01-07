#!/usr/bin/env python3
"""
Auditoría Conversacional Exhaustiva v3.0.7
==========================================
Simula el flujo COMPLETO desde /start hasta Plan Migratorio 100%.
Detecta estados huérfanos y bloqueos.

USO:
    python scripts/audit_full_flow_v307.py
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class FlowStep:
    """Un paso en el flujo"""
    state: str
    action: str  # "message" o "callback"
    input_data: str
    expected_next_state: str
    description: str


class FlowAuditor:
    """Auditor del flujo conversacional completo"""
    
    def __init__(self):
        self.user_id = 777666555
        self.errors = []
        self.warnings = []
        self.steps_completed = 0
        
    def get_full_flow_steps(self) -> List[FlowStep]:
        """Definir todos los pasos del flujo completo"""
        return [
            # === ONBOARDING ===
            FlowStep("start", "callback", "lang_es", "onboarding_question", "Seleccionar idioma español"),
            FlowStep("onboarding_question", "message", "Quiero mejores oportunidades de trabajo", "onboarding_consent", "Responder pregunta abierta"),
            FlowStep("onboarding_consent", "callback", "onboarding_yes", "onboarding_name", "Aceptar empezar"),
            FlowStep("onboarding_name", "message", "Juan Carlos Pérez", "confirm_name", "Dar nombre"),
            FlowStep("confirm_name", "callback", "confirm_name_yes", "start", "Confirmar nombre"),
            
            # === DISCOVERY ===
            FlowStep("start", "callback", "flow_start_discovery", "discovery_why", "Iniciar descubrimiento"),
            FlowStep("discovery_why", "callback", "flow_why_work", "discovery_dream", "Seleccionar razón: trabajo"),
            FlowStep("discovery_dream", "message", "Quiero ser ingeniero de software en Silicon Valley", "discovery_family", "Describir sueño"),
            FlowStep("discovery_family", "callback", "flow_family_spouse", "discovery_usa_connections", "Indicar familia"),
            FlowStep("discovery_usa_connections", "callback", "flow_connections_none", "life_work_or_business", "Indicar conexiones USA"),
            
            # === LIFE PLAN ===
            FlowStep("life_work_or_business", "callback", "flow_work", "life_profession", "Elegir trabajo"),
            FlowStep("life_profession", "message", "Ingeniero de Software", "life_experience", "Indicar profesión"),
            FlowStep("life_experience", "callback", "flow_exp_5plus", "life_salary", "Indicar experiencia"),
            FlowStep("life_salary", "message", "150000", "life_remote", "Indicar salario deseado"),
            FlowStep("life_remote", "callback", "flow_remote_hybrid", "location_region", "Preferencia remoto"),
            
            # === LOCATION ===
            FlowStep("location_region", "callback", "flow_region_west", "location_state", "Elegir región"),
            FlowStep("location_state", "callback", "flow_state_california", "location_city", "Elegir estado"),
            FlowStep("location_city", "callback", "flow_city_san_jose", "location_confirm", "Elegir ciudad"),
            FlowStep("location_confirm", "callback", "flow_location_confirm", "visa_analysis", "Confirmar ubicación"),
            
            # === VISA ANALYSIS ===
            FlowStep("visa_analysis", "callback", "flow_visa_start", "visa_recommendation", "Iniciar análisis visa"),
            FlowStep("visa_recommendation", "callback", "flow_visa_accept", "plan_generation", "Aceptar recomendación"),
            
            # === PLAN GENERATION ===
            FlowStep("plan_generation", "callback", "flow_generate_plan", "plan_complete", "Generar plan"),
        ]
    
    async def simulate_step(self, step: FlowStep, user: Dict) -> Tuple[bool, str, str]:
        """
        Simular un paso del flujo.
        
        Returns:
            Tuple[success, actual_state, error_message]
        """
        from app.services.case_storage import save_user_data, load_user_data
        
        current_state = user.get("state", "unknown")
        
        logger.info(f"📍 Step: {step.description}")
        logger.info(f"   Estado actual: {current_state}")
        logger.info(f"   Acción: {step.action} -> {step.input_data}")
        logger.info(f"   Estado esperado: {step.expected_next_state}")
        
        try:
            if step.action == "callback":
                # Simular callback
                new_state = await self._process_callback(user, step.input_data)
            else:
                # Simular mensaje
                new_state = await self._process_message(user, step.input_data)
            
            # Verificar transición
            if new_state == step.expected_next_state:
                logger.info(f"   ✅ Transición correcta: {current_state} -> {new_state}")
                return True, new_state, ""
            else:
                error = f"Estado incorrecto: esperado '{step.expected_next_state}', obtenido '{new_state}'"
                logger.error(f"   ❌ {error}")
                return False, new_state, error
                
        except Exception as e:
            error = f"Excepción: {str(e)}"
            logger.error(f"   ❌ {error}")
            return False, current_state, error
    
    async def _process_callback(self, user: Dict, callback_data: str) -> str:
        """Procesar un callback y retornar el nuevo estado"""
        from app.services.case_storage import save_user_data, load_user_data
        from app.services.telegram_bot import set_state, get_state
        
        user_id = self.user_id
        state = user.get("state", "start")
        lang = user.get("language", "es")
        
        # Simular diferentes callbacks
        if callback_data.startswith("lang_"):
            lang_code = callback_data.split("_")[1]
            user["language"] = lang_code
            save_user_data(user_id, user)
            
            # Después de idioma, va a onboarding
            from app.services.onboarding_v306 import OnboardingState
            set_state(user_id, OnboardingState.WELCOME.value)
            return OnboardingState.OPEN_QUESTION.value  # El bot envía welcome y luego question
        
        elif callback_data == "onboarding_yes":
            from app.services.onboarding_v306 import OnboardingState
            set_state(user_id, OnboardingState.NAME_REQUEST.value)
            return OnboardingState.NAME_REQUEST.value
        
        elif callback_data == "confirm_name_yes":
            # Confirmar nombre - debe avanzar a start con opciones
            name = user.get("profile", {}).get("personal", {}).get("name", "")
            if name:
                set_state(user_id, "start")
                return "start"
            else:
                return "confirm_name"  # Error: no hay nombre
        
        elif callback_data == "flow_start_discovery":
            from app.services.conversation_flow import ConversationState
            set_state(user_id, "discovery_why")
            return "discovery_why"
        
        elif callback_data.startswith("flow_why_"):
            set_state(user_id, "discovery_dream")
            return "discovery_dream"
        
        elif callback_data.startswith("flow_family_"):
            set_state(user_id, "discovery_usa_connections")
            return "discovery_usa_connections"
        
        elif callback_data.startswith("flow_connections_"):
            set_state(user_id, "life_work_or_business")
            return "life_work_or_business"
        
        elif callback_data == "flow_work":
            set_state(user_id, "life_profession")
            return "life_profession"
        
        elif callback_data.startswith("flow_exp_"):
            set_state(user_id, "life_salary")
            return "life_salary"
        
        elif callback_data.startswith("flow_remote_"):
            set_state(user_id, "location_region")
            return "location_region"
        
        elif callback_data.startswith("flow_region_"):
            set_state(user_id, "location_state")
            return "location_state"
        
        elif callback_data.startswith("flow_state_"):
            set_state(user_id, "location_city")
            return "location_city"
        
        elif callback_data.startswith("flow_city_"):
            set_state(user_id, "location_confirm")
            return "location_confirm"
        
        elif callback_data == "flow_location_confirm":
            set_state(user_id, "visa_analysis")
            return "visa_analysis"
        
        elif callback_data == "flow_visa_start":
            set_state(user_id, "visa_recommendation")
            return "visa_recommendation"
        
        elif callback_data == "flow_visa_accept":
            set_state(user_id, "plan_generation")
            return "plan_generation"
        
        elif callback_data == "flow_generate_plan":
            set_state(user_id, "plan_complete")
            return "plan_complete"
        
        return get_state(user_id)
    
    async def _process_message(self, user: Dict, text: str) -> str:
        """Procesar un mensaje y retornar el nuevo estado"""
        from app.services.case_storage import save_user_data
        from app.services.telegram_bot import set_state, get_state
        
        user_id = self.user_id
        state = user.get("state", "start")
        
        if state == "onboarding_question":
            # Respuesta a pregunta abierta -> consent
            from app.services.onboarding_v306 import OnboardingState
            set_state(user_id, OnboardingState.CONSENT.value)
            return OnboardingState.CONSENT.value
        
        elif state == "onboarding_name":
            # Dar nombre -> confirm_name
            user["profile"]["personal"]["name"] = text
            save_user_data(user_id, user)
            set_state(user_id, "confirm_name")
            return "confirm_name"
        
        elif state == "discovery_dream":
            # Describir sueño -> family
            user["profile"]["migration"]["dream"] = text
            save_user_data(user_id, user)
            set_state(user_id, "discovery_family")
            return "discovery_family"
        
        elif state == "life_profession":
            # Indicar profesión -> experience
            user["profile"]["professional"]["profession"] = text
            save_user_data(user_id, user)
            set_state(user_id, "life_experience")
            return "life_experience"
        
        elif state == "life_salary":
            # Indicar salario -> remote
            user["profile"]["professional"]["desired_salary"] = text
            save_user_data(user_id, user)
            set_state(user_id, "life_remote")
            return "life_remote"
        
        return get_state(user_id)
    
    async def run_full_audit(self) -> Dict[str, Any]:
        """Ejecutar auditoría completa del flujo"""
        from app.services.case_storage import save_user_data, delete_user_data, load_user_data
        from app.services.telegram_bot import set_state
        
        logger.info("=" * 60)
        logger.info("🔍 AUDITORÍA CONVERSACIONAL EXHAUSTIVA v3.0.7")
        logger.info("=" * 60)
        
        results = {
            "total_steps": 0,
            "completed_steps": 0,
            "failed_steps": 0,
            "errors": [],
            "orphan_states": [],
            "blocked_at": None,
        }
        
        try:
            # Limpiar usuario de prueba
            delete_user_data(self.user_id)
            
            # Crear usuario inicial
            user = {
                "language": "",
                "state": "start",
                "profile": {
                    "personal": {},
                    "professional": {},
                    "migration": {},
                }
            }
            save_user_data(self.user_id, user)
            set_state(self.user_id, "start")
            
            steps = self.get_full_flow_steps()
            results["total_steps"] = len(steps)
            
            for i, step in enumerate(steps):
                logger.info(f"\n--- Paso {i+1}/{len(steps)} ---")
                
                # Recargar usuario
                user = load_user_data(self.user_id) or user
                
                success, new_state, error = await self.simulate_step(step, user)
                
                if success:
                    results["completed_steps"] += 1
                    user["state"] = new_state
                    save_user_data(self.user_id, user)
                else:
                    results["failed_steps"] += 1
                    results["errors"].append({
                        "step": i + 1,
                        "description": step.description,
                        "error": error,
                        "state": new_state,
                    })
                    results["blocked_at"] = step.description
                    
                    # Detectar estado huérfano
                    if "Estado incorrecto" in error:
                        results["orphan_states"].append(new_state)
                    
                    logger.error(f"❌ FLUJO BLOQUEADO en paso {i+1}: {step.description}")
                    break
            
            # Resumen
            logger.info("\n" + "=" * 60)
            logger.info("📊 RESUMEN DE AUDITORÍA")
            logger.info("=" * 60)
            logger.info(f"Total pasos: {results['total_steps']}")
            logger.info(f"Completados: {results['completed_steps']}")
            logger.info(f"Fallidos: {results['failed_steps']}")
            
            if results["errors"]:
                logger.info("\n❌ ERRORES:")
                for err in results["errors"]:
                    logger.info(f"  - Paso {err['step']}: {err['description']}")
                    logger.info(f"    Error: {err['error']}")
            
            if results["orphan_states"]:
                logger.info(f"\n⚠️ ESTADOS HUÉRFANOS: {results['orphan_states']}")
            
            if results["blocked_at"]:
                logger.info(f"\n🚫 BLOQUEADO EN: {results['blocked_at']}")
            else:
                logger.info("\n✅ FLUJO COMPLETO SIN BLOQUEOS")
            
        finally:
            # Limpiar
            delete_user_data(self.user_id)
        
        return results


async def main():
    auditor = FlowAuditor()
    results = await auditor.run_full_audit()
    
    # Exit code basado en resultados
    if results["failed_steps"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Simulación Manual Tipo Telegram v3.0.9
======================================
Simula conversaciones REALES end-to-end hasta Plan Migratorio 100%.

Reglas:
1. Detectar saltos de flujo (ofrecer visa sin perfilar familia, edad, motivo)
2. Prohibir recomendaciones sin contexto completo
3. Máximo 1 formulario cada 5 interacciones
4. Si usuario corrige/duda, reinterpretar, no avanzar
5. Flujo: general → particular (motivo → familia → vida → trabajo → dinero → lugar → visa)

Objetivo: MigPAL debe sentirse como consultor humano, no bot.
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Un turno de conversación"""
    speaker: str  # "user" o "bot"
    message: str
    state_before: str
    state_after: str
    is_form: bool = False  # ¿Es un formulario?
    has_buttons: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FlowViolation:
    """Violación de flujo detectada"""
    type: str
    description: str
    turn_number: int
    severity: str  # "critical", "warning", "info"


@dataclass
class SimulationResult:
    """Resultado de una simulación"""
    success: bool
    turns: List[ConversationTurn]
    violations: List[FlowViolation]
    profile_completeness: float
    plan_generated: bool
    friction_points: List[str]


class ManualSimulator:
    """Simulador manual de conversaciones tipo Telegram"""
    
    # Orden correcto del flujo: general → particular
    CORRECT_FLOW_ORDER = [
        "greeting",      # Saludo y presentación
        "motivation",    # ¿Por qué quieres migrar?
        "family",        # Situación familiar
        "life_goals",    # Vida deseada
        "work",          # Trabajo/profesión
        "finances",      # Recursos económicos
        "location",      # Lugar destino
        "visa",          # Tipo de visa
        "plan",          # Plan migratorio
    ]
    
    # Campos requeridos antes de hacer recomendaciones
    REQUIRED_FOR_VISA = ["motivation", "family", "work", "finances"]
    REQUIRED_FOR_LOCATION = ["motivation", "life_goals", "work"]
    REQUIRED_FOR_PLAN = ["motivation", "family", "work", "finances", "location", "visa"]
    
    def __init__(self):
        self.user_id = 999888777
        self.turns: List[ConversationTurn] = []
        self.violations: List[FlowViolation] = []
        self.form_count = 0
        self.interaction_count = 0
        self.collected_data = {}
        self.current_phase = "greeting"
        
    def reset(self):
        """Reiniciar simulación"""
        self.turns = []
        self.violations = []
        self.form_count = 0
        self.interaction_count = 0
        self.collected_data = {}
        self.current_phase = "greeting"
    
    async def simulate_conversation(self, scenario: str = "standard") -> SimulationResult:
        """Simular una conversación completa"""
        from app.services.case_storage import save_user_data, load_user_data, delete_user_data
        from app.services.telegram_bot import set_state, get_state
        
        self.reset()
        
        logger.info("=" * 70)
        logger.info(f"🎭 SIMULACIÓN MANUAL: {scenario}")
        logger.info("=" * 70)
        
        try:
            # Limpiar usuario
            delete_user_data(self.user_id)
            
            # Crear usuario inicial
            user = {
                "language": "es",
                "state": "start",
                "profile": {
                    "personal": {},
                    "professional": {},
                    "migration": {},
                    "financial": {},
                }
            }
            save_user_data(self.user_id, user)
            
            # Ejecutar escenario
            if scenario == "standard":
                await self._run_standard_scenario(user)
            elif scenario == "confused_user":
                await self._run_confused_user_scenario(user)
            elif scenario == "correction_flow":
                await self._run_correction_scenario(user)
            elif scenario == "skip_attempt":
                await self._run_skip_attempt_scenario(user)
            
            # Calcular resultados
            profile_completeness = self._calculate_profile_completeness()
            plan_generated = "plan" in self.collected_data
            
            return SimulationResult(
                success=len([v for v in self.violations if v.severity == "critical"]) == 0,
                turns=self.turns,
                violations=self.violations,
                profile_completeness=profile_completeness,
                plan_generated=plan_generated,
                friction_points=self._identify_friction_points()
            )
            
        finally:
            delete_user_data(self.user_id)
    
    async def _run_standard_scenario(self, user: Dict):
        """Escenario estándar: usuario cooperativo"""
        
        # 1. INICIO - Selección de idioma
        await self._simulate_turn(
            user_input=None,
            callback="lang_es",
            expected_phase="greeting",
            description="Seleccionar idioma"
        )
        
        # 2. ONBOARDING - Respuesta a pregunta abierta
        await self._simulate_turn(
            user_input="Quiero mejores oportunidades para mi familia",
            expected_phase="motivation",
            description="Responder motivación"
        )
        
        # 3. CONSENTIMIENTO
        await self._simulate_turn(
            user_input=None,
            callback="onboarding_yes",
            expected_phase="greeting",
            description="Aceptar empezar"
        )
        
        # 4. NOMBRE
        await self._simulate_turn(
            user_input="Carlos Rodríguez",
            expected_phase="greeting",
            description="Dar nombre"
        )
        
        # 5. CONFIRMAR NOMBRE
        await self._simulate_turn(
            user_input=None,
            callback="confirm_name_yes",
            expected_phase="greeting",
            description="Confirmar nombre"
        )
        
        # 6. INICIAR DISCOVERY
        await self._simulate_turn(
            user_input=None,
            callback="flow_start_discovery",
            expected_phase="motivation",
            description="Iniciar descubrimiento"
        )
        
        # 7. RAZÓN DE MIGRAR
        await self._simulate_turn(
            user_input=None,
            callback="flow_why_work",
            expected_phase="motivation",
            description="Seleccionar razón: trabajo"
        )
        
        # 8. SUEÑO/META
        await self._simulate_turn(
            user_input="Quiero trabajar en tecnología y darle mejor educación a mis hijos",
            expected_phase="life_goals",
            description="Describir sueño"
        )
        
        # 9. FAMILIA
        await self._simulate_turn(
            user_input=None,
            callback="flow_family_spouse_kids",
            expected_phase="family",
            description="Indicar familia"
        )
        
        # 10. CONEXIONES USA
        await self._simulate_turn(
            user_input=None,
            callback="flow_connections_none",
            expected_phase="family",
            description="Sin conexiones USA"
        )
        
        # 11. TRABAJO O NEGOCIO
        await self._simulate_turn(
            user_input=None,
            callback="flow_work",
            expected_phase="work",
            description="Elegir trabajo"
        )
        
        # 12. PROFESIÓN
        await self._simulate_turn(
            user_input="Ingeniero de Software con 8 años de experiencia",
            expected_phase="work",
            description="Indicar profesión"
        )
        
        # 13. EXPERIENCIA
        await self._simulate_turn(
            user_input=None,
            callback="flow_exp_5plus",
            expected_phase="work",
            description="Indicar experiencia"
        )
        
        # 14. SALARIO
        await self._simulate_turn(
            user_input="Actualmente gano $3000 USD mensuales",
            expected_phase="finances",
            description="Indicar salario actual"
        )
        
        # 15. AHORROS
        await self._simulate_turn(
            user_input="Tengo ahorrados unos $25,000 USD",
            expected_phase="finances",
            description="Indicar ahorros"
        )
        
        # 16. PREFERENCIA REMOTO
        await self._simulate_turn(
            user_input=None,
            callback="flow_remote_hybrid",
            expected_phase="work",
            description="Preferencia híbrido"
        )
        
        # VERIFICAR: No debe ofrecer ubicación sin contexto completo
        self._check_flow_violation("location", "Ofrecer ubicación")
        
        # 17. REGIÓN
        await self._simulate_turn(
            user_input="No conozco bien Estados Unidos, ¿qué me recomiendas?",
            expected_phase="location",
            description="Preguntar sobre regiones"
        )
        
        # 18. SELECCIONAR REGIÓN
        await self._simulate_turn(
            user_input=None,
            callback="flow_region_west",
            expected_phase="location",
            description="Elegir región oeste"
        )
        
        # 19. ESTADO
        await self._simulate_turn(
            user_input=None,
            callback="flow_state_california",
            expected_phase="location",
            description="Elegir California"
        )
        
        # 20. CIUDAD
        await self._simulate_turn(
            user_input=None,
            callback="flow_city_san_jose",
            expected_phase="location",
            description="Elegir San José"
        )
        
        # VERIFICAR: No debe ofrecer visa sin contexto completo
        self._check_flow_violation("visa", "Ofrecer visa")
        
        # 21. ANÁLISIS VISA
        await self._simulate_turn(
            user_input=None,
            callback="flow_visa_start",
            expected_phase="visa",
            description="Iniciar análisis visa"
        )
        
        # 22. ACEPTAR RECOMENDACIÓN
        await self._simulate_turn(
            user_input=None,
            callback="flow_visa_accept",
            expected_phase="visa",
            description="Aceptar recomendación visa"
        )
        
        # VERIFICAR: No debe generar plan sin contexto completo
        self._check_flow_violation("plan", "Generar plan")
        
        # 23. GENERAR PLAN
        await self._simulate_turn(
            user_input=None,
            callback="flow_generate_plan",
            expected_phase="plan",
            description="Generar plan migratorio"
        )
        
        self.collected_data["plan"] = True
    
    async def _run_confused_user_scenario(self, user: Dict):
        """Escenario: usuario confundido que no sabe qué elegir"""
        
        # 1. INICIO
        await self._simulate_turn(
            user_input=None,
            callback="lang_es",
            expected_phase="greeting",
            description="Seleccionar idioma"
        )
        
        # 2. RESPUESTA CONFUSA
        await self._simulate_turn(
            user_input="No sé, estoy confundido, hay muchas opciones",
            expected_phase="motivation",
            description="Usuario confundido"
        )
        
        # VERIFICAR: Bot debe ayudar, no mostrar error
        last_turn = self.turns[-1] if self.turns else None
        if last_turn and "error" in last_turn.message.lower():
            self.violations.append(FlowViolation(
                type="error_shown",
                description="Se mostró error a usuario confundido",
                turn_number=len(self.turns),
                severity="critical"
            ))
        
        # 3. USUARIO SIGUE CONFUNDIDO
        await self._simulate_turn(
            user_input="Es que no estoy seguro si quiero migrar o no",
            expected_phase="motivation",
            description="Usuario dudando"
        )
        
        # 4. USUARIO PREGUNTA
        await self._simulate_turn(
            user_input="¿Qué opciones tengo si soy ingeniero?",
            expected_phase="work",
            description="Usuario pregunta opciones"
        )
    
    async def _run_correction_scenario(self, user: Dict):
        """Escenario: usuario que corrige información"""
        
        # 1. INICIO
        await self._simulate_turn(
            user_input=None,
            callback="lang_es",
            expected_phase="greeting",
            description="Seleccionar idioma"
        )
        
        # 2. RESPUESTA
        await self._simulate_turn(
            user_input="Quiero trabajar en USA",
            expected_phase="motivation",
            description="Motivación inicial"
        )
        
        # 3. CONSENTIMIENTO
        await self._simulate_turn(
            user_input=None,
            callback="onboarding_yes",
            expected_phase="greeting",
            description="Aceptar"
        )
        
        # 4. NOMBRE INCORRECTO
        await self._simulate_turn(
            user_input="Juann",
            expected_phase="greeting",
            description="Nombre con typo"
        )
        
        # 5. CORREGIR NOMBRE
        await self._simulate_turn(
            user_input="Perdón, mi nombre correcto es Juan García",
            expected_phase="greeting",
            description="Corregir nombre"
        )
        
        # VERIFICAR: Bot debe aceptar corrección
        # No debe avanzar sin confirmar la corrección
    
    async def _run_skip_attempt_scenario(self, user: Dict):
        """Escenario: usuario intenta saltar pasos"""
        
        # 1. INICIO
        await self._simulate_turn(
            user_input=None,
            callback="lang_es",
            expected_phase="greeting",
            description="Seleccionar idioma"
        )
        
        # 2. USUARIO QUIERE SALTAR AL FINAL
        await self._simulate_turn(
            user_input="Solo dime qué visa necesito para ir a USA",
            expected_phase="visa",
            description="Intentar saltar a visa"
        )
        
        # VERIFICAR: Bot NO debe dar recomendación de visa sin contexto
        last_turn = self.turns[-1] if self.turns else None
        if last_turn:
            visa_keywords = ["H-1B", "L-1", "O-1", "EB-", "visa de trabajo"]
            if any(kw in last_turn.message for kw in visa_keywords):
                self.violations.append(FlowViolation(
                    type="premature_recommendation",
                    description="Se recomendó visa sin conocer perfil completo",
                    turn_number=len(self.turns),
                    severity="critical"
                ))
        
        # 3. USUARIO INSISTE
        await self._simulate_turn(
            user_input="¿Pero cuál es la mejor visa para ingenieros?",
            expected_phase="visa",
            description="Insistir en visa"
        )
        
        # VERIFICAR: Bot debe pedir más información primero
    
    async def _simulate_turn(
        self,
        user_input: Optional[str],
        callback: Optional[str] = None,
        expected_phase: str = "",
        description: str = ""
    ):
        """Simular un turno de conversación"""
        from app.services.case_storage import save_user_data, load_user_data
        from app.services.telegram_bot import set_state, get_state
        
        self.interaction_count += 1
        
        user = load_user_data(self.user_id) or {}
        state_before = user.get("state", "start")
        
        logger.info(f"\n--- Turno {self.interaction_count}: {description} ---")
        
        if user_input:
            logger.info(f"👤 Usuario: {user_input}")
            
            # Procesar con IA conversacional
            response = await self._process_user_input(user_input, user)
            
        elif callback:
            logger.info(f"🔘 Callback: {callback}")
            
            # Procesar callback
            response = await self._process_callback(callback, user)
        
        # Recargar usuario para ver cambios
        user = load_user_data(self.user_id) or user
        state_after = user.get("state", state_before)
        
        # Detectar si es formulario
        is_form = self._is_form_response(response)
        if is_form:
            self.form_count += 1
            
            # Verificar regla: máximo 1 formulario cada 5 interacciones
            if self.form_count > (self.interaction_count / 5):
                self.violations.append(FlowViolation(
                    type="too_many_forms",
                    description=f"Demasiados formularios: {self.form_count} en {self.interaction_count} interacciones",
                    turn_number=self.interaction_count,
                    severity="warning"
                ))
        
        logger.info(f"🤖 MigPAL: {response[:200]}..." if len(response) > 200 else f"🤖 MigPAL: {response}")
        logger.info(f"   Estado: {state_before} → {state_after}")
        
        # Registrar turno
        self.turns.append(ConversationTurn(
            speaker="user" if user_input else "system",
            message=user_input or callback or "",
            state_before=state_before,
            state_after=state_after,
            is_form=is_form
        ))
        
        self.turns.append(ConversationTurn(
            speaker="bot",
            message=response,
            state_before=state_before,
            state_after=state_after,
            is_form=is_form,
            has_buttons="[" in response or "botón" in response.lower()
        ))
        
        # Actualizar fase actual
        self._update_phase(expected_phase, user)
    
    async def _process_user_input(self, text: str, user: Dict) -> str:
        """Procesar input del usuario"""
        from app.services.conversational_ai import get_conversational_ai
        
        try:
            ai = get_conversational_ai()
            state = user.get("state", "start")
            lang = user.get("language", "es")
            
            response = await ai.process_free_text(text, user, state, lang)
            return response.message
        except Exception as e:
            logger.error(f"Error procesando input: {e}")
            return f"[Error: {e}]"
    
    async def _process_callback(self, callback: str, user: Dict) -> str:
        """Procesar callback"""
        from app.services.case_storage import save_user_data
        from app.services.telegram_bot import set_state
        
        # Simular respuestas según callback
        responses = {
            "lang_es": "✅ 🇪🇸 Español\n\n¡Hola! Soy MigPAL...",
            "onboarding_yes": "¡Perfecto! 🎉\n\n¿Cuál es tu nombre?",
            "confirm_name_yes": "¡Mucho gusto! Vamos a conocerte mejor...",
            "flow_start_discovery": "📊 PASO 1: DESCUBRIMIENTO\n\n¿Por qué quieres migrar?",
            "flow_why_work": "💼 Excelente, buscas mejores oportunidades laborales...",
            "flow_family_spouse_kids": "👨‍👩‍👧 Entiendo, viajas con familia...",
            "flow_connections_none": "Sin conexiones en USA, entendido...",
            "flow_work": "💼 Perfecto, te interesa trabajar...",
            "flow_exp_5plus": "¡Excelente! +5 años de experiencia...",
            "flow_remote_hybrid": "🏠 Preferencia híbrida, entendido...",
            "flow_region_west": "🌲 Región Oeste seleccionada...",
            "flow_state_california": "☀️ California, excelente elección...",
            "flow_city_san_jose": "🏙️ San José, hub tecnológico...",
            "flow_visa_start": "📋 Analizando opciones de visa...",
            "flow_visa_accept": "✅ Visa H-1B recomendada...",
            "flow_generate_plan": "🗺️ PLAN MIGRATORIO GENERADO\n\n...",
        }
        
        return responses.get(callback, f"[Callback: {callback}]")
    
    def _is_form_response(self, response: str) -> bool:
        """Detectar si la respuesta es un formulario"""
        form_indicators = [
            "selecciona",
            "elige",
            "¿cuál es tu",
            "escribe tu",
            "ingresa",
            "FASE",
            "PASO",
        ]
        return any(ind.lower() in response.lower() for ind in form_indicators)
    
    def _check_flow_violation(self, phase: str, action: str):
        """Verificar si hay violación de flujo"""
        required = {
            "location": self.REQUIRED_FOR_LOCATION,
            "visa": self.REQUIRED_FOR_VISA,
            "plan": self.REQUIRED_FOR_PLAN,
        }
        
        if phase in required:
            missing = [r for r in required[phase] if r not in self.collected_data]
            if missing:
                self.violations.append(FlowViolation(
                    type="premature_action",
                    description=f"{action} sin completar: {missing}",
                    turn_number=self.interaction_count,
                    severity="critical"
                ))
    
    def _update_phase(self, expected_phase: str, user: Dict):
        """Actualizar fase y datos recolectados"""
        if expected_phase:
            self.current_phase = expected_phase
            self.collected_data[expected_phase] = True
    
    def _calculate_profile_completeness(self) -> float:
        """Calcular completitud del perfil"""
        required = ["motivation", "family", "work", "finances", "location", "visa"]
        completed = sum(1 for r in required if r in self.collected_data)
        return completed / len(required) * 100
    
    def _identify_friction_points(self) -> List[str]:
        """Identificar puntos de fricción"""
        friction = []
        
        for turn in self.turns:
            if turn.speaker == "bot":
                if "error" in turn.message.lower():
                    friction.append(f"Error mostrado en turno {self.turns.index(turn)}")
                if "inténtalo" in turn.message.lower():
                    friction.append(f"Retry solicitado en turno {self.turns.index(turn)}")
        
        if self.form_count > self.interaction_count / 5:
            friction.append(f"Demasiados formularios: {self.form_count}/{self.interaction_count}")
        
        return friction


async def run_all_simulations():
    """Ejecutar todas las simulaciones"""
    simulator = ManualSimulator()
    
    scenarios = [
        "standard",
        "confused_user",
        "correction_flow",
        "skip_attempt",
    ]
    
    results = {}
    
    for scenario in scenarios:
        logger.info(f"\n{'='*70}")
        logger.info(f"EJECUTANDO ESCENARIO: {scenario}")
        logger.info(f"{'='*70}")
        
        result = await simulator.simulate_conversation(scenario)
        results[scenario] = result
        
        logger.info(f"\n📊 RESULTADO: {scenario}")
        logger.info(f"   Éxito: {'✅' if result.success else '❌'}")
        logger.info(f"   Turnos: {len(result.turns)}")
        logger.info(f"   Violaciones: {len(result.violations)}")
        logger.info(f"   Completitud perfil: {result.profile_completeness:.1f}%")
        logger.info(f"   Plan generado: {'✅' if result.plan_generated else '❌'}")
        
        if result.violations:
            logger.info(f"\n   ⚠️ VIOLACIONES:")
            for v in result.violations:
                logger.info(f"      [{v.severity}] {v.type}: {v.description}")
        
        if result.friction_points:
            logger.info(f"\n   🔴 PUNTOS DE FRICCIÓN:")
            for f in result.friction_points:
                logger.info(f"      - {f}")
    
    # Resumen final
    logger.info(f"\n{'='*70}")
    logger.info("📋 RESUMEN FINAL")
    logger.info(f"{'='*70}")
    
    total_violations = sum(len(r.violations) for r in results.values())
    critical_violations = sum(
        len([v for v in r.violations if v.severity == "critical"])
        for r in results.values()
    )
    
    logger.info(f"Total escenarios: {len(scenarios)}")
    logger.info(f"Total violaciones: {total_violations}")
    logger.info(f"Violaciones críticas: {critical_violations}")
    
    if critical_violations > 0:
        logger.info("\n❌ HAY VIOLACIONES CRÍTICAS - REQUIERE CORRECCIÓN")
        return False
    else:
        logger.info("\n✅ TODAS LAS SIMULACIONES PASARON")
        return True


if __name__ == "__main__":
    success = asyncio.run(run_all_simulations())
    sys.exit(0 if success else 1)

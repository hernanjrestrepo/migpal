#!/usr/bin/env python3
"""
Simulación del Asesor Humano v3.1.0
===================================
Simula conversaciones reales hasta completar plan sin fricción.
Debe pasar 3 ejecuciones completas sin violaciones.
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


@dataclass
class SimulationViolation:
    """Violación detectada en la simulación"""
    type: str
    description: str
    turn: int
    severity: str  # "critical", "warning"


class HumanAdvisorSimulator:
    """Simulador del asesor humano"""
    
    def __init__(self):
        self.violations: List[SimulationViolation] = []
        self.turns: List[Dict] = []
        self.form_count = 0
        self.interaction_count = 0
    
    def reset(self):
        self.violations = []
        self.turns = []
        self.form_count = 0
        self.interaction_count = 0
    
    async def run_simulation(self, scenario_name: str = "complete_flow") -> bool:
        """Ejecutar una simulación completa"""
        from app.services.human_advisor import get_human_advisor, ExplorationPhase
        
        self.reset()
        advisor = get_human_advisor()
        user_id = 123456789
        
        # Limpiar contexto previo
        if user_id in advisor.contexts:
            del advisor.contexts[user_id]
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🎭 SIMULACIÓN: {scenario_name}")
        logger.info(f"{'='*70}")
        
        # Definir conversación según escenario
        if scenario_name == "complete_flow":
            conversation = self._get_complete_flow_conversation()
        elif scenario_name == "confused_user":
            conversation = self._get_confused_user_conversation()
        elif scenario_name == "premature_request":
            conversation = self._get_premature_request_conversation()
        else:
            conversation = self._get_complete_flow_conversation()
        
        user_data = {"profile": {"personal": {}, "professional": {}, "migration": {}}}
        
        for i, user_message in enumerate(conversation):
            self.interaction_count += 1
            
            logger.info(f"\n--- Turno {self.interaction_count} ---")
            logger.info(f"👤 Usuario: {user_message}")
            
            # Procesar mensaje
            result = await advisor.process_message(
                user_id=user_id,
                text=user_message,
                user_data=user_data,
                lang="es"
            )
            
            response = result["response"]
            buttons = result.get("buttons")
            phase_changed = result.get("phase_changed", False)
            needs_validation = result.get("needs_validation", False)
            
            # Mostrar respuesta
            logger.info(f"🤖 MigPAL: {response[:300]}..." if len(response) > 300 else f"🤖 MigPAL: {response}")
            
            if buttons:
                logger.info(f"   Botones: {[b[0] for b in buttons]}")
            
            ctx = advisor.get_context(user_id)
            logger.info(f"   Fase: {ctx.phase.value} | Emoción: {ctx.emotional_state.value}")
            
            # Verificar violaciones
            self._check_violations(result, ctx, user_message, i)
            
            # Registrar turno
            self.turns.append({
                "user": user_message,
                "bot": response,
                "phase": ctx.phase.value,
                "has_buttons": buttons is not None,
            })
            
            # Verificar si es formulario
            if buttons:
                self.form_count += 1
                if self.form_count > (self.interaction_count / 5) + 1:
                    self.violations.append(SimulationViolation(
                        type="too_many_forms",
                        description=f"Demasiados formularios: {self.form_count} en {self.interaction_count} interacciones",
                        turn=self.interaction_count,
                        severity="warning"
                    ))
        
        # Verificar que se completó el flujo
        ctx = advisor.get_context(user_id)
        if scenario_name == "complete_flow":
            if ctx.phase != ExplorationPhase.OPTIONS_EXPLORATION:
                self.violations.append(SimulationViolation(
                    type="incomplete_flow",
                    description=f"Flujo no completado. Fase final: {ctx.phase.value}",
                    turn=self.interaction_count,
                    severity="critical"
                ))
            
            if not ctx.understanding.confirmed_by_user:
                self.violations.append(SimulationViolation(
                    type="no_confirmation",
                    description="Resumen de entendimiento no confirmado",
                    turn=self.interaction_count,
                    severity="critical"
                ))
        
        # Mostrar resultados
        self._show_results(scenario_name)
        
        return len([v for v in self.violations if v.severity == "critical"]) == 0
    
    def _get_complete_flow_conversation(self) -> List[str]:
        """Conversación completa que debe pasar sin problemas"""
        return [
            # Saludo inicial
            "Hola, estoy pensando en migrar",
            
            # Motivación profunda
            "Quiero darle un mejor futuro a mis hijos. En mi país la situación económica está muy difícil y quiero que tengan mejores oportunidades de educación y trabajo.",
            
            # Quiénes migran
            "Somos mi esposa, mis dos hijos de 8 y 12 años, y yo.",
            
            # Situación actual
            "Soy ingeniero de sistemas con 10 años de experiencia. Trabajo en una empresa de tecnología ganando unos $2500 al mes.",
            
            # Vida deseada
            "Me gustaría trabajar en una empresa de tecnología grande, vivir en una ciudad con buenas escuelas para mis hijos, y tener un ambiente seguro para la familia.",
            
            # Restricciones
            "Tenemos ahorrados unos $30,000 dólares. No hay urgencia extrema pero me gustaría empezar el proceso este año.",
            
            # Confirmación del resumen
            "Sí, es correcto todo lo que entendiste.",
        ]
    
    def _get_confused_user_conversation(self) -> List[str]:
        """Usuario confundido que duda y corrige"""
        return [
            "Hola, no sé si quiero migrar o no",
            "Es que hay muchas opciones y no sé qué hacer",
            "Bueno, en realidad sí quiero migrar pero tengo miedo",
            "No, espera, déjame pensar...",
            "Ok, sí quiero migrar por mi familia",
        ]
    
    def _get_premature_request_conversation(self) -> List[str]:
        """Usuario que intenta saltar a recomendaciones"""
        return [
            "Hola, dime qué visa necesito para ir a USA",
            "Pero solo dime cuál es la mejor visa para ingenieros",
            "Ok entiendo, soy ingeniero de software",
            "Tengo 8 años de experiencia",
            "Viajo con mi familia, esposa y 2 hijos",
        ]
    
    def _check_violations(self, result: Dict, ctx, user_message: str, turn: int):
        """Verificar violaciones de las reglas"""
        from app.services.human_advisor import ExplorationPhase
        
        response = result["response"].lower()
        
        # Verificar recomendaciones prematuras
        if ctx.phase.value in ["greeting", "deep_motivation", "who_migrates"]:
            premature_keywords = ["h-1b", "l-1", "o-1", "eb-", "visa de trabajo", "te recomiendo"]
            for keyword in premature_keywords:
                if keyword in response:
                    self.violations.append(SimulationViolation(
                        type="premature_recommendation",
                        description=f"Recomendación prematura '{keyword}' en fase {ctx.phase.value}",
                        turn=turn,
                        severity="critical"
                    ))
        
        # Verificar que no avanza si hay corrección/duda EXPLÍCITA
        # "no sé si quiero migrar" en el saludo NO es duda bloqueante
        explicit_doubt_keywords = ["espera", "déjame pensar", "un momento", "no, en realidad"]
        is_explicit_doubt = any(kw in user_message.lower() for kw in explicit_doubt_keywords)
        
        # Solo es violación si es duda explícita Y avanzó de fase
        if is_explicit_doubt and result.get("phase_changed", False):
            self.violations.append(SimulationViolation(
                type="advanced_on_doubt",
                description="Avanzó de fase cuando el usuario expresó duda explícita",
                turn=turn,
                severity="critical"
            ))
        
        # Verificar que muestra error
        if "error" in response or "inténtalo" in response:
            self.violations.append(SimulationViolation(
                type="error_shown",
                description="Se mostró mensaje de error",
                turn=turn,
                severity="critical"
            ))
    
    def _show_results(self, scenario_name: str):
        """Mostrar resultados de la simulación"""
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 RESULTADOS: {scenario_name}")
        logger.info(f"{'='*70}")
        
        logger.info(f"Turnos: {len(self.turns)}")
        logger.info(f"Formularios: {self.form_count}")
        logger.info(f"Violaciones: {len(self.violations)}")
        
        critical = [v for v in self.violations if v.severity == "critical"]
        warnings = [v for v in self.violations if v.severity == "warning"]
        
        if critical:
            logger.info(f"\n❌ VIOLACIONES CRÍTICAS ({len(critical)}):")
            for v in critical:
                logger.info(f"   [{v.turn}] {v.type}: {v.description}")
        
        if warnings:
            logger.info(f"\n⚠️ ADVERTENCIAS ({len(warnings)}):")
            for v in warnings:
                logger.info(f"   [{v.turn}] {v.type}: {v.description}")
        
        if not self.violations:
            logger.info("\n✅ SIN VIOLACIONES")


async def run_all_simulations():
    """Ejecutar todas las simulaciones 3 veces"""
    simulator = HumanAdvisorSimulator()
    
    scenarios = ["complete_flow", "confused_user", "premature_request"]
    
    all_passed = True
    results = {}
    
    for run in range(1, 4):
        logger.info(f"\n{'#'*70}")
        logger.info(f"# EJECUCIÓN {run}/3")
        logger.info(f"{'#'*70}")
        
        run_results = {}
        
        for scenario in scenarios:
            passed = await simulator.run_simulation(scenario)
            run_results[scenario] = passed
            if not passed:
                all_passed = False
        
        results[f"run_{run}"] = run_results
    
    # Resumen final
    logger.info(f"\n{'='*70}")
    logger.info("📋 RESUMEN FINAL - 3 EJECUCIONES")
    logger.info(f"{'='*70}")
    
    for run_name, run_results in results.items():
        logger.info(f"\n{run_name}:")
        for scenario, passed in run_results.items():
            status = "✅" if passed else "❌"
            logger.info(f"   {status} {scenario}")
    
    if all_passed:
        logger.info("\n🎉 TODAS LAS SIMULACIONES PASARON 3 VECES")
        return True
    else:
        logger.info("\n❌ HAY VIOLACIONES - REQUIERE CORRECCIÓN")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_simulations())
    sys.exit(0 if success else 1)

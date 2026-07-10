#!/usr/bin/env python3
"""
MigPAL Real Conversation Simulator v1.0
=======================================
Simula conversaciones humanas reales para probar el flujo completo de MigPAL.

Este script simula inputs humanos reales incluyendo:
- Saludos confusos ("ajá que pasa?")
- Preguntas ("qué es una visa O-1?")
- Frustración ("ya te dije mi nombre")
- Información parcial ("soy ingeniero")
- Correcciones ("no, mi nombre es Juan, no Pedro")
- Respuestas fuera de contexto
- Emojis y texto informal

Uso:
    python simulate_real_conversation.py [--user-id USER_ID] [--verbose]
"""

import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Agregar el path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.case_storage import delete_user_data, save_user_data
from app.services.conversational_ai import ConversationalAI
from app.services.flow_governor import InputInterpreter, interpret_user_input
from app.services.profile_validator import PriorityIntentHandler, get_profile_based_intro

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SimulatedMessage:
    """Representa un mensaje simulado del usuario"""

    text: str
    expected_intent: str | None = None
    expected_response_contains: list[str] = field(default_factory=list)
    should_not_contain: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ConversationScenario:
    """Escenario de conversación completo"""

    name: str
    description: str
    messages: list[SimulatedMessage]
    expected_final_state: str = ""
    expected_profile_fields: dict[str, Any] = field(default_factory=dict)


# ============== ESCENARIOS DE PRUEBA ==============

SCENARIOS = [
    ConversationScenario(
        name="confused_user",
        description="Usuario confundido que no entiende qué es MigPAL",
        messages=[
            SimulatedMessage(
                text="ajá que pasa?",
                expected_intent="confusion",
                expected_response_contains=["entiendo", "confuso", "explicar"],
                should_not_contain=["basado en tu perfil"],
                description="Saludo confuso - NO debe guardarse como nombre",
            ),
            SimulatedMessage(
                text="qué es esto?",
                expected_intent="question",
                expected_response_contains=["MigPAL", "ayudar", "migración"],
                description="Pregunta sobre el servicio",
            ),
            SimulatedMessage(
                text="no entiendo nada",
                expected_intent="confusion",
                expected_response_contains=["explicar", "claro"],
                description="Expresión de confusión",
            ),
        ],
    ),
    ConversationScenario(
        name="frustrated_user",
        description="Usuario frustrado que repite información",
        messages=[
            SimulatedMessage(
                text="ya te dije que me llamo Juan",
                expected_intent="frustration",
                expected_response_contains=["perdona", "claro", "Juan"],
                description="Frustración por repetir nombre",
            ),
            SimulatedMessage(
                text="otra vez lo mismo?",
                expected_intent="frustration",
                expected_response_contains=["ayudar", "mejor"],
                description="Frustración por repetición",
            ),
        ],
    ),
    ConversationScenario(
        name="question_asker",
        description="Usuario que hace muchas preguntas",
        messages=[
            SimulatedMessage(
                text="qué es una visa O-1?",
                expected_intent="question",
                expected_response_contains=["O-1", "visa", "habilidades"],
                description="Pregunta sobre visa O-1",
            ),
            SimulatedMessage(
                text="cuánto cuesta el proceso?",
                expected_intent="question",
                expected_response_contains=["costo", "precio", "$"],
                description="Pregunta sobre costos",
            ),
            SimulatedMessage(
                text="es seguro usar MigPAL?",
                expected_intent="concern",
                expected_response_contains=["seguro", "confiable"],
                description="Preocupación sobre seguridad",
            ),
        ],
    ),
    ConversationScenario(
        name="normal_flow",
        description="Usuario que sigue el flujo normal",
        messages=[
            SimulatedMessage(
                text="Hola, quiero migrar a USA",
                expected_intent="greeting",
                expected_response_contains=["hola", "ayudar"],
                description="Saludo normal",
            ),
            SimulatedMessage(
                text="Me llamo Carlos Pérez",
                expected_intent="providing_info",
                expected_response_contains=["Carlos", "gusto"],
                description="Proporciona nombre",
            ),
            SimulatedMessage(
                text="Soy ingeniero de software con 10 años de experiencia",
                expected_intent="providing_info",
                expected_response_contains=["ingeniero", "experiencia"],
                description="Proporciona profesión",
            ),
        ],
        expected_profile_fields={"name": "Carlos Pérez", "profession": "ingeniero"},
    ),
    ConversationScenario(
        name="correction_flow",
        description="Usuario que corrige información",
        messages=[
            SimulatedMessage(
                text="Me llamo Pedro",
                expected_intent="providing_info",
                description="Proporciona nombre inicial",
            ),
            SimulatedMessage(
                text="Perdón, me equivoqué. Mi nombre es Pablo, no Pedro",
                expected_intent="correction",
                expected_response_contains=["actualizo", "Pablo"],
                description="Corrige nombre",
            ),
        ],
    ),
    ConversationScenario(
        name="profile_not_confirmed",
        description="Verificar que no se use 'basado en tu perfil' sin confirmación",
        messages=[
            SimulatedMessage(
                text="Hola",
                expected_intent="greeting",
                should_not_contain=["basado en tu perfil"],
                description="Saludo - no debe asumir perfil",
            ),
            SimulatedMessage(
                text="qué visa me recomiendas?",
                expected_intent="question",
                should_not_contain=["basado en tu perfil"],
                expected_response_contains=["cuéntame", "conocer", "información"],
                description="Pregunta de visa sin perfil - debe pedir más info",
            ),
        ],
    ),
]


class ConversationSimulator:
    """Simulador de conversaciones"""

    def __init__(self, user_id: int = 9999999999):
        self.user_id = user_id
        self.priority_handler = PriorityIntentHandler()
        self.input_interpreter = InputInterpreter()
        self.conversational_ai = ConversationalAI()
        self.results: list[dict[str, Any]] = []

    def reset_user(self):
        """Resetea el usuario de prueba"""
        try:
            delete_user_data(self.user_id)
        except:
            pass

        # Crear perfil limpio
        user_data = {
            "user_id": self.user_id,
            "state": "start",
            "language": "es",
            "profile": {
                "personal": {"telegram_name": "TestUser"},
                "education": {},
                "work": {},
                "languages": {},
                "history": {},
                "financial": {},
                "migration": {},
            },
            "family_members": [],
            "current_family_index": 0,
            "preferences": {},
            "selected_route": {},
            "documents": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        save_user_data(self.user_id, user_data)
        return user_data

    def analyze_message(self, text: str, user_data: dict[str, Any]) -> dict[str, Any]:
        """Analiza un mensaje y retorna el análisis"""
        state = user_data.get("state", "start")
        lang = user_data.get("language", "es")

        # 1. Detectar intent prioritario
        should_interrupt, intent_type, empathic_response = self.priority_handler.should_interrupt_flow(text)

        # 2. Interpretar input
        interpreted = interpret_user_input(text, state)

        # 3. Detectar intent conversacional
        conv_intent = self.conversational_ai.detect_intent(text)

        # 4. Verificar si se puede usar "basado en tu perfil"
        profile_intro = get_profile_based_intro(self.user_id, user_data, lang)

        return {
            "text": text,
            "priority_intent": {
                "should_interrupt": should_interrupt,
                "type": intent_type,
                "empathic_response": empathic_response,
            },
            "interpreted": {
                "type": interpreted.input_type.value,
                "confidence": interpreted.confidence,
                "extracted_data": interpreted.extracted_data,
                "should_advance": interpreted.should_advance,
            },
            "conversational_intent": conv_intent.value,
            "profile_intro": profile_intro,
            "can_use_profile_based": "basado en" in profile_intro.lower(),
        }

    def run_scenario(self, scenario: ConversationScenario, verbose: bool = False) -> dict[str, Any]:
        """Ejecuta un escenario de conversación"""
        print(f"\n{'='*60}")
        print(f"ESCENARIO: {scenario.name}")
        print(f"Descripción: {scenario.description}")
        print(f"{'='*60}")

        # Resetear usuario
        user_data = self.reset_user()

        results = {"scenario": scenario.name, "passed": True, "messages": [], "errors": []}

        for i, msg in enumerate(scenario.messages):
            print(f"\n--- Mensaje {i+1}: {msg.description} ---")
            print(f"Usuario: {msg.text}")

            # Analizar mensaje
            analysis = self.analyze_message(msg.text, user_data)

            if verbose:
                print(f"Análisis: {json.dumps(analysis, indent=2, ensure_ascii=False)}")

            msg_result = {"text": msg.text, "analysis": analysis, "checks": []}

            # Verificar intent esperado
            if msg.expected_intent:
                detected_intent = analysis["priority_intent"]["type"] or analysis["conversational_intent"]
                if msg.expected_intent.lower() in str(detected_intent).lower():
                    msg_result["checks"].append(
                        {
                            "check": "expected_intent",
                            "passed": True,
                            "expected": msg.expected_intent,
                            "actual": detected_intent,
                        }
                    )
                    print(f"✅ Intent correcto: {detected_intent}")
                else:
                    msg_result["checks"].append(
                        {
                            "check": "expected_intent",
                            "passed": False,
                            "expected": msg.expected_intent,
                            "actual": detected_intent,
                        }
                    )
                    results["passed"] = False
                    results["errors"].append(
                        f"Intent incorrecto en mensaje {i+1}: esperado {msg.expected_intent}, obtenido {detected_intent}"
                    )
                    print(f"❌ Intent incorrecto: esperado {msg.expected_intent}, obtenido {detected_intent}")

            # Verificar que NO contenga ciertas frases
            if msg.should_not_contain:
                for phrase in msg.should_not_contain:
                    if phrase.lower() in analysis["profile_intro"].lower():
                        msg_result["checks"].append(
                            {"check": "should_not_contain", "passed": False, "phrase": phrase}
                        )
                        results["passed"] = False
                        results["errors"].append(f"Mensaje {i+1} contiene frase prohibida: '{phrase}'")
                        print(f"❌ Contiene frase prohibida: '{phrase}'")
                    else:
                        msg_result["checks"].append(
                            {"check": "should_not_contain", "passed": True, "phrase": phrase}
                        )
                        print(f"✅ No contiene: '{phrase}'")

            # Verificar respuesta empática si hay intent prioritario
            if analysis["priority_intent"]["should_interrupt"]:
                if analysis["priority_intent"]["empathic_response"]:
                    print(f"🤖 Respuesta empática: {analysis['priority_intent']['empathic_response']}")
                else:
                    print("⚠️ Sin respuesta empática para intent prioritario")

            results["messages"].append(msg_result)

            # Actualizar user_data con datos extraídos
            if analysis["interpreted"]["extracted_data"]:
                for field, value in analysis["interpreted"]["extracted_data"].items():
                    if field == "name":
                        user_data["profile"]["personal"]["name"] = value
                    elif field == "profession":
                        user_data["profile"]["work"]["profession"] = value
                save_user_data(self.user_id, user_data)

        # Resumen del escenario
        if results["passed"]:
            print(f"\n✅ ESCENARIO PASÓ: {scenario.name}")
        else:
            print(f"\n❌ ESCENARIO FALLÓ: {scenario.name}")
            for error in results["errors"]:
                print(f"   - {error}")

        return results

    def run_all_scenarios(self, verbose: bool = False) -> dict[str, Any]:
        """Ejecuta todos los escenarios"""
        print("\n" + "=" * 70)
        print("SIMULACIÓN DE CONVERSACIONES REALES - MigPAL v3.2.0")
        print("=" * 70)

        all_results = {
            "timestamp": datetime.now().isoformat(),
            "total_scenarios": len(SCENARIOS),
            "passed": 0,
            "failed": 0,
            "scenarios": [],
        }

        for scenario in SCENARIOS:
            result = self.run_scenario(scenario, verbose)
            all_results["scenarios"].append(result)
            if result["passed"]:
                all_results["passed"] += 1
            else:
                all_results["failed"] += 1

        # Resumen final
        print("\n" + "=" * 70)
        print("RESUMEN FINAL")
        print("=" * 70)
        print(f"Total escenarios: {all_results['total_scenarios']}")
        print(f"Pasaron: {all_results['passed']} ✅")
        print(f"Fallaron: {all_results['failed']} ❌")
        print(f"Tasa de éxito: {all_results['passed']/all_results['total_scenarios']*100:.1f}%")

        if all_results["failed"] > 0:
            print("\nEscenarios fallidos:")
            for scenario in all_results["scenarios"]:
                if not scenario["passed"]:
                    print(f"  - {scenario['scenario']}")
                    for error in scenario["errors"]:
                        print(f"    • {error}")

        return all_results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Simulador de conversaciones MigPAL")
    parser.add_argument("--user-id", type=int, default=9999999999, help="ID de usuario para pruebas")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar análisis detallado")
    parser.add_argument("--scenario", "-s", type=str, help="Ejecutar solo un escenario específico")

    args = parser.parse_args()

    simulator = ConversationSimulator(user_id=args.user_id)

    if args.scenario:
        # Buscar escenario específico
        scenario = next((s for s in SCENARIOS if s.name == args.scenario), None)
        if scenario:
            result = simulator.run_scenario(scenario, args.verbose)
            sys.exit(0 if result["passed"] else 1)
        else:
            print(f"Escenario no encontrado: {args.scenario}")
            print(f"Escenarios disponibles: {[s.name for s in SCENARIOS]}")
            sys.exit(1)
    else:
        results = simulator.run_all_scenarios(args.verbose)
        sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()

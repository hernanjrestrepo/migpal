#!/usr/bin/env python3
"""
SEGMENTO 1/4: Simulación de 30 conversaciones tipo humano
Incluye: typos, correcciones, off-topic, botones, silencio
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Simulación de conversaciones tipo humano
HUMAN_CONVERSATIONS = [
    # 1. Typos comunes
    {"type": "typo", "inputs": ["hla", "qiero migrar", "tengo 30 anios", "soi de colombia"]},
    # 2. Correcciones
    {
        "type": "correction",
        "inputs": ["me llamo Juan", "no, perdón, me llamo Pedro", "mi nombre es Pedro García"],
    },
    # 3. Off-topic
    {
        "type": "off_topic",
        "inputs": ["¿qué hora es?", "cuéntame un chiste", "¿cuál es tu película favorita?"],
    },
    # 4. Respuestas muy cortas
    {"type": "short", "inputs": ["si", "no", "ok", "ya", "mm"]},
    # 5. Respuestas muy largas
    {
        "type": "long",
        "inputs": [
            "Bueno mira, te cuento que yo soy ingeniero de sistemas con más de 15 años de experiencia trabajando en empresas multinacionales, tengo una maestría en administración de empresas y actualmente gano alrededor de 8000 dólares mensuales, estoy casado y tengo 2 hijos de 5 y 8 años, mi esposa es médica y queremos migrar porque la situación económica en nuestro país está muy difícil"
        ],
    },
    # 6. Preguntas antes de responder
    {
        "type": "question_first",
        "inputs": [
            "¿para qué necesitas mi nombre?",
            "¿es seguro dar mis datos?",
            "¿quién va a ver esta información?",
        ],
    },
    # 7. Frustración
    {
        "type": "frustration",
        "inputs": [
            "ya te dije mi nombre",
            "no entiendo qué quieres",
            "esto es muy confuso",
            "otra vez lo mismo?",
        ],
    },
    # 8. Cambio de idioma
    {"type": "language_switch", "inputs": ["I want to migrate", "quiero ir a USA", "how much does it cost?"]},
    # 9. Emojis y símbolos
    {
        "type": "emoji",
        "inputs": ["👋 hola!", "🇨🇴 soy de Colombia", "💰 tengo $50,000", "✈️ quiero viajar pronto"],
    },
    # 10. Números en diferentes formatos
    {"type": "numbers", "inputs": ["tengo 50000 dolares", "tengo $50,000", "tengo cincuenta mil", "50k USD"]},
    # 11. Fechas en diferentes formatos
    {
        "type": "dates",
        "inputs": ["nací el 15/03/1990", "nací en marzo de 1990", "tengo 34 años", "1990-03-15"],
    },
    # 12. Información parcial
    {"type": "partial", "inputs": ["Juan", "Colombia", "ingeniero"]},
    # 13. Información con contexto
    {
        "type": "context",
        "inputs": [
            "mi nombre completo es Juan Carlos Pérez García",
            "vivo en Bogotá, Colombia desde hace 10 años",
        ],
    },
    # 14. Negaciones
    {
        "type": "negation",
        "inputs": ["no tengo hijos", "no estoy casado", "no tengo visa", "nunca he viajado a USA"],
    },
    # 15. Confirmaciones ambiguas
    {"type": "ambiguous", "inputs": ["creo que sí", "tal vez", "no estoy seguro", "puede ser"]},
    # 16. Múltiples datos en un mensaje
    {"type": "multiple", "inputs": ["Soy Juan, tengo 35 años, soy de México y trabajo como abogado"]},
    # 17. Preguntas sobre el proceso
    {
        "type": "process_questions",
        "inputs": ["¿cuánto cuesta?", "¿cuánto tiempo toma?", "¿qué documentos necesito?"],
    },
    # 18. Expresiones coloquiales
    {"type": "colloquial", "inputs": ["pues sí", "órale", "chévere", "bacano", "dale"]},
    # 19. Mensajes vacíos o solo espacios
    {"type": "empty", "inputs": ["   ", ".", "..."]},
    # 20. Caracteres especiales
    {"type": "special_chars", "inputs": ["Juan O'Brien", "María José", "São Paulo", "Müller"]},
    # 21. URLs y emails
    {"type": "urls", "inputs": ["mi email es juan@gmail.com", "mi linkedin es linkedin.com/in/juan"]},
    # 22. Teléfonos
    {"type": "phones", "inputs": ["+57 300 123 4567", "3001234567", "(300) 123-4567"]},
    # 23. Montos con diferentes monedas
    {
        "type": "currencies",
        "inputs": ["tengo 200 millones de pesos", "gano 5000 euros", "ahorro $3000 al mes"],
    },
    # 24. Profesiones complejas
    {
        "type": "professions",
        "inputs": [
            "soy ingeniero de software senior",
            "trabajo como gerente de proyectos IT",
            "soy médico especialista en cardiología",
        ],
    },
    # 25. Situaciones familiares complejas
    {
        "type": "family",
        "inputs": [
            "viajo con mi esposa y 3 hijos",
            "somos 5: yo, mi esposa, 2 hijos y mi mamá",
            "viajo solo pero mi familia viene después",
        ],
    },
    # 26. Urgencia
    {
        "type": "urgency",
        "inputs": ["necesito irme ya", "es urgente", "tengo que salir este mes", "no puedo esperar"],
    },
    # 27. Dudas sobre visas
    {
        "type": "visa_questions",
        "inputs": [
            "¿qué visa me conviene?",
            "¿puedo trabajar con visa de turista?",
            "¿cuánto dura la visa H1B?",
        ],
    },
    # 28. Comparaciones
    {
        "type": "comparisons",
        "inputs": [
            "¿es mejor Miami o Houston?",
            "¿qué diferencia hay entre H1B y L1?",
            "¿conviene más estudiar o trabajar?",
        ],
    },
    # 29. Silencio (timeout)
    {"type": "silence", "inputs": []},
    # 30. Secuencia completa realista
    {
        "type": "realistic",
        "inputs": [
            "hola",
            "quiero migrar a estados unidos",
            "me llamo Carlos",
            "soy de Venezuela",
            "tengo 32 años",
            "soy ingeniero",
            "no, perdón, soy arquitecto",
            "viajo con mi esposa y un hijo de 5 años",
            "tenemos como 30 mil dólares ahorrados",
            "¿cuánto cuesta el proceso?",
            "ok, gracias",
        ],
    },
]


class ConversationSimulator:
    """Simula conversaciones y detecta problemas"""

    def __init__(self):
        self.results = []
        self.bugs_found = []

    async def simulate_input(self, text: str, user_id: int = 12345) -> dict[str, Any]:
        """Simula un input del usuario y verifica la respuesta"""
        result = {"input": text, "responded": False, "response_time": 0, "error": None, "response": None}

        try:
            # Importar módulos necesarios
            from app.services.availability_watchdog import get_empathic_fallback
            from app.services.flow_governor import InputType, interpret_user_input
            from app.services.memory_profiler import detect_correction

            start_time = datetime.now()

            # 1. Interpretar input
            interpreted = interpret_user_input(text, "")
            result["interpreted_type"] = interpreted.input_type.value
            result["interpreted_confidence"] = interpreted.confidence
            result["extracted_data"] = interpreted.extracted_data

            # 2. Detectar corrección
            is_correction, corrected_field = detect_correction(text)
            result["is_correction"] = is_correction
            result["corrected_field"] = corrected_field

            # 3. Verificar que hay respuesta
            if interpreted.input_type != InputType.UNKNOWN or interpreted.extracted_data:
                result["responded"] = True

            # 4. Obtener fallback si es necesario
            if not result["responded"]:
                fallback = get_empathic_fallback()
                result["response"] = fallback.get_phase_fallback("unknown", "es")
                result["responded"] = True

            result["response_time"] = (datetime.now() - start_time).total_seconds()

        except Exception as e:
            result["error"] = str(e)
            result["responded"] = False
            self.bugs_found.append({"input": text, "error": str(e), "type": "exception"})

        return result

    async def run_conversation(self, conv: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta una conversación completa"""
        conv_result = {
            "type": conv["type"],
            "inputs": conv["inputs"],
            "results": [],
            "all_responded": True,
            "errors": [],
        }

        for text in conv["inputs"]:
            if text.strip():  # Ignorar inputs vacíos para silencio
                result = await self.simulate_input(text)
                conv_result["results"].append(result)

                if not result["responded"]:
                    conv_result["all_responded"] = False

                if result["error"]:
                    conv_result["errors"].append(result["error"])

        return conv_result

    async def run_all_simulations(self) -> list[dict[str, Any]]:
        """Ejecuta todas las 30 simulaciones"""
        results = []

        for i, conv in enumerate(HUMAN_CONVERSATIONS, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"CONVERSACIÓN {i}/30: {conv['type'].upper()}")
            logger.info(f"{'='*60}")

            result = await self.run_conversation(conv)
            results.append(result)

            # Mostrar resultados
            for r in result["results"]:
                status = "✅" if r["responded"] else "❌"
                logger.info(f"{status} Input: '{r['input'][:50]}...' -> {r.get('interpreted_type', 'N/A')}")
                if r["error"]:
                    logger.info(f"   ⚠️ Error: {r['error']}")
                if r.get("extracted_data"):
                    logger.info(f"   📝 Datos: {r['extracted_data']}")

        return results


def analyze_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Analiza los resultados y genera reporte de bugs"""
    analysis = {
        "total_conversations": len(results),
        "total_inputs": 0,
        "responded": 0,
        "not_responded": 0,
        "errors": [],
        "bugs": [],
    }

    for conv in results:
        for r in conv["results"]:
            analysis["total_inputs"] += 1
            if r["responded"]:
                analysis["responded"] += 1
            else:
                analysis["not_responded"] += 1
                analysis["bugs"].append(
                    {
                        "type": conv["type"],
                        "input": r["input"],
                        "error": r.get("error"),
                        "cause": "No response generated",
                    }
                )

            if r.get("error"):
                analysis["errors"].append({"type": conv["type"], "input": r["input"], "error": r["error"]})

    return analysis


async def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("SEGMENTO 1/4: SIMULACIÓN DE 30 CONVERSACIONES")
    logger.info("=" * 60)

    simulator = ConversationSimulator()
    results = await simulator.run_all_simulations()

    # Analizar resultados
    analysis = analyze_results(results)

    # Mostrar resumen
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMEN DE SIMULACIÓN")
    logger.info("=" * 60)
    logger.info(f"Total conversaciones: {analysis['total_conversations']}")
    logger.info(f"Total inputs: {analysis['total_inputs']}")
    logger.info(f"✅ Respondidos: {analysis['responded']}")
    logger.info(f"❌ Sin respuesta: {analysis['not_responded']}")
    logger.info(f"⚠️ Errores: {len(analysis['errors'])}")

    # Mostrar bugs encontrados
    if analysis["bugs"]:
        logger.info("\n" + "=" * 60)
        logger.info("🐛 BUGS ENCONTRADOS")
        logger.info("=" * 60)
        for bug in analysis["bugs"]:
            logger.info(f"- Tipo: {bug['type']}")
            logger.info(f"  Input: {bug['input']}")
            logger.info(f"  Causa: {bug['cause']}")
            if bug.get("error"):
                logger.info(f"  Error: {bug['error']}")
            logger.info("")

    # Tasa de respuesta
    response_rate = (
        (analysis["responded"] / analysis["total_inputs"] * 100) if analysis["total_inputs"] > 0 else 0
    )
    logger.info(f"\n📈 TASA DE RESPUESTA: {response_rate:.1f}%")

    if response_rate < 100:
        logger.info("⚠️ ALERTA: El bot no responde al 100% de los inputs")
    else:
        logger.info("✅ El bot responde a todos los inputs")

    return analysis


if __name__ == "__main__":
    asyncio.run(main())

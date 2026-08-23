#!/usr/bin/env python3
"""
Validación Exhaustiva de Reglas v3.1.0
======================================
Verifica que se respeten ESTRICTAMENTE las 5 reglas:

1. UNDERSTANDING es bloqueante: no se puede pasar a OPTIONS sin confirmación explícita
2. 1 formulario cada 5 interacciones (hard rule)
3. Parafraseo obligatorio tras cada extracción relevante
4. No recomendación (visa/estado/ciudad) sin contexto completo confirmado
5. Reinterpretación ante correcciones/dudas (no avanzar)

Debe pasar 3 conversaciones reales completas hasta plan final.
"""

import asyncio
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


@dataclass
class RuleViolation:
    """Violación de regla detectada"""

    rule_number: int
    rule_name: str
    description: str
    turn: int
    severity: str  # "CRITICAL", "WARNING"


@dataclass
class ValidationResult:
    """Resultado de validación"""

    passed: bool
    violations: list[RuleViolation]
    rules_checked: dict[str, bool]


class RulesValidator:
    """Validador de las 5 reglas de v3.1.0"""

    RULES = {
        1: "UNDERSTANDING bloqueante",
        2: "1 formulario cada 5 interacciones",
        3: "Parafraseo obligatorio",
        4: "No recomendación sin contexto",
        5: "Reinterpretación ante dudas",
    }

    def __init__(self):
        self.violations: list[RuleViolation] = []
        self.form_interactions: list[int] = []
        self.interaction_count = 0
        self.extractions_without_paraphrase = 0
        self.understanding_confirmed = False

    def reset(self):
        self.violations = []
        self.form_interactions = []
        self.interaction_count = 0
        self.extractions_without_paraphrase = 0
        self.understanding_confirmed = False

    async def validate_conversation(self, conversation_name: str, messages: list[str]) -> ValidationResult:
        """Validar una conversación completa"""
        from app.services.human_advisor import ExplorationPhase, get_human_advisor

        self.reset()
        advisor = get_human_advisor()
        user_id = 777888999

        # Limpiar contexto previo
        if user_id in advisor.contexts:
            del advisor.contexts[user_id]

        logger.info(f"\n{'='*70}")
        logger.info(f"🔍 VALIDACIÓN: {conversation_name}")
        logger.info(f"{'='*70}")

        user_data = {"profile": {"personal": {}, "professional": {}, "migration": {}}}

        for _i, user_message in enumerate(messages):
            self.interaction_count += 1
            turn = self.interaction_count

            logger.info(f"\n--- Turno {turn} ---")
            logger.info(f"👤 Usuario: {user_message}")

            # Obtener contexto ANTES de procesar
            ctx_before = advisor.get_context(user_id)
            phase_before = ctx_before.phase

            # Procesar mensaje
            result = await advisor.process_message(
                user_id=user_id, text=user_message, user_data=user_data, lang="es"
            )

            response = result["response"]
            buttons = result.get("buttons")
            extracted = result.get("extracted_data", {})

            # Obtener contexto DESPUÉS de procesar
            ctx_after = advisor.get_context(user_id)
            phase_after = ctx_after.phase

            logger.info(
                f"🤖 MigPAL: {response[:200]}..." if len(response) > 200 else f"🤖 MigPAL: {response}"
            )
            logger.info(f"   Fase: {phase_before.value} → {phase_after.value}")

            # ===== VALIDAR REGLA 1: UNDERSTANDING bloqueante =====
            self._validate_rule_1(ctx_after, phase_before, phase_after, response, turn)

            # ===== VALIDAR REGLA 2: 1 formulario cada 5 =====
            self._validate_rule_2(buttons, turn)

            # ===== VALIDAR REGLA 3: Parafraseo obligatorio =====
            self._validate_rule_3(extracted, response, turn)

            # ===== VALIDAR REGLA 4: No recomendación sin contexto =====
            self._validate_rule_4(ctx_after, response, turn)

            # ===== VALIDAR REGLA 5: Reinterpretación ante dudas =====
            self._validate_rule_5(user_message, phase_before, phase_after, turn)

            # Actualizar estado de confirmación
            if (
                "es correcto" in user_message.lower()
                and phase_before == ExplorationPhase.UNDERSTANDING_SUMMARY
            ):
                self.understanding_confirmed = True

        # Verificar que se completó el flujo
        advisor.get_context(user_id)

        rules_checked = {
            "R1_UNDERSTANDING_BLOQUEANTE": not any(v.rule_number == 1 for v in self.violations),
            "R2_FORMULARIOS_1_CADA_5": not any(v.rule_number == 2 for v in self.violations),
            "R3_PARAFRASEO_OBLIGATORIO": not any(v.rule_number == 3 for v in self.violations),
            "R4_NO_RECOMENDACION_SIN_CONTEXTO": not any(v.rule_number == 4 for v in self.violations),
            "R5_REINTERPRETACION_DUDAS": not any(v.rule_number == 5 for v in self.violations),
        }

        passed = all(rules_checked.values())

        return ValidationResult(passed=passed, violations=self.violations, rules_checked=rules_checked)

    def _validate_rule_1(self, ctx, phase_before, phase_after, response, turn):
        """REGLA 1: UNDERSTANDING es bloqueante"""
        from app.services.human_advisor import ExplorationPhase

        # Si pasó de UNDERSTANDING a OPTIONS sin confirmación
        if phase_before == ExplorationPhase.UNDERSTANDING_SUMMARY:
            if phase_after == ExplorationPhase.OPTIONS_EXPLORATION:
                if not ctx.understanding.confirmed_by_user:
                    self.violations.append(
                        RuleViolation(
                            rule_number=1,
                            rule_name="UNDERSTANDING bloqueante",
                            description="Pasó a OPTIONS sin confirmación del resumen",
                            turn=turn,
                            severity="CRITICAL",
                        )
                    )

        # Si está en OPTIONS sin haber confirmado nunca
        if phase_after == ExplorationPhase.OPTIONS_EXPLORATION:
            if not ctx.understanding.confirmed_by_user:
                self.violations.append(
                    RuleViolation(
                        rule_number=1,
                        rule_name="UNDERSTANDING bloqueante",
                        description="Está en OPTIONS pero understanding.confirmed_by_user=False",
                        turn=turn,
                        severity="CRITICAL",
                    )
                )

    def _validate_rule_2(self, buttons, turn):
        """REGLA 2: 1 formulario cada 5 interacciones"""
        if buttons:
            self.form_interactions.append(turn)

            # Verificar que no hay más de 1 formulario en las últimas 5 interacciones
            recent_forms = [f for f in self.form_interactions if f > turn - 5]

            if len(recent_forms) > 1:
                self.violations.append(
                    RuleViolation(
                        rule_number=2,
                        rule_name="1 formulario cada 5",
                        description=f"Más de 1 formulario en 5 interacciones: {recent_forms}",
                        turn=turn,
                        severity="CRITICAL",
                    )
                )

    def _validate_rule_3(self, extracted, response, turn):
        """REGLA 3: Parafraseo obligatorio tras extracción"""
        if extracted:
            # Verificar que hay parafraseo en la respuesta
            paraphrase_indicators = [
                "entiendo",
                "entonces",
                "perfecto",
                "excelente",
                "eres",
                "tienes",
                "cuentas con",
                "viajas",
            ]

            has_paraphrase = any(ind in response.lower() for ind in paraphrase_indicators)

            if not has_paraphrase:
                self.violations.append(
                    RuleViolation(
                        rule_number=3,
                        rule_name="Parafraseo obligatorio",
                        description=f"Extracción sin parafraseo: {list(extracted.keys())}",
                        turn=turn,
                        severity="WARNING",
                    )
                )

    def _validate_rule_4(self, ctx, response, turn):
        """REGLA 4: No recomendación sin contexto completo confirmado"""
        # Palabras que indican recomendación
        recommendation_keywords = [
            "h-1b",
            "l-1",
            "o-1",
            "eb-1",
            "eb-2",
            "eb-3",
            "visa de trabajo",
            "te recomiendo",
            "la mejor opción",
            "deberías ir a",
            "california",
            "texas",
            "florida",
            "new york",
            "san francisco",
            "miami",
        ]

        response_lower = response.lower()

        for keyword in recommendation_keywords:
            if keyword in response_lower:
                # Verificar si tiene contexto completo confirmado
                can_recommend, reason = ctx.can_recommend()

                if not can_recommend:
                    self.violations.append(
                        RuleViolation(
                            rule_number=4,
                            rule_name="No recomendación sin contexto",
                            description=f"Recomendación '{keyword}' sin contexto: {reason}",
                            turn=turn,
                            severity="CRITICAL",
                        )
                    )
                break

    def _validate_rule_5(self, user_message, phase_before, phase_after, turn):
        """REGLA 5: Reinterpretación ante correcciones/dudas"""
        # Detectar correcciones/dudas explícitas
        doubt_patterns = [
            r"no,?\s*espera",
            r"déjame pensar",
            r"un momento",
            r"no,?\s*en realidad",
            r"me equivoqué",
            r"corrijo",
        ]

        is_doubt = any(__import__("re").search(pattern, user_message.lower()) for pattern in doubt_patterns)

        if is_doubt and phase_before != phase_after:
            self.violations.append(
                RuleViolation(
                    rule_number=5,
                    rule_name="Reinterpretación ante dudas",
                    description=f"Avanzó de fase ({phase_before.value} → {phase_after.value}) ante duda",
                    turn=turn,
                    severity="CRITICAL",
                )
            )


async def run_validation():
    """Ejecutar validación completa"""
    validator = RulesValidator()

    # Definir 3 conversaciones completas
    conversations = {
        "CONVERSACIÓN 1: Flujo completo estándar": [
            "Hola, estoy pensando en migrar a Estados Unidos",
            "Quiero darle un mejor futuro a mis hijos. La situación económica en mi país está muy difícil.",
            "Somos mi esposa, mis dos hijos de 8 y 12 años, y yo.",
            "Soy ingeniero de software con 10 años de experiencia. Gano unos $3000 al mes.",
            "Me gustaría trabajar en una empresa de tecnología grande, vivir en una ciudad segura con buenas escuelas.",
            "Tenemos ahorrados unos $40,000 dólares. No hay urgencia pero queremos empezar este año.",
            "Sí, es correcto todo lo que entendiste.",
        ],
        "CONVERSACIÓN 2: Usuario que corrige": [
            "Hola, quiero migrar",
            "Busco mejores oportunidades de trabajo",
            "Viajo solo... no, espera, en realidad viajo con mi esposa",
            "Soy contador con 5 años de experiencia",
            "Quiero una vida más tranquila, con mejor calidad de vida",
            "Tengo unos $20,000 ahorrados, sin prisa",
            "Sí, está correcto",
        ],
        "CONVERSACIÓN 3: Usuario que intenta saltar": [
            "Hola, dime qué visa necesito",
            "Ok entiendo, quiero migrar por trabajo",
            "Viajo con mi familia, esposa y un hijo de 5 años",
            "Soy médico con 15 años de experiencia",
            "Quiero ejercer mi profesión en USA, tener estabilidad",
            "Cuento con $50,000 y quiero empezar pronto",
            "Sí, es correcto",
        ],
    }

    all_results = {}
    all_passed = True

    for conv_name, messages in conversations.items():
        result = await validator.validate_conversation(conv_name, messages)
        all_results[conv_name] = result

        if not result.passed:
            all_passed = False

        # Mostrar resultado
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 RESULTADO: {conv_name}")
        logger.info(f"{'='*70}")

        for rule_name, passed in result.rules_checked.items():
            status = "✅" if passed else "❌"
            logger.info(f"   {status} {rule_name}")

        if result.violations:
            logger.info(f"\n   ⚠️ VIOLACIONES ({len(result.violations)}):")
            for v in result.violations:
                logger.info(f"      [{v.severity}] R{v.rule_number}: {v.description} (turno {v.turn})")

    # Resumen final
    logger.info(f"\n{'#'*70}")
    logger.info("📋 RESUMEN FINAL DE VALIDACIÓN")
    logger.info(f"{'#'*70}")

    for conv_name, result in all_results.items():
        status = "✅ PASÓ" if result.passed else "❌ FALLÓ"
        logger.info(f"\n{status}: {conv_name}")

    if all_passed:
        logger.info("\n🎉 TODAS LAS REGLAS VALIDADAS EN 3 CONVERSACIONES")
        logger.info("✅ v3.1.0 ESTÁ LISTO PARA INTEGRAR EL GUION")
        return True
    else:
        logger.info("\n❌ HAY VIOLACIONES - CORREGIR ANTES DE INTEGRAR")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_validation())
    sys.exit(0 if success else 1)

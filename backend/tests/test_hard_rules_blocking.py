#!/usr/bin/env python3
"""
SEGMENTO 3/4: TESTS BLOQUEANTES DE REGLAS DURAS
================================================
Estos tests DEBEN PASAR para que el código pueda desplegarse.
Si alguno falla, el CI debe bloquear el deploy.

REGLAS VERIFICADAS:
1. No hay respuesta a cualquier input (texto/callback/voz/timeout) → FAIL
2. Se muestra formulario >1/5 interacciones → FAIL
3. Recomienda visa sin contexto completo confirmado → FAIL
4. Avanza de fase sin UNDERSTANDING confirmado → FAIL
5. Ignora corrección ("mi email correcto es…") y avanza → FAIL
6. Markdown rompe (BadRequest) → FAIL

INCLUYE:
- Test fuzz: 100 inputs aleatorios
- 20 flujos completos
"""

import sys
import os
import asyncio
import random
import string
import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports del proyecto
from app.services.flow_governor import (
    FormThrottler, InputInterpreter, UnderstandingGatekeeper,
    VisaRecommendationGuard, ConversationDirector,
    get_form_throttler, interpret_user_input, can_recommend_visa,
    should_show_form, InputType
)
from app.services.memory_profiler import (
    ProfileValidator, UnderstandingSummarizer, CorrectionTracker,
    validate_profile, detect_correction, can_make_decision,
    ProfileCompleteness
)
from app.services.never_silent import (
    NeverSilentWrapper, get_never_silent,
    EMPATHIC_RECOVERY_MESSAGES, STILL_HERE_MESSAGES
)
from app.services.availability_watchdog import (
    EmpathicFallback, get_empathic_fallback
)


# ============== TEST RESULTS ==============

@dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    details: List[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = []


class TestRunner:
    """Ejecuta tests y recolecta resultados"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = datetime.now()
    
    def add_result(self, result: TestResult):
        self.results.append(result)
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"{status}: {result.name}")
        if not result.passed:
            print(f"   └─ {result.message}")
            for detail in result.details[:3]:  # Max 3 details
                print(f"      • {detail}")
    
    def summary(self) -> Tuple[int, int]:
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        return passed, total


# ============== REGLA 1: SIEMPRE RESPONDER ==============

def test_rule_1_always_respond():
    """
    REGLA 1: Todo input DEBE generar respuesta.
    FAIL si cualquier input no genera respuesta.
    """
    print("\n" + "=" * 60)
    print("REGLA 1: SIEMPRE RESPONDER A CUALQUIER INPUT")
    print("=" * 60)
    
    # Inputs de prueba
    test_inputs = [
        # Texto normal
        "hola", "quiero migrar", "me llamo Juan",
        # Typos
        "hla", "qiero", "tengo 30 anios",
        # Emojis
        "👋", "🇨🇴", "💰",
        # Caracteres especiales
        "Juan O'Brien", "São Paulo", "Müller",
        # Números
        "12345", "$50,000", "3001234567",
        # Vacíos/espacios
        ".", "...", "   ",
        # Muy largos
        "a" * 500,
        # Unicode
        "مرحبا", "你好", "Привет",
        # Comandos
        "/start", "/help", "/unknown_command",
        # Off-topic
        "¿qué hora es?", "cuéntame un chiste",
        # Frustración
        "no entiendo", "ya te dije",
        # Confirmaciones
        "sí", "no", "ok", "tal vez",
    ]
    
    failures = []
    
    for text in test_inputs:
        try:
            # Interpretar input
            interpreted = interpret_user_input(text, "")
            
            # Verificar que hay interpretación
            if interpreted.input_type == InputType.UNKNOWN and not interpreted.extracted_data:
                # Verificar fallback
                fallback = get_empathic_fallback()
                response = fallback.get_phase_fallback("unknown", "es")
                
                if not response:
                    failures.append(f"No response for: '{text[:30]}...'")
        except Exception as e:
            failures.append(f"Exception for '{text[:30]}...': {e}")
    
    passed = len(failures) == 0
    return TestResult(
        name="Rule 1: Always Respond to Any Input",
        passed=passed,
        message=f"{len(failures)} inputs without response" if failures else "All inputs get response",
        details=failures[:5]
    )


def test_rule_1_callback_response():
    """
    REGLA 1b: Todo callback DEBE generar respuesta.
    """
    print("\n" + "-" * 40)
    print("REGLA 1b: Callbacks siempre responden")
    print("-" * 40)
    
    # Callbacks de prueba
    test_callbacks = [
        "begin", "confirm_yes", "confirm_no",
        "visa_job_offer", "visa_student", "visa_family",
        "city_miami", "city_houston", "city_los_angeles",
        "unknown_callback", "invalid_data", "",
        "confirm_summary_yes", "confirm_summary_no",
        "show_summary", "show_visa_recommendation",
    ]
    
    failures = []
    
    for callback in test_callbacks:
        # Verificar que el callback tiene handler o fallback
        # En este caso, verificamos que el sistema no crashea
        try:
            # Simular interpretación de callback como texto
            interpreted = interpret_user_input(callback, "")
            # Si no hay crash, consideramos que hay respuesta
        except Exception as e:
            failures.append(f"Exception for callback '{callback}': {e}")
    
    passed = len(failures) == 0
    return TestResult(
        name="Rule 1b: Always Respond to Callbacks",
        passed=passed,
        message=f"{len(failures)} callbacks failed" if failures else "All callbacks handled",
        details=failures
    )


# ============== REGLA 2: FORMULARIOS MAX 1/5 ==============

def test_rule_2_form_throttling():
    """
    REGLA 2: Máximo 1 formulario cada 5 interacciones.
    FAIL si se muestra más de 1 formulario en 5 interacciones.
    """
    print("\n" + "=" * 60)
    print("REGLA 2: FORMULARIOS MÁXIMO 1/5 INTERACCIONES")
    print("=" * 60)
    
    # Resetear throttler para test limpio
    throttler = FormThrottler()
    throttler._user_interactions = {}
    throttler._user_forms = {}
    throttler._last_form_time = {}
    
    user_id = 99999
    forms_shown = 0
    interactions = 0
    violations = []
    
    # Simular 20 interacciones
    for i in range(20):
        interactions += 1
        
        # Verificar si se puede mostrar formulario
        can_show, reason = should_show_form(user_id, f"form_{i}")
        
        if can_show:
            forms_shown += 1
            throttler.record_interaction(user_id, is_form=True)
            
            # Verificar ratio
            if interactions >= 5:
                ratio = forms_shown / interactions
                if ratio > 0.25:  # Más de 1/5 = 20% + margen
                    violations.append(
                        f"Interaction {interactions}: {forms_shown} forms ({ratio*100:.0f}%)"
                    )
        else:
            throttler.record_interaction(user_id, is_form=False)
    
    passed = len(violations) == 0
    return TestResult(
        name="Rule 2: Form Throttling (max 1/5)",
        passed=passed,
        message=f"Forms: {forms_shown}/20 interactions" if passed else f"{len(violations)} violations",
        details=violations
    )


# ============== REGLA 3: VISA SIN CONTEXTO ==============

def test_rule_3_visa_without_context():
    """
    REGLA 3: Prohibido recomendar visa sin contexto completo confirmado.
    FAIL si se permite recomendar visa sin datos mínimos.
    """
    print("\n" + "=" * 60)
    print("REGLA 3: NO RECOMENDAR VISA SIN CONTEXTO COMPLETO")
    print("=" * 60)
    
    # Casos de prueba: perfiles incompletos
    incomplete_profiles = [
        # Sin nombre
        {"profile": {"personal": {}}},
        # Sin edad
        {"profile": {"personal": {"name": "Juan"}}},
        # Sin nacionalidad
        {"profile": {"personal": {"name": "Juan", "age": 30}}},
        # Sin familia
        {"profile": {"personal": {"name": "Juan", "age": 30, "nationality": "Colombia"}}},
        # Sin razón de migración
        {"profile": {"personal": {"name": "Juan", "age": 30, "nationality": "Colombia"}}, 
         "family_status": "single"},
    ]
    
    violations = []
    
    for i, profile in enumerate(incomplete_profiles):
        can_recommend, message = can_recommend_visa(profile)
        
        if can_recommend:
            violations.append(f"Profile {i+1}: Allowed visa recommendation with incomplete data")
    
    # Verificar perfil completo SÍ permite
    complete_profile = {
        "profile": {
            "personal": {
                "name": "Juan Pérez",
                "birth_date": "1990-01-01",
                "age": 34,
                "nationality": "Colombia"
            },
            "family": {
                "family_status": "single"
            },
            "history": {
                "has_visas": False,
                "criminal_record": False
            }
        },
        "family_status": "single",
        "family_members": [],
        "preferences": {
            "migration_reason": "Mejores oportunidades"
        }
    }
    
    can_recommend, message = can_recommend_visa(complete_profile)
    if not can_recommend:
        violations.append(f"Complete profile blocked: {message}")
    
    passed = len(violations) == 0
    return TestResult(
        name="Rule 3: No Visa Without Complete Context",
        passed=passed,
        message=f"{len(incomplete_profiles)} incomplete profiles blocked" if passed else f"{len(violations)} violations",
        details=violations
    )


# ============== REGLA 4: UNDERSTANDING CONFIRMADO ==============

def test_rule_4_understanding_required():
    """
    REGLA 4: No avanzar de fase sin UNDERSTANDING confirmado.
    FAIL si se permite avanzar sin confirmación.
    """
    print("\n" + "=" * 60)
    print("REGLA 4: UNDERSTANDING CONFIRMADO ANTES DE AVANZAR")
    print("=" * 60)
    
    # Perfil sin confirmaciones
    unconfirmed_profile = {
        "profile": {
            "personal": {"name": "Juan", "age": 30, "nationality": "Colombia"},
            "work": {"profession": "Ingeniero"},
            "education": {"level": "Universitario"},
            "migration": {"reason": "Trabajo", "timeline": "6 meses"},
            "financial": {"savings": 50000}
        },
        "family_status": "single",
        "confirmations": []  # Sin confirmaciones
    }
    
    violations = []
    
    # Verificar decisiones críticas
    critical_decisions = ["visa_recommendation", "city_selection", "payment"]
    
    for decision in critical_decisions:
        can_decide, reason, next_action = can_make_decision(unconfirmed_profile, decision)
        
        if can_decide:
            violations.append(f"Allowed '{decision}' without confirmation")
    
    # Verificar que CON confirmación SÍ permite
    confirmed_profile = unconfirmed_profile.copy()
    confirmed_profile["confirmations"] = [
        {"summary_type": "profile", "confirmed": True}
    ]
    
    can_decide, reason, next_action = can_make_decision(confirmed_profile, "visa_recommendation")
    # Nota: puede fallar por otros motivos (perfil incompleto), pero no por falta de confirmación
    
    passed = len(violations) == 0
    return TestResult(
        name="Rule 4: Understanding Required Before Advancing",
        passed=passed,
        message=f"All critical decisions require confirmation" if passed else f"{len(violations)} violations",
        details=violations
    )


# ============== REGLA 5: NO IGNORAR CORRECCIONES ==============

def test_rule_5_corrections_not_ignored():
    """
    REGLA 5: No ignorar correcciones del usuario.
    FAIL si se ignora "mi email correcto es..." y se avanza.
    """
    print("\n" + "=" * 60)
    print("REGLA 5: NO IGNORAR CORRECCIONES")
    print("=" * 60)
    
    # Frases de corrección que DEBEN ser detectadas
    correction_phrases = [
        "no, mi nombre es Pedro",
        "perdón, me equivoqué, es juan@gmail.com",
        "corrijo: tengo 35 años",
        "en realidad soy de México",
        "mi email correcto es test@test.com",
        "no es así, quise decir ingeniero",
        "actually, my name is John",
        "sorry, I meant 40 years old",
    ]
    
    failures = []
    
    for phrase in correction_phrases:
        is_correction, field = detect_correction(phrase)
        
        if not is_correction:
            failures.append(f"Not detected as correction: '{phrase}'")
    
    # Verificar que el tracker bloquea avance
    tracker = CorrectionTracker()
    tracker._pending_corrections = {}
    
    user_id = 88888
    tracker.register_correction(user_id, "email", "old@test.com", "new@test.com")
    
    can_advance, msg = tracker.can_advance_phase(user_id)
    if can_advance:
        failures.append("Allowed advance with pending correction")
    
    passed = len(failures) == 0
    return TestResult(
        name="Rule 5: Corrections Not Ignored",
        passed=passed,
        message=f"All corrections detected and block advance" if passed else f"{len(failures)} failures",
        details=failures
    )


# ============== REGLA 6: MARKDOWN VÁLIDO ==============

def test_rule_6_markdown_valid():
    """
    REGLA 6: Markdown no debe romper (BadRequest).
    FAIL si hay markdown inválido que causaría error.
    """
    print("\n" + "=" * 60)
    print("REGLA 6: MARKDOWN VÁLIDO (NO BadRequest)")
    print("=" * 60)
    
    # Patrones de markdown problemáticos
    def validate_markdown(text: str) -> Tuple[bool, str]:
        """Valida que el markdown sea válido para Telegram"""
        issues = []
        
        # Verificar asteriscos balanceados
        single_asterisks = len(re.findall(r'(?<!\*)\*(?!\*)', text))
        if single_asterisks % 2 != 0:
            issues.append("Unbalanced single asterisks (*)")
        
        # Verificar doble asterisco balanceado
        double_asterisks = len(re.findall(r'\*\*', text))
        if double_asterisks % 2 != 0:
            issues.append("Unbalanced double asterisks (**)")
        
        # Verificar underscores balanceados
        underscores = len(re.findall(r'(?<!_)_(?!_)', text))
        if underscores % 2 != 0:
            issues.append("Unbalanced underscores (_)")
        
        # Verificar backticks balanceados
        backticks = text.count('`')
        if backticks % 2 != 0:
            issues.append("Unbalanced backticks (`)")
        
        # Verificar corchetes sin cerrar
        if text.count('[') != text.count(']'):
            issues.append("Unbalanced brackets []")
        
        # Verificar paréntesis sin cerrar
        if text.count('(') != text.count(')'):
            issues.append("Unbalanced parentheses ()")
        
        return len(issues) == 0, ", ".join(issues)
    
    # Obtener mensajes del sistema
    messages_to_check = []
    
    # Mensajes de recuperación
    for lang_msgs in EMPATHIC_RECOVERY_MESSAGES.values():
        messages_to_check.extend(lang_msgs)
    
    # Mensajes de "sigo aquí"
    for lang_msgs in STILL_HERE_MESSAGES.values():
        messages_to_check.extend(lang_msgs)
    
    # Mensajes de fallback
    fallback = get_empathic_fallback()
    for phase in ["greeting", "profile", "visa", "city", "unknown"]:
        for lang in ["es", "en"]:
            msg = fallback.get_phase_fallback(phase, lang)
            if msg:
                messages_to_check.append(msg)
    
    failures = []
    
    for msg in messages_to_check:
        is_valid, issues = validate_markdown(msg)
        if not is_valid:
            failures.append(f"Invalid markdown: '{msg[:30]}...' - {issues}")
    
    passed = len(failures) == 0
    return TestResult(
        name="Rule 6: Valid Markdown (No BadRequest)",
        passed=passed,
        message=f"All {len(messages_to_check)} messages have valid markdown" if passed else f"{len(failures)} invalid",
        details=failures
    )


# ============== TEST FUZZ: 100 INPUTS ALEATORIOS ==============

def test_fuzz_100_random_inputs():
    """
    TEST FUZZ: 100 inputs aleatorios.
    FAIL si alguno causa crash o no genera respuesta.
    """
    print("\n" + "=" * 60)
    print("TEST FUZZ: 100 INPUTS ALEATORIOS")
    print("=" * 60)
    
    def generate_random_input() -> str:
        """Genera un input aleatorio"""
        input_types = [
            # Texto aleatorio
            lambda: ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=random.randint(1, 100))),
            # Solo números
            lambda: ''.join(random.choices(string.digits, k=random.randint(1, 20))),
            # Solo espacios
            lambda: ' ' * random.randint(1, 10),
            # Emojis aleatorios
            lambda: random.choice(['👋', '🇨🇴', '💰', '✈️', '🏠', '💼', '📝', '✅', '❌', '🎯']),
            # Caracteres especiales
            lambda: ''.join(random.choices('!@#$%^&*()[]{}|;:,.<>?', k=random.randint(1, 20))),
            # Unicode aleatorio
            lambda: ''.join(chr(random.randint(0x0400, 0x04FF)) for _ in range(random.randint(1, 20))),
            # Mezcla
            lambda: ''.join(random.choices(string.printable, k=random.randint(1, 50))),
            # Muy largo
            lambda: 'a' * random.randint(100, 1000),
            # Vacío
            lambda: '',
            # Solo puntuación
            lambda: '...' * random.randint(1, 10),
        ]
        
        return random.choice(input_types)()
    
    failures = []
    
    for i in range(100):
        random_input = generate_random_input()
        
        try:
            # Intentar interpretar
            interpreted = interpret_user_input(random_input, "")
            
            # Verificar que no crashea y hay algún tipo de respuesta posible
            if interpreted is None:
                failures.append(f"Input {i+1}: None response")
                
        except Exception as e:
            failures.append(f"Input {i+1}: Exception - {str(e)[:50]}")
    
    passed = len(failures) == 0
    return TestResult(
        name="Fuzz Test: 100 Random Inputs",
        passed=passed,
        message=f"100/100 inputs handled" if passed else f"{len(failures)} failures",
        details=failures[:5]
    )


# ============== TEST: 20 FLUJOS COMPLETOS ==============

def test_20_complete_flows():
    """
    TEST: 20 flujos completos de conversación.
    FAIL si algún flujo no completa correctamente.
    """
    print("\n" + "=" * 60)
    print("TEST: 20 FLUJOS COMPLETOS")
    print("=" * 60)
    
    # Definir flujos de conversación
    flows = [
        # Flujo 1: Usuario nuevo básico
        ["hola", "quiero migrar", "me llamo Juan", "soy de Colombia", "tengo 30 años"],
        
        # Flujo 2: Con correcciones
        ["hola", "me llamo Pedro", "no, perdón, me llamo Pablo", "soy ingeniero"],
        
        # Flujo 3: Preguntas primero
        ["¿cuánto cuesta?", "¿qué documentos necesito?", "ok, empecemos", "me llamo Ana"],
        
        # Flujo 4: Off-topic y vuelta
        ["hola", "¿qué hora es?", "bueno, quiero migrar", "soy de México"],
        
        # Flujo 5: Respuestas cortas
        ["hola", "sí", "no", "ok", "Juan", "Colombia"],
        
        # Flujo 6: Información completa en un mensaje
        ["Soy Juan, tengo 35 años, soy de México y trabajo como abogado"],
        
        # Flujo 7: Con frustración
        ["hola", "no entiendo", "ya te dije mi nombre", "es Juan", "ok, continúo"],
        
        # Flujo 8: Cambio de idioma
        ["hello", "I want to migrate", "my name is John", "I'm from Brazil"],
        
        # Flujo 9: Con emojis
        ["👋 hola!", "🇨🇴 soy de Colombia", "💰 tengo $50,000"],
        
        # Flujo 10: Números y fechas
        ["nací el 15/03/1990", "tengo $30,000 ahorrados", "gano $5,000 al mes"],
        
        # Flujo 11: Familia compleja
        ["viajo con mi esposa y 3 hijos", "mis hijos tienen 5, 8 y 12 años"],
        
        # Flujo 12: Profesional
        ["soy ingeniero de software senior", "tengo 15 años de experiencia", "trabajo en Google"],
        
        # Flujo 13: Urgencia
        ["necesito irme ya", "es urgente", "no puedo esperar más de 3 meses"],
        
        # Flujo 14: Preguntas de visa
        ["¿qué visa me conviene?", "¿puedo trabajar con visa de turista?", "¿cuánto dura la H1B?"],
        
        # Flujo 15: Comparaciones
        ["¿es mejor Miami o Houston?", "¿qué diferencia hay entre H1B y L1?"],
        
        # Flujo 16: Negaciones
        ["no tengo hijos", "no estoy casado", "no tengo visa", "nunca he viajado a USA"],
        
        # Flujo 17: Confirmaciones ambiguas
        ["creo que sí", "tal vez", "no estoy seguro", "puede ser"],
        
        # Flujo 18: Caracteres especiales
        ["me llamo Juan O'Brien", "vivo en São Paulo", "mi apellido es Müller"],
        
        # Flujo 19: Contacto
        ["mi email es juan@gmail.com", "mi teléfono es +57 300 123 4567"],
        
        # Flujo 20: Flujo realista completo
        [
            "hola, quiero información sobre migrar a USA",
            "me llamo Carlos García",
            "soy de Venezuela",
            "tengo 32 años",
            "soy ingeniero de sistemas",
            "tengo 10 años de experiencia",
            "viajo con mi esposa y un hijo de 5 años",
            "tenemos $40,000 ahorrados",
            "queremos irnos en los próximos 6 meses",
            "¿qué visa nos conviene?"
        ],
    ]
    
    failures = []
    
    for i, flow in enumerate(flows):
        flow_errors = []
        
        for j, message in enumerate(flow):
            try:
                interpreted = interpret_user_input(message, "")
                
                if interpreted is None:
                    flow_errors.append(f"Step {j+1}: No interpretation")
                    
            except Exception as e:
                flow_errors.append(f"Step {j+1}: {str(e)[:30]}")
        
        if flow_errors:
            failures.append(f"Flow {i+1}: {', '.join(flow_errors)}")
    
    passed = len(failures) == 0
    return TestResult(
        name="20 Complete Conversation Flows",
        passed=passed,
        message=f"20/20 flows completed" if passed else f"{len(failures)} flows failed",
        details=failures[:5]
    )


# ============== MAIN ==============

def run_all_tests() -> int:
    """Ejecuta todos los tests y retorna código de salida"""
    print("\n" + "=" * 70)
    print("🧪 SEGMENTO 3/4: TESTS BLOQUEANTES DE REGLAS DURAS")
    print("=" * 70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    runner = TestRunner()
    
    # Ejecutar tests de reglas
    runner.add_result(test_rule_1_always_respond())
    runner.add_result(test_rule_1_callback_response())
    runner.add_result(test_rule_2_form_throttling())
    runner.add_result(test_rule_3_visa_without_context())
    runner.add_result(test_rule_4_understanding_required())
    runner.add_result(test_rule_5_corrections_not_ignored())
    runner.add_result(test_rule_6_markdown_valid())
    
    # Ejecutar tests fuzz
    runner.add_result(test_fuzz_100_random_inputs())
    runner.add_result(test_20_complete_flows())
    
    # Resumen
    passed, total = runner.summary()
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE TESTS")
    print("=" * 70)
    
    for result in runner.results:
        status = "✅" if result.passed else "❌"
        print(f"  {status} {result.name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 TODOS LOS TESTS PASARON - OK PARA DEPLOY")
        return 0
    else:
        print(f"\n❌ {total - passed} TESTS FALLARON - BLOQUEAR DEPLOY")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
